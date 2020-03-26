#!flask/bin/python
from flask import Flask, jsonify, request, abort, g, make_response
import sqlite3
from uuid import uuid4

DATABASE = "sharingbox.db"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, isolation_level=None)
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
        return jsonify(message=str(e)), 400

    return jsonify(message=str(e)), 500


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
    if not request.json:
        abort(make_response(jsonify(message="Body should contains JSON"), 400))

    if "user_name" not in request.json or "rfid_uid" not in request.json:
        abort(make_response(jsonify(message="Request parameters not set"), 400))

    user_params = (request.json["user_name"], request.json["rfid_uid"])
    res = query_db("""insert into users(user_name, rfid_uid) values(?,?)""", user_params)
    return jsonify({"result": res})


@app.route('/users', methods=['GET'])
def get_user():
    rfid_id = request.args.get("rfid_id")
    if rfid_id is None:
        abort(make_response(jsonify(message="rfid_id parameter not set"), 400))

    res = query_db("""select * from users where rfid_uid=?""", (rfid_id,))
    if len(res) == 0:
        abort(make_response(jsonify(message="User with rfid_id=%s not found" % rfid_id), 404))

    return jsonify({"result": res})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
