import argparse
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import Base, SessionLocal, engine
from app.models import Collection, Disbursement, Merchant, Region, Subscriber, Transaction


REGIONS = ("North", "South", "East", "West", "Central")
CATEGORIES = ("Retail", "Grocery", "Travel", "Utilities", "Telecom", "E-commerce", "Healthcare")


def add_batches(db, model, records, batch_size=5000):
    for offset in range(0, len(records), batch_size):
        db.bulk_insert_mappings(model, records[offset:offset + batch_size])
        db.commit()


def add_transaction_batch(db, transaction_rows, collection_rows):
    add_batches(db, Transaction, transaction_rows)
    if not collection_rows:
        return
    references = [row["transaction_ref"] for row in collection_rows]
    transaction_ids = {}
    for offset in range(0, len(references), 900):
        batch_refs = references[offset:offset + 900]
        transaction_ids.update({
            reference: identifier for identifier, reference in
            db.query(Transaction.id, Transaction.transaction_ref).filter(Transaction.transaction_ref.in_(batch_refs)).all()
        })
    for row in collection_rows:
        reference = row.pop("transaction_ref")
        transaction_id = transaction_ids.get(reference)
        if transaction_id is None:
            raise RuntimeError(f"Seeded transaction reference was not found: {reference}")
        row["transaction_id"] = transaction_id
    add_batches(db, Collection, collection_rows)


def main():
    parser = argparse.ArgumentParser(description="Seed reproducible merchant analytics demo data")
    parser.add_argument("--small", action="store_true", help="Create a small test dataset")
    args = parser.parse_args()
    merchant_count, subscriber_count, transaction_count = (20, 100, 500) if args.small else (100, 50_000, 500_000)
    random.seed(41)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Transaction).count():
            raise SystemExit("Transactions already exist; refusing to duplicate seed data.")
        for region_name in REGIONS:
            if db.query(Region).filter(Region.name == region_name).first() is None:
                db.add(Region(name=region_name))
        db.commit()
        region_ids = [r.id for r in db.query(Region).all()]
        start = datetime.utcnow() - timedelta(days=730)
        end = datetime.utcnow()
        merchant_rows = []
        for i in range(merchant_count):
            merchant_rows.append({"code": f"MRC-{i + 1:05d}", "name": f"Merchant {i + 1:03d}",
                                  "category": CATEGORIES[i % len(CATEGORIES)],
                                  "region_id": region_ids[i % len(region_ids)],
                                  "status": "active" if i % 9 else "dormant",
                                  "created_at": start})
        add_batches(db, Merchant, merchant_rows)
        active_merchant_ids = [m.id for m in db.query(Merchant).filter(Merchant.status == "active").all()]
        subscriber_rows = []
        for i in range(subscriber_count):
            joined = start.date() + timedelta(days=random.randrange(731))
            subscriber_rows.append({"merchant_id": active_merchant_ids[i % len(active_merchant_ids)],
                                    "subscriber_ref": f"SUB-{i + 1:07d}", "joined_at": joined,
                                    "status": "active" if i % 13 else "inactive"})
        add_batches(db, Subscriber, subscriber_rows)
        transaction_rows, collection_rows, disbursement_rows = [], [], []
        channels = ("USSD", "APP", "WEB", "POS", "API")
        for i in range(transaction_count):
            merchant_id = active_merchant_ids[random.randrange(len(active_merchant_ids))]
            occurred = start + timedelta(seconds=random.randrange(int((end - start).total_seconds())))
            amount = round(random.lognormvariate(5.2, 0.8), 2)
            successful = random.random() < 0.96
            transaction_rows.append({
                "merchant_id": merchant_id, "transaction_ref": f"TX-{i + 1:09d}",
                "occurred_at": occurred, "amount": Decimal(str(amount)),
                "status": "successful" if successful else "failed", "channel": channels[i % len(channels)],
            })
            if successful and i % 2 == 0:
                collection_rows.append({
                    "merchant_id": merchant_id, "transaction_ref": f"TX-{i + 1:09d}", "collected_at": occurred,
                    "amount": Decimal(str(amount)), "status": "successful",
                })
            if successful and i % 5 == 0:
                disbursement_rows.append({
                    "merchant_id": merchant_id, "disbursed_at": occurred + timedelta(hours=random.randrange(48)),
                    "amount": Decimal(str(round(amount * random.uniform(0.7, 0.98), 2))),
                    "status": "successful", "reference": f"DIS-{i + 1:09d}",
                })
            if len(transaction_rows) >= 5000:
                add_transaction_batch(db, transaction_rows, collection_rows)
                add_batches(db, Disbursement, disbursement_rows)
                transaction_rows, collection_rows, disbursement_rows = [], [], []
        if transaction_rows:
            add_transaction_batch(db, transaction_rows, collection_rows)
            add_batches(db, Disbursement, disbursement_rows)
        print(f"Seeded {merchant_count} merchants, {subscriber_count} subscribers, "
              f"{transaction_count} transactions across 24 months.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
