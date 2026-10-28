
import csv
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from database import SessionLocal
from models import InventoryRecord, ProductMapping, SalesRecord

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_ROOT / "reports"
WINDOW_DAYS = 14
DATA_LABEL = "SYNTHETIC - development/testing only"


def write_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()

    try:
        mappings = (
            db.query(ProductMapping)
            .filter_by(review_status="APPROVED")
            .order_by(ProductMapping.inventory_item_id)
            .all()
        )

        inventory_records = db.query(InventoryRecord).all()
        sales_records = (
            db.query(SalesRecord)
            .filter_by(order_status="COMPLETED")
            .all()
        )

        if not mappings:
            raise ValueError("No approved product mappings found.")

        dated_completed_sales = [
            sale for sale in sales_records
            if sale.order_date is not None
        ]

        if not dated_completed_sales:
            raise ValueError(
                "No dated COMPLETED sales are available for forecasting."
            )

        # Anchor the sample window to the latest completed order date.
        end_date = max(
            sale.order_date.date()
            for sale in dated_completed_sales
        )
        start_date = end_date - timedelta(days=WINDOW_DAYS - 1)

        # Aggregate available stock by inventory ID.
        # Multiple inventory rows for an ID are summed.
        stock_by_inventory_id = defaultdict(int)
        stock_row_count = defaultdict(int)

        for record in inventory_records:
            stock_by_inventory_id[record.inventory_item_id] += (
                record.available_qty
            )
            stock_row_count[record.inventory_item_id] += 1

        # Build the list of completed sales inside the 14-day window.
        window_sales = [
            sale for sale in dated_completed_sales
            if start_date <= sale.order_date.date() <= end_date
        ]

        # Aggregate sales quantity by sales item ID.
        quantity_by_sales_id = defaultdict(int)
        for sale in window_sales:
            if sale.sales_item_id:
                quantity_by_sales_id[sale.sales_item_id] += (
                    sale.item_quantity
                )

        # Approved sales IDs determine which products can be matched.
        approved_sales_ids = {
            mapping.sales_item_id for mapping in mappings
        }

        # Report approved product mappings, including products with
        # no completed sales during the observation window.
        demand_rows = []

        for mapping in mappings:
            sales_id = mapping.sales_item_id
            inventory_id = mapping.inventory_item_id

            units_sold = quantity_by_sales_id.get(sales_id, 0)
            average_daily_demand = units_sold / WINDOW_DAYS
            available_stock = stock_by_inventory_id.get(
                inventory_id, 0
            )

            if units_sold > 0:
                stock_coverage_days = (
                    available_stock / average_daily_demand
                )
                coverage_text = round(stock_coverage_days, 2)
                demand_status = "Demand observed"
            else:
                coverage_text = "N/A - no completed demand in window"
                demand_status = "No completed demand observed"

            demand_rows.append({
                "data_label": DATA_LABEL,
                "window_start": start_date.isoformat(),
                "window_end": end_date.isoformat(),
                "window_days": WINDOW_DAYS,
                "inventory_item_id": inventory_id,
                "sales_item_id": sales_id,
                "inventory_description": mapping.inventory_description,
                "sales_description": mapping.sales_description,
                "inventory_rows_aggregated": stock_row_count.get(
                    inventory_id, 0
                ),
                "available_stock": available_stock,
                "completed_units_sold": units_sold,
                "average_daily_demand": round(
                    average_daily_demand, 4
                ),
                "estimated_stock_coverage_days": coverage_text,
                "demand_status": demand_status,
            })

        demand_path = (
            REPORT_DIR / "demand_stock_coverage_SYNTHETIC.csv"
        )

        write_csv(
            demand_path,
            list(demand_rows[0].keys()),
            demand_rows,
        )

        # Keep unmatched completed sales separate.
        # Group by original sales ID, SKU, and product description.
        unmatched_totals = defaultdict(
            lambda: {"units": 0, "rows": 0}
        )

        for sale in window_sales:
            sales_id = sale.sales_item_id or ""
            if sales_id in approved_sales_ids:
                continue

            key = (
                sales_id,
                sale.product_sku or "",
                sale.item_name or "",
            )
            unmatched_totals[key]["units"] += sale.item_quantity
            unmatched_totals[key]["rows"] += 1

        unmatched_rows = []

        for (sales_id, sku, name), totals in sorted(
            unmatched_totals.items()
        ):
            unmatched_rows.append({
                "data_label": DATA_LABEL,
                "window_start": start_date.isoformat(),
                "window_end": end_date.isoformat(),
                "sales_item_id": sales_id,
                "product_sku": sku,
                "item_name": name,
                "completed_order_rows": totals["rows"],
                "completed_units_sold": totals["units"],
                "mapping_status": "UNMATCHED - manual review required",
            })

        unmatched_path = (
            REPORT_DIR / "unmatched_completed_sales_SYNTHETIC.csv"
        )

        unmatched_fields = [
            "data_label",
            "window_start",
            "window_end",
            "sales_item_id",
            "product_sku",
            "item_name",
            "completed_order_rows",
            "completed_units_sold",
            "mapping_status",
        ]

        write_csv(
            unmatched_path,
            unmatched_fields,
            unmatched_rows,
        )

        print("Synthetic demand report generated.")
        print(f"Observation window: {start_date} to {end_date}")
        print(f"Calendar days: {WINDOW_DAYS}")
        print(f"Approved mappings reported: {len(demand_rows)}")
        print(f"Unmatched products reported: {len(unmatched_rows)}")
        print(f"Demand report: {demand_path}")
        print(f"Unmatched sales report: {unmatched_path}")
        print("No database records were changed.")
        print("Development/testing data only; not for purchasing decisions.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
