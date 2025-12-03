from typing import List, Dict, Literal
from db import get_connection

# 1) find_books({ q, by: "title" | "author" })
def find_books(q: str, by: Literal["title", "author"] = "title") -> List[Dict]:
    """
    Search books by title or author.
    Returns list of {isbn, title, author, price, stock}
    """
    column = "title" if by == "title" else "author"
    sql = f"""
        SELECT isbn, title, author, price, stock
        FROM books
        WHERE {column} LIKE ?
        ORDER BY title
        """
    pattern = f"%{q}%"

    conn = get_connection()
    try:
        cur = conn.execute(sql, (pattern,))
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# 2) create_order({ customer_id, items: [{ isbn, qty }] })
def create_order(customer_id: int, name: str,
    email: str, items: List[Dict]) -> Dict:
    """
    Create a new order and reduce stock.
    items = [ {"isbn": "978...", "qty": 2}, ... ]

    Returns:
        {
        "order_id": int,
        "total_items": int,
        "items": [...],
        }
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # 2.1: إنشاء order جديد
        cur.execute(
            "INSERT INTO orders (customer_id, created_at, status) VALUES (?, datetime('now'), 'pending')",
            (customer_id,),
        )
        order_id = cur.lastrowid

        total_items = 0
        result_items = []

        # 2.2: إضافة كل عنصر وتحديث المخزون
        for item in items:
            isbn = item["isbn"]
            qty = int(item["qty"])

            # التحقق من توفر المخزون
            cur.execute("SELECT stock, title FROM books WHERE isbn = ?", (isbn,))
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Book with ISBN {isbn} not found")
            if row["stock"] < qty:
                raise ValueError(
                    f"Not enough stock for '{row['title']}' (isbn={isbn}). "
                    f"Available={row['stock']}, requested={qty}"
                )

            # إضافة عنصر الطلب
            cur.execute(
                "INSERT INTO order_items (order_id, isbn, qty) VALUES (?, ?, ?)",
                (order_id, isbn, qty),
            )

            # تقليل المخزون
            cur.execute(
                "UPDATE books SET stock = stock - ? WHERE isbn = ?",
                (qty, isbn),
            )

            total_items += qty
            result_items.append(
                {
                    "isbn": isbn,
                    "title": row["title"],
                    "qty": qty,
                }
            )
        cur.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
        row = cur.fetchone()

        if row is None:
            add_customer(customer_id, name, email)

        conn.commit()

        return {
            "order_id": order_id,
            "total_items": total_items,
            "items": result_items,
        }

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# 3) restock_book({ isbn, qty })
def restock_book(isbn: str, qty: int) -> Dict:
    """
    Increase stock for a book.
    Returns {isbn, new_stock}
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE books SET stock = stock + ? WHERE isbn = ?", (qty, isbn))
        if cur.rowcount == 0:
            raise ValueError(f"Book with ISBN {isbn} not found")

        cur.execute("SELECT stock FROM books WHERE isbn = ?", (isbn,))
        stock = cur.fetchone()["stock"]
        conn.commit()

        return {"isbn": isbn, "new_stock": stock}
    finally:
        conn.close()


# 4) update_price({ isbn, price })
def update_price(isbn: str, price: float) -> Dict:
    """
    Update price for a book.
    Returns {isbn, new_price}
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE books SET price = ? WHERE isbn = ?", (price, isbn))
        if cur.rowcount == 0:
            raise ValueError(f"Book with ISBN {isbn} not found")

        conn.commit()
        return {"isbn": isbn, "new_price": price}
    finally:
        conn.close()


# 5) order_status({ order_id })
def order_status(order_id: int) -> Dict:
    """
    Return order summary with items.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # معلومات الطلب + العميل
        cur.execute(
            """
            SELECT  o.id, o.created_at, o.status,
                    c.id AS customer_id, c.name AS customer_name, c.email AS customer_email
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
            """,
            (order_id,),
        )
        order_row = cur.fetchone()
        if order_row is None:
            raise ValueError(f"Order {order_id} not found")

        # العناصر
        cur.execute(
            """
            SELECT oi.isbn, oi.qty,
                    b.title, b.author, b.price
            FROM order_items oi
            JOIN books b ON oi.isbn = b.isbn
            WHERE oi.order_id = ?
            """,
            (order_id,),
        )
        items_rows = cur.fetchall()

        items = []
        total_price = 0.0
        for r in items_rows:
            line_total = r["price"] * r["qty"]
            total_price += line_total
            items.append(
                {
                    "isbn": r["isbn"],
                    "title": r["title"],
                    "author": r["author"],
                    "qty": r["qty"],
                    "unit_price": r["price"],
                    "line_total": line_total,
                }
            )

        return {
            "order_id": order_row["id"],
            "created_at": order_row["created_at"],
            "status": order_row["status"],
            "customer": {
                "id": order_row["customer_id"],
                "name": order_row["customer_name"],
                "email": order_row["customer_email"],
            },
            "items": items,
            "total_price": total_price,
        }
    finally:
        conn.close()


# 6) inventory_summary()
def inventory_summary(low_stock_threshold: int = 3) -> Dict:
    """
    Returns low-stock titles and counts per stock level.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # الكتب ذات المخزون القليل
        cur.execute(
            """
            SELECT isbn, title, author, stock
            FROM books
            WHERE stock <= ?
            ORDER BY stock ASC, title
            """,
            (low_stock_threshold,),
        )
        low_stock = [dict(row) for row in cur.fetchall()]

        # عدد الكتب حسب مستوى المخزون (optional)
        cur.execute(
            """
            SELECT
                CASE
                    WHEN stock = 0 THEN 'out'
                    WHEN stock BETWEEN 1 AND ? THEN 'low'
                    ELSE 'ok'
                END AS level,
                COUNT(*) AS count
            FROM books
            GROUP BY level
            """,
            (low_stock_threshold,),
        )
        levels = {row["level"]: row["count"] for row in cur.fetchall()}

        return {
            "low_stock_titles": low_stock,
            "stock_levels": levels,
        }
    finally:
        conn.close()


#This because avoid the error if we add order for customer not in the customer table if we do order_status
def add_customer(customer_id, name, email):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO customers (name, email) VALUES (?, ?)",
            (name, email)
        )
        customer_id = cur.lastrowid  
        conn.commit()
        return customer_id           
    finally:
        conn.close()


# def add_book(isbn: str, title: str, author: str, price: float, stock: int = 0) -> Dict:
#     conn = get_connection()
#     try:
#         cur = conn.cursor()
#         cur.execute(
#             """
#             INSERT INTO books (isbn, title, author, price, stock)
#             VALUES (?, ?, ?, ?, ?)
#             """,
#             (isbn, title, author, price, stock),
#         )
#         conn.commit()
#         return {
#             "isbn": isbn,
#             "title": title,
#             "author": author,
#             "price": price,
#             "stock": stock,
#         }
#     finally:
#         conn.close()
