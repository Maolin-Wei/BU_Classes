import sqlite3


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        '''
        self.conn.execute(query)
        self.conn.commit()

    def is_username_exist(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None

    def add_user(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        self.conn.commit()

    def validate_login(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result and result[0] == password

    def close(self):
        if self.conn:
            self.conn.close()
