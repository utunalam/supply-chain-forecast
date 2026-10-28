
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
import csv

from database import SessionLocal
from models import InventoryRecord, ProductMapping, SalesRecord


# SYNTHETIC - development/testing only
LEAD_TIME_DAYS = 7
SAFETY_STOCK_DAYS = 3
DEMAND_WINDOW_DAYS = 14

# Explicitly classified as slow-moving based on the user's assessment.
SLOW_MOVING_INVENTORY_IDS = {"929004100109"}

BACKEND_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BACKEND_DIR.parent / "reports"

OUTPUT_FILE = (
    REPORTS_DIR / "replenishment_recommendations_SYNTHETIC.csv"
)
UNMATCHED_FILE = (
    REPORTS_DIR / "unmatched_replenishment_products_SYNTHETIC.csv"
)


def to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    return None


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()

    try:
        mappings = (
            db.query(ProductMapping)
            .filter(ProductMapping.review_status == "APPROVED")
            .all()
        )

        inventory_records = db.query(InventoryRecord).all()

        completed_sales = (
            db.query(SalesRecord)
            .filter(SalesRecord.order_status == "COMPLETED")
            .all()
        )

        if not completed_sales:
            print("No completed sales found. No report was generated.")
            return

        dated_sales = [
            (sale, to_date(sale.order_date))
            for sale in completed_sales
        ]
        dated_sales = [
            (sale, sale_date)
            for sale, sale_date in dated_sales
            if sale_date is not None
        ]

        if not dated_sales:
            print("Completed sales have no usable order dates.")
            return

        latest_sales_date = max(
            sale_date for _, sale_date in dated_sales
        )
        window_start = latest_sales_date - timedelta(
            days=DEMAND_WINDOW_DAYS - 1
        )

        sales_units = defaultdict(float)

        for sale, sale_date in dated_sales:
            if window_start <= sale_date <= latest_sales_date:
                if sale.sales_item_id:
                    sales_id = str(sale.sales_item_id).strip()
                    sales_units[sales_id] += float(
                        sale.item_quantity or 0
                    )

        inventory_by_item = defaultdict(list)

        for record in inventory_records:
            if record.inventory_item_id:
                inventory_id = str(
                    record.inventory_item_id
                ).strip()
                inventory_by_item[inventory_id].append(record)

        # Select the latest dated inventory snapshot for each product.
        latest_stock_by_item = {}
        inventory_review_by_item = {}

        for inventory_id, records in inventory_by_item.items():
            dated_records = [
                (record, to_date(record.snapshot_date))
                for record in records
            ]
            dated_records = [
                (record, snapshot_date)
                for record, snapshot_date in dated_records
                if snapshot_date is not None
            ]

            if not dated_records:
                inventory_review_by_item[inventory_id] = (
                    "REVIEW: no snapshot dates available"
                )
                continue

            latest_snapshot_date = max(
                snapshot_date
                for _, snapshot_date in dated_records
            )

            latest_records = [
                record
                for record, snapshot_date in dated_records
                if snapshot_date == latest_snapshot_date
            ]

            if len(latest_records) > 1:
                inventory_review_by_item[inventory_id] = (
                    "REVIEW: multiple records share the latest "
                    "snapshot date; stock is ambiguous"
                )
                continue

            latest_record = latest_records[0]

            latest_stock_by_item[inventory_id] = {
                "quantity": float(latest_record.available_qty or 0),
                "snapshot_date": latest_snapshot_date,
                "record_count": len(records),
            }

            if len(records) > 1:
                inventory_review_by_item[inventory_id] = (
                    "Multiple dated snapshots found; latest date selected"
                )
            else:
                inventory_review_by_item[inventory_id] = (
                    "One dated inventory record found"
                )

        report_rows = []
        mapped_sales_ids = set()

        for mapping in mappings:
            inventory_id = str(
                mapping.inventory_item_id
            ).strip()
            sales_id = str(mapping.sales_item_id).strip()
            mapped_sales_ids.add(sales_id)

            stock_info = latest_stock_by_item.get(inventory_id)
            review_note = inventory_review_by_item.get(
                inventory_id,
                "REVIEW: no inventory record found",
            )

            units_sold = sales_units.get(sales_id, 0.0)
            average_daily_demand = (
                units_sold / DEMAND_WINDOW_DAYS
            )

            reorder_point = average_daily_demand * (
                LEAD_TIME_DAYS + SAFETY_STOCK_DAYS
            )

            is_slow_moving = (
                inventory_id in SLOW_MOVING_INVENTORY_IDS
            )

            if stock_info is None:
                current_stock = None
                snapshot_date = None
                snapshot_count = len(
                    inventory_by_item.get(inventory_id, [])
                )
                suggested_replenishment = None
                recommendation = "REVIEW INVENTORY DATA"

            else:
                current_stock = stock_info["quantity"]
                snapshot_date = stock_info["snapshot_date"]
                snapshot_count = stock_info["record_count"]

                if "REVIEW: multiple records share" in review_note:
                    suggested_replenishment = None
                    recommendation = (
                        "REVIEW: ambiguous latest snapshot"
                    )

                else:
                    suggested_replenishment = max(
                        0.0, reorder_point - current_stock
                    )

                    if is_slow_moving and units_sold == 0:
                        recommendation = (
                            "SLOW-MOVING: review longer demand history"
                        )
                        review_note = (
                            "Slow-moving product; no completed sales "
                            "during the 14-day demand window. Review a "
                            "longer historical period before confirming "
                            "replenishment needs. "
                            + review_note
                        )

                    elif average_daily_demand == 0:
                        recommendation = (
                            "REVIEW: no completed demand in window"
                        )

                    elif current_stock <= reorder_point:
                        recommendation = "REPLENISHMENT REVIEW"

                    else:
                        recommendation = (
                            "Stock above provisional reorder point"
                        )

            report_rows.append({
                "data_label": (
                    "SYNTHETIC - development/testing only"
                ),
                "demand_window_start": window_start.isoformat(),
                "demand_window_end": latest_sales_date.isoformat(),
                "inventory_item_id": inventory_id,
                "sales_item_id": sales_id,
                "inventory_description": (
                    mapping.inventory_description or ""
                ),
                "sales_description": (
                    mapping.sales_description or ""
                ),
                "completed_units_in_window": round(
                    units_sold, 4
                ),
                "average_daily_demand": round(
                    average_daily_demand, 4
                ),
                "lead_time_days_assumed": LEAD_TIME_DAYS,
                "safety_stock_days_assumed": SAFETY_STOCK_DAYS,
                "provisional_reorder_point_units": round(
                    reorder_point, 4
                ),
                "available_stock_latest_snapshot": (
                    round(current_stock, 4)
                    if current_stock is not None
                    else ""
                ),
                "latest_snapshot_date": (
                    snapshot_date.isoformat()
                    if snapshot_date is not None
                    else ""
                ),
                "inventory_rows_found": snapshot_count,
                "suggested_replenishment_units_provisional": (
                    round(suggested_replenishment, 4)
                    if suggested_replenishment is not None
                    else ""
                ),
                "recommendation": recommendation,
                "review_note": review_note,
            })

        report_fields = [
            "data_label",
            "demand_window_start",
            "demand_window_end",
            "inventory_item_id",
            "sales_item_id",
            "inventory_description",
            "sales_description",
            "completed_units_in_window",
            "average_daily_demand",
            "lead_time_days_assumed",
            "safety_stock_days_assumed",
            "provisional_reorder_point_units",
            "available_stock_latest_snapshot",
            "latest_snapshot_date",
            "inventory_rows_found",
            "suggested_replenishment_units_provisional",
            "recommendation",
            "review_note",
        ]

        with OUTPUT_FILE.open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=report_fields
            )
            writer.writeheader()
            writer.writerows(report_rows)

        unmatched_rows = []

        for sales_id, units_sold in sorted(sales_units.items()):
            if sales_id not in mapped_sales_ids:
                unmatched_rows.append({
                    "data_label": (
                        "SYNTHETIC - development/testing only"
                    ),
                    "sales_item_id": sales_id,
                    "completed_units_in_window": round(
                        units_sold, 4
                    ),
                    "review_note": (
                        "No approved inventory mapping; "
                        "replenishment cannot be calculated safely"
                    ),
                })

        with UNMATCHED_FILE.open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            fields = [
                "data_label",
                "sales_item_id",
                "completed_units_in_window",
                "review_note",
            ]
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(unmatched_rows)

        print("=" * 65)
        print("SYNTHETIC REPLENISHMENT REPORT")
        print("SYNTHETIC - development/testing only")
        print("=" * 65)
        print(
            f"Demand window: {window_start} to {latest_sales_date}"
        )
        print(f"Lead time assumed: {LEAD_TIME_DAYS} days")
        print(f"Safety stock assumed: {SAFETY_STOCK_DAYS} days")
        print(f"Approved mappings processed: {len(report_rows)}")
        print(f"Unmatched sales products: {len(unmatched_rows)}")
        print(f"Replenishment report: {OUTPUT_FILE}")
        print(f"Unmatched products report: {UNMATCHED_FILE}")
        print("Inventory selected by latest snapshot date.")
        print("Ambiguous latest snapshots are flagged.")
        print("Adria is classified as slow-moving.")
        print("Database records were not modified.")
        print("Testing only; not for purchasing decisions.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
