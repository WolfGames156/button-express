from flask import Flask, render_template, jsonify, session, request
import json
import os
import time
from threading import Lock
from keep_alive import keep_alive
import uuid

app = Flask(__name__)
app.secret_key = "super-secret-key"  # bunu mutlaka değiştir

DATA_FILE = "counter.json"
active_users = {}
active_users_lock = Lock()
USER_TIMEOUT = 20


def load_counter():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f).get("count", 0)
    return 0


def save_counter(count):
    with open(DATA_FILE, "w") as f:
        json.dump({"count": count}, f)


counter = load_counter()


def cleanup_active_users():
    now = time.time()
    with active_users_lock:
        to_delete = [
            user for user, ts in active_users.items()
            if now - ts > USER_TIMEOUT
        ]
        for user in to_delete:
            del active_users[user]


def update_active_user():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    user_id = session["user_id"]
    with active_users_lock:
        active_users[user_id] = time.time()
    cleanup_active_users()


@app.route("/")
def index():
    update_active_user()
    return render_template("index.html")


@app.route("/increment", methods=["POST"])
def increment():
    global counter
    counter += 1
    save_counter(counter)
    update_active_user()
    return jsonify({"count": counter})


@app.route("/get_count")
def get_count():
    update_active_user()
    with active_users_lock:
        online_count = len(active_users)
    return jsonify({"count": counter, "online": online_count})


if __name__ == "__main__":
    keep_alive()
    app.run(host="0.0.0.0", port=81)
