
"""Load cleaned retail transactions into PostgreSQL."""

import logging
from decimal import Decimal

import pandas as pd
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from sales_pipeline.quality import prepare_rejected_records
from sales_pipeline.transform import TransformationResult

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000



def prepare_records(
    df: pd.DataFrame,
    transaction_type: str,
    source_file_id: int,
) -> list[dict]:
    """Convert cleaned rows into source-aware database records."""
    records = []

    for index, row in df.iterrows():
        customer_id = row.get("CustomerID")

        if pd.isna(customer_id):
            customer_id = None
        elif isinstance(customer_id, (int, float)):
            if float(customer_id).is_integer():
                customer_id = str(int(customer_id))
            else:
                customer_id = str(customer_id)
        else:
            customer_id = str(customer_id)

        record = {
            "source_file_id": source_file_id,
            "source_row_id": int(index) + 2,
            "invoice_no": str(row["InvoiceNo"]),
            "stock_code": str(row["StockCode"]),
            "description": (
                None
                if pd.isna(row.get("Description"))
                else str(row["Description"])
            ),
            "quantity": int(row["Quantity"]),
            "unit_price": Decimal(str(row["UnitPrice"])),
            "total_price": Decimal(str(row["TotalPrice"])),
            "invoice_date": row["InvoiceDate"].to_pydatetime(),
            "customer_id": customer_id,
            "country": (
                None
                if pd.isna(row.get("Country"))
                else str(row["Country"])
            ),
            "transaction_type": transaction_type,
        }

        records.append(record)

    return records




def load_transactions(
    result: TransformationResult,
    connection: Connection,
    source_file_id: int,
) -> int:
    """Load valid transactions without source-row duplicates."""
    metadata = MetaData()

    transactions = Table(
        "transactions",
        metadata,
        schema="retail",
        autoload_with=connection,
    )

    sales = prepare_records(
        result.sales,
        "SALE",
        source_file_id,
    )

    cancellations = prepare_records(
        result.cancellations,
        "CANCELLATION",
        source_file_id,
    )

    records = sales + cancellations
    inserted_count = 0

    logger.info("Preparing %d transactions", len(records))

    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]

        statement = insert(transactions).values(batch)

        statement = statement.on_conflict_do_nothing(
            index_elements=[
                "source_file_id",
                "source_row_id",
            ]
        ).returning(transactions.c.transaction_id)

        response = connection.execute(statement)
        inserted_count += len(response.fetchall())

    logger.info(
        "New transactions prepared: %d",
        inserted_count,
    )

    return inserted_count




def load_rejected_records(
    rejected: pd.DataFrame,
    connection: Connection,
    source_file_id: int,
) -> int:
    """Load rejected rows with source file identification."""
    metadata = MetaData()

    rejected_table = Table(
        "rejected_transactions",
        metadata,
        schema="retail",
        autoload_with=connection,
    )

    records = prepare_rejected_records(rejected)

    for record in records:
        record["source_file_id"] = source_file_id

    inserted_count = 0

    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]

        statement = insert(rejected_table).values(batch)

        statement = statement.on_conflict_do_nothing(
            index_elements=[
                "source_file_id",
                "source_row_id",
            ]
        ).returning(rejected_table.c.rejection_id)

        response = connection.execute(statement)
        inserted_count += len(response.fetchall())

    logger.info(
        "New rejected records prepared: %d",
        inserted_count,
    )

    return inserted_count


def register_source_file(
    connection: Connection,
    file_hash: str,
    file_name: str,
) -> int:
    """Register a source file and return its database ID."""
    from sqlalchemy import text

    statement = text("""
        INSERT INTO retail.source_files (
            file_hash,
            file_name
        )
        VALUES (
            :file_hash,
            :file_name
        )
        ON CONFLICT (file_hash)
        DO UPDATE SET
            file_name = EXCLUDED.file_name
        RETURNING source_file_id
    """)

    source_file_id = connection.execute(
        statement,
        {
            "file_hash": file_hash,
            "file_name": file_name,
        },
    ).scalar_one()

    logger.info(
        "Source file registered with ID: %d",
        source_file_id,
    )

    return source_file_id
