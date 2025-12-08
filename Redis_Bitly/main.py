#!/usr/local/bin/python3
import redis
from flask import Flask, request, jsonify, redirect, abort 

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
app = Flask(__name__)

@app.route("/<shortUrl>", methods=['GET'])
def getLongUrl(shortUrl):
    url = r.get(f"url:{shortUrl}")
    if not url:
        abort(404)
    return redirect(url, code=302)

@app.route("/shorten", methods=['POST'])
def shorten():
    data = request.get_json(silent=True) or {}
    shortUrl = data.get("shortUrl")
    longUrl = data.get("longUrl")

    if not longUrl:
        return jsonify({"error": "missing long url"}), 400
    if not shortUrl:
        return jsonify({"error": "missing short url"}), 400
    
    key = f"url:{shortUrl}"

    if r.exists(key):
        return jsonify({"error": "short url exists"}), 400
        
    r.set(key, longUrl)
    return jsonify({"success": "got it"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port= 8000)
