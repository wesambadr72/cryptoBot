import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crypto_prices.db")

def get_connection():
    return sqlite3.connect(DB_FILE)

# إنشاء الجداول إذا لم تكن موجودة
def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    # جدول الأسعار
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_history (
        symbol TEXT,
        price REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (symbol, timestamp)
    )
    ''')

    # جدول التنبيهات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sent_alerts (
        symbol TEXT,
        price_before REAL,
        price_after REAL,
        percentage_change REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (symbol, timestamp)
    )
    ''')

    # جدول العملات المراقبة
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS watched_coins (
        symbol TEXT PRIMARY KEY
    )
    ''')

    conn.commit()
    conn.close()

# دوال مساعدة للتعامل مع البيانات
def save_price(symbol, price, timestamp=None):
    conn = get_connection()
    cursor = conn.cursor()
    if not timestamp:
        timestamp = datetime.now()
    cursor.execute(
        "INSERT INTO price_history (symbol, price, timestamp) VALUES (?, ?, ?)",
        (symbol, price, timestamp)
    )
    conn.commit()
    conn.close()

def get_old_price(symbol, minutes=15):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT price FROM price_history
        WHERE symbol = ? AND timestamp <= datetime('now', ?)
        ORDER BY timestamp DESC LIMIT 1
    ''', (symbol, f"-{minutes} minutes"))
    result = cursor.fetchone()
    conn.close()
    return float(result[0]) if result else None

def already_alerted(symbol, minutes=15):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 FROM sent_alerts
        WHERE symbol = ? AND timestamp >= datetime('now', ?)
        LIMIT 1
    ''', (symbol, f"-{minutes} minutes"))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# دالة لحفظ التنبيه
def save_alert(symbol, price_before, price_after, percentage_change):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sent_alerts (symbol, price_before, price_after, percentage_change)
        VALUES (?, ?, ?, ?)
    ''', (symbol, price_before, price_after, percentage_change))
    conn.commit()
    conn.close()

# دوال لإدارة العملات المراقبة
def load_watched_coins():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM watched_coins")
    coins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return coins

def add_coin(symbol):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO watched_coins (symbol) VALUES (?)", (symbol,))
    conn.commit()
    conn.close()

def remove_coin(symbol):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watched_coins WHERE symbol = ?", (symbol,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
    print("Database setup completed ✅")
