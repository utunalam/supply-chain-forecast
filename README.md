# Supply Chain Forecasting System

A prototype exploring how sales and inventory data can support replenishment planning for e-commerce Key Account Managers.

**Project status:** Working prototype — development and testing only  
**Data:** Synthetic sample data; not for purchasing decisions.

## 1. Project Overview

E-commerce Key Account Managers need to monitor product sales, stock availability, and product performance. When sales and inventory information comes from different reports, manual comparison can take time and make it harder to identify products that need attention.

This project explores how programming and data analysis can help bring these processes together.

The system processes sales and inventory reports, matches records to products, generates demand and replenishment indicators, and displays the results through a web dashboard.

The project also includes a REST API for managing product master data through CRUD operations.

### Project Objectives

- Reduce manual effort when reviewing sales and inventory reports.
- Improve visibility into product demand and available stock.
- Identify products that may require replenishment or further review.
- Demonstrate how Python, APIs, databases, and a web dashboard can work together.
- Establish a foundation for future daily data-refresh automation.

### Intended Users

- E-commerce Key Account Managers
- E-commerce operations teams
- Inventory planners
- Supply chain teams

## 2. Live Application

- **Frontend dashboard:** https://supply-chain-forecast.pages.dev
- **Backend API:** https://acommerce-supply-chain-forecast-api.onrender.com
- **API documentation:** https://acommerce-supply-chain-forecast-api.onrender.com/docs
- **Health check:** https://acommerce-supply-chain-forecast-api.onrender.com/health

The Render free service may sleep after inactivity, so the first request may take longer as the service starts up.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend logic and data processing |
| FastAPI | REST API and HTTP endpoints |
| Uvicorn | Runs the FastAPI application |
| SQLAlchemy | Database interaction through Python |
| SQLite | Local development database |
| Pydantic | API request and response validation |
| React | Frontend dashboard |
| Vite | Frontend development and production build tooling |
| CSV and Excel | Sales, inventory, mapping, and report files |
| Git and GitHub | Version control and source code management |
| Render | Backend hosting |
| Cloudflare Pages | Frontend hosting |

## 4. System Architecture

The application contains two related but currently separate workflows.

### A. Data processing and replenishment workflow

1. Sales and inventory reports are provided as input files.
2. Input files are validated for required columns and basic data-quality issues.
3. Product mapping associates source records with the appropriate product.
4. Import scripts load the relevant sales, inventory, and mapping records.
5. Data-quality checks identify unmatched records and other potential issues.
6. Demand and replenishment scripts generate output reports.
7. FastAPI serves the generated replenishment report.
8. The React dashboard requests the report and displays its results.

### B. Product CRUD workflow

1. A client sends an HTTP request to a FastAPI endpoint.
2. FastAPI validates the request using the relevant schema.
3. The endpoint uses SQLAlchemy and a database session to perform the requested operation.
4. The database stores or retrieves the product record.
5. FastAPI returns a response to the client.

**Current limitation:** CRUD operations do not automatically trigger the data-processing workflow or regenerate the replenishment report. The dashboard reads a pre-generated report rather than recalculating it on every request.

## 5. Repository Structure

The main project structure is:

```text
supply-chain-forecast/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── requirements.txt
│   ├── validate_reports.py
│   ├── import_reports.py
│   ├── import_product_mappings.py
│   ├── data_quality_checks.py
│   ├── build_demand_report.py
│   ├── build_replenishment_report.py
│   ├── build_baseline_forecast.py
│   ├── evaluate_baseline_forecast.py
│   └── update_schema.py
├── frontend/
├── data/
│   ├── incoming/
│   └── product_mapping_review.csv
├── reports/
├── .gitignore
└── README.md
```

The frontend directory contains the React application. The data directory contains input files and product-mapping information. The reports directory contains generated output files.

## 6. Data Inputs and Outputs

### Input files

The synthetic input files include:

- `data/incoming/Inventory_Report_SYNTHETIC.csv`
- `data/incoming/Sales_QTY_Breakdown_SYNTHETIC.xlsx`
- `data/product_mapping_review.csv`

### Generated reports

The project includes reports such as:

- `reports/baseline_forecast_SYNTHETIC.csv`
- `reports/baseline_forecast_evaluation_SYNTHETIC.csv`
- `reports/data_quality_report_SYNTHETIC.csv`
- `reports/demand_stock_coverage_SYNTHETIC.csv`
- `reports/replenishment_recommendations_SYNTHETIC.csv`
- `reports/unmatched_completed_sales_SYNTHETIC.csv`
- `reports/unmatched_replenishment_products_SYNTHETIC.csv`

These reports support data-quality review, demand analysis, baseline forecasting, and replenishment planning.

## 7. Replenishment Calculation

The current dashboard demonstrates a simple replenishment approach using average daily demand, assumed lead time, and assumed safety-stock days.

### Average daily demand

Average daily demand is calculated as:

Average daily demand = Units sold during the demand window ÷ Number of days in the window

For the Wi-Fi LED Strip example:

- Units sold: 7
- Demand window: 14 days
- Average daily demand: 7 ÷ 14 = 0.5 units per day

### Provisional reorder point

The prototype uses the following calculation:

Reorder point = Average daily demand × (Lead time days + Safety-stock days)

Using the current assumptions:

- Average daily demand: 0.5 units per day
- Lead time: 7 days
- Safety stock: 3 days

Reorder point = 0.5 × (7 + 3) = 5 units

The latest recorded stock for this example is 35 units, which is above the provisional reorder point. The displayed suggested replenishment is therefore zero units.

These calculations are illustrative and must be validated against real business requirements before being used for purchasing decisions.

A zero-demand product may still require further review. Zero recorded sales do not necessarily mean that future demand will remain zero.

## 8. Backend API and CRUD

The backend provides product-management endpoints and endpoints for application health and replenishment data.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| GET | `/replenishment` | Retrieve the generated replenishment report |
| POST | `/skus` | Create a SKU |
| GET | `/skus` | Retrieve the SKU list |
| GET | `/skus/{sku_id}` | Retrieve one SKU by database ID |
| PATCH | `/skus/{sku_id}` | Update an existing SKU |
| DELETE | `/skus/{sku_id}` | Delete an existing SKU |

### CRUD operations

**Create:** A POST request sends product details to the backend. The API validates the request and saves the new record.

**Read:** GET requests retrieve product records from the database.

**Update:** PATCH changes selected fields of an existing product.

**Delete:** DELETE removes the selected product record.

### Database ID versus SKU code

The database ID and SKU code are different values.

For example:

- Database ID: `8`
- SKU code: `325644001`

The `/skus/{sku_id}` endpoints expect the database ID. Entering the SKU code into this parameter can return a 404 response because the API searches by database ID.

### Validation and error handling

The application uses Pydantic schemas to validate request fields and SQLAlchemy to interact with the database. The API handles conditions such as missing records and duplicate SKU codes.

Common HTTP responses include:

- `200 OK`: Request completed successfully.
- `201 Created`: A new record was created.
- `404 Not Found`: The requested record does not exist.
- `409 Conflict`: A request conflicts with an existing record, such as a duplicate SKU code.
- `422 Unprocessable Entity`: The request failed validation.

## 9. Local Development Setup

### Prerequisites

Install:

- Python
- Node.js and npm
- Git
- A code editor such as Visual Studio Code

### Step 1: Clone the repository

```bash
git clone https://github.com/utunalam/supply-chain-forecast.git
cd supply-chain-forecast
```

### Step 2: Set up the Python environment

From the project root in PowerShell:

```powershell
python -m venv backend/.venv
```

Activate the environment:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

### Step 3: Start the backend

From the project root:

```powershell
python -m uvicorn main:app --app-dir .\backend --reload --host 127.0.0.1 --port 8000
```

Alternatively, use the project's Python executable explicitly:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn main:app --app-dir .\backend --reload --host 127.0.0.1 --port 8000
```

Keep the terminal running while testing the backend.

### Step 4: Test the backend

Open these URLs:

- API documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- Replenishment report: `http://127.0.0.1:8000/replenishment`

### Step 5: Set up the frontend

Open another terminal:

```powershell
cd frontend
npm ci
```

Configure the frontend environment variable for local development:

```text
VITE_API_URL=http://127.0.0.1:8000
```

Save it in the frontend's local environment configuration file. Do not commit secret credentials.

Start the frontend:

```powershell
npm run dev
```

Open the local URL shown in the terminal, usually `http://localhost:5173`.

## 10. Data Validation and Report Generation

The backend directory contains scripts to validate, import, check, and process reports.

The main script purposes are:

| Script | Purpose |
|---|---|
| `validate_reports.py` | Checks input reports |
| `import_reports.py` | Imports sales and inventory records |
| `import_product_mappings.py` | Imports product mappings |
| `data_quality_checks.py` | Identifies data-quality issues |
| `build_demand_report.py` | Builds demand and stock-coverage output |
| `build_replenishment_report.py` | Generates replenishment recommendations |
| `build_baseline_forecast.py` | Builds the baseline forecast |
| `evaluate_baseline_forecast.py` | Evaluates baseline forecast output |
| `update_schema.py` | Supports database schema updates |

Example commands from the project root:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\validate_reports.py
```

```powershell
.\backend\.venv\Scripts\python.exe .\backend\import_reports.py
```

```powershell
.\backend\.venv\Scripts\python.exe .\backend\data_quality_checks.py
```

```powershell
.\backend\.venv\Scripts\python.exe .\backend\build_demand_report.py
```

```powershell
.\backend\.venv\Scripts\python.exe .\backend\build_replenishment_report.py
```

Run validation and resolve data-quality issues before publishing updated reports.

**Important:** The current importer needs additional work before safe repeated daily use. Its handling of previously imported sales records and repeated source filenames can cause new records to be skipped or existing inventory history to be overwritten. Do not assume that replacing the input files and rerunning the importer is a reliable daily-refresh process yet.

The complete processing sequence should be verified against the scripts before running it on any new dataset.

## 11. Deployment

### Frontend deployment

The React frontend is hosted on Cloudflare Pages.

- Repository: `utunalam/supply-chain-forecast`
- Branch: `master`
- Root directory: `frontend`
- Build command: `npm run build`
- Build output directory: `dist`
- Environment variable: `VITE_API_URL`

Production API URL:

```text
https://acommerce-supply-chain-forecast-api.onrender.com
```

### Backend deployment

The FastAPI backend is hosted on Render.

- Repository: `utunalam/supply-chain-forecast`
- Branch: `master`
- Build command:

```bash
pip install -r backend/requirements.txt
```

- Start command:

```bash
uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

The `FRONTEND_ORIGIN` environment variable specifies the frontend origins permitted by the backend's CORS configuration.

The deployed backend must have access to the required report files and database configuration. Local database files are not committed to Git, so database persistence and production storage need to be configured separately for a production system.

### Deployment verification

After deployment:

1. Check the backend health endpoint.
2. Check the replenishment endpoint.
3. Open the frontend dashboard.
4. Inspect browser Network tools to confirm that API requests succeed.
5. Review Render and Cloudflare deployment logs if errors occur.

A successful deployment does not by itself guarantee that data processing, persistence, or forecasting is working correctly.

## 12. Current Limitations

The current project is a working prototype, not a production-ready supply chain planning system.

Known limitations include:

- Synthetic data is used for demonstration.
- The dashboard reads a pre-generated replenishment report.
- CRUD changes do not automatically regenerate the report.
- Daily input retrieval and report refresh are not fully automated.
- The report-import workflow needs safer handling of repeated imports and historical records.
- The baseline calculations and assumptions require validation against real demand.
- Production authentication and access controls are not yet implemented for the CRUD endpoints.
- Production-grade database persistence, monitoring, and recovery need further work.
- The system has not been benchmarked for large-scale SKU volumes.

The deployed CRUD endpoints should not be used for sensitive or real business data until authentication and appropriate access controls have been added.

## 13. Future Improvements

Potential next steps include:

1. Improve import logic to identify new records reliably and avoid duplicates.
2. Preserve historical inventory snapshots for accurate stock analysis.
3. Automate daily retrieval and validation of sales and inventory reports.
4. Run data-processing and replenishment scripts through a controlled scheduled workflow.
5. Publish updated reports only after successful validation.
6. Connect report generation to the application's refresh workflow.
7. Add authentication, role-based permissions, and audit logging.
8. Use persistent production database storage.
9. Evaluate forecast performance against historical actual sales.
10. Investigate more advanced forecasting methods where the data supports them.
11. Add monitoring, error notifications, and recovery procedures.
12. Measure operational impact using forecast error, stockout frequency, excess inventory, and time spent preparing reports.

## 14. Project Learning Outcomes

This project demonstrates practical experience exploring:

- Python application development
- REST API design and CRUD operations
- Database modelling and SQLAlchemy
- Data validation and product mapping
- Sales and inventory report processing
- Demand and replenishment calculations
- React frontend and backend communication
- Git and GitHub version control
- Deployment using Render and Cloudflare Pages
- Debugging, testing, and documenting a multi-component application

## 15. Disclaimer

This project is intended for learning, demonstration, and development purposes.

All sample data and associated recommendations are synthetic. They must not be used as the basis for actual purchasing, replenishment, or other operational decisions.

The system requires additional data validation, automation, security controls, and forecasting evaluation before it can be considered for production use.
