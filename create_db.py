def create_tables(cursor):
    cursor.execute("""CREATE TABLE users (
                        user_id integer primary key autoincrement,
                        user_name text,
                        rfid_uid integer not null,
                        UNIQUE(rfid_uid)
                      )""")

    cursor.execute("""CREATE TABLE devices (
                        device_id integer primary key autoincrement
                      )""")

    cursor.execute("""CREATE TABLE equipments (
                        equipment_id integer primary key autoincrement,
                        device_id integer not null,
                        FOREIGN KEY(device_id) REFERENCES devices(device_id)
                      )""")

    cursor.execute("""CREATE TABLE rents (
                        rent_id integer primary key autoincrement,
                        equipment_id integer not null,
                        user_id integer not null,
                        begin_time datetime not null,
                        end_time datetime,
                        FOREIGN KEY(equipment_id) REFERENCES equipments(equipment_id),
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                      )""")
