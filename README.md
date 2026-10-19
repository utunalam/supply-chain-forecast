# Supply Chain Forecasting System

A beginner-friendly Python project to help businesses manage product information, understand sales trends, forecast demand, and make better inventory replenishment decisions.

**Project status:** In development  
**Current version:** 0.1.0  
**Built with:** Python, FastAPI, SQLite, and Pydantic

## 1. About This Project

Managing inventory can be challenging when sales and stock reports are stored in separate Excel files. Businesses need to understand which products are selling, how much stock is available, and when to replenish inventory.

This project aims to build a simple system that brings these tasks together. The long-term goal is to automate the process of collecting sales and inventory data, forecasting future demand, and recommending how much stock to replenish.

The project is being developed step by step, starting with a backend API for managing product information.

## 2. Project Goals

The planned system aims to help users:

- Manage product and SKU information.
- Import daily sales and inventory reports from Excel.
- Analyse historical sales and inventory data.
- Forecast future sales, orders, units sold, and GMV.
- Identify products that may need replenishment.
- Recommend replenishment quantities based on demand and available stock.
- Reduce repetitive manual work through automation.

**Note:** Sales forecasting, Excel imports, and automated replenishment are planned features. They are not implemented in the current version.

## 3. Current Features

The current backend provides a REST API for SKU (Stock Keeping Unit) management.

| Feature | Description |
|---|---|
| Create a SKU | Add a product to the database. |
| View all SKUs | Retrieve the list of products. |
| View one SKU | Retrieve a product by its ID. |
| Update a SKU | Modify product details. |
| Delete a SKU | Remove a product record. |
| Health check | Check whether the API is running. |

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language. |
| FastAPI | Builds the backend API. |
| SQLite | Stores product information in a local database. |
| Pydantic | Validates incoming API data. |
| Uvicorn | Runs the API server. |
| Git and GitHub | Track code changes and store the project online. |

## 5. Project Structure

```text
supply-chain-forecast/
├── backend/
│   ├── .venv/          # Local Python virtual environment (not uploaded)
│   ├── database.py     # Database connection
│   ├── main.py         # API endpoints and application
│   ├── models.py       # Database table definitions
│   └── schemas.py      # Request data validation
├── data/
│   ├── incoming/       # Planned location for incoming reports
│   └── archive/        # Planned location for processed reports
├── logs/               # Planned location for application logs
├── reports/            # Planned location for generated reports
└── .gitignore          # Files Git should ignore
```

Some folders are reserved for future features and may not yet contain files.

### What do the backend files do?

- **`main.py`** — Defines the API endpoints that users can call.
- **`database.py`** — Opens a connection to the SQLite database.
- **`models.py`** — Defines the database table for SKU records.
- **`schemas.py`** — Defines the structure and validation rules for API requests.

## 6. Getting Started

These instructions are for Windows users using PowerShell.

### Prerequisites

Install:

- Python 3.10 or newer.
- Git.
- Visual Studio Code (recommended).

### Step 1: Clone the repository

Open PowerShell and run:

```powershell
git clone https://github.com/utunalam/supply-chain-forecast.git
cd supply-chain-forecast
```

### Step 2: Create a virtual environment

From the project root, run:

```powershell
cd backend
python -m venv .venv
```

A virtual environment keeps this project's Python packages separate from other projects.

### Step 3: Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run this command for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment again.

### Step 4: Install dependencies

With the virtual environment activated, run:

```powershell
python -m pip install --upgrade pip
python -m pip install fastapi "uvicorn[standard]" sqlalchemy
```

The current application uses Python's built-in `sqlite3` module for its database connection. SQLAlchemy is installed in the initial environment but is not currently used by the application.

### Step 5: Start the API

Make sure your terminal is in the `backend` directory and run:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal open while using the API.

### Step 6: Open the API documentation

Visit:

- **Interactive API documentation:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health
- **Root endpoint:** http://127.0.0.1:8000/

The interactive documentation lets you test the API directly from your browser without building a frontend.

## 7. How to Test the API

Open http://127.0.0.1:8000/docs.

Expand the endpoint you want to test, click **Try it out**, enter the required information, and click **Execute**.

### Create a product

Select `POST /skus` and use this example request:

```json
{
  "sku_code": "ADI-001-BLK-M",
  "product_name": "Adidas Black Shirt Medium",
  "category": "Apparel",
  "is_active": true
}
```

This creates a product record in the local SQLite database.

### View all products

Select `GET /skus` and click **Execute** to retrieve all stored SKUs.

### View one product

Select `GET /skus/{sku_id}` and enter a product ID, such as `1`.

### Update a product

Select `PATCH /skus/{sku_id}` and enter the product ID. For example:

```json
{
  "category": "Clothing"
}
```

This updates the product's category without requiring you to submit every field.

### Delete a product

Select `DELETE /skus/{sku_id}` and enter the product ID.

**Caution:** This permanently deletes that SKU record from the local database. Only test this operation with a record you are comfortable deleting.

## 8. Understanding Some Key Terms

- **SKU (Stock Keeping Unit):** A unique identifier used to distinguish a product or product variant, such as a particular shirt size and colour.
- **GMV (Gross Merchandise Value):** The total value of merchandise sold over a specified period, before accounting for certain deductions. The exact calculation depends on the business definition used.
- **Demand forecasting:** Estimating future sales or demand using historical data and other relevant factors.
- **Inventory replenishment:** Deciding when and how much stock to order or bring into inventory.
- **API (Application Programming Interface):** A way for software systems to communicate and exchange data.
- **CRUD:** Create, Read, Update, and Delete — the four basic operations for managing data.

## 9. Development Roadmap

The project will be developed incrementally.

- [x] Set up the Python backend.
- [x] Connect the application to a local SQLite database.
- [x] Create the SKU database table.
- [x] Implement SKU create, read, update, and delete endpoints.
- [x] Add interactive API documentation using FastAPI.
- [ ] Add automated tests and improve error handling.
- [ ] Import daily sales and inventory Excel reports.
- [ ] Validate and store historical sales and stock data.
- [ ] Forecast future sales, orders, units sold, and GMV.
- [ ] Generate SKU-level replenishment recommendations.
- [ ] Automate report processing and output generation.
- [ ] Build a user-friendly frontend dashboard.

## 10. Learning Objectives

This project is also a practical learning exercise in:

- Python backend development.
- REST API design.
- Database operations and SQL fundamentals.
- Data validation and error handling.
- Git and GitHub version control.
- Data analysis and forecasting.
- Supply chain and inventory management.

## 11. Contributing and Feedback

This project is under active development. Suggestions, feedback, and ideas for improving the system are welcome.

If you are learning Python, data analytics, or supply chain management, feel free to explore the code and follow the project's progress.

## 12. License

No open-source license has been selected yet. Unless a license is added, the project should not be assumed to be available for unrestricted reuse.

---

**Repository:** https://github.com/utunalam/supply-chain-forecast

**Current focus:** Building a reliable foundation for SKU management before adding sales forecasting and inventory replenishment capabilities.