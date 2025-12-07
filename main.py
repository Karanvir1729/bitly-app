import os
import redis
from flask import Flask, request, jsonify, redirect, abort

# Environment variables for Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

app = Flask(__name__)


@app.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.get_json(silent=True) or {}

    # Long URL from client
    original_url = data.get("url")
    # Desired short code from client
    desired_code = data.get("code")

    if not original_url or not isinstance(original_url, str):
        return jsonify({"error": "Missing or invalid 'url' field"}), 400

    if not desired_code or not isinstance(desired_code, str):
        return jsonify({"error": "Missing or invalid 'code' field"}), 400

    # Optionally enforce simple allowed characters
    if not desired_code.isalnum():
        return jsonify({"error": "Short code must be alphanumeric"}), 400

    key = f"url:{desired_code}"

    # Check if code is already taken
    if r.exists(key):
        return (
            jsonify(
                {
                    "error": "Requested short code is already in use",
                    "code": desired_code,
                }
            ),
            409,
        )

    # Store mapping
    r.set(key, original_url)

    base_url = os.getenv("BASE_URL", "http://localhost/")
    if not base_url.endswith("/"):
        base_url += "/"

    short_url = base_url + desired_code

    return jsonify(
        {
            "code": desired_code,
            "short_url": short_url,
            "original_url": original_url,
        }
    ), 201


@app.route("/<code>", methods=["GET"])
def redirect_code(code):
    key = f"url:{code}"
    url = r.get(key)
    if not url:
        abort(404)
    return redirect(url, code=302)


if __name__ == "__main__":
    # For local testing only; in Docker we use gunicorn
    app.run(host="0.0.0.0", port=8000)

