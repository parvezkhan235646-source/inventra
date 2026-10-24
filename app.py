from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "inventra-demo-key"

# Simple file storage: no SQL or MongoDB
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def load_data():
    """Read products and sales from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"products": [], "sales": []}
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    # Keep older demo data working after updates.
    data.setdefault("products", [])
    data.setdefault("sales", [])
    return data


def save_data(data):
    """Save products and sales to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def money(amount):
    return f"₹{amount:.2f}"


@app.template_filter("money")
def money_filter(amount):
    return money(amount)


def low_stock_products(products):
    return [p for p in products if p["quantity"] <= p["min_stock"]]


@app.route("/")
def dashboard():
    data = load_data()
    products = data["products"]
    sales = data["sales"]
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template(
        "main.html",
        page="dashboard",
        total_products=len(products),
        total_units=sum(p["quantity"] for p in products),
        inventory_value=sum(p["price"] * p["quantity"] for p in products),
        low_stock=low_stock_products(products),
        today_sales=sum(s["total"] for s in sales if s["date"].startswith(today)),
        sales=sales[-5:][::-1]
    )


@app.route("/products")
def products():
    data = load_data()
    search = request.args.get("search", "").strip().lower()
    product_list = data["products"]
    if search:
        product_list = [p for p in product_list if
                        search in p["name"].lower() or
                        search in p["category"].lower() or
                        search == str(p["id"])]
    return render_template("main.html", page="products", products=product_list, search=search)


def save_product_from_form(product, form):
    product["name"] = form.get("name", "").strip()
    product["category"] = form.get("category", "").strip() or "General"
    product["price"] = round(float(form.get("price", "")), 2)
    product["quantity"] = int(form.get("quantity", ""))
    product["min_stock"] = int(form.get("min_stock", ""))
    if not product["name"]:
        raise ValueError("Product name is required.")
    if product["price"] < 0 or product["quantity"] < 0 or product["min_stock"] < 0:
        raise ValueError("Price and quantities cannot be negative.")


@app.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        data = load_data()
        try:
            product = {"id": max([p["id"] for p in data["products"]]) + 1}
            save_product_from_form(product, request.form)
            data["products"].append(product)
            save_data(data)
            flash(f"Product added successfully! Product ID: {product['id']}", "success")
            return redirect(url_for("products"))
        except (ValueError, KeyError):
            flash("Please enter valid product details.", "error")
    return render_template("main.html", page="product_form", product=None, page_title="Add Product")


@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    data = load_data()
    product = next((p for p in data["products"] if p["id"] == product_id), None)
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    if request.method == "POST":
        try:
            updated = dict(product)
            save_product_from_form(updated, request.form)
            product.update(updated)
            save_data(data)
            flash(f"Product ID {product_id} updated successfully.", "success")
            return redirect(url_for("products"))
        except (ValueError, KeyError):
            flash("Please enter valid product details.", "error")
    return render_template("main.html", page="product_form", product=product, page_title="Edit Product")


@app.route("/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    data = load_data()
    data["products"] = [p for p in data["products"] if p["id"] != product_id]
    save_data(data)
    flash("Product deleted.", "success")
    return redirect(url_for("products"))


@app.route("/billing", methods=["GET", "POST"])
def billing():
    data = load_data()
    available_products = [p for p in data["products"] if p["quantity"] > 0]

    if request.method == "POST":
        try:
            product_ids = request.form.getlist("product_id[]")
            quantities = request.form.getlist("quantity[]")
            discount_percent = float(request.form.get("discount", 0))
            tax_percent = float(request.form.get("tax", 0))
            if not product_ids or len(product_ids) != len(quantities):
                raise ValueError("Add at least one product to the bill.")
            if not 0 <= discount_percent <= 100 or not 0 <= tax_percent <= 100:
                raise ValueError("Discount and tax must be between 0 and 100.")

            # Combine duplicate product rows before checking stock.
            requested = {}
            for product_id_text, quantity_text in zip(product_ids, quantities):
                if not product_id_text:
                    continue
                product_id = int(product_id_text)
                quantity = int(quantity_text)
                if quantity <= 0:
                    raise ValueError("Each quantity must be at least 1.")
                requested[product_id] = requested.get(product_id, 0) + quantity
            if not requested:
                raise ValueError("Select at least one product.")

            line_items = []
            subtotal = 0
            for product_id, quantity in requested.items():
                product = next((p for p in data["products"] if p["id"] == product_id), None)
                if product is None:
                    raise ValueError("A selected product was not found.")
                if quantity > product["quantity"]:
                    raise ValueError(f"Not enough stock for {product['name']} (ID {product_id}).")
                line_total = round(product["price"] * quantity, 2)
                subtotal += line_total
                line_items.append({
                    "product_id": product["id"], "product_name": product["name"],
                    "quantity": quantity, "unit_price": product["price"], "subtotal": line_total
                })

            subtotal = round(subtotal, 2)
            discount = round(subtotal * discount_percent / 100, 2)
            tax = round((subtotal - discount) * tax_percent / 100, 2)
            total = round(subtotal - discount + tax, 2)

            # Reduce stock only after every selected item passes validation.
            for item in line_items:
                product = next(p for p in data["products"] if p["id"] == item["product_id"])
                product["quantity"] -= item["quantity"]

            now = datetime.now()
            invoice = "SW-" + now.strftime("%Y%m%d%H%M%S%f")
            sale = {
                "invoice": invoice,
                "date": now.strftime("%Y-%m-%d %H:%M:%S"),
                "line_items": line_items,
                "product_name": ", ".join(item["product_name"] for item in line_items),
                "quantity": sum(item["quantity"] for item in line_items),
                "subtotal": subtotal, "discount": discount, "tax": tax, "total": total
            }
            data["sales"].append(sale)
            save_data(data)
            return render_template("main.html", page="receipt", sale=sale)
        except (ValueError, KeyError) as error:
            flash(f"Billing error: {error}", "error")
            # A clear error is shown below; no stock is changed for invalid bills.
            data = load_data()
            available_products = [p for p in data["products"] if p["quantity"] > 0]

    return render_template("main.html", page="billing", products=available_products)


@app.route("/reports")
def reports():
    data = load_data()
    sales = data["sales"][::-1]
    return render_template("main.html", page="reports", sales=sales,
                           total_revenue=sum(s["total"] for s in data["sales"]),
                           total_orders=len(sales))


if __name__ == "__main__":
    # Create sample products on the first run only.
    if not os.path.exists(DATA_FILE):
        save_data({"products": [
            {"id": 1, "name": "Laptop", "category": "Electronics", "price": 50000.0, "quantity": 10, "min_stock": 8},
            {"id": 2, "name": "Mouse", "category": "Electronics", "price": 500.0, "quantity": 30, "min_stock": 10},
            {"id": 3, "name": "Mobile phone", "category": "Electronics", "price": 15000.0, "quantity": 6, "min_stock": 5}
        ], "sales": []})
    app.run(debug=True)
