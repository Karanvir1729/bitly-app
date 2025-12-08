from cassandra.cluster import Cluster
import uuid
from flask import Flask, request, jsonify

# Connect to Cassandra
cluster = Cluster(['10.128.0.3', '10.128.0.4', '10.128.0.5', '10.128.0.6'])
session = cluster.connect()

# Create keyspace and table if needed
session.execute("""
    CREATE KEYSPACE IF NOT EXISTS notesapp
    WITH replication = {
        'class': 'SimpleStrategy',
        'replication_factor': 3
    }
""")
session.set_keyspace("notesapp")

session.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id uuid PRIMARY KEY,
        title text,
        body text
    )
""")

# Prepared statements
write_query = session.prepare(
    "INSERT INTO notes (id, title, body) VALUES (?, ?, ?)"
)
read_query = session.prepare(
    "SELECT id, title, body FROM notes WHERE id = ?"
)

# Flask app
app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/notes", methods=["POST"])
def write_note():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    body = data.get("body")

    if not isinstance(title, str) or not title:
        return jsonify({"error": "title is required and must be a nonempty string"}), 400
    if not isinstance(body, str) or not body:
        return jsonify({"error": "body is required and must be a nonempty string"}), 400

    note_id = uuid.uuid1()
    session.execute(write_query, (note_id, title, body))

    return jsonify({
        "id": str(note_id),
        "title": title,
        "body": body,
    }), 201


@app.route("/notes/<note_id>", methods=["GET"])
def read_note(note_id):
    try:
        parsed_id = uuid.UUID(note_id)
    except ValueError:
        return jsonify({"error": "invalid uuid"}), 400

    rows = session.execute(read_query, (parsed_id,))
    row = rows.one()
    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify({
        "id": str(row.id),
        "title": row.title,
        "body": row.body,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
