""""View your database data in the terminal"""
import sqlite3

def view():
    db_connection = sqlite3.connect('courses.sqlite')
    db_cursor = db_connection.cursor()
    db_cursor.execute("SELECT * FROM User")
    rows = db_cursor.fetchall()
    db_connection.close()
    return rows


print(view())
