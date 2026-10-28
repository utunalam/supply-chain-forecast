
import csv
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from database import SessionLocal
from models import ProductMapping, SalesRecord

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_ROOT / "reports"

TEST_DAYS = 7
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
            .order_by(ProductMapping.sales_item_id)
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
            raise ValueError("No dated positive completed sales found.")

        # Reserve the latest 7 calendar days for testing.
        latest_date = max(
            sale.order_date.date() for sale in dated_sales
        )
        test_start = latest_date - timedelta(days=TEST_DAYS - 1)

        training_sales = [
            sale for sale in dated_sales
            if sale.order_date.date() < test_start
        ]

        if not training_sales:
            raise ValueError(
                "No earlier completed sales are available for training."
            )

        training_start = min(
            sale.order_date.date() for sale in training_sales
        )
        training_end = test_start - timedelta(days=1)
        training_days = (test_start - training_start).days

        if training_days <= 0:
            raise ValueError("The training period has no calendar days.")

        # Sum completed units by product in the training period.
        training_totals = defaultdict(int)

        for sale in training_sales:
            training_totals[sale.sales_item_id] += sale.item_quantity

        # Sum completed units by product in the test period.
        test_totals = defaultdict(int)

        for sale in dated_sales:
            sale_date = sale.order_date.date()

            if test_start <= sale_date <= latest_date:
                test_totals[sale.sales_item_id] += sale.item_quantity

        report_rows = []
        full_precision_errors = []

        for mapping in mappings:
            sales_id = mapping.sales_item_id

            training_units = training_totals.get(sales_id, 0)
            actual_units = test_totals.get(sales_id, 0)

            # Baseline: training-period average daily demand.
            average_daily_demand = training_units / training_days
            forecast_units = average_daily_demand * TEST_DAYS

            # Keep full precision for calculations.
            absolute_error = abs(forecast_units - actual_units)
            full_precision_errors.append(absolute_error)

            report_rows.append({
                "data_label": DATA_LABEL,
                "inventory_item_id": mapping.inventory_item_id,
                "sales_item_id": sales_id,
                "product_description": mapping.sales_description,
                "training_start": training_start.isoformat(),
                "training_end": training_end.isoformat(),
                "training_calendar_days": training_days,
                "test_start": test_start.isoformat(),
                "test_end": latest_date.isoformat(),
                "test_calendar_days": TEST_DAYS,
                "training_completed_units": training_units,
                "average_daily_demand": round(
                    average_daily_demand, 4
                ),
                "forecast_test_period_units": round(forecast_units, 4),
                "actual_test_period_units": actual_units,
                "absolute_error_units": round(absolute_error, 4),
                "overall_mae_units": "",
                "evaluation_note": (
                    "Small synthetic sample; interpret cautiously"
                ),
            })

        # Calculate MAE from unrounded errors, then round for display.
        mae = sum(full_precision_errors) / len(full_precision_errors)
        displayed_mae = round(mae, 4)

        for row in report_rows:
            row["overall_mae_units"] = displayed_mae

        output_path = (
            REPORT_DIR / "baseline_forecast_evaluation_SYNTHETIC.csv"
        )

        write_csv(
            output_path,
            list(report_rows[0].keys()),
            report_rows,
        )

        print("=" * 65)
        print("SYNTHETIC BASELINE FORECAST EVALUATION")
        print(DATA_LABEL)
        print("=" * 65)
        print(f"Training period: {training_start} to {training_end}")
        print(f"Test period:     {test_start} to {latest_date}")
        print(f"Training days:   {training_days}")
        print(f"Test days:       {TEST_DAYS}")
        print()

        print("PRODUCT-LEVEL RESULTS")
        print("-" * 65)

        for row in report_rows:
            print(
                f"Sales ID: {row['sales_item_id']}\n"
                f"  Product:         {row['product_description']}\n"
                f"  Training units:  {row['training_completed_units']}\n"
                f"  Daily average:   {row['average_daily_demand']:.4f}\n"
                f"  Forecast units:  {row['forecast_test_period_units']:.4f}\n"
                f"  Actual units:    {row['actual_test_period_units']}\n"
                f"  Absolute error:  {row['absolute_error_units']:.4f}\n"
            )

        print("-" * 65)
        print(
            "Overall MAE: "
            f"{mae:.4f} units per product over the "
            f"{TEST_DAYS}-day test period"
        )
        print(f"Products evaluated: {len(report_rows)}")
        print(f"CSV report: {output_path}")
        print("Database records were not modified.")
        print("Development/testing only; not for purchasing decisions.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
