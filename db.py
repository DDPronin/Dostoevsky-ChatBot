
import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot.db')
        self.create_table()

    def create_table(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, _id INTEGER, username TEXT, first_name TEXT, last_name TEXT, dialog_context TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS requests
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, response TEXT)''')
        self.conn.commit()

    def add_request(self, message, response):
        c = self.conn.cursor()
        c.execute("INSERT INTO requests (message, response) VALUES (?, ?)", (message, response))
        self.conn.commit()
    
    def delete_dialog_context(self, _id):
        c = self.conn.cursor()
        c.execute("UPDATE users SET dialog_context='' WHERE _id=?", (_id,))
        self.conn.commit()
   
   
    def check_user_exists(self, _id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE _id=?", (_id,))
        user = c.fetchone()
        return user is not None

    def get_dialog_context(self, _id):
        c = self.conn.cursor()
        c.execute("SELECT dialog_context FROM users WHERE _id=?", (_id,))
        dialog_context = c.fetchone()
        return dialog_context[0] if dialog_context else None 
    
    def add_user(self, _id, username, first_name, last_name):
        c = self.conn.cursor()
        dialog_context = ''
        c.execute("INSERT INTO users (_id, username, first_name, last_name, dialog_context) VALUES (?, ?, ?, ?, ?)", (_id, username, first_name, last_name, dialog_context))
        self.conn.commit()        

    def add_dialog_context(self, dialog_context):
        c = self.conn.cursor()
        c.execute("INSERT INTO users (dialog_context) VALUES (?)", (dialog_context,))
        self.conn.commit()
    

  