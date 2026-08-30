# ============================================================
# SMALLBUSINESS ASSISTANT
# Version 2.0
# Python + Streamlit + SQLite + Pandas
# No AI / No Hugging Face
# ============================================================

import sqlite3
import hashlib
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SmallBusiness Assistant",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. DATABASE CONFIGURATION
# ============================================================

DB = Path("smallbusiness.db")


# ============================================================
# 3. DATABASE CONNECTION
# ============================================================

def get_connection():
    return sqlite3.connect(
        DB,
        check_same_thread=False
    )


# ============================================================
# 4. PASSWORD SECURITY
# ============================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# 5. CREATE DATABASE TABLES
# ============================================================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            business_name TEXT,
            category TEXT,
            city TEXT,
            phone TEXT,
            email TEXT,
            start_date TEXT,
            budget REAL DEFAULT 0,
            goal TEXT,
            FOREIGN KEY(user_id)
            REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            buy_price REAL DEFAULT 0,
            sell_price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 5,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment TEXT
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            expense_date TEXT NOT NULL,
            category TEXT,
            description TEXT,
            amount REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            spent REAL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_date TEXT NOT NULL,
            task TEXT NOT NULL,
            priority TEXT,
            status TEXT
        );
        """
    )

    conn.commit()
    conn.close()


# ============================================================
# 6. INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# 7. DATABASE INSERT / UPDATE / DELETE FUNCTION
# ============================================================

def execute(query, params=()):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        query,
        params
    )

    conn.commit()

    last_id = cursor.lastrowid

    conn.close()

    return last_id


# ============================================================
# 8. DATABASE READ FUNCTION
# ============================================================

def query_df(query, params=()):

    conn = get_connection()

    data = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    return data


# ============================================================
# 9. RUPEE FORMAT
# ============================================================

def rupees(value):

    return f"₹{float(value):,.2f}"


# ============================================================
# 10. SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""

if "show_profile" not in st.session_state:
    st.session_state.show_profile = False


# ============================================================
# 11. CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
        linear-gradient(
            135deg,
            #f8fafc,
            #eef2ff,
            #fff7ed
        );
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    .hero {
        padding: 30px;
        border-radius: 28px;
        background: rgba(255,255,255,0.96);
        box-shadow:
            0 12px 35px
            rgba(15,23,42,0.10);
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 40px;
        font-weight: 900;
        color: #312e81;
    }

    .hero-subtitle {
        font-size: 17px;
        color: #475569;
    }

    .feature-card {
        padding: 24px;
        border-radius: 22px;
        background: rgba(255,255,255,0.96);
        box-shadow:
            0 8px 25px
            rgba(15,23,42,0.08);
        min-height: 150px;
    }

    .feature-card h3 {
        color: #4f46e5;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 12. LOGIN / REGISTER SCREEN
# ============================================================

def authentication_screen():

    st.title("🏪 SmallBusiness Assistant")

    st.write(
        "Your simple digital business management system."
    )

    login_tab, register_tab = st.tabs(
        [
            "🔐 Login",
            "📝 Create Account"
        ]
    )

    with login_tab:

        st.subheader("Welcome Back")

        username = st.text_input(
            "👤 Username",
            key="login_username"
        )

        password = st.text_input(
            "🔑 Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "🚀 Login",
            use_container_width=True
        ):

            if not username.strip() or not password:

                st.error(
                    "Please enter username and password."
                )

            else:

                result = query_df(
                    """
                    SELECT id, username
                    FROM users
                    WHERE username = ?
                    AND password = ?
                    """,
                    (
                        username.strip(),
                        hash_password(password)
                    )
                )

                if result.empty:

                    st.error(
                        "Incorrect username or password."
                    )

                else:

                    st.session_state.logged_in = True

                    st.session_state.user_id = int(
                        result.iloc[0]["id"]
                    )

                    st.session_state.username = str(
                        result.iloc[0]["username"]
                    )

                    st.success(
                        "Login successful!"
                    )

                    st.rerun()


    with register_tab:

        st.subheader("Create New Account")

        new_username = st.text_input(
            "👤 Choose Username",
            key="new_username"
        )

        new_password = st.text_input(
            "🔑 Create Password",
            type="password",
            key="new_password"
        )

        confirm_password = st.text_input(
            "🔐 Confirm Password",
            type="password",
            key="confirm_password"
        )

        if st.button(
            "✨ Create Account",
            use_container_width=True
        ):

            username_clean = new_username.strip()

            if len(username_clean) < 3:

                st.error(
                    "Username must contain at least 3 characters."
                )

            elif len(new_password) < 4:

                st.error(
                    "Password must contain at least 4 characters."
                )

            elif new_password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                existing = query_df(
                    """
                    SELECT id
                    FROM users
                    WHERE username = ?
                    """,
                    (username_clean,)
                )

                if not existing.empty:

                    st.error(
                        "This username already exists."
                    )

                else:

                    user_id = execute(
                        """
                        INSERT INTO users
                        (
                            username,
                            password,
                            created_at
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            username_clean,
                            hash_password(new_password),
                            datetime.now().isoformat()
                        )
                    )

                    execute(
                        """
                        INSERT INTO profiles
                        (
                            user_id,
                            full_name,
                            business_name,
                            category,
                            city,
                            phone,
                            email,
                            start_date,
                            budget,
                            goal
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            "",
                            "",
                            "Retail",
                            "",
                            "",
                            "",
                            str(date.today()),
                            0,
                            ""
                        )
                    )

                    st.success(
                        "Account created successfully!"
                    )

                    st.info(
                        "Now open the Login tab and login."
                    )


# ============================================================
# 13. SHOW LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    authentication_screen()

    st.stop()


# ============================================================
# END OF PART 1
# ============================================================
# ============================================================
# PART 2 — MAIN APPLICATION
# ============================================================


# ============================================================
# 14. USER ID
# ============================================================

USER_ID = st.session_state.user_id


# ============================================================
# 15. LOAD USER PROFILE
# ============================================================

profile_df = query_df(
    """
    SELECT *
    FROM profiles
    WHERE user_id = ?
    """,
    (USER_ID,)
)

if profile_df.empty:

    execute(
        """
        INSERT INTO profiles
        (
            user_id,
            full_name,
            business_name,
            category,
            city,
            phone,
            email,
            start_date,
            budget,
            goal
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            USER_ID,
            "",
            "",
            "Retail",
            "",
            "",
            "",
            str(date.today()),
            0,
            ""
        )
    )

    profile_df = query_df(
        """
        SELECT *
        FROM profiles
        WHERE user_id = ?
        """,
        (USER_ID,)
    )


profile = profile_df.iloc[0]


full_name = str(
    profile["full_name"] or ""
).strip()

business_name = str(
    profile["business_name"] or ""
).strip()

category = str(
    profile["category"] or "Retail"
).strip()

city = str(
    profile["city"] or ""
).strip()


if not full_name:

    full_name = st.session_state.username


if not business_name:

    business_name = "My Business"


# ============================================================
# 16. SIDEBAR
# ============================================================

st.sidebar.title("🏪 SmallBusiness")

st.sidebar.caption(
    "Plan • Track • Analyse • Grow"
)

st.sidebar.markdown("---")

st.sidebar.write(
    f"👤 **{full_name}**"
)

st.sidebar.write(
    f"🏪 **{business_name}**"
)

if city:

    st.sidebar.write(
        f"📍 **{city}**"
    )

st.sidebar.markdown("---")


# ============================================================
# 17. NAVIGATION
# ============================================================

PAGES = [

    "🏠 Dashboard",

    "👤 My Profile",

    "📦 Inventory",

    "💵 Sales",

    "💸 Expenses",

    "👥 Customers",

    "📊 Analytics",

    "🧮 Calculators",

    "📋 Tasks & Goals",

    "📥 Reports",

    "📚 Business Guide",

    "⚙️ Settings"

]


page = st.sidebar.radio(
    "📌 MENU",
    PAGES
)


# ============================================================
# 18. LOGOUT
# ============================================================

st.sidebar.markdown("---")

if st.sidebar.button(
    "🚪 Logout",
    use_container_width=True
):

    st.session_state.logged_in = False

    st.session_state.user_id = None

    st.session_state.username = ""

    st.rerun()


# ============================================================
# 19. DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    sales_data = query_df(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS total
        FROM sales
        WHERE user_id = ?
        """,
        (USER_ID,)
    )

    expense_data = query_df(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = ?
        """,
        (USER_ID,)
    )

    total_sales = float(
        sales_data.iloc[0]["total"]
    )

    total_expenses = float(
        expense_data.iloc[0]["total"]
    )

    net_result = (
        total_sales - total_expenses
    )

    product_count = int(
        query_df(
            """
            SELECT COUNT(*) AS total
            FROM products
            WHERE user_id = ?
            """,
            (USER_ID,)
        ).iloc[0]["total"]
    )

    customer_count = int(
        query_df(
            """
            SELECT COUNT(*) AS total
            FROM customers
            WHERE user_id = ?
            """,
            (USER_ID,)
        ).iloc[0]["total"]
    )

    pending_tasks = int(
        query_df(
            """
            SELECT COUNT(*) AS total
            FROM tasks
            WHERE user_id = ?
            AND status != 'Completed'
            """,
            (USER_ID,)
        ).iloc[0]["total"]
    )


    # --------------------------------------------------------
    # HERO
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="hero">

            <div class="hero-title">
                🏪 SmallBusiness Assistant
            </div>

            <div class="hero-subtitle">
                Your simple digital business manager
            </div>

            <br>

            <h2>
                Welcome back, {full_name} 👋
            </h2>

            <p>
                Manage your business,
                track finances,
                monitor inventory
                and plan your growth.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # MAIN METRICS
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "💵 Total Sales",
            rupees(total_sales)
        )

    with col2:

        st.metric(
            "💸 Total Expenses",
            rupees(total_expenses)
        )

    with col3:

        st.metric(
            "📈 Net Result",
            rupees(net_result)
        )

    with col4:

        st.metric(
            "👥 Customers",
            customer_count
        )


    # --------------------------------------------------------
    # BUSINESS OVERVIEW
    # --------------------------------------------------------

    st.markdown(
        "### 📌 Business Overview"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            f"""
            <div class="feature-card">

                <h3>📦 Inventory</h3>

                <div class="big-number">
                    {product_count}
                </div>

                <p>
                    Products registered
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            f"""
            <div class="feature-card">

                <h3>💰 Net Result</h3>

                <div class="big-number">
                    {rupees(net_result)}
                </div>

                <p>
                    Sales minus expenses
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            f"""
            <div class="feature-card">

                <h3>📋 Tasks</h3>

                <div class="big-number">
                    {pending_tasks}
                </div>

                <p>
                    Pending tasks
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )


    # --------------------------------------------------------
    # INVENTORY ALERT
    # --------------------------------------------------------

    st.markdown(
        "### ⚠️ Inventory Alerts"
    )

    low_stock = query_df(
        """
        SELECT
            name,
            category,
            stock,
            reorder_level
        FROM products
        WHERE user_id = ?
        AND stock <= reorder_level
        ORDER BY stock ASC
        """,
        (USER_ID,)
    )

    if low_stock.empty:

        st.success(
            "✅ All products are above their reorder level."
        )

    else:

        st.warning(
            f"⚠️ {len(low_stock)} product(s) "
            "need stock attention."
        )

        st.dataframe(
            low_stock,
            use_container_width=True,
            hide_index=True
        )


    # --------------------------------------------------------
    # RECENT SALES
    # --------------------------------------------------------

    st.markdown(
        "### 🧾 Recent Sales"
    )

    recent_sales = query_df(
        """
        SELECT
            sale_date,
            product,
            quantity,
            amount,
            payment
        FROM sales
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 8
        """,
        (USER_ID,)
    )

    if recent_sales.empty:

        st.info(
            "No sales recorded yet."
        )

    else:

        st.dataframe(
            recent_sales,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 20. MY PROFILE
# ============================================================
elif page == "👤 My Profile":

    st.header("👤 My Business Profile")

    st.caption(
        "Update your personal and business information."
    )

    categories = [
        "Retail",
        "Food",
        "Clothing",
        "Digital Services",
        "Freelancer",
        "Tuition",
        "Home Business",
        "Beauty",
        "Handmade",
        "Other"
    ]

    current_category = str(
        profile["category"] or "Retail"
    )

    category_index = (
        categories.index(current_category)
        if current_category in categories
        else 0
    )

    with st.form("profile_form"):
        col1, col2 = st.columns(2)

        with col1:

            new_full_name = st.text_input(
                "👤 Full Name",
                value=str(profile["full_name"] or "")
            )

            new_business_name = st.text_input(
                "🏪 Business Name",
                value=str(profile["business_name"] or "")
            )

            new_category = st.selectbox(
                "📂 Business Category",
                categories,
                index=category_index
            )

            new_city = st.text_input(
                "📍 City",
                value=str(profile["city"] or "")
            )

        with col2:

            new_phone = st.text_input(
                "📱 Phone",
                value=str(profile["phone"] or "")
            )

            new_email = st.text_input(
                "📧 Email",
                value=str(profile["email"] or "")
            )

            new_budget = st.number_input(
                "💰 Business Budget ₹",
                min_value=0.0,
                value=float(profile["budget"] or 0)
            )

            new_goal = st.text_area(
                "🎯 Business Goal",
                value=str(profile["goal"] or "")
            )

        submitted = st.form_submit_button(
            "💾 Save Profile",
            use_container_width=True
        )

        if submitted:

            execute(
                """
                UPDATE profiles
                SET
                    full_name = ?,
                    business_name = ?,
                    category = ?,
                    city = ?,
                    phone = ?,
                    email = ?,
                    budget = ?,
                    goal = ?
                WHERE user_id = ?
                """,
                (
                    new_full_name.strip(),
                    new_business_name.strip(),
                    new_category,
                    new_city.strip(),
                    new_phone.strip(),
                    new_email.strip(),
                    new_budget,
                    new_goal.strip(),
                    USER_ID
                )
            )

            st.success("✅ Profile updated successfully.")
            st.rerun()


# ============================================================
# 21. INVENTORY
# ============================================================

elif page == "📦 Inventory":

    st.header(
        "📦 Inventory Management"
    )

    st.caption(
        "Add products, monitor stock and identify low-stock items."
    )


    with st.form(
        "add_product"
    ):

        st.subheader(
            "➕ Add New Product"
        )

        col1, col2 = st.columns(2)

        with col1:

            product_name = st.text_input(
                "Product Name"
            )

            product_category = st.text_input(
                "Category"
            )

        with col2:

            buy_price = st.number_input(
                "Buy Price ₹",
                min_value=0.0
            )

            sell_price = st.number_input(
                "Selling Price ₹",
                min_value=0.0
            )


        col1, col2 = st.columns(2)

        with col1:

            stock = st.number_input(
                "Current Stock",
                min_value=0,
                step=1
            )

        with col2:

            reorder_level = st.number_input(
                "Reorder Level",
                min_value=0,
                value=5,
                step=1
            )


        add_product = st.form_submit_button(
            "➕ Add Product",
            use_container_width=True
        )


        if add_product:

            if not product_name.strip():

                st.error(
                    "Please enter a product name."
                )

            elif sell_price < buy_price:

                st.warning(
                    "Selling price is lower than buy price."
                )

                execute(
                    """
                    INSERT INTO products
                    (
                        user_id,
                        name,
                        category,
                        buy_price,
                        sell_price,
                        stock,
                        reorder_level,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        USER_ID,
                        product_name.strip(),
                        product_category.strip(),
                        buy_price,
                        sell_price,
                        int(stock),
                        int(reorder_level),
                        datetime.now().isoformat()
                    )
                )

                st.success(
                    "Product added successfully."
                )

                st.rerun()

            else:

                execute(
                    """
                    INSERT INTO products
                    (
                        user_id,
                        name,
                        category,
                        buy_price,
                        sell_price,
                        stock,
                        reorder_level,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        USER_ID,
                        product_name.strip(),
                        product_category.strip(),
                        buy_price,
                        sell_price,
                        int(stock),
                        int(reorder_level),
                        datetime.now().isoformat()
                    )
                )

                st.success(
                    "Product added successfully."
                )

                st.rerun()


    st.markdown("---")

    st.subheader(
        "📋 Product List"
    )

    inventory = query_df(
        """
        SELECT
            id,
            name,
            category,
            buy_price,
            sell_price,
            stock,
            reorder_level
        FROM products
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (USER_ID,)
    )


    if inventory.empty:

        st.info(
            "No products added yet."
        )

    else:

        st.dataframe(
            inventory,
            use_container_width=True,
            hide_index=True
        )

        st.markdown(
            "### 🗑️ Delete Product"
        )

        product_ids = inventory["id"].tolist()

        delete_id = st.selectbox(
            "Select Product",
            product_ids
        )

        if st.button(
            "🗑️ Delete Selected Product",
            use_container_width=True
        ):

            execute(
                """
                DELETE FROM products
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    int(delete_id),
                    USER_ID
                )
            )

            st.success(
                "Product deleted."
            )

            st.rerun()


# ============================================================
# 22. SALES
# ============================================================

elif page == "💵 Sales":

    st.header(
        "💵 Sales Tracker"
    )

    products = query_df(
        """
        SELECT *
        FROM products
        WHERE user_id = ?
        AND stock > 0
        ORDER BY name
        """,
        (USER_ID,)
    )


    if products.empty:

        st.warning(
            "Add products with available stock before recording a sale."
        )

    else:

        product_names = products["name"].tolist()

        with st.form(
            "sales_form"
        ):

            sale_date = st.date_input(
                "📅 Sale Date",
                date.today()
            )

            selected_product = st.selectbox(
                "📦 Product",
                product_names
            )

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=1,
                step=1
            )

            payment = st.selectbox(
                "💳 Payment Method",
                [
                    "Cash",
                    "UPI",
                    "Card",
                    "Bank Transfer",
                    "Other"
                ]
            )

            selected_row = products[
                products["name"]
                == selected_product
            ].iloc[0]

            available_stock = int(
                selected_row["stock"]
            )

            total_amount = (
                float(selected_row["sell_price"])
                * int(quantity)
            )

            st.info(
                f"Available Stock: {available_stock} | "
                f"Total Sale: {rupees(total_amount)}"
            )


            record_sale = st.form_submit_button(
                "➕ Record Sale",
                use_container_width=True
            )


            if record_sale:

                if quantity > available_stock:

                    st.error(
                        "Not enough stock available."
                    )

                else:

                    execute(
                        """
                        INSERT INTO sales
                        (
                            user_id,
                            sale_date,
                            product,
                            quantity,
                            amount,
                            payment
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            USER_ID,
           str(sale_date),
                            selected_product,
                            int(quantity),
                            total_amount,
                            payment
                        )
                    )

                    execute(
                        """
                        UPDATE products
                        SET stock = stock - ?
                        WHERE id = ?
                        AND user_id = ?
                        """,
                        (
                            int(quantity),
                            int(selected_row["id"]),
                            USER_ID
                        )
                    )

                    st.success(
                        "✅ Sale recorded and stock updated."
                    )

                    st.rerun()


    st.markdown("---")

    st.subheader(
        "🧾 Sales History"
    )

    sales_history = query_df(
        """
        SELECT
            id,
            sale_date,
            product,
            quantity,
            amount,
            payment
        FROM sales
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (USER_ID,)
    )


    if sales_history.empty:

        st.info(
            "No sales recorded yet."
        )

    else:

        st.dataframe(
            sales_history,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 23. EXPENSES
# ============================================================

elif page == "💸 Expenses":

    st.header(
        "💸 Expense Tracker"
    )

    with st.form(
        "expense_form"
    ):

        expense_date = st.date_input(
            "📅 Expense Date",
            date.today()
        )

        expense_category = st.selectbox(
            "📂 Category",
            [
                "Rent",
                "Salary",
                "Stock Purchase",
                "Transport",
                "Marketing",
                "Utilities",
                "Equipment",
                "Other"
            ]
        )

        description = st.text_input(
            "Description"
        )

        amount = st.number_input(
            "💰 Amount ₹",
            min_value=0.0
        )

        add_expense = st.form_submit_button(
            "➕ Add Expense",
            use_container_width=True
        )


        if add_expense:

            if amount <= 0:

                st.error(
                    "Enter an amount greater than zero."
                )

            else:

                execute(
                    """
                    INSERT INTO expenses
                    (
                        user_id,
                        expense_date,
                        category,
                        description,
                        amount
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        USER_ID,
                        str(expense_date),
                        expense_category,
                        description.strip(),
                        amount
                    )
                )

                st.success(
                    "Expense added successfully."
                )

                st.rerun()


    st.markdown("---")

    st.subheader(
        "📋 Expense History"
    )

    expense_history = query_df(
        """
        SELECT
            id,
            expense_date,
            category,
            description,
            amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (USER_ID,)
    )


    if expense_history.empty:

        st.info(
            "No expenses recorded yet."
        )

    else:

        st.dataframe(
            expense_history,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 24. CUSTOMERS
# ============================================================

elif page == "👥 Customers":

    st.header(
        "👥 Customer Manager"
    )

    with st.form(
        "customer_form"
    ):

        customer_name = st.text_input(
            "Customer Name"
        )

        customer_phone = st.text_input(
            "Phone"
        )

        customer_email = st.text_input(
            "Email"
        )

        customer_spent = st.number_input(
            "Total Spent ₹",
            min_value=0.0
        )

        add_customer = st.form_submit_button(
            "➕ Add Customer",
            use_container_width=True
        )


        if add_customer:

            if not customer_name.strip():

                st.error(
                    "Please enter customer name."
                )

            else:

                execute(
                    """
                    INSERT INTO customers
                    (
                        user_id,
                        name,
                        phone,
                        email,
                        spent,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        USER_ID,
                        customer_name.strip(),
                        customer_phone.strip(),
                        customer_email.strip(),
                        customer_spent,
                        datetime.now().isoformat()
                    )
                )

                st.success(
                    "Customer added successfully."
                )

                st.rerun()


    st.markdown("---")

    customers = query_df(
        """
        SELECT
            id,
            name,
            phone,
            email,
            spent
        FROM customers
        WHERE user_id = ?
        ORDER BY spent DESC
        """,
        (USER_ID,)
    )


    if customers.empty:

        st.info(
            "No customers added yet."
        )

    else:

        st.dataframe(
            customers,
            use_container_width=True,
            hide_index=True
  )
      # ============================================================
# PROFILE - CONTINUED
# ============================================================

            new_phone = st.text_input(
                "Phone Number",
                value=str(profile["phone"] or ""),
            )

        with col2:

            new_email = st.text_input(
                "Email",
                value=str(profile["email"] or ""),
            )

            new_city = st.text_input(
                "City",
                value=str(profile["city"] or ""),
            )

            new_budget = st.number_input(
                "Business Budget ₹",
                min_value=0.0,
                value=float(profile["budget"] or 0),
                step=100.0,
            )

            new_goal = st.text_area(
                "Business Goal",
                value=str(profile["goal"] or ""),
                placeholder="Example: Increase monthly sales and get more customers.",
            )

        if st.form_submit_button(
            "💾 Save Profile",
            use_container_width=True,
        ):

            execute(
                """
                UPDATE profiles
                SET
                    full_name = ?,
                    business_name = ?,
                    category = ?,
                    city = ?,
                    phone = ?,
                    email = ?,
                    budget = ?,
                    goal = ?
                WHERE user_id = ?
                """,
                (
                    new_full_name.strip(),
                    new_business_name.strip(),
                    new_category,
                    new_city.strip(),
                    new_phone.strip(),
                    new_email.strip(),
                    new_budget,
                    new_goal.strip(),
                    USER_ID,
                ),
            )

            st.success("✅ Profile updated successfully!")
            st.rerun()


# ============================================================
# INVENTORY
# ============================================================

elif page == "📦 Inventory":

    st.header("📦 Products & Inventory")

    st.write(
        "Add products, monitor stock and identify products "
        "that need to be reordered."
    )

    with st.form("add_product_form"):

        st.subheader("➕ Add New Product")

        col1, col2 = st.columns(2)

        with col1:

            product_name = st.text_input(
                "Product Name"
            )

            product_category = st.text_input(
                "Category"
            )

            buy_price = st.number_input(
                "Buy Price ₹",
                min_value=0.0,
                step=10.0,
            )

        with col2:

            sell_price = st.number_input(
                "Selling Price ₹",
                min_value=0.0,
                step=10.0,
            )

            stock = st.number_input(
                "Current Stock",
                min_value=0,
                step=1,
            )

            reorder_level = st.number_input(
                "Reorder Level",
                min_value=0,
                value=5,
                step=1,
            )

        if st.form_submit_button(
            "➕ Add Product",
            use_container_width=True,
        ):

            if not product_name.strip():

                st.error(
                    "Please enter a product name."
                )

            else:

                execute(
                    """
                    INSERT INTO products
                    (
                        user_id,
                        name,
                        category,
                        buy_price,
                        sell_price,
                        stock,
                        reorder_level,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        USER_ID,
                        product_name.strip(),
                        product_category.strip(),
                        buy_price,
                        sell_price,
                        int(stock),
                        int(reorder_level),
                        datetime.now().isoformat(),
                    ),
                )

                st.success(
                    "✅ Product added successfully!"
                )

                st.rerun()

    st.markdown("---")

    st.subheader("📋 Product List")

    products_df = query_df(
        """
        SELECT
            id,
            name,
            category,
            buy_price,
            sell_price,
            stock,
            reorder_level
        FROM products
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (USER_ID,),
    )

    if products_df.empty:

        st.info(
            "📦 No products added yet."
        )

    else:

        products_display = products_df.copy()

        products_display["buy_price"] = (
            products_display["buy_price"]
            .apply(rupees)
        )

        products_display["sell_price"] = (
            products_display["sell_price"]
            .apply(rupees)
        )

        st.dataframe(
            products_display,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        st.subheader("⚠️ Low Stock Products")

        low_stock = products_df[
            products_df["stock"]
            <= products_df["reorder_level"]
        ]

        if low_stock.empty:

            st.success(
                "✅ No low-stock products."
            )

        else:

            st.warning(
                f"⚠️ {len(low_stock)} product(s) "
                "need attention."
            )

            st.dataframe(
                low_stock[
                    [
                        "id",
                        "name",
                        "category",
                        "stock",
                        "reorder_level",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("---")

        st.subheader("🗑️ Delete Product")

        delete_id = st.number_input(
            "Product ID",
            min_value=1,
            step=1,
        )

        if st.button(
            "🗑️ Delete Selected Product",
            use_container_width=True,
        ):

            execute(
                """
                DELETE FROM products
                WHERE id = ? AND user_id = ?
                """,
                (
                    int(delete_id),
                    USER_ID,
                ),
            )

            st.success(
                "Product deleted."
            )

            st.rerun()


# ============================================================
# SALES
# ============================================================

elif page == "💵 Sales":

    st.header("💵 Sales Tracker")

    products_df = query_df(
        """
        SELECT *
        FROM products
        WHERE user_id = ?
        ORDER BY name
        """,
        (USER_ID,),
    )

    if products_df.empty:

        st.warning(
            "📦 Please add products first "
            "from the Inventory section."
        )

    else:

        product_names = (
            products_df["name"].tolist()
        )

        with st.form("sales_form"):

            sale_date = st.date_input(
                "📅 Sale Date",
                value=date.today(),
            )

            selected_product = st.selectbox(
                "📦 Product",
                product_names,
            )

            quantity = st.number_input(
                "🔢 Quantity",
                min_value=1,
                value=1,
                step=1,
            )

            payment_method = st.selectbox(
                "💳 Payment Method",
                [
                    "Cash",
                    "UPI",
                    "Card",
                    "Bank Transfer",
                    "Other",
                ],
            )

            selected_row = products_df[
                products_df["name"]
                == selected_product
            ].iloc[0]

            available_stock = int(
                selected_row["stock"]
            )

            selling_price = float(
                selected_row["sell_price"]
            )

            total_amount = (
                selling_price
                * int(quantity)
            )

            st.info(
                f"💰 Total Sale: "
                f"{rupees(total_amount)}\n\n"
                f"📦 Available Stock: "
                f"{available_stock}"
            )

            if st.form_submit_button(
                "💵 Record Sale",
                use_container_width=True,
            ):

                if int(quantity) > available_stock:

                    st.error(
                        "❌ Not enough stock available."
                    )

                elif selling_price <= 0:

                    st.error(
                        "❌ Selling price must be greater than ₹0."
                    )

                else:

                    execute(
                        """
                        INSERT INTO sales
                        (
                            user_id,
                            sale_date,
                            product,
                            quantity,
                            amount,
                            payment
                        )
                        VALUES (?,?,?,?,?,?)
                        """,
                        (
                            USER_ID,
                            str(sale_date),
                            selected_product,
                            int(quantity),
                            total_amount,
                            payment_method,
                        ),
                    )

                    execute(
                        """
                        UPDATE products
                        SET stock = stock - ?
                        WHERE id = ? AND user_id = ?
                        """,
                        (
                            int(quantity),
                            int(selected_row["id"]),
                            USER_ID,
                        ),
                    )

                    st.success(
                        "✅ Sale recorded and stock updated!"
                    )

                    st.rerun()

    st.markdown("---")

    st.subheader("🧾 Sales History")

    sales_df = query_df(
        """
        SELECT
            id,
            sale_date,
            product,
            quantity,
            amount,
            payment
        FROM sales
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (USER_ID,),
    )

    if sales_df.empty:

        st.info(
            "No sales recorded yet."
        )

    else:

        sales_display = sales_df.copy()

        sales_display["amount"] = (
            sales_display["amount"]
            .apply(rupees)
        )

        st.dataframe(
            sales_display,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# EXPENSES
# ============================================================

elif page == "💸 Expenses":

    st.header("💸 Expense Tracker")

    with st.form("expense_form"):

        expense_date = st.date_input(
            "📅 Expense Date",
            value=date.today(),
        )

        expense_category = st.selectbox(
            "📂 Expense Category",
            [
                "Rent",
                "Salary",
                "Stock Purchase",
                "Transport",
                "Marketing",
                "Utilities",
                "Equipment",
                "Packaging",
                "Other",
            ],
        )

        expense_description = st.text_input(
            "📝 Description"
        )

        expense_amount = st.number_input(
            "💰 Amount ₹",
            min_value=0.0,
            step=10.0,
        )

        if st.form_submit_button(
            "➕ Add Expense",
            use_container_width=True,
        ):

            if expense_amount <= 0:

                st.error(
                    "Enter an amount greater than ₹0."
                )

            else:

                execute(
                    """
                    INSERT INTO expenses
                    (
                        user_id,
                        expense_date,
                        category,
                        description,
                        amount
                    )
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        USER_ID,
                        str(expense_date),
                        expense_category,
                        expense_description.strip(),
                        expense_amount,
                    ),
                )

                st.success(
                    "✅ Expense added successfully!"
                )

                st.rerun()

    st.markdown("---")

    st.subheader("📋 Expense History")

    expenses_df = query_df(
        """
        SELECT
            id,
            expense_date,
            category,
            description,
            amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (USER_ID,),
    )

    if expenses_df.empty:

        st.info(
            "No expenses recorded yet."
        )

    else:

        expenses_display = expenses_df.copy()

        expenses_display["amount"] = (
            expenses_display["amount"]
            .apply(rupees)
        )

        st.dataframe(
            expenses_display,
            use_container_width=True,
            hide_index=True,
)
      # ============================================================
# CUSTOMERS
# ============================================================

elif page == "👥 Customers":

    st.header("👥 Customer Manager")

    st.write(
        "Store customer information and keep track of "
        "their total spending."
    )

    with st.form("customer_form"):

        st.subheader("➕ Add Customer")

        col1, col2 = st.columns(2)

        with col1:

            customer_name = st.text_input(
                "👤 Customer Name"
            )

            customer_phone = st.text_input(
                "📱 Phone Number"
            )

        with col2:

            customer_email = st.text_input(
                "📧 Email"
            )

            customer_spent = st.number_input(
                "💰 Total Spent ₹",
                min_value=0.0,
                step=100.0,
            )

        if st.form_submit_button(
            "➕ Add Customer",
            use_container_width=True,
        ):

            if not customer_name.strip():

                st.error(
                    "Please enter customer name."
                )

            else:

                execute(
                    """
                    INSERT INTO customers
                    (
                        user_id,
                        name,
                        phone,
                        email,
                        spent,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?)
                    """,
                    (
                        USER_ID,
                        customer_name.strip(),
                        customer_phone.strip(),
                        customer_email.strip(),
                        customer_spent,
                        datetime.now().isoformat(),
                    ),
                )

                st.success(
                    "✅ Customer added successfully!"
                )

                st.rerun()

    st.markdown("---")

    st.subheader("👥 Customer List")

    customers_df = query_df(
        """
        SELECT
            id,
            name,
            phone,
            email,
            spent
        FROM customers
        WHERE user_id = ?
        ORDER BY spent DESC
        """,
        (USER_ID,),
    )

    if customers_df.empty:

        st.info(
            "No customers added yet."
        )

    else:

        customer_display = customers_df.copy()

        customer_display["spent"] = (
            customer_display["spent"]
            .apply(rupees)
        )

        st.dataframe(
            customer_display,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        st.subheader("🗑️ Delete Customer")

        customer_id = st.number_input(
            "Customer ID",
            min_value=1,
            step=1,
        )

        if st.button(
            "🗑️ Delete Customer",
            use_container_width=True,
        ):

            execute(
                """
                DELETE FROM customers
                WHERE id = ? AND user_id = ?
                """,
                (
                    int(customer_id),
                    USER_ID,
                ),
            )

            st.success(
                "Customer deleted."
            )

            st.rerun()


# ============================================================
# ANALYTICS
# ============================================================

elif page == "📊 Analytics":

    st.header("📊 Business Analytics")

    sales_data = query_df(
        """
        SELECT *
        FROM sales
        WHERE user_id = ?
        """,
        (USER_ID,),
    )

    expense_data = query_df(
        """
        SELECT *
        FROM expenses
        WHERE user_id = ?
        """,
        (USER_ID,),
    )

    total_sales = (
        float(sales_data["amount"].sum())
        if not sales_data.empty
        else 0
    )

    total_expenses = (
        float(expense_data["amount"].sum())
        if not expense_data.empty
        else 0
    )

    net_result = (
        total_sales - total_expenses
    )

    a, b, c = st.columns(3)

    a.metric(
        "💵 Revenue",
        rupees(total_sales),
    )

    b.metric(
        "💸 Expenses",
        rupees(total_expenses),
    )

    c.metric(
        "📈 Net Result",
        rupees(net_result),
    )

    st.markdown("---")

    # --------------------------------------------------------
    # PROFIT STATUS
    # --------------------------------------------------------

    if net_result > 0:

        st.success(
            "📈 Your recorded revenue is higher "
            "than your recorded expenses."
        )

    elif net_result < 0:

        st.warning(
            "⚠️ Your recorded expenses are higher "
            "than your recorded revenue."
        )

    else:

        st.info(
            "ℹ️ Revenue and expenses are currently equal."
        )

    # --------------------------------------------------------
    # SALES ANALYSIS
    # --------------------------------------------------------

    if not sales_data.empty:

        st.subheader("📈 Sales by Product")

        product_sales = (
            sales_data
            .groupby("product", as_index=False)["amount"]
            .sum()
            .sort_values(
                "amount",
                ascending=False,
            )
        )

        st.bar_chart(
            product_sales.set_index("product")
        )

        st.subheader("📅 Daily Sales")

        daily_sales = (
            sales_data
            .groupby("sale_date", as_index=False)["amount"]
            .sum()
        )

        daily_sales["sale_date"] = pd.to_datetime(
            daily_sales["sale_date"]
        )

        daily_sales = daily_sales.sort_values(
            "sale_date"
        )

        st.line_chart(
            daily_sales.set_index(
                "sale_date"
            )["amount"]
        )

    else:

        st.info(
            "📊 Add sales to see sales analytics."
        )

    # --------------------------------------------------------
    # EXPENSE ANALYSIS
    # --------------------------------------------------------

    if not expense_data.empty:

        st.subheader("💸 Expenses by Category")

        category_expenses = (
            expense_data
            .groupby("category", as_index=False)["amount"]
            .sum()
            .sort_values(
                "amount",
                ascending=False,
            )
        )

        st.bar_chart(
            category_expenses.set_index(
                "category"
            )
        )

    else:

        st.info(
            "💸 Add expenses to see expense analytics."
        )

    # --------------------------------------------------------
    # BUSINESS HEALTH SCORE
    # --------------------------------------------------------

    st.markdown("---")

    st.subheader("⭐ Business Health Score")

    health_score = 50

    if total_sales > 0:
        health_score += 20

    if total_sales > total_expenses:
        health_score += 20

    low_stock_count = int(
        query_df(
            """
            SELECT COUNT(*) AS total
            FROM products
            WHERE user_id = ?
            AND stock <= reorder_level
            """,
            (USER_ID,),
        ).iloc[0]["total"]
    )

    if low_stock_count > 0:
        health_score -= 10

    health_score = max(
        0,
        min(100, health_score),
    )

    st.progress(
        health_score / 100
    )

    st.metric(
        "Business Health",
        f"{health_score}/100",
    )

    st.caption(
        "This is a simple rule-based indicator "
        "for your dashboard. It is not a financial rating."
    )


# ============================================================
# CALCULATORS
# ============================================================

elif page == "🧮 Calculators":

    st.header("🧮 Business Calculators")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "💹 Profit & Margin",
            "⚖️ Break-Even",
            "🏷️ Discount",
            "🧾 GST",
        ]
    )

    # --------------------------------------------------------
    # PROFIT & MARGIN
    # --------------------------------------------------------

    with tab1:

        st.subheader(
            "💹 Profit & Profit Margin"
        )

        buy = st.number_input(
            "Cost Price ₹",
            min_value=0.0,
            step=10.0,
            key="calc_buy",
        )

        sell = st.number_input(
            "Selling Price ₹",
            min_value=0.0,
            step=10.0,
            key="calc_sell",
        )

        if sell > 0:

            profit = sell - buy

            margin = (
                profit / sell
            ) * 100

            st.metric(
                "Profit / Unit",
                rupees(profit),
            )

            st.metric(
                "Profit Margin",
                f"{margin:.2f}%",
            )

        else:

            st.info(
                "Enter a selling price."
            )

    # --------------------------------------------------------
    # BREAK EVEN
    # --------------------------------------------------------

    with tab2:

        st.subheader(
            "⚖️ Break-Even Calculator"
        )

        fixed_cost = st.number_input(
            "Fixed Costs ₹",
            min_value=0.0,
            step=100.0,
            key="fixed_cost",
        )

        unit_price = st.number_input(
            "Selling Price / Unit ₹",
            min_value=0.0,
            step=10.0,
            key="unit_price",
        )

        variable_cost = st.number_input(
            "Variable Cost / Unit ₹",
            min_value=0.0,
            step=10.0,
            key="variable_cost",
        )

        contribution = (
            unit_price
            - variable_cost
        )

        if contribution > 0:

            break_even_units = (
                fixed_cost
                / contribution
            )

            break_even_sales = (
                break_even_units
                * unit_price
            )

            st.metric(
                "Break-Even Units",
                f"{break_even_units:.2f}",
            )

            st.metric(
                "Break-Even Sales",
                rupees(break_even_sales),
            )

        else:

            st.warning(
                "Selling price must be greater "
                "than variable cost."
            )

    # --------------------------------------------------------
    # DISCOUNT
    # --------------------------------------------------------

    with tab3:

        st.subheader(
            "🏷️ Discount Calculator"
        )

        original_price = st.number_input(
            "Original Price ₹",
            min_value=0.0,
            step=10.0,
            key="original_price",
        )

        discount_percent = st.number_input(
            "Discount %",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
            key="discount_percent",
        )

        discount_amount = (
            original_price
            * discount_percent
            / 100
        )

        final_price = (
            original_price
            - discount_amount
        )

        st.metric(
            "💰 Final Price",
            rupees(final_price),
        )

        st.metric(
            "💵 You Save",
            rupees(discount_amount),
        )

    # --------------------------------------------------------
    # GST
    # --------------------------------------------------------

    with tab4:

        st.subheader(
            "🧾 GST Calculator"
        )

        gst_base = st.number_input(
            "Amount Before GST ₹",
            min_value=0.0,
            step=100.0,
            key="gst_base",
        )

        gst_percent = st.number_input(
            "GST %",
            min_value=0.0,
            max_value=100.0,
            value=18.0,
            step=1.0,
            key="gst_percent",
        )

        gst_amount = (
            gst_base
            * gst_percent
            / 100
        )

        final_gst_amount = (
            gst_base
            + gst_amount
        )

        st.metric(
            "🧾 GST Amount",
            rupees(gst_amount),
        )

        st.metric(
            "💰 Final Amount",
            rupees(final_gst_amount),
  )
      # ============================================================
# TASKS & GOALS
# ============================================================

elif page == "📋 Tasks & Goals":

    st.header("📋 Tasks & Goals")

    st.write(
        "Plan your daily business work and track completion."
    )

    with st.form("task_form"):

        st.subheader("➕ Add New Task")

        col1, col2 = st.columns(2)

        with col1:

            task_date = st.date_input(
                "📅 Task Date",
                value=date.today(),
            )

            task_name = st.text_input(
                "📝 Task"
            )

        with col2:

            priority = st.selectbox(
                "🔥 Priority",
                [
                    "Low",
                    "Medium",
                    "High",
                    "Urgent",
                ],
            )

            status = st.selectbox(
                "📌 Status",
                [
                    "Pending",
                    "In Progress",
                    "Completed",
                ],
            )

        if st.form_submit_button(
            "➕ Add Task",
            use_container_width=True,
        ):

            if not task_name.strip():

                st.error(
                    "Please enter a task."
                )

            else:

                execute(
                    """
                    INSERT INTO tasks
                    (
                        user_id,
                        task_date,
                        task,
                        priority,
                        status
                    )
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        USER_ID,
                        str(task_date),
                        task_name.strip(),
                        priority,
                        status,
                    ),
                )

                st.success(
                    "✅ Task added successfully!"
                )

                st.rerun()

    st.markdown("---")

    # --------------------------------------------------------
    # TASK SUMMARY
    # --------------------------------------------------------

    tasks = query_df(
        """
        SELECT *
        FROM tasks
        WHERE user_id = ?
        ORDER BY task_date DESC, id DESC
        """,
        (USER_ID,),
    )

    total_tasks = len(tasks)

    completed_tasks = (
        len(
            tasks[
                tasks["status"] == "Completed"
            ]
        )
        if not tasks.empty
        else 0
    )

    pending_tasks = (
        len(
            tasks[
                tasks["status"] != "Completed"
            ]
        )
        if not tasks.empty
        else 0
    )

    a, b, c = st.columns(3)

    a.metric(
        "📋 Total Tasks",
        total_tasks,
    )

    b.metric(
        "⏳ Pending",
        pending_tasks,
    )

    c.metric(
        "✅ Completed",
        completed_tasks,
    )

    # --------------------------------------------------------
    # TASK PROGRESS
    # --------------------------------------------------------

    if total_tasks > 0:

        task_progress = (
            completed_tasks
            / total_tasks
        )

        st.subheader(
            "📈 Task Completion"
        )

        st.progress(
            task_progress
        )

        st.caption(
            f"{completed_tasks} of "
            f"{total_tasks} tasks completed."
        )

    st.markdown("---")

    # --------------------------------------------------------
    # TASK TABLE
    # --------------------------------------------------------

    st.subheader(
        "📝 Your Tasks"
    )

    if tasks.empty:

        st.info(
            "No tasks added yet."
        )

    else:

        display_tasks = tasks[
            [
                "id",
                "task_date",
                "task",
                "priority",
                "status",
            ]
        ].copy()

        display_tasks.columns = [
            "ID",
            "Date",
            "Task",
            "Priority",
            "Status",
        ]

        st.dataframe(
            display_tasks,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        # ----------------------------------------------------
        # UPDATE TASK STATUS
        # ----------------------------------------------------

        st.subheader(
            "🔄 Update Task Status"
        )

        task_id = st.number_input(
            "Task ID",
            min_value=1,
            step=1,
        )

        new_status = st.selectbox(
            "New Status",
            [
                "Pending",
                "In Progress",
                "Completed",
            ],
            key="new_task_status",
        )

        if st.button(
            "🔄 Update Status",
            use_container_width=True,
        ):

            execute(
                """
                UPDATE tasks
                SET status = ?
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    new_status,
                    int(task_id),
                    USER_ID,
                ),
            )

            st.success(
                "Task status updated."
            )

            st.rerun()

        # ----------------------------------------------------
        # DELETE TASK
        # ----------------------------------------------------

        st.subheader(
            "🗑️ Delete Task"
        )

        delete_task_id = st.number_input(
            "Task ID to Delete",
            min_value=1,
            step=1,
            key="delete_task_id",
        )

        if st.button(
            "🗑️ Delete Task",
            use_container_width=True,
        ):

            execute(
                """
                DELETE FROM tasks
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    int(delete_task_id),
                    USER_ID,
                ),
            )

            st.success(
                "Task deleted."
            )

            st.rerun()


# ============================================================
# REPORTS & EXPORT
# ============================================================

elif page == "📥 Reports":

    st.header("📥 Reports & Export")

    st.write(
        "Download your business data as CSV files."
    )

    # --------------------------------------------------------
    # PRODUCTS REPORT
    # --------------------------------------------------------

    products_report = query_df(
        """
        SELECT
            id,
            name,
            category,
            buy_price,
            sell_price,
            stock,
            reorder_level
        FROM products
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (USER_ID,),
    )

    st.subheader(
        "📦 Products Report"
    )

    if products_report.empty:

        st.info(
            "No product data available."
        )

    else:

        st.dataframe(
            products_report,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download Products CSV",
            data=products_report.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="products_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")

    # --------------------------------------------------------
    # SALES REPORT
    # --------------------------------------------------------

    sales_report = query_df(
        """
        SELECT
            id,
            sale_date,
            product,
            quantity,
            amount,
            payment
        FROM sales
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (USER_ID,),
    )

    st.subheader(
        "💵 Sales Report"
    )

    if sales_report.empty:

        st.info(
            "No sales data available."
        )

    else:

        st.dataframe(
            sales_report,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download Sales CSV",
            data=sales_report.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="sales_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")

    # --------------------------------------------------------
    # EXPENSE REPORT
    # --------------------------------------------------------

    expenses_report = query_df(
        """
        SELECT
            id,
            expense_date,
            category,
            description,
            amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (USER_ID,),
    )

    st.subheader(
        "💸 Expenses Report"
    )

    if expenses_report.empty:

        st.info(
            "No expense data available."
        )

    else:

        st.dataframe(
            expenses_report,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download Expenses CSV",
            data=expenses_report.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="expenses_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")

    # --------------------------------------------------------
    # CUSTOMER REPORT
    # --------------------------------------------------------

    customers_report = query_df(
        """
        SELECT
            id,
            name,
            phone,
            email,
            spent
        FROM customers
        WHERE user_id = ?
        ORDER BY spent DESC
        """,
        (USER_ID,),
    )

    st.subheader(
        "👥 Customers Report"
    )

    if customers_report.empty:

        st.info(
            "No customer data available."
        )

    else:

        st.dataframe(
            customers_report,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download Customers CSV",
            data=customers_report.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="customers_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")

    # --------------------------------------------------------
    # TASK REPORT
    # --------------------------------------------------------

    tasks_report = query_df(
        """
        SELECT
            id,
            task_date,
            task,
            priority,
            status
        FROM tasks
        WHERE user_id = ?
        ORDER BY task_date DESC
        """,
        (USER_ID,),
    )

    st.subheader(
        "📋 Tasks Report"
    )

    if tasks_report.empty:

        st.info(
            "No task data available."
        )

    else:

        st.dataframe(
            tasks_report,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download Tasks CSV",
            data=tasks_report.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="tasks_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")

    # --------------------------------------------------------
    # FINANCIAL SUMMARY
    # --------------------------------------------------------

    st.subheader(
        "📊 Financial Summary"
    )

    total_sales = float(
        query_df(
            """
            SELECT COALESCE(
                SUM(amount), 0
            ) AS total
            FROM sales
            WHERE user_id = ?
            """,
            (USER_ID,),
        ).iloc[0]["total"]
    )

    total_expenses = float(
        query_df(
            """
            SELECT COALESCE(
                SUM(amount), 0
            ) AS total
            FROM expenses
            WHERE user_id = ?
            """,
            (USER_ID,),
        ).iloc[0]["total"]
    )

    summary = pd.DataFrame(
        [
            {
                "Total Sales": total_sales,
                "Total Expenses": total_expenses,
                "Net Result":
                    total_sales
                    - total_expenses,
            }
        ]
    )

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "⬇️ Download Financial Summary",
        data=summary.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="financial_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )
  # ============================================================
# BUSINESS GUIDE
# ============================================================

elif page == "📚 Business Guide":

    st.header("📚 Business Guide")

    st.write(
        "Simple practical tips to help you manage "
        "and grow your small business."
    )

    guide = {
        "💰 Pricing": (
            "Calculate your product cost first. "
            "Then consider operating costs, competition "
            "and your desired profit before setting a price."
        ),

        "📦 Inventory": (
            "Monitor stock regularly. Set a reorder level "
            "so you can identify products that need restocking."
        ),

        "💵 Cash Flow": (
            "Track money coming into the business and "
            "money going out of the business."
        ),

        "📣 Marketing": (
            "Test different marketing methods and measure "
            "which methods actually generate customers and sales."
        ),

        "👥 Customers": (
            "Maintain organized customer information and "
            "focus on providing good service and encouraging "
            "repeat purchases."
        ),

        "📊 Business Analysis": (
            "Review sales, expenses, inventory and net result "
            "regularly instead of making decisions only by guesswork."
        ),

        "🎯 Goal Setting": (
            "Set measurable business goals such as monthly "
            "sales, number of customers or inventory targets."
        ),

        "📱 Digital Tools": (
            "Use digital records to reduce manual calculation "
            "and keep your business information organized."
        ),

        "🧾 Record Keeping": (
            "Record sales and expenses consistently. "
            "Incomplete records make business analysis unreliable."
        ),

        "📈 Growth": (
            "Before expanding, check whether your existing "
            "products, customers and cash flow can support growth."
        ),
    }

    for title, description in guide.items():

        with st.expander(title):

            st.write(description)


# ============================================================
# SETTINGS
# ============================================================

elif page == "⚙️ Settings":

    st.header("⚙️ Settings")

    st.subheader("👤 Account Information")

    st.write(
        f"Username: **{st.session_state.username}**"
    )

    st.write(
        f"Name: **{full_name}**"
    )

    st.write(
        f"Business: **{business_name}**"
    )

    st.markdown("---")

    # --------------------------------------------------------
    # APP INFORMATION
    # --------------------------------------------------------

    st.subheader("ℹ️ Application Information")

    info1, info2, info3 = st.columns(3)

    with info1:

        st.info(
            "🐍 Python\n\n"
            "Application language"
        )

    with info2:

        st.info(
            "🎈 Streamlit\n\n"
            "Web application framework"
        )

    with info3:

        st.info(
            "🗄️ SQLite\n\n"
            "Local database"
        )

    st.markdown("---")

    # --------------------------------------------------------
    # DATA MANAGEMENT
    # --------------------------------------------------------

    st.subheader("🗄️ Data Management")

    st.warning(
        "Deleting your business data is permanent."
    )

    if "confirm_delete" not in st.session_state:

        st.session_state.confirm_delete = False

    if st.button(
        "🗑️ Delete My Business Data",
        use_container_width=True,
    ):

        st.session_state.confirm_delete = True

    if st.session_state.confirm_delete:

        st.error(
            "⚠️ This will permanently delete your "
            "profile, products, sales, expenses, "
            "customers and tasks."
        )

        confirm = st.checkbox(
            "I understand that this action cannot be undone.",
            key="delete_confirmation",
        )

        if confirm:

            if st.button(
                "⚠️ YES, DELETE MY DATA",
                use_container_width=True,
            ):

                conn = get_connection()
                cur = conn.cursor()

                tables = [
                    "profiles",
                    "products",
                    "sales",
                    "expenses",
                    "customers",
                    "tasks",
                ]

                for table in tables:

                    cur.execute(
                        f"""
                        DELETE FROM {table}
                        WHERE user_id = ?
                        """,
                        (USER_ID,),
                    )

                conn.commit()
                conn.close()

                st.session_state.confirm_delete = False

                st.success(
                    "All business data has been deleted."
                )

                st.rerun()

    st.markdown("---")

    # --------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------

    st.subheader("🚪 Account")

    if st.button(
        "🚪 Logout",
        use_container_width=True,
    ):

        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = ""

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div class="footer">

        <b>🏪 SmallBusiness Assistant</b>

        <br><br>

        Plan • Track • Analyse • Grow

        <br><br>

        Python • Streamlit • Pandas • SQLite

        <br><br>

        No Hugging Face • No API Token Required

    </div>
    """,
    unsafe_allow_html=True,
)
