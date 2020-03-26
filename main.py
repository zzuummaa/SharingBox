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
        db.row_factory = make_dicts
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


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
        return my_response(error="Request parameters not set", code=400)

    user_params = (request.json["user_name"], request.json["rfid_uid"])
    res = query_db("""insert into users(user_name, rfid_uid) values(?,?)""", user_params)
    return my_response()


@app.route('/users/<rfid_id>', methods=['GET'])
def get_user(rfid_id):
    res = query_db("""select * from users where rfid_uid=?""", (rfid_id,))
    if len(res) == 0:
        return my_response(error="User with rfid_id=%s not found" % rfid_id, code=404)

    return my_response({"user": res[0]})


@app.route('/devices', methods=['GET'])
def add_device():
    token = uuid4().hex
    res = query_db("""insert into devices(device_token) values(?)""", (token,))
    return my_response({"token": token})


@app.route('/devices/<token>', methods=['GET'])
def get_device(token):
    res = query_db("""select * from devices where device_token=?""", (token,))
    if len(res) == 0:
        abort(make_response(jsonify(message="Device with token=%s not found" % token), 404))

    return my_response({"device": res[0]})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
