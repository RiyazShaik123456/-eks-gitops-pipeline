from flask import Flask, jsonify
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import os
import socket

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "app_requests_total", "Total requests received", ["endpoint"]
)

APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")


@app.route("/")
def index():
    REQUEST_COUNT.labels(endpoint="/").inc()
    return jsonify(
        message="Hello from the DevOps demo app",
        version=APP_VERSION,
        hostname=socket.gethostname(),
    )


@app.route("/health")
def health():
    REQUEST_COUNT.labels(endpoint="/health").inc()
    return jsonify(status="ok"), 200


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
