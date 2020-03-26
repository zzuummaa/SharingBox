import sqlite3
import os

db_path = "sharingbox.db"
os.remove(db_path) if os.path.exists(db_path) else None
conn = sqlite3.connect(db_path) # или :memory: чтобы сохранить в RAM
cursor = conn.cursor()

cursor.execute("""CREATE TABLE users (
                    user_id integer primary key autoincrement,
                    user_name text,
                    rfid_uid int not null,
                    UNIQUE(rfid_uid)
                  )""")

cursor.execute("""CREATE TABLE devices (
                    device_id integer primary key autoincrement,
                    device_token text not null
                  )""")

cursor.execute("""CREATE TABLE rents (
                    rent_id integer primary key autoincrement,
                    user_id integer not null,
                    begin_time datetime not null,
                    end_time datetime,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                  )""")
