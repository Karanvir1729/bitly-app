#!/usr/bin/python
from flask import Flask, request, jsonify, redirect, abort
from cassandra.cluster import Cluster
import os

# Defaults pointing at your cluster:
# 10.128.0.3, 10.128.0.4, 10.128.0.5 with RF=3
CASSANDRA_CONTACT_POINTS = os.getenv(
    "CASSANDRA_CONTACT_POINTS",
    "10.128.0.3,10.128.0.4,10.128.0.5",
)
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "urlshortener")
CASSANDRA_RF = int(os.getenv("CASSANDRA_RF", "3"))

contact_points = [h.strip() for h in CASSANDRA_CONTACT_POINTS.split(",") if h.strip()]

cluster = Cluster(contact_points)
session = cluster.connect()

# Create keyspace if needed
session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
    WITH replication = {{
        'class': 'SimpleStrategy',
        'replication_factor': {CASSANDRA_RF}
    }}
""")

session.set_keyspace(CASSANDRA_KEYSPACE)

# Create table if needed
session.execute("""
    CREATE TABLE IF NOT EXISTS urls (
        code text PRIMARY KEY,
        original_url text
    )
""")

# Prepare statements
select_url_stmt = session.prepare("SELECT original_url FROM urls WHERE code = ?")
insert_url_stmt = session.prepare("INSERT INTO urls (code, original_url) VALUES (?, ?)")

app = Flask(__name__)


@app.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.get_json(silent=True) or {}

    original_url = data.get("url")
    desired_code = data.get("code")

    if not original_url or not isinstance(original_url, str):
        return jsonify({"error": "Missing or invalid 'url' field"}), 400

    if not desired_code or not isinstance(desired_code, str):
        return jsonify({"error": "Missing or invalid 'code' field"}), 400

    if not desired_code.isalnum():
        return jsonify({"error": "Short code must be alphanumeric"}), 400

    # Check if code already exists
    rows = session.execute(select_url_stmt, [desired_code])
    existing = rows.one()
    if existing is not None:
        return (
            jsonify(
                {
                    "error": "Requested short code is already in use",
                    "code": desired_code,
                    "original_url": existing.original_url,
                }
            ),
            409,
        )

    # Insert new mapping
    session.execute(insert_url_stmt, [desired_code, original_url])

    base_url = os.getenv("BASE_URL", "http://localhost:8000/")
    if not base_url.endswith("/"):
        base_url += "/"

    short_url = base_url + desired_code

    return (
        jsonify(
            {
                "code": desired_code,
                "short_url": short_url,
                "original_url": original_url,
            }
        ),
        201,
    )


@app.route("/<code>", methods=["GET"])
def redirect_code(code):
    rows = session.execute(select_url_stmt, [code])
    row = rows.one()
    if row is None:
        abort(404)
    return redirect(row.original_url, code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)