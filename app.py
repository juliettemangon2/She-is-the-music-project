from flask import Flask, request, jsonify
from main import aggregate_song_data, build_multi_song_insights
import json
import os

app = Flask(__name__)

DATABASE_FILE = os.path.join(os.path.dirname(__file__), "database.json")

@app.route('/')
def index():
    try:
        with open(os.path.join('templates', 'index.html'), 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>index.html not found</h1>", 404

@app.route('/api/database', methods=['GET'])
def get_database():
    try:
        if not os.path.exists(DATABASE_FILE):
            return jsonify({"songs": [], "derived_insights": {}})
        with open(DATABASE_FILE, "r") as f:
            db = json.load(f)

        insights = {}
        if len(db) > 1:
            insights = build_multi_song_insights(db)

        return jsonify({"songs": db, "derived_insights": insights})
    except Exception as e:
        return jsonify({"error": f"Failed to load database: {str(e)}"}), 500

@app.route('/api/songdata', methods=['GET'])
def songdata():
    try:
        artists = request.args.getlist('artist')
        titles = request.args.getlist('title')

        if len(artists) != len(titles) or len(artists) == 0:
            return jsonify({'error': 'Mismatched artist and title counts.'}), 400

        result = aggregate_song_data(artists, titles)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
