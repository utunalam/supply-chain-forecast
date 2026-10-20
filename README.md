# Supply Chain Forecasting System

A beginner-friendly backend API built with Python, FastAPI, SQLAlchemy, and SQLite to manage product and SKU information.

This project is the foundation of a Supply Chain Forecasting System. The current version focuses on SKU management through CRUD operations (Create, Read, Update, and Delete). Sales forecasting, inventory analysis, Excel report processing, and replenishment recommendations are planned for future development.

**Project status:** In development  
**Current version:** 0.1.0

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Local Setup Instructions](#4-local-setup-instructions)
5. [Testing the API](#5-testing-the-api)
6. [API Endpoints](#6-api-endpoints)
7. [How the Backend Works](#7-how-the-backend-works)
8. [Development Roadmap](#8-development-roadmap)

## 1. Project Overview

Managing product information is an important part of supply chain management. Before a system can forecast demand or recommend inventory replenishment, it needs a reliable way to store and retrieve product data.

The current backend allows users to:

- Create new SKU records.
- Retrieve all SKUs or a specific SKU.
- Update selected SKU fields.
- Delete SKU records.
- Check whether the API is running.
- Validate incoming data using Pydantic schemas.

The application uses SQLAlchemy ORM to interact with a local SQLite database.

The long-term goal is to expand the system to process daily sales and inventory reports, forecast demand, and recommend SKU-level replenishment quantities.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Main programming language |
| FastAPI | Backend API framework |
| SQLAlchemy | Object-relational mapper (ORM) for database operations |
| SQLite | Local database |
| Pydantic | Request validation and response schemas |
| Uvicorn | Runs the API server |
| Git and GitHub | Version control and project hosting |

## 3. Project Structure

```text
supply-chain-forecast/
├── backend/
│   ├── .venv/                 # Local Python environment
│   ├── requirements.txt       # Python dependencies
│   ├── main.py                # API endpoints and application setup
│   ├── database.py            # SQLAlchemy engine and sessions
│   ├── models.py              # SQLAlchemy database models
│   ├── schemas.py             # Request and response validation
│   └── supply_chain.db        # Local SQLite database
├── data/
│   ├── incoming/              # Planned input reports
│   └── archive/               # Planned archived reports
├── logs/                      # Planned application logs
├── reports/                   # Planned generated reports
├── .gitignore
└── README.md
```

Some folders and files are planned for future features and may not yet contain application code or data.

The `.venv` directory contains the project's local Python environment and should not be committed to GitHub.

## 4. Local Setup Instructions

These instructions use Windows PowerShell.

### Step 1: Clone the repository

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

If PowerShell blocks script execution, you can allow scripts for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment again.

### Step 4: Install dependencies

Make sure the terminal is in the `backend` directory and the virtual environment is activated.

```powershell
python -m pip install -r requirements.txt
```

The dependencies are defined in `backend/requirements.txt`, including FastAPI, Uvicorn, and SQLAlchemy.

### Step 5: Run the API server

From the `backend` directory, run:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Keep the terminal open while using the API.

The `--reload` option automatically restarts the development server when Python files change.

### Step 6: Open the API documentation

Open these URLs in your browser:

- **Interactive API documentation:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health
- **Root endpoint:** http://127.0.0.1:8000/

FastAPI generates interactive API documentation automatically, allowing you to test endpoints without building a frontend.

## 5. Testing the API

Open http://127.0.0.1:8000/docs.

For each endpoint:

1. Expand the endpoint.
2. Click **Try it out**.
3. Enter the required parameters or JSON request body.
4. Click **Execute**.
5. Review the HTTP status code and response body.

### Create a SKU

Select `POST /skus` and enter this example:

```json
{
  "sku_code": "ADI-001-BLK-M",
  "product_name": "Adidas Black Shirt Medium",
  "category": "Apparel",
  "is_active": true
}
```

A successful response returns `201 Created` and the newly created SKU, including its database-generated ID and creation timestamp.

The actual ID and timestamp depend on the database state and execution time.

**Important:** Use a unique SKU code. Submitting a code that already exists returns `409 Conflict`.

### Retrieve all SKUs

Select `GET /skus` and click **Execute** to retrieve all stored SKU records.

No input parameters are required.

### Retrieve one SKU

Select `GET /skus/{sku_id}` and enter an existing product ID, such as `1` or `4`, depending on your database.

A successful request returns `200 OK`. An ID that does not exist returns `404 Not Found`.

### Update a SKU

Select `PATCH /skus/{sku_id}` and enter the product ID.

For example, to update only the category:

```json
{
  "category": "Clothing"
}
```

Only the supplied field is intended to change.

**Important:** Replace all example values in Swagger's request body with the values you actually intend to submit. Do not submit placeholder values such as `"string"` unless you deliberately want to save that text.

### Delete a SKU

Select `DELETE /skus/{sku_id}` and enter the product ID.

**Warning:** Deleting a SKU permanently removes that record from the local database. Use this endpoint carefully when testing.

## 6. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Displays an API status message |
| `GET` | `/health` | Checks API availability |
| `POST` | `/skus` | Creates a new SKU |
| `GET` | `/skus` | Lists all SKUs |
| `GET` | `/skus/{sku_id}` | Retrieves one SKU by ID |
| `PATCH` | `/skus/{sku_id}` | Updates selected SKU fields |
| `DELETE` | `/skus/{sku_id}` | Deletes a SKU |

### Common HTTP status codes

| Status code | Meaning |
|---|---|
| `200 OK` | Request completed successfully |
| `201 Created` | A new SKU was created |
| `400 Bad Request` | The update request is invalid, such as an empty update |
| `404 Not Found` | The requested SKU does not exist |
| `409 Conflict` | The SKU code already exists |
| `422 Unprocessable Entity` | Request validation failed |

## 7. How the Backend Works

The backend is divided into four main Python files.

### `main.py` — API endpoints

Defines the FastAPI application and the endpoints for creating, retrieving, updating, and deleting SKUs.

It also uses dependency injection to obtain database sessions for requests.

### `database.py` — Database connection

Configures the SQLAlchemy engine, session factory, and database base class.

The SQLite database is stored beside `database.py`, so the database location does not depend on the terminal's current working directory.

The `get_db()` dependency provides a database session to an endpoint and closes it when the request finishes.

### `models.py` — Database model

Defines the `SKU` SQLAlchemy model, which maps Python attributes to columns in the `skus` database table.

The model includes:

- `id`
- `sku_code`
- `product_name`
- `category`
- `is_active`
- `created_at`

### `schemas.py` — Request and response validation

Defines the Pydantic schemas used to validate incoming data and structure API responses.

- `SKUCreate` defines the fields required or accepted when creating a SKU.
- `SKUUpdate` defines the fields that can be supplied for a partial update.
- `SKUResponse` defines the fields returned to API clients.

### What is SQLAlchemy ORM?

ORM stands for **Object-Relational Mapper**.

Instead of manually writing SQL statements for every database operation, SQLAlchemy lets the application work with Python objects that represent database records.

For example:

```python
db.add(new_sku)
db.commit()
db.refresh(new_sku)
```

These operations add a new SKU object to the database session, save the transaction, and refresh the object with the saved database values.

This approach separates database operations from API request handling and makes the code easier to maintain as the project grows.

## 8. Development Roadmap

### Completed

- [x] Set up the FastAPI backend.
- [x] Connect to a local SQLite database.
- [x] Define the SQLAlchemy database model.
- [x] Implement SKU CRUD endpoints.
- [x] Add Pydantic request and response schemas.
- [x] Generate interactive API documentation.
- [x] Configure Python dependencies in `requirements.txt`.

### Planned

- [ ] Add automated tests.
- [ ] Import daily sales and inventory Excel reports.
- [ ] Store and validate historical data.
- [ ] Forecast sales, orders, units, and GMV.
- [ ] Generate SKU-level replenishment recommendations.
- [ ] Automate report processing.
- [ ] Build a frontend dashboard.

The current version is the foundation of the larger system. The planned forecasting and replenishment features will be developed in later stages.
