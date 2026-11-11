# StockPilot — Inventory Management System

StockPilot helps small shops and individuals track inventory without spreadsheets. Add products, record stock in and out, get low-stock alerts, and export your data to CSV. It runs locally on Windows with Python, Flask and SQLite, and needs no database server.

## Features

- Dashboard with product count, unit count, stock value and low-stock metrics
- Create, edit, search and delete products
- Track stock-in and stock-out movements with notes
- Prevent stock-out transactions that exceed available quantity
- Low-stock highlighting based on each product's threshold
- Transaction history
- Export current inventory to CSV
- SQLite persistence; no external database server required
- Basic automated tests

## Requirements

- Windows 10 or 11
- Python 3.10 or newer
- Internet connection for the initial dependency installation

## Run on Windows

Open PowerShell in the project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks virtual-environment activation, run this once in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open **http://127.0.0.1:5000** in your browser. The SQLite database (`stockpilot.db`) is created automatically on first run.

To stop the server, press `Ctrl+C` in the terminal.

## Run tests

With the virtual environment activated:

```powershell
pytest -v
```

Tests use a temporary SQLite database and do not modify your personal inventory database.

## Project structure

```text
StockPilot/
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── products.html
│   ├── product_form.html
│   ├── stock.html
│   └── transactions.html
├── static/
│   ├── style.css
│   └── app.js
└── tests/
    └── test_app.py
```

## Data and security notes

- This is a local demonstration application, not a production multi-user inventory service.
- The default Flask secret key is for local development only. Set a strong `SECRET_KEY` environment variable before deployment.
- Do not expose the development server directly to the public internet.
- Do not commit real customer data, credentials, API keys, or confidential client files.
- Inventory values are illustrative and displayed in USD by default.
