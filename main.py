#!flask/bin/python
from flask import Flask, jsonify, request, g
import sqlite3
import datetime
from create_db import create_tables

from os import path
import platform

if platform.system() == 'Linux':
    DATABASE = "/db/sharingbox.db"
elif platform.system() == "Windows":
    DATABASE = "sharingbox.db"


def my_response(content=None, error=None, code=200):
    if content is None:
        content = {}
    content.update({"error": error, "is_ok": True if code == 200 else False})
    return jsonify(content), code


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, isolation_level=None)
        query_db("""PRAGMA foreign_keys = 1""")
        db.row_factory = make_dicts
    return db


def query_db(query, args=(), ret_lastrowid=False, ret_rowcount=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    if ret_lastrowid:
        return cur.lastrowid
    elif ret_rowcount:
        return cur.rowcount
    return rv


app = Flask(__name__)


class ValidationError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


@app.errorhandler(ValidationError)
def handle_database_error(e):
    return my_response(error=str(e), code=e.code)


@app.errorhandler(sqlite3.DatabaseError)
def handle_database_error(e):
    if isinstance(e, sqlite3.IntegrityError):
        return my_response(error=str(e), code=400)

    return my_response(error=str(e), code=500)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    return "[]"


@app.route('/users', methods=['POST'])
def add_user():
    if not request.is_json:
        return my_response(error="Body should contains JSON", code=400)

    if "user_name" not in request.json or "rfid_uid" not in request.json:
        return my_response(error="Invalid request parameters", code=400)

    user_params = (request.json["user_name"], request.json["rfid_uid"])
    query_db("""insert into users(user_name, rfid_uid) values(?,?)""", user_params)
    return my_response()


def user_by_rfid(rfid_id):
    res = query_db("""select * from users where rfid_uid=?""", (rfid_id,))
    if len(res) == 0:
        raise ValidationError("User with rfid_id=%s not found" % rfid_id, code=404)

    return res[0]


@app.route('/users/<rfid_id>', methods=['GET'])
def get_user(rfid_id):
    user = user_by_rfid(rfid_id)
    return my_response({"user": user})


@app.route('/users/<rfid_id>/rents', methods=['GET'])
def get_user_equipment(rfid_id):
    user_id = user_by_rfid(rfid_id)["user_id"]
    if 'current_rental' in request.args:
        current_rental = int(request.args.get('current_rental'))
        query_str = """select * from rents where user_id=? and end_time is %s""" % ("not null" if current_rental > 0 else "null")
        res = query_db(query_str, (user_id,))
    else:
        res = query_db("""select * from rents where user_id=?""", (user_id,))
    return my_response({"rents": res})


@app.route('/devices', methods=['POST'])
def add_device():
    device_id = query_db("""insert into devices default values""", ret_lastrowid=True)
    return my_response({"device_id": device_id})


@app.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    res = query_db("""select * from devices where device_id=?""", (device_id,))
    if len(res) == 0:
        return my_response(error="Device with id=%s not found" % device_id, code=404)

    return my_response({"device": res[0]})


@app.route('/devices/<int:device_id>/equipments', methods=['GET'])
def get_device_equipment(device_id):
    res = query_db("""select * from equipments where device_id=?""", (device_id,))
    return my_response({"equipments": res})


@app.route('/equipments', methods=['POST'])
def add_equipment():
    if not request.is_json:
        return my_response(error="Body should contains JSON", code=400)

    if "device_id" not in request.json:
        return my_response(error="Invalid request parameters", code=400)

    device_id = request.json["device_id"]

    equipment_id = query_db("""insert into equipments(device_id) values(?)""", (device_id,), ret_lastrowid=True)

    return my_response({"equipment_id": equipment_id})


@app.route('/equipments/<equipment_id>', methods=['GET'])
def get_equipment(equipment_id):
    res = query_db("""select * from equipments where equipment_id=?""", (equipment_id,))
    if len(res) == 0:
        return my_response(error="Equipment with id=%s not found" % id, code=404)

    return my_response({"equipment": res[0]})


@app.route('/equipments/<equipment_id>', methods=['PUT'])
def update_equipment(equipment_id):
    if not request.is_json:
        return my_response(error="Body should contains JSON", code=400)

    query_params = {}
    if "device_id" in request.json: query_params["device_id"] = request.json["device_id"]

    if len(query_params) == 0:
        return my_response()

    query_params_str = ""
    for key, val in query_params.items():
        query_params_str = query_params_str + key + "=" + (str(val) if val is not None else "null") + ","

    row_count = query_db("update equipments set %s where equipment_id=%s" % (query_params_str[:-1], equipment_id), ret_rowcount=True)
    if row_count == 0:
        return my_response(error="Equipment with id=%s not found" % equipment_id, code=404)

    return my_response()


@app.route('/rents', methods=['POST'])
def start_rent():
    if not request.is_json:
        return my_response(error="Body should contains JSON", code=400)

    if "equipment_id" not in request.json:
        return my_response(error="Request should contains equipment_id", code=400)
    else:
        equipment_id = request.json["equipment_id"]

    if "user_id" in request.json:
        user_id = request.json["user_id"]
    elif "rfid_id" in request.json:
        user_id = user_by_rfid(request.json["rfid_id"])["user_id"]
    else:
        return my_response(error="Request should contains rfid_id or user_id", code=400)

    begin_time = datetime.datetime.now()

    # Dangeeeeerooouuuuus!!! Not transactional call with insert new opened rent.
    opened_rents_count = len(query_db("select * from rents where equipment_id = ? and end_time is null", (equipment_id,)))
    if opened_rents_count > 0:
        return my_response(error="Equipment with id=%s already rented" % equipment_id, code=403)

    rent_id = query_db("insert into rents(equipment_id, user_id, begin_time) values(?,?,?)", (equipment_id, user_id, begin_time), ret_lastrowid=True)
    return my_response({"rent_id": rent_id})


@app.route('/rents/<id>', methods=['PUT'])
def finish_rent(id):
    end_time = datetime.datetime.now()
    row_count = query_db("update rents set end_time=? where rent_id=?", (end_time, id), ret_rowcount=True)
    if row_count == 0:
        return my_response(error="Rent with id=%s not found" % id, code=404)

    return my_response()


@app.route('/rents/<id>', methods=['GET'])
def get_rent(id):
    res = query_db("""select * from rents where rent_id=?""", (id,))
    if len(res) == 0:
        return my_response(error="Equipment with id=%s not found" % id, code=404)

    return my_response({"rent": res[0]})


if __name__ == '__main__':
    if not path.exists(DATABASE):
        cursor = get_db().cursor()
        create_tables(cursor)
        cursor.close()

    app.run(debug=True, host='0.0.0.0', port=80)
