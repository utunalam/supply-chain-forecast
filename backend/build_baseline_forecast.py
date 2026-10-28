
import csv
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from database import SessionLocal
from models import ProductMapping, SalesRecord

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_ROOT / "reports"

HISTORY_DAYS = 14
FORECAST_DAYS = 7
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

        completed_sales = (
            db.query(SalesRecord)
            .filter_by(order_status="COMPLETED")
            .all()
        )

        dated_sales = [
            sale for sale in completed_sales
            if sale.order_date is not None
            and sale.sales_item_id
            and sale.item_quantity is not None
            and sale.item_quantity > 0
        ]

        if not mappings:
            raise ValueError("No approved product mappings found.")

        if not dated_sales:
            raise ValueError("No positive, dated completed sales found.")

        # Use the latest completed order date as the history end date.
        history_end = max(
            sale.order_date.date() for sale in dated_sales
        )
        history_start = history_end - timedelta(
            days=HISTORY_DAYS - 1
        )

        # Prepare completed sales totals by product and date.
        daily_sales = defaultdict(int)

        for sale in dated_sales:
            sale_date = sale.order_date.date()

            if history_start <= sale_date <= history_end:
                daily_sales[
                    (sale.sales_item_id, sale_date)
                ] += sale.item_quantity

        report_rows = []

        for mapping in mappings:
            sales_id = mapping.sales_item_id
            total_units = 0

            # Include every calendar day, including zero-sale days.
            for day_number in range(HISTORY_DAYS):
                day = history_start + timedelta(days=day_number)
                units = daily_sales.get((sales_id, day), 0)
                total_units += units

                report_rows.append({
                    "data_label": DATA_LABEL,
                    "record_type": "DAILY_HISTORY",
                    "inventory_item_id": mapping.inventory_item_id,
                    "sales_item_id": sales_id,
                    "product_description": mapping.sales_description,
                    "date": day.isoformat(),
                    "completed_units_sold": units,
                    "average_daily_demand": "",
                    "forecast_units": "",
                    "forecast_method": "",
                })

            average_daily_demand = total_units / HISTORY_DAYS

            # A simple baseline: repeat the average daily demand.
            for day_number in range(1, FORECAST_DAYS + 1):
                forecast_date = history_end + timedelta(
                    days=day_number
                )

                report_rows.append({
                    "data_label": DATA_LABEL,
                    "record_type": "BASELINE_FORECAST",
                    "inventory_item_id": mapping.inventory_item_id,
                    "sales_item_id": sales_id,
                    "product_description": mapping.sales_description,
                    "date": forecast_date.isoformat(),
                    "completed_units_sold": "",
                    "average_daily_demand": round(
                        average_daily_demand, 4
                    ),
                    "forecast_units": round(
                        average_daily_demand, 4
                    ),
                    "forecast_method": "14-day average baseline",
                })

        output_path = (
            REPORT_DIR / "baseline_forecast_SYNTHETIC.csv"
        )

        fieldnames = [
            "data_label",
            "record_type",
            "inventory_item_id",
            "sales_item_id",
            "product_description",
            "date",
            "completed_units_sold",
            "average_daily_demand",
            "forecast_units",
            "forecast_method",
        ]

        write_csv(output_path, fieldnames, report_rows)

        print("Synthetic baseline forecast generated.")
        print(f"History window: {history_start} to {history_end}")
        print(f"History days: {HISTORY_DAYS}")
        print(f"Forecast days: {FORECAST_DAYS}")
        print(f"Approved mappings: {len(mappings)}")
        print(f"Output: {output_path}")
        print("Database records were not modified.")
        print("Development/testing only; not for purchasing decisions.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
