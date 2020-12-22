#!/usr/bin/python

import sqlite3

def main():
  conn = sqlite3.connect('test.db')
  print("Opened database successfully")

  conn.execute('''CREATE TABLE USERS
         (id INTEGER PRIMARY KEY    AUTOINCREMENT,
         uid           TEXT    NOT NULL);''')
  print("Table created successfully")

  conn.close()

if __name__ == "__main__":
  main()
