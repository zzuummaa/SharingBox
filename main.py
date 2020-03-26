#!flask/bin/python
from flask import Flask, jsonify, request, abort, g, make_response
import sqlite3
from uuid import uuid4

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
    res = query_db("""insert into users(user_name, rfid_uid) values(?,?)""", user_params)
    return my_response()


@app.route('/users/<rfid_id>', methods=['GET'])
def get_user(rfid_id):
    res = query_db("""select * from users where rfid_uid=?""", (rfid_id,))
    if len(res) == 0:
        return my_response(error="User with rfid_id=%s not found" % rfid_id, code=404)

    return my_response({"user": res[0]})


@app.route('/devices', methods=['POST'])
def add_device():
    device_id = query_db("""insert into devices default values""", ret_lastrowid=True)
    return my_response({"device_id": device_id})


@app.route('/devices/<id>', methods=['GET'])
def get_device(id):
    res = query_db("""select * from devices where device_id=?""", (id,))
    if len(res) == 0:
        return my_response(error="Device with id=%s not found" % id, code=404)

    return my_response({"device": res[0]})


@app.route('/equipments', methods=['POST'])
def add_equipment():
    if not request.is_json:
        return my_response(error="Body should contains JSON", code=400)

    if "device_id" not in request.json:
        return my_response(error="Invalid request parameters", code=400)

    device_id = request.json["device_id"]
    user_id = request.json["user_id"] if "user_id" in request.json else None

    equipment_id = query_db("""insert into equipments(device_id, user_id) values(?,?)""", (device_id, user_id), ret_lastrowid=True)

    return my_response({"equipment_id": equipment_id})


@app.route('/equipments/<id>', methods=['GET'])
def get_equipment(id):
    res = query_db("""select * from equipments where equipment_id=?""", (id,))
    if len(res) == 0:
        return my_response(error="Equipment with id=%s not found" % id, code=404)

    return my_response({"equipment": res[0]})


@app.route('/equipments/<id>', methods=['PUT'])
def update_equipment(id):
    if not request.is_json:
        return my_response(error="Body should contains JSON", code=400)

    query_params = {}
    if "device_id" in request.json: query_params["device_id"] = request.json["device_id"]

    if len(query_params) == 0:
        return my_response()

    query_params_str = ""
    for key, val in query_params.items():
        query_params_str = query_params_str + key + "=" + (str(val) if val is not None else "null") + ","

    row_count = query_db("update equipments set %s where equipment_id=%s" % (query_params_str[:-1], id), ret_rowcount=True)
    if row_count == 0:
        return my_response(error="Equipment with id=%s not found" % id, code=404)

    return my_response()


@app.route('/rents', methods=['POST'])
def add_rent():
    if not request.is_json:
        return my_response(error="Body should contains JSON", code=400)

    if "user_id" in request.json:
        user_id = request.json["user_id"]
    elif "rfid_id" in request.json:
        res = get_user(request.json["user_id"])
        if res["is_ok"]:
            user_id = res["user"]["user_id"]
        else:
            return res
    else:
        return my_response(error="Request should contains rfid_id or user_id", code=400)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
