# Data Engineering Workflow

This document outlines the end-to-end data pipeline workflow for the FMCG project.

## 1. Setup Phase

*   **Objective**: Initialize the environment and prepare required resources.
*   **Notebooks**:
    *   `1_codes/1_setup/setup_catalog.ipynb`: Creates the necessary Hive Metastore / Unity Catalog databases (`fmcg_bronze`, `fmcg_silver`, `fmcg_gold`).
    *   `1_codes/1_setup/dim_date_table_creation.ipynb`: Generates the Date dimension table required for time-series analysis.

## 2. Ingestion & Bronze Layer

*   **Objective**: Ingest raw data from source locations into the Bronze layer (Delta tables).
*   **Sources**:
    *   **Parent Company Data**: Located in `0_data/1_parent_company/`.
    *   **Child Company Data**: Located in **AWS S3** (`landing` folder).
*   **Process**:
    *   **Ingestion**: Spark reads raw files (CSV, JSON, Parquet) from the source locations.
    *   **Bronze Load**: Data is saved as-is into the **Bronze** layer tables (e.g., `bronze_orders`, `bronze_products`).
    *   **File Movement (Child Company)**: Upon successful ingestion, the raw files in the S3 `landing` folder are moved to a `processed` folder to ensure they are not re-processed. This logic is handled within the Bronze layer notebook.

## 3. Silver Layer (Processing & Cleaning)

*   **Objective**: Cleanse, validate, and normalize data into Dimension and Fact tables.
*   **Dimension Processing** (`1_codes/2_dimension_data_processing/`):
    *   `1_customers_data_processing.ipynb`: Cleans customer data, handles duplicates, and loads to `dim_customers`.
    *   `2_products_data_processing.ipynb`: Standardizes product information and loads to `dim_products`.
    *   `3_pricing_data_processing.ipynb`: Processes pricing information into `dim_gross_price`.
*   **Fact Processing** (`1_codes/3_fact_data_processing/`):
    *   `1_full_load_fact.ipynb`: Performs initial full load of sales transactions into `fact_orders`.
    *   `2_incremental_load_fact.ipynb`: Handles daily/periodic incremental updates to `fact_orders`.

## 4. Gold Layer (Aggregation & Enrichment)

*   **Objective**: Create business-ready views and aggregates.
*   **Process**:
    *   Data from Fact and Dimension tables in the Silver layer is joined.
    *   Complex logic (KPI calculations, currency conversion) is applied.
*   **Key Asset**:
    *   `vw_fact_orders_enriched`: Defined in `2_dashboarding/denormalise_table_query_fmcg.txt`. This view creates a wide table joining Orders with Customers, Products, and Date dimensions for easy reporting.

## 5. Dashboarding & Reporting

*   **Objective**: Visualize key performance indicators (KPIs).
*   **Output**:
    *   `fmcg_dashboard.pdf`: A generated report showing sales trends, top products, and regional performance.
*   **Tools**:
    *   **Power BI** is connected to the Databricks Warehouse using the **Server Hostname** and **HTTP Path** via a Personal Access Token (PAT).
    *   It imports/queries data from the Gold layer (`vw_fact_orders_enriched`) to generate the reports.

## Pipeline Orchestration

The entire workflow can be orchestrated using **Databricks Workflows (Jobs)**. A typical job would have dependencies set up as follows:

1.  **Task 1**: `setup_catalog` (Run once)
2.  **Task 2**: `dim_date_creation` (Run once)
3.  **Task 3**: `bronze_ingestion` (Parallel inputs)
4.  **Task 4**: `dimension_processing` (Dependent on Bronze)
5.  **Task 5**: `fact_processing` (Dependent on Dimensions & Bronze)
6.  **Task 6**: `gold_view_refresh` (Dependent on Facts)
