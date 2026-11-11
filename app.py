import csv
import io
import os
import sqlite3
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, url_for, Response
from database import init_db, get_db, DB_PATH

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["DATABASE"] = DB_PATH

@app.before_request
def ensure_database():
    init_db()

@app.template_filter("money")
def money(value):
    return "${:,.2f}".format(float(value or 0))

@app.route("/")
def dashboard():
    db = get_db()
    stats = {
        "products": db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "units": db.execute("SELECT COALESCE(SUM(quantity), 0) FROM products").fetchone()[0],
        "stock_value": db.execute("SELECT COALESCE(SUM(quantity * price), 0) FROM products").fetchone()[0],
        "low_stock": db.execute("SELECT COUNT(*) FROM products WHERE quantity <= low_stock_threshold").fetchone()[0],
    }
    products = db.execute("""
        SELECT * FROM products ORDER BY
        CASE WHEN quantity <= low_stock_threshold THEN 0 ELSE 1 END,
        updated_at DESC LIMIT 6
    """).fetchall()
    movements = db.execute("""
        SELECT m.*, p.name AS product_name, p.sku
        FROM movements m JOIN products p ON p.id = m.product_id
        ORDER BY m.created_at DESC LIMIT 6
    """).fetchall()
    return render_template("dashboard.html", stats=stats, products=products, movements=movements)

@app.route("/products")
def products():
    db = get_db()
    q = request.args.get("q", "").strip()
    if q:
        rows = db.execute("""
            SELECT * FROM products
            WHERE name LIKE ? OR sku LIKE ? OR category LIKE ?
            ORDER BY name COLLATE NOCASE
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = db.execute("SELECT * FROM products ORDER BY name COLLATE NOCASE").fetchall()
    return render_template("products.html", products=rows, q=q)

def product_form_values():
    name = request.form.get("name", "").strip()
    sku = request.form.get("sku", "").strip().upper()
    category = request.form.get("category", "").strip() or "Uncategorized"
    try:
        price = float(request.form.get("price", "0"))
        quantity = int(request.form.get("quantity", "0"))
        threshold = int(request.form.get("low_stock_threshold", "5"))
    except ValueError:
        raise ValueError("Price, quantity and low-stock threshold must be valid numbers.")
    if not name or not sku:
        raise ValueError("Product name and SKU are required.")
    if price < 0 or quantity < 0 or threshold < 0:
        raise ValueError("Price, quantity and threshold cannot be negative.")
    return name, sku, category, price, quantity, threshold

@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        try:
            values = product_form_values()
            db = get_db()
            db.execute("""
                INSERT INTO products (name, sku, category, price, quantity, low_stock_threshold)
                VALUES (?, ?, ?, ?, ?, ?)
            """, values)
            db.commit()
            flash("Product added successfully.", "success")
            return redirect(url_for("products"))
        except sqlite3.IntegrityError:
            flash("That SKU already exists. Use a unique SKU.", "error")
        except (ValueError, NameError) as exc:
            flash(str(exc), "error")
    return render_template("product_form.html", product=None, title="Add product")

@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    if request.method == "POST":
        try:
            values = product_form_values()
            db.execute("""
                UPDATE products SET name=?, sku=?, category=?, price=?, quantity=?,
                    low_stock_threshold=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
            """, (*values, product_id))
            db.commit()
            flash("Product updated.", "success")
            return redirect(url_for("products"))
        except sqlite3.IntegrityError:
            flash("That SKU is already assigned to another product.", "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("product_form.html", product=product, title="Edit product")

@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    db = get_db()
    db.execute("DELETE FROM movements WHERE product_id = ?", (product_id,))
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("products"))

@app.route("/products/<int:product_id>/stock", methods=["GET", "POST"])
def stock(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    if request.method == "POST":
        movement_type = request.form.get("movement_type")
        note = request.form.get("note", "").strip()
        try:
            amount = int(request.form.get("quantity", "0"))
        except ValueError:
            amount = 0
        if amount <= 0 or movement_type not in ("IN", "OUT"):
            flash("Enter a positive quantity and choose stock in or stock out.", "error")
        elif movement_type == "OUT" and amount > product["quantity"]:
            flash("Not enough stock available for this transaction.", "error")
        else:
            delta = amount if movement_type == "IN" else -amount
            db.execute("UPDATE products SET quantity=quantity+?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                       (delta, product_id))
            db.execute("INSERT INTO movements (product_id, movement_type, quantity, note) VALUES (?, ?, ?, ?)",
                       (product_id, movement_type, amount, note))
            db.commit()
            flash("Stock movement recorded.", "success")
            return redirect(url_for("products"))
    return render_template("stock.html", product=product)

@app.route("/transactions")
def transactions():
    db = get_db()
    rows = db.execute("""
        SELECT m.*, p.name AS product_name, p.sku
        FROM movements m JOIN products p ON p.id=m.product_id
        ORDER BY m.created_at DESC
    """).fetchall()
    return render_template("transactions.html", movements=rows)

@app.route("/export.csv")
def export_csv():
    db = get_db()
    rows = db.execute("SELECT name, sku, category, price, quantity, low_stock_threshold FROM products ORDER BY name").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "SKU", "Category", "Unit price", "Quantity", "Low stock threshold"])
    for row in rows:
        writer.writerow(tuple(row))
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=stockpilot-inventory.csv"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
