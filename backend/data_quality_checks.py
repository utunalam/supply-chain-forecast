
import csv
from collections import Counter
from datetime import date
from pathlib import Path

from database import SessionLocal
from models import InventoryRecord, ProductMapping, SalesRecord

DATA_LABEL = "SYNTHETIC - development/testing only"

EXPECTED_SALES_STATUSES = {
    "COMPLETED",
    "CANCELLED",
    "IN_PROGRESS",
    "BACK_ORDERED",
    "IN_TRANSIT",
}


def main():
    db = SessionLocal()

    try:
        inventory = db.query(InventoryRecord).all()
        sales = db.query(SalesRecord).all()
        mappings = db.query(ProductMapping).all()

        results = []

        def add_result(category, check, issues, details):
            results.append({
                "data_label": DATA_LABEL,
                "category": category,
                "check": check,
                "issues_found": issues,
                "result": "PASS" if issues == 0 else "REVIEW",
                "details": details,
            })

        # 1. DATA VALIDATION
        missing_inventory = sum(
            not r.inventory_item_id or not r.item_description
            or r.available_qty is None
            for r in inventory
        )
        negative_stock = sum(
            r.available_qty is not None and r.available_qty < 0
            for r in inventory
        )
        missing_sales = sum(
            not r.sales_item_id or r.order_date is None
            or r.item_quantity is None
            for r in sales
        )
        negative_sales = sum(
            r.item_quantity is not None and r.item_quantity < 0
            for r in sales
        )

        add_result(
            "Data validation",
            "Missing required inventory fields",
            missing_inventory,
            "Checks item ID, description and available quantity.",
        )
        add_result(
            "Data validation",
            "Negative inventory quantities",
            negative_stock,
            "Negative stock requires investigation.",
        )
        add_result(
            "Data validation",
            "Missing required sales fields",
            missing_sales,
            "Checks sales item ID, order date and quantity.",
        )
        add_result(
            "Data validation",
            "Negative sales quantities",
            negative_sales,
            "Negative quantities require investigation.",
        )

        # 2. PRODUCT MAPPING
        inventory_ids = {
            r.inventory_item_id for r in inventory if r.inventory_item_id
        }
        sales_ids = {
            r.sales_item_id for r in sales if r.sales_item_id
        }

        invalid_approved = sum(
            m.review_status == "APPROVED"
            and (
                m.inventory_item_id not in inventory_ids
                or m.sales_item_id not in sales_ids
            )
            for m in mappings
        )

        pending = sum(m.review_status == "PENDING" for m in mappings)

        approved_sales_ids = {
            m.sales_item_id
            for m in mappings
            if m.review_status == "APPROVED"
        }

        unmatched_sales_ids = {
            r.sales_item_id
            for r in sales
            if r.sales_item_id
            and r.order_status
            and r.order_status.strip().upper() == "COMPLETED"
            and r.sales_item_id not in approved_sales_ids
        }

        add_result(
            "Product mapping",
            "Invalid approved mapping references",
            invalid_approved,
            "Approved mappings must reference imported inventory and sales IDs.",
        )
        add_result(
            "Product mapping",
            "Pending mappings",
            pending,
            "Pending mappings must not be used for matched forecasting.",
        )
        add_result(
            "Product mapping",
            "Completed sales without approved mappings",
            len(unmatched_sales_ids),
            "Unmatched sales must remain separate pending review.",
        )

        # 3. SALES VALIDITY
        future_orders = sum(
            r.order_date is not None
            and r.order_date.date() > date.today()
            for r in sales
        )

        invalid_date_sequences = sum(
            r.order_date is not None
            and r.completed_date is not None
            and r.completed_date.date() < r.order_date.date()
            for r in sales
        )

        unexpected_statuses = sum(
            not r.order_status
            or r.order_status.strip().upper() not in EXPECTED_SALES_STATUSES
            for r in sales
        )

        add_result(
            "Sales validity",
            "Future order dates",
            future_orders,
            "Orders after today's date require review.",
        )
        add_result(
            "Sales validity",
            "Invalid order/completed date sequences",
            invalid_date_sequences,
            "Completed date should not precede order date.",
        )
        add_result(
            "Sales validity",
            "Unexpected sales statuses",
            unexpected_statuses,
            "Checks statuses against the configured expected list.",
        )

        # 4. DUPLICATE DETECTION
        inventory_keys = [
            (r.source_file, r.source_row_number)
            for r in inventory
            if r.source_file is not None and r.source_row_number is not None
        ]
        sales_keys = [
            (r.source_file, r.source_row_number)
            for r in sales
            if r.source_file is not None and r.source_row_number is not None
        ]
        mapping_keys = [
            (m.inventory_item_id, m.sales_item_id)
            for m in mappings
        ]

        def duplicate_count(keys):
            counts = Counter(keys)
            return sum(n - 1 for n in counts.values() if n > 1)

        add_result(
            "Duplicate detection",
            "Duplicate inventory source references",
            duplicate_count(inventory_keys),
            "Checks repeated source filename and row-number pairs.",
        )
        add_result(
            "Duplicate detection",
            "Duplicate sales source references",
            duplicate_count(sales_keys),
            "Checks repeated source filename and row-number pairs.",
        )
        add_result(
            "Duplicate detection",
            "Duplicate mapping pairs",
            duplicate_count(mapping_keys),
            "Checks repeated inventory/sales ID pairs.",
        )

        # 5. STOCK AND DEMAND EXCEPTIONS
        zero_stock = sum(
            r.available_qty is not None and r.available_qty == 0
            for r in inventory
        )

        completed_demand_ids = {
            r.sales_item_id
            for r in sales
            if r.sales_item_id
            and r.order_status
            and r.order_status.strip().upper() == "COMPLETED"
            and r.item_quantity is not None
            and r.item_quantity > 0
        }

        no_observed_demand = sum(
            m.review_status == "APPROVED"
            and m.sales_item_id not in completed_demand_ids
            for m in mappings
        )

        add_result(
            "Stock and demand exceptions",
            "Zero-stock inventory records",
            zero_stock,
            "Zero stock is an exception for review, not automatically an error.",
        )
        add_result(
            "Stock and demand exceptions",
            "Approved mappings without positive completed sales",
            no_observed_demand,
            "No observed demand does not mean future demand will be zero.",
        )

        # Save CSV report.
        project_root = Path(__file__).resolve().parent.parent
        report_dir = project_root / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / "data_quality_report_SYNTHETIC.csv"

        with report_path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as file:
            fieldnames = [
                "data_label",
                "category",
                "check",
                "issues_found",
                "result",
                "details",
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        passed = sum(r["result"] == "PASS" for r in results)
        review = sum(r["result"] == "REVIEW" for r in results)

        print("=" * 65)
        print("SUPPLY CHAIN DATA QUALITY SUMMARY")
        print(DATA_LABEL)
        print("=" * 65)
        print(f"Inventory records: {len(inventory)}")
        print(f"Sales records: {len(sales)}")
        print(f"Product mappings: {len(mappings)}")
        print(f"Grouped checks: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Needs review: {review}")
        print(f"CSV report: {report_path}")
        print("Database records were not modified.")
        print("Synthetic development data only.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
