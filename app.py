import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime, date
import io

# ---------------------------------------------------------------------------
# APP CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Small Business Assistant", page_icon="🏪", layout="wide")

DB_NAME = "business.db"


# ---------------------------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            business_name TEXT,
            currency TEXT DEFAULT 'Rs.',
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            cost REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            low_stock_alert INTEGER DEFAULT 5,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER,
            customer_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            unit_price REAL,
            total REAL,
            sale_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT,
            description TEXT,
            amount REAL,
            expense_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task TEXT,
            done INTEGER DEFAULT 0,
            due_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password, business_name):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password, business_name, created_at) VALUES (?, ?, ?, ?)",
            (username, hash_pw(password), business_name, str(datetime.now())),
        )
        conn.commit()
        return True, "Account created! Please log in."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()


def login_user(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, username, business_name, currency FROM users WHERE username=? AND password=?",
        (username, hash_pw(password)),
    )
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "business_name": row[2], "currency": row[3]}
    return None


def run_query(query, params=(), fetch=False):
    conn = get_conn()
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data


def df_query(query, params=()):
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None


# ---------------------------------------------------------------------------
# LOGIN / REGISTER PAGE
# ---------------------------------------------------------------------------
def auth_page():
    st.title("🏪 Small Business Assistant")
    st.caption("Manage products, sales, expenses & customers — all in one place.")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                user = login_user(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            business_name = st.text_input("Business name")
            submitted = st.form_submit_button("Create Account")
            if submitted:
                if not new_username or not new_password:
                    st.error("Username and password are required.")
                else:
                    ok, msg = register_user(new_username, new_password, business_name)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------
def dashboard_page(uid, currency):
    st.header("📊 Dashboard")

    products = df_query("SELECT * FROM products WHERE user_id=?", (uid,))
    sales = df_query("SELECT * FROM sales WHERE user_id=?", (uid,))
    expenses = df_query("SELECT * FROM expenses WHERE user_id=?", (uid,))

    total_sales = sales["total"].sum() if not sales.empty else 0
    total_expenses = expenses["amount"].sum() if not expenses.empty else 0
    profit = total_sales - total_expenses
    low_stock = products[products["stock"] <= products["low_stock_alert"]] if not products.empty else pd.DataFrame()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales", f"{currency} {total_sales:,.2f}")
    c2.metric("Total Expenses", f"{currency} {total_expenses:,.2f}")
    c3.metric("Net Profit", f"{currency} {profit:,.2f}")
    c4.metric("Products", len(products))

    if not low_stock.empty:
        st.warning(f"⚠️ {len(low_stock)} product(s) are low on stock!")
        st.dataframe(low_stock[["name", "stock", "low_stock_alert"]], use_container_width=True, hide_index=True)

    st.subheader("Recent Sales")
    if not sales.empty:
        st.dataframe(sales.sort_values("sale_date", ascending=False).head(10), use_container_width=True, hide_index=True)
    else:
        st.info("No sales recorded yet.")


# ---------------------------------------------------------------------------
# PRODUCTS PAGE
# ---------------------------------------------------------------------------
def products_page(uid):
    st.header("📦 Products & Inventory")

    with st.expander("➕ Add New Product"):
        with st.form("add_product", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Product name")
            category = col2.text_input("Category")
            price = col1.number_input("Selling price", min_value=0.0, step=1.0)
            cost = col2.number_input("Cost price", min_value=0.0, step=1.0)
            stock = col1.number_input("Initial stock", min_value=0, step=1)
            alert = col2.number_input("Low stock alert threshold", min_value=0, step=1, value=5)
            submitted = st.form_submit_button("Add Product")
            if submitted and name:
                run_query(
                    "INSERT INTO products (user_id, name, category, price, cost, stock, low_stock_alert) VALUES (?,?,?,?,?,?,?)",
                    (uid, name, category, price, cost, stock, alert),
                )
                st.success(f"Added '{name}'")
                st.rerun()

    products = df_query("SELECT * FROM products WHERE user_id=?", (uid,))
    st.subheader("Product List")
    if products.empty:
        st.info("No products yet. Add one above.")
        return

    st.dataframe(products.drop(columns=["user_id"]), use_container_width=True, hide_index=True)

    st.subheader("Update Stock / Delete Product")
    prod_names = products["name"].tolist()
    selected = st.selectbox("Select product", prod_names)
    prod_row = products[products["name"] == selected].iloc[0]

    col1, col2, col3 = st.columns(3)
    new_stock = col1.number_input("New stock value", min_value=0, value=int(prod_row["stock"]), step=1)
    if col1.button("Update Stock"):
        run_query("UPDATE products SET stock=? WHERE id=?", (new_stock, int(prod_row["id"])))
        st.success("Stock updated.")
        st.rerun()

    if col2.button("🗑️ Delete Product"):
        run_query("DELETE FROM products WHERE id=?", (int(prod_row["id"]),))
        st.warning(f"Deleted '{selected}'")
        st.rerun()
        
# ---------------------------------------------------------------------------
# CUSTOMERS PAGE
# ---------------------------------------------------------------------------
def customers_page(uid):
    st.header("👥 Customers")

    with st.expander("➕ Add New Customer"):
        with st.form("add_customer", clear_on_submit=True):
            name = st.text_input("Customer name")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Add Customer")
            if submitted and name:
                run_query(
                    "INSERT INTO customers (user_id, name, phone, email, notes) VALUES (?,?,?,?,?)",
                    (uid, name, phone, email, notes),
                )
                st.success(f"Added customer '{name}'")
                st.rerun()

    customers = df_query("SELECT * FROM customers WHERE user_id=?", (uid,))
    if customers.empty:
        st.info("No customers yet.")
        return
    st.dataframe(customers.drop(columns=["user_id"]), use_container_width=True, hide_index=True)

    selected = st.selectbox("Select customer to delete", customers["name"].tolist())
    if st.button("🗑️ Delete Customer"):
        cust_id = int(customers[customers["name"] == selected].iloc[0]["id"])
        run_query("DELETE FROM customers WHERE id=?", (cust_id,))
        st.warning(f"Deleted '{selected}'")
        st.rerun()


# ---------------------------------------------------------------------------
# SALES / INVOICE PAGE
# ---------------------------------------------------------------------------
def sales_page(uid, currency):
    st.header("🧾 Sales & Invoice")

    products = df_query("SELECT * FROM products WHERE user_id=?", (uid,))
    customers = df_query("SELECT * FROM customers WHERE user_id=?", (uid,))

    if products.empty:
        st.info("Add products first before recording a sale.")
        return

    with st.form("record_sale", clear_on_submit=True):
        prod_name = st.selectbox("Product", products["name"].tolist())
        cust_name = st.selectbox("Customer (optional)", ["-- Walk-in --"] + customers["name"].tolist())
        qty = st.number_input("Quantity", min_value=1, step=1, value=1)
        submitted = st.form_submit_button("Record Sale")

        if submitted:
            prod_row = products[products["name"] == prod_name].iloc[0]
            available = int(prod_row["stock"])
            if qty > available:
                st.error(f"Only {available} units in stock.")
            else:
                unit_price = float(prod_row["price"])
                total = unit_price * qty
                cust_id = None
                if cust_name != "-- Walk-in --":
                    cust_id = int(customers[customers["name"] == cust_name].iloc[0]["id"])

                run_query(
                    "INSERT INTO sales (user_id, product_id, customer_id, product_name, quantity, unit_price, total, sale_date) VALUES (?,?,?,?,?,?,?,?)",
                    (uid, int(prod_row["id"]), cust_id, prod_name, qty, unit_price, total, str(date.today())),
                )
                run_query("UPDATE products SET stock = stock - ? WHERE id=?", (qty, int(prod_row["id"])))

                st.success(f"Sale recorded: {qty} x {prod_name} = {currency} {total:,.2f}")

                invoice_text = f"""
                    INVOICE
                    -------
                    Date: {date.today()}
                    Customer: {cust_name}
                    Product: {prod_name}
                    Quantity: {qty}
                    Unit Price: {currency} {unit_price:,.2f}
                    Total: {currency} {total:,.2f}
                """
                st.download_button(
                    "⬇️ Download Invoice (.txt)",
                    invoice_text,
                    file_name=f"invoice_{prod_name}_{date.today()}.txt",
                )
                st.rerun()

    st.subheader("All Sales")
    sales = df_query("SELECT * FROM sales WHERE user_id=? ORDER BY sale_date DESC", (uid,))
    if not sales.empty:
        st.dataframe(sales.drop(columns=["user_id"]), use_container_width=True, hide_index=True)
    else:
        st.info("No sales yet.")


# ---------------------------------------------------------------------------
# EXPENSES PAGE
# ---------------------------------------------------------------------------
def expenses_page(uid, currency):
    st.header("💸 Expenses")

    with st.form("add_expense", clear_on_submit=True):
        category = st.selectbox("Category", ["Rent", "Utilities", "Supplies", "Salaries", "Marketing", "Other"])
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, step=1.0)
        exp_date = st.date_input("Date", value=date.today())
        submitted = st.form_submit_button("Add Expense")
        if submitted and amount > 0:
            run_query(
                "INSERT INTO expenses (user_id, category, description, amount, expense_date) VALUES (?,?,?,?,?)",
                (uid, category, description, amount, str(exp_date)),
            )
            st.success(f"Added expense: {currency} {amount:,.2f}")
            st.rerun()

    expenses = df_query("SELECT * FROM expenses WHERE user_id=? ORDER BY expense_date DESC", (uid,))
    if not expenses.empty:
        st.dataframe(expenses.drop(columns=["user_id"]), use_container_width=True, hide_index=True)
    else:
        st.info("No expenses recorded yet.")


# ---------------------------------------------------------------------------
# TASKS PAGE
# ---------------------------------------------------------------------------
def tasks_page(uid):
    st.header("✅ Tasks")

    with st.form("add_task", clear_on_submit=True):
        task = st.text_input("Task description")
        due = st.date_input("Due date", value=date.today())
        submitted = st.form_submit_button("Add Task")
        if submitted and task:
            run_query("INSERT INTO tasks (user_id, task, due_date) VALUES (?,?,?)", (uid, task, str(due)))
            st.rerun()

    tasks = df_query("SELECT * FROM tasks WHERE user_id=? ORDER BY done, due_date", (uid,))
    if tasks.empty:
        st.info("No tasks yet.")
        return

    for _, row in tasks.iterrows():
        col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
        done = col1.checkbox("", value=bool(row["done"]), key=f"task_{row['id']}")
        if done != bool(row["done"]):
            run_query("UPDATE tasks SET done=? WHERE id=?", (int(done), int(row["id"])))
            st.rerun()
        label = f"~~{row['task']}~~" if done else row["task"]
        col2.markdown(f"{label}  \n📅 Due: {row['due_date']}")
        if col3.button("🗑️", key=f"del_task_{row['id']}"):
            run_query("DELETE FROM tasks WHERE id=?", (int(row["id"]),))
            st.rerun()


# ---------------------------------------------------------------------------
# ANALYTICS PAGE
# ---------------------------------------------------------------------------
def analytics_page(uid, currency):
    st.header("📈 Analytics")

    sales = df_query("SELECT * FROM sales WHERE user_id=?", (uid,))
    expenses = df_query("SELECT * FROM expenses WHERE user_id=?", (uid,))

    if sales.empty and expenses.empty:
        st.info("No data yet to analyze. Record some sales/expenses first.")
        return

    if not sales.empty:
        sales["sale_date"] = pd.to_datetime(sales["sale_date"])
        daily_sales = sales.groupby(sales["sale_date"].dt.date)["total"].sum()
        st.subheader("Sales Over Time")
        st.line_chart(daily_sales)

        st.subheader("Top Selling Products")
        top_products = sales.groupby("product_name")["quantity"].sum().sort_values(ascending=False).head(10)
        st.bar_chart(top_products)

    if not expenses.empty:
        st.subheader("Expenses by Category")
        exp_by_cat = expenses.groupby("category")["amount"].sum()
        st.bar_chart(exp_by_cat)

    total_sales = sales["total"].sum() if not sales.empty else 0
    total_expenses = expenses["amount"].sum() if not expenses.empty else 0
    st.metric("Overall Profit", f"{currency} {total_sales - total_expenses:,.2f}")
# ---------------------------------------------------------------------------
# REPORTS / BACKUP PAGE
# ---------------------------------------------------------------------------
def reports_page(uid):
    st.header("📁 Reports & Backup")

    st.subheader("Download Reports (CSV)")
    tables = {
        "Products": "products",
        "Sales": "sales",
        "Expenses": "expenses",
        "Customers": "customers",
    }
    for label, table in tables.items():
        df = df_query(f"SELECT * FROM {table} WHERE user_id=?", (uid,))
        if not df.empty:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(f"⬇️ Download {label} CSV", csv, file_name=f"{table}.csv", key=f"dl_{table}")
        else:
            st.caption(f"No data yet for {label}.")

    st.divider()
    st.subheader("Full Backup")
    st.caption("Downloads all your business data as a single CSV bundle (zipped in one file per table above). For a full database file backup, download each table above and store safely.")

    st.divider()
    st.subheader("Restore from CSV")
    st.caption("Upload a previously downloaded CSV to re-import data into a table.")
    restore_table = st.selectbox("Table to restore into", list(tables.values()))
    uploaded = st.file_uploader("Upload CSV file", type="csv")
    if uploaded and st.button("Import Data"):
        try:
            df = pd.read_csv(uploaded)
            conn = get_conn()
            df.to_sql(restore_table, conn, if_exists="append", index=False)
            conn.close()
            st.success(f"Imported {len(df)} rows into {restore_table}.")
        except Exception as e:
            st.error(f"Import failed: {e}")


# ---------------------------------------------------------------------------
# SETTINGS PAGE
# ---------------------------------------------------------------------------
def settings_page(user):
    st.header("⚙️ Settings")

    with st.form("settings_form"):
        business_name = st.text_input("Business name", value=user["business_name"] or "")
        currency = st.text_input("Currency symbol", value=user["currency"] or "Rs.")
        submitted = st.form_submit_button("Save Settings")
        if submitted:
            run_query(
                "UPDATE users SET business_name=?, currency=? WHERE id=?",
                (business_name, currency, user["id"]),
            )
            st.session_state.user["business_name"] = business_name
            st.session_state.user["currency"] = currency
            st.success("Settings saved.")
            st.rerun()

    st.divider()
    if st.button("🚪 Log Out"):
        st.session_state.user = None
        st.rerun()


# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------
def main_app():
    user = st.session_state.user
    uid = user["id"]
    currency = user["currency"] or "Rs."

    st.sidebar.title(f"🏪 {user['business_name'] or 'My Business'}")
    st.sidebar.caption(f"Logged in as {user['username']}")

    page = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Products", "Sales", "Customers", "Expenses", "Tasks", "Analytics", "Reports", "Settings"],
    )

    if page == "Dashboard":
        dashboard_page(uid, currency)
    elif page == "Products":
        products_page(uid)
    elif page == "Sales":
        sales_page(uid, currency)
    elif page == "Customers":
        customers_page(uid)
    elif page == "Expenses":
        expenses_page(uid, currency)
    elif page == "Tasks":
        tasks_page(uid)
    elif page == "Analytics":
        analytics_page(uid, currency)
    elif page == "Reports":
        reports_page(uid)
    elif page == "Settings":
        settings_page(user)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
if st.session_state.user is None:
    auth_page()
else:
    main_app()
    
