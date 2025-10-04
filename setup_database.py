import sqlite3
import os

def setup_database():
    # إنشاء قاعدة البيانات إذا لم تكن موجودة
    conn = sqlite3.connect('crypto_prices.db')
    cursor = conn.cursor()

    # إنشاء جدول لتتبع الأسعار
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_history (
        symbol TEXT,
        price REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (symbol, timestamp)
    )
    ''')

    # إنشاء جدول للتنبيهات المرسلة لتجنب التكرار
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

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()