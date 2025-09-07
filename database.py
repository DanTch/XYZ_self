import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="bot.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # جدول کاربران
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            score INTEGER DEFAULT 0,
            invited_by INTEGER,
            vip_purchase_count INTEGER DEFAULT 0,
            reseller_purchase_count INTEGER DEFAULT 0,
            FOREIGN KEY (invited_by) REFERENCES users(user_id)
        )
        """)
        
        # جدول پرداخت‌های در انتظار
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            photo_file_id TEXT
        )
        """)
        
        self.conn.commit()

    def add_user(self, user_id, first_name, last_name, username, invited_by=None):
        # بررسی وجود کاربر
        self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if self.cursor.fetchone():
            return False
        
        # افزودن کاربر جدید
        self.cursor.execute("""
        INSERT INTO users (user_id, first_name, last_name, username, invited_by, score)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, first_name, last_name, username, invited_by, NEW_USER_BONUS))
        
        # افزودن پاداش به دعوت‌کننده
        if invited_by:
            self.add_points(invited_by, REFERRAL_BONUS)
        
        self.conn.commit()
        return True

    def add_points(self, user_id, points):
        self.cursor.execute("UPDATE users SET score = score + ? WHERE user_id = ?", (points, user_id))
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def get_referrals(self, user_id):
        self.cursor.execute("SELECT user_id, first_name, username FROM users WHERE invited_by = ?", (user_id,))
        return self.cursor.fetchall()

    def add_pending_payment(self, user_id, amount, photo_file_id):
        self.cursor.execute("""
        INSERT INTO pending_payments (user_id, amount, photo_file_id)
        VALUES (?, ?, ?)
        """, (user_id, amount, photo_file_id))
        self.conn.commit()

    def update_payment_status(self, payment_id, status):
        self.cursor.execute("UPDATE pending_payments SET status = ? WHERE id = ?", (status, payment_id))
        self.conn.commit()

    def close(self):
        self.conn.close()