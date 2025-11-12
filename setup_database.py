import sqlite3
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cryptoAssitantBot.db")

def get_connection():
    return sqlite3.connect(DB_FILE)

# إنشاء الجداول إذا لم تكن موجودة
def setup_database():
    conn = None
    try:
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

        # جدول الأخبار المُعالجة
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_news (
            uniq_id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        #جدول المشتركين
        cursor.execute('''
        CREATE TABLE subscribers (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            subscription_type TEXT,
            start_date TEXT,
            end_date TEXT,
            is_active INTEGER,
            payment_method TEXT,
            payment_reference TEXT
        )
        ''')

        # جدول المدفوعات (دفعات NOWPayments)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                user_id INTEGER,
                order_id TEXT,
                amount REAL,
                currency TEXT,
                status TEXT,
                payment_date DATETIME,
                network TEXT
            )
        ''')

        # جدول المدفوعات المعلقة (pending_payments)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_payments (
            user_id INTEGER,
            order_id TEXT PRIMARY KEY,
            amount REAL,
            currency TEXT,
            status TEXT,
            payment_address TEXT,
            payment_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in setup_database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# إضافة مشترك جديد
def add_subscriber(user_id, username, duration_value, duration_type='months', subscription_type='premium', payment_method='NOWPayments', payment_reference='N/A'):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        start_date = datetime.now()
        if duration_type == 'months':
            end_date = start_date + relativedelta(months=duration_value)
        elif duration_type == 'days':
            end_date = start_date + relativedelta(days=duration_value)
        else:
            raise ValueError("duration_type must be 'months' or 'days'")
        cursor.execute('''
            INSERT OR REPLACE INTO subscribers 
            (user_id, username, subscription_type, start_date, end_date, is_active, payment_method, payment_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, subscription_type, start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S'), 1, payment_method, payment_reference))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in add_subscriber: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


# الاستعلام عن مشترك
def get_subscriber(user_id):
    conn = None
    result = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM subscribers WHERE user_id=?', (user_id,))
        result = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database error in get_subscriber: {e}")
    finally:
        if conn:
            conn.close()
    return result

# تحديث حالة مشترك بعد دفع ناجح

def activate_subscriber(user_id, months, username=None):
    add_subscriber(user_id, username, months, duration_type='months', subscription_type='premium', payment_method='NOWPayments', payment_reference='N/A')


# إضافة دفعة جديدة

def add_payment(payment_id, user_id, order_id, amount, currency, status, network="TON"):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payments 
            (payment_id, user_id, order_id, amount, currency, status, payment_date, network)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (payment_id, user_id, order_id, amount, currency, status, datetime.now(), network))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in add_payment: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def add_pending_payment(user_id, order_id, amount, currency, status, payment_address, payment_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pending_payments 
            (user_id, order_id, amount, currency, status, payment_address, payment_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, order_id, amount, currency, status, payment_address, payment_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in add_pending_payment: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

#تحديث حالة الدفع
def update_payment_status(payment_id, status):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE payments SET status=? WHERE payment_id=?
        ''', (status, payment_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_payment_status: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# إزالة دفعة معلقة
def remove_pending_payment(order_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM pending_payments WHERE order_id=?
        ''', (order_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in remove_pending_payment: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def get_pending_payment(order_id):
    conn = None
    payment = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, order_id, amount, currency, status, payment_address, payment_id, created_at
            FROM pending_payments WHERE order_id=?
        ''', (order_id,))
        payment = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database error in get_pending_payment: {e}")
    finally:
        if conn:
            conn.close()
    return payment

# دوال لإدارة الاشتراكات
def get_expired_subscribers():
    conn = None
    result = []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, payment_reference FROM subscribers
            WHERE end_date < CURRENT_TIMESTAMP AND is_active = 1
        ''')
        result = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error in get_expired_subscribers: {e}")
    finally:
        if conn:
            conn.close()
    return result

def get_subscribers_about_to_expire(days=2):
    conn = None
    result = []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, end_date FROM subscribers
            WHERE end_date BETWEEN CURRENT_TIMESTAMP AND datetime(CURRENT_TIMESTAMP, ? || ' days')
            AND is_active = 1
        ''', (days,))
        result = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error in get_subscribers_about_to_expire: {e}")
    finally:
        if conn:
            conn.close()
    return result

def update_subscriber_status(user_id, is_active):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE subscribers SET is_active=? WHERE user_id=?
        ''', (is_active, user_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_subscriber_status: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
# دوال مساعدة للتعامل مع البيانات
def save_price(symbol, price, timestamp=None):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if not timestamp:
            timestamp = datetime.now()
        cursor.execute(
            "INSERT INTO price_history (symbol, price, timestamp) VALUES (?, ?, ?)",
            (symbol, price, timestamp)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in save_price: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def get_old_price(symbol, minutes=15):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT price FROM price_history
            WHERE symbol = ? AND timestamp <= datetime('now', ?)
            ORDER BY timestamp DESC LIMIT 1
        ''', (symbol, f"-{minutes} minutes"))
        result = cursor.fetchone()
        return float(result[0]) if result else None
    except sqlite3.Error as e:
        print(f"Database error in get_old_price: {e}")
        return None
    finally:
        if conn:
            conn.close()

def already_alerted(symbol, minutes=15):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 1 FROM sent_alerts
            WHERE symbol = ? AND timestamp >= datetime('now', ?)
            LIMIT 1
        ''', (symbol, f"-{minutes} minutes"))
        result = cursor.fetchone()
        return result is not None
    except sqlite3.Error as e:
        print(f"Database error in already_alerted: {e}")
        return False
    finally:
        if conn:
            conn.close()

# دالة لحفظ التنبيه
def save_alert(symbol, price_before, price_after, percentage_change):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sent_alerts (symbol, price_before, price_after, percentage_change)
            VALUES (?, ?, ?, ?)
        ''', (symbol, price_before, price_after, percentage_change))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in save_alert: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
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
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO watched_coins (symbol) VALUES (?)", (symbol,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in add_coin: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def remove_coin(symbol):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM watched_coins WHERE symbol = ?", (symbol,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in remove_coin: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close() 



def get_watched_currencies(user_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT symbol FROM watched_currencies WHERE user_id=?",
            (user_id,)
        )
        results = cursor.fetchall()
        return [row[0] for row in results]
    except sqlite3.Error as e:
        print(f"Database error in get_watched_currencies: {e}")
        return []
    finally:
        if conn:
            conn.close()


# دوال للتعامل مع الأخبار المُعالجة
def is_news_processed(uniq_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_news WHERE uniq_id = ?", (uniq_id,))
        result = cursor.fetchone()
        return result is not None
    except sqlite3.Error as e:
        print(f"Database error in is_news_processed: {e}")
        return False
    finally:
        if conn:
            conn.close()

def mark_news_as_processed(uniq_id, title, link):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO processed_news (uniq_id, title, link) VALUES (?, ?, ?)",
            (uniq_id, title, link)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in mark_news_as_processed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    setup_database()
    print("Database setup completed ✅")
