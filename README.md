# Retail Sales Data Engineering Pipeline

An end-to-end data engineering project that transforms raw retail transactions into a PostgreSQL data warehouse and an interactive analytics dashboard.

## Project Overview

This project uses the UCI Online Retail dataset, containing over 540,000 transaction records.

The pipeline extracts data from Excel, validates and transforms transactions, tracks rejected records, and loads clean data into PostgreSQL.

A star-schema data warehouse supports SQL analytics and an interactive Streamlit dashboard.

## Technologies

- Python and Pandas
- PostgreSQL
- SQLAlchemy
- Docker and Docker Compose
- SQL and dimensional modeling
- Streamlit and Matplotlib
- Pytest
- Ruff
- GitHub Actions

## Architecture

```text
Excel Dataset
     |
     v
Extract and Validate
     |
     v
Transform and Data Quality
     |
     +----> Rejected Transactions
     |
     v
PostgreSQL Retail Layer
     |
     v
Data Warehouse (Star Schema)
     |
     +----> SQL Analytics
     |
     +----> Streamlit Dashboard
```

## Data Warehouse

The warehouse uses a star schema with one fact table and four dimensions.

**Fact Table**
- `warehouse.fact_sales`

**Dimension Tables**
- `warehouse.dim_product`
- `warehouse.dim_customer`
- `warehouse.dim_country`
- `warehouse.dim_date`

Each fact row represents one valid sales or cancellation transaction line.

## Key Features

- Data extraction from Excel
- Data validation and transformation
- Rejected-record tracking with rejection reasons
- Decimal-based financial calculations
- PostgreSQL loading with conflict handling
- SHA-256-based source file identification
- Atomic transactions and rollback
- Data warehouse with fact and dimension tables
- Automated warehouse refresh
- Data reconciliation checks
- Interactive analytics dashboard
- Unit and integration testing

## Dataset

Source: UCI Machine Learning Repository — Online Retail.

https://archive.ics.uci.edu/dataset/352/online+retail

The original dataset contains 541,909 rows.

After validation:
- Valid sales: 530,104
- Cancellation rows: 9,288
- Rejected rows: 2,517

The retail and warehouse layers each contain 539,392 valid transaction lines.

### Initialize the Database

For a fresh PostgreSQL database, initialize the final
schema using:

```bash
docker compose exec -T postgres \
  psql -v ON_ERROR_STOP=1 \
  -U sales_user -d sales_analytics \
  -f /dev/stdin < sql/bootstrap.sql
```

This creates the retail and warehouse schemas, including
source tracking, transaction tables, dimensions, facts,
constraints, and indexes.

The bootstrap script is intended for a new, empty database.

Historical migrations in `sql/migrations/` document
changes made during project development and should not
be applied after bootstrap.

Once initialized, run the ETL pipeline:

```bash
python3 -m sales_pipeline.main
```

Start the analytics dashboard:

```bash
streamlit run dashboard.py
```


## Setup

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python3 -m pip install -e ".[dev]"
```

### 4. Configure PostgreSQL

Create a `.env` file using `.env.example` as a template.

Start PostgreSQL:

```bash
docker compose up -d
```

### 5. Prepare the dataset and database

Place `Online Retail.xlsx` in `data/raw/`.

Create the database schema and apply the required migrations before the first pipeline run.

### 6. Run the pipeline

```bash
python3 -m sales_pipeline.main
```

### 7. Start the dashboard

```bash
streamlit run dashboard.py
```

## Testing

Run unit tests:

```bash
python3 -m pytest -v
```

Run integration tests against properly configured PostgreSQL databases:

```bash
python3 -m pytest tests/integration -v -m integration
```

Check code quality:

```bash
ruff check .
ruff format --check .
```

GitHub Actions automatically runs the code-quality checks and unit tests. Database integration tests are run separately.

## Dashboard

The Streamlit dashboard includes:

- Gross sales
- Cancellation value
- Net sales
- Number of orders
- Monthly sales trends
- Top products
- Top customers
- Country and date filters

Screenshots will be added here.

## Future Improvements

- Automated integration testing in GitHub Actions
- More advanced product classification
- Improved incremental warehouse updates
- Historical product attribute tracking
- Dashboard deployment

## Project Purpose

This project demonstrates practical skills in Python, SQL, data pipelines, PostgreSQL, data quality, dimensional modeling, testing, and business intelligence.
