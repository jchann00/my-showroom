import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from config.settings import DB_PATH
from database.models import Product, PostRecord


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize SQLite database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            price INTEGER NOT NULL,
            rating REAL NOT NULL,
            review_count INTEGER NOT NULL,
            is_rocket INTEGER NOT NULL,
            category TEXT NOT NULL,
            original_url TEXT NOT NULL,
            image_url TEXT,
            deeplink TEXT,
            created_at TEXT NOT NULL,
            posted_at TEXT,
            status TEXT DEFAULT 'pending',
            showroom_num INTEGER
        )
    """)

    # Ensure showroom_num column exists on existing databases
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN showroom_num INTEGER")
    except Exception:
        pass

    # Posts history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            post_type TEXT DEFAULT 'affiliate',
            platform TEXT DEFAULT 'threads',
            main_text TEXT NOT NULL,
            comment_1 TEXT,
            comment_2 TEXT,
            comment_3 TEXT,
            image_paths TEXT,
            platform_post_id TEXT,
            status TEXT DEFAULT 'pending',
            scheduled_at TEXT,
            published_at TEXT,
            error_msg TEXT,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # System Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            module TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_log(level: str, module: str, message: str):
    """Save system log to database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (timestamp, level, module, message) VALUES (?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), level, module, message),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[LOG ERROR] {e}: {message}")


def is_product_exists(product_id: str) -> bool:
    """Check if product already exists in DB."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM products WHERE product_id = ?", (product_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def save_product(product: Product) -> bool:
    """Save or update product with automatic showroom_num assignment."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if product.showroom_num is None:
            cursor.execute("SELECT COALESCE(MAX(showroom_num), 0) + 1 FROM products")
            product.showroom_num = cursor.fetchone()[0]

        cursor.execute("""
            INSERT OR REPLACE INTO products (
                product_id, title, price, rating, review_count, is_rocket,
                category, original_url, image_url, deeplink, created_at, posted_at, status, showroom_num
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product.product_id, product.title, product.price, product.rating,
            product.review_count, 1 if product.is_rocket else 0, product.category,
            product.original_url, product.image_url, product.deeplink,
            product.created_at, product.posted_at, product.status, product.showroom_num
        ))
        conn.commit()
        return True
    except Exception as e:
        save_log("ERROR", "db", f"Failed to save product {product.product_id}: {e}")
        return False
    finally:
        conn.close()


def get_pending_product(category: Optional[str] = None) -> Optional[Product]:
    """Retrieve an unposted product matching criteria."""
    conn = get_connection()
    cursor = conn.cursor()
    if category:
        cursor.execute("""
            SELECT * FROM products 
            WHERE status = 'pending' AND category = ?
            ORDER BY showroom_num ASC LIMIT 1
        """, (category,))
    else:
        cursor.execute("""
            SELECT * FROM products 
            WHERE status = 'pending' 
            ORDER BY showroom_num ASC LIMIT 1
        """)
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return Product(
        product_id=row["product_id"],
        title=row["title"],
        price=row["price"],
        rating=row["rating"],
        review_count=row["review_count"],
        is_rocket=bool(row["is_rocket"]),
        category=row["category"],
        original_url=row["original_url"],
        image_url=row["image_url"],
        deeplink=row["deeplink"],
        created_at=row["created_at"],
        posted_at=row["posted_at"],
        status=row["status"],
        showroom_num=row["showroom_num"] if "showroom_num" in row.keys() else None,
    )


def mark_product_posted(product_id: str):
    """Mark product as posted."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE products SET status = 'posted', posted_at = ? WHERE product_id = ?", (now_str, product_id))
    conn.commit()
    conn.close()


def save_post_record(record: PostRecord) -> int:
    """Save post record and return inserted ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (
            product_id, post_type, platform, main_text, comment_1, comment_2, comment_3,
            image_paths, platform_post_id, status, scheduled_at, published_at, error_msg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.product_id, record.post_type, record.platform, record.main_text,
        record.comment_1, record.comment_2, record.comment_3, record.image_paths,
        record.platform_post_id, record.status, record.scheduled_at, record.published_at, record.error_msg
    ))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id


def get_recent_posts(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent posts for the dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, pr.title as product_title, pr.price, pr.category, pr.image_url
        FROM posts p
        LEFT JOIN products pr ON p.product_id = pr.product_id
        ORDER BY p.id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_recent_products(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent sourced products ordered by showroom_num."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM products 
        ORDER BY 
          CASE WHEN showroom_num IS NOT NULL THEN showroom_num ELSE 999999 END ASC,
          created_at DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_product_link(product_id: str, new_link: str) -> bool:
    """Updates a product's affiliate/landing link directly."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE products SET deeplink = ? WHERE product_id = ?", (new_link.strip(), product_id))
        conn.commit()
        return True
    except Exception as e:
        save_log("ERROR", "db", f"Failed to update link for {product_id}: {e}")
        return False
    finally:
        conn.close()


def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent logs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats() -> Dict[str, Any]:
    """Get system stats for dashboard counter cards."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'pending'")
    pending_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM posts WHERE status IN ('published', 'simulated')")
    published_posts = cursor.fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT COUNT(*) FROM posts WHERE status IN ('published', 'simulated') AND published_at LIKE ?",
        (f"{today}%",)
    )
    today_posts = cursor.fetchone()[0]

    # Calculate post ratio in last 10 posts
    cursor.execute("SELECT post_type FROM posts WHERE status IN ('published', 'simulated') ORDER BY id DESC LIMIT 10")
    recent_types = [r[0] for r in cursor.fetchall()]
    conn.close()

    return {
        "total_products": total_products,
        "pending_products": pending_products,
        "published_posts": published_posts,
        "today_posts": today_posts,
        "recent_post_types": recent_types
    }


# Auto-init on module import
init_db()
