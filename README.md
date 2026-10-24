 Inventra — Smart Inventory Management

Inventra is a beginner-friendly inventory and billing project built with Python, Flask, Jinja templates, HTML, and CSS. Product and sales data is stored in a local `data.json` file (no SQL, SQLite, or MongoDB required).

## Run on Windows
Open the extracted project folder in VS Code, then run these commands in its terminal:
   ```powershell
   py -m pip install Flask
   py app.py
   ```
Open http://127.0.0.1:5000 in your browser.

The project-root `app.py` launcher starts the Flask application from its existing application folder, which contains the templates, styles, and `data.json`. You can also open that folder directly and run `py app.py` there.

## Features
- Live dashboard with inventory value, today's sales, and low-stock alerts
- Add, search by product name/category/ID, edit, restock, and delete products
- Product IDs shown in the catalog, checkout, and invoices
- Multi-product checkout with discount and tax calculations
- Automatic stock deduction after a valid sale
- Printable invoice and sales history reports
- Responsive layout for desktop and mobile screens
- One Jinja template handles the dashboard, catalog, product form, checkout, invoice, and reports

## Storage
The app reads and writes `data.json` in the application folder, independently of the current terminal directory. Existing products and sales remain in the same format. If `data.json` is missing, the first run creates three sample products.

## Demo idea
Create one invoice with 2 notebooks (₹50 each) and 3 blue pens (₹10 each). Subtotal = ₹130 before discount or tax. The invoice lists both products and stock is reduced for both. New invoices use the `SW-` prefix; existing invoice numbers are preserved.

## Important
This is a local hackathon demo. JSON storage is simple but is not ideal for simultaneous users or large datasets. Do not expose Flask's development server publicly.
