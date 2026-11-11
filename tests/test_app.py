import os
import tempfile
import pytest

@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test_stockpilot.db"
    monkeypatch.setenv("STOCKPILOT_DATABASE", str(db_path))
    import database
    database.DB_PATH = str(db_path)
    import app as app_module
    app_module.app.config.update(TESTING=True, SECRET_KEY="test")
    database.init_db()
    with app_module.app.test_client() as client:
        yield client

def add_product(client, sku="TEST-001", quantity="10"):
    return client.post("/products/add", data={
        "name": "Test Keyboard", "sku": sku, "category": "Accessories",
        "price": "25.50", "quantity": quantity, "low_stock_threshold": "3"
    }, follow_redirects=True)

def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Good to see you" in response.data

def test_add_and_search_product(client):
    response = add_product(client)
    assert response.status_code == 200
    assert b"Test Keyboard" in response.data
    assert client.get("/products?q=TEST-001").status_code == 200

def test_duplicate_sku_rejected(client):
    add_product(client)
    response = client.post("/products/add", data={
        "name": "Another product", "sku": "TEST-001", "category": "Other",
        "price": "1", "quantity": "1", "low_stock_threshold": "1"
    }, follow_redirects=True)
    assert b"SKU already exists" in response.data

def test_stock_in_and_out(client):
    add_product(client)
    response = client.post("/products/1/stock", data={
        "movement_type": "IN", "quantity": "5", "note": "Delivery"
    }, follow_redirects=True)
    assert b"Stock movement recorded" in response.data
    response = client.post("/products/1/stock", data={
        "movement_type": "OUT", "quantity": "2", "note": "Sale"
    }, follow_redirects=True)
    assert b"Stock movement recorded" in response.data

def test_prevent_negative_stock(client):
    add_product(client, quantity="2")
    response = client.post("/products/1/stock", data={
        "movement_type": "OUT", "quantity": "3"
    }, follow_redirects=True)
    assert b"Not enough stock" in response.data

def test_csv_export(client):
    add_product(client)
    response = client.get("/export.csv")
    assert response.status_code == 200
    assert b"Test Keyboard" in response.data
