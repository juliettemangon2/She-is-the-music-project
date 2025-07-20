from flask import Flask, request, jsonify, render_template
from main import main as process_song

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/songdata')
def song_data():
    artist = request.args.get('artist')
    title = request.args.get('title')
    if not artist or not title:
        return jsonify({"error": "Missing artist or title"}), 400

    result = process_song(artist, title)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
