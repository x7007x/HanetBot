from flask import Flask, request, jsonify, render_template
import redis
import json

r = redis.from_url(
    'redis://default:LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx@redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com:17683'
)

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'https://ahmed-negm.pages.dev'

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok"})

@app.route("/webapp")
def webapp():
    return render_template("index.html")

@app.route('/save_data', methods=['POST'])
def save_data():
    try:
        json_data = request.get_json(force=True)
        r.set("bot_data", json.dumps(json_data))
        return jsonify({"status": "success", "message": "Data saved to Redis"})
    except Exception as e:
        return jsonify({"status": "error", "detail": f"Error saving data: {e}"}), 500

@app.route('/get_data', methods=['GET'])
def get_data():
    raw = r.get("bot_data")
    if not raw:
        return jsonify({"status": "error", "detail": "No data found in Redis"}), 404
    data = json.loads(raw)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
