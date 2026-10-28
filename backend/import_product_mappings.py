
import csv
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models import ProductMapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAPPING_FILE = PROJECT_ROOT / "data" / "product_mapping_review.csv"


def main():
    if not MAPPING_FILE.exists():
        raise FileNotFoundError(
            f"Mapping file not found: {MAPPING_FILE}"
        )

    with MAPPING_FILE.open(
        encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)
        required_columns = {
            "inventory_item_id",
            "inventory_description",
            "sales_item_id",
            "sales_description",
            "match_method",
            "review_status",
            "internal_product_code",
        }

        if not reader.fieldnames:
            raise ValueError("The mapping CSV has no header.")

        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        rows = list(reader)

    approved = [
        row for row in rows
        if row["review_status"].strip().upper() == "APPROVED"
    ]

    unexpected_statuses = [
        row["review_status"].strip()
        for row in rows
        if row["review_status"].strip().upper()
        not in {"APPROVED", "PENDING"}
    ]

    if unexpected_statuses:
        raise ValueError(
            f"Unexpected review statuses: {unexpected_statuses}"
        )

    if not approved:
        print("No approved mappings to import.")
        return

    db = SessionLocal()
    imported = 0
    skipped = 0

    try:
        for row in approved:
            inventory_id = row["inventory_item_id"].strip()
            sales_id = row["sales_item_id"].strip()

            if not inventory_id or not sales_id:
                raise ValueError(
                    "Inventory and sales IDs cannot be blank."
                )

            existing = (
                db.query(ProductMapping)
                .filter_by(
                    inventory_item_id=inventory_id,
                    sales_item_id=sales_id,
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            mapping = ProductMapping(
                inventory_item_id=inventory_id,
                sales_item_id=sales_id,
                inventory_description=row[
                    "inventory_description"
                ].strip(),
                sales_description=row[
                    "sales_description"
                ].strip(),
                match_method=row["match_method"].strip(),
                review_status="APPROVED",
                internal_product_code=(
                    row["internal_product_code"].strip() or None
                ),
            )

            db.add(mapping)
            imported += 1

        db.commit()

        print("Mapping import completed.")
        print(f"Approved mappings in CSV: {len(approved)}")
        print(f"New mappings imported: {imported}")
        print(f"Existing mappings skipped: {skipped}")
        print("Pending mappings were not imported.")

    except (IntegrityError, ValueError):
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
