from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import time

app = Flask(__name__)
metrics = PrometheusMetrics(app)

@app.route('/api/hello')
def hello():
    return jsonify({
        "message": "Hello from the developer of AutoScaleX"
    })

@app.route('/api/data')
def get_data():
    time.sleep(1)
    return jsonify({
        "timestamp": time.time(),
        "data": "Sample data"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
