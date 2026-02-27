from flask import Flask, jsonify, request
import zcatalyst_sdk
import os
import logging
import json

app = Flask(__name__)

# ── Logger setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("catalyst-app")


@app.route('/')
def index():
    return 'Web App with Python Flask!'


@app.route('/bucket')
def get_bucket_details():
    # ── Log incoming request ─────────────────────────────────
    logger.info("▶ REQUEST  %s %s", request.method, request.path)
    logger.info("  Headers: %s", json.dumps(dict(request.headers)))

    try:
        catalyst_app = zcatalyst_sdk.initialize(req=request)
        stratus = catalyst_app.stratus()
        bucket = stratus.bucket('techgiants')
        bucket_details = bucket.get_details()

        response_data = {
            'status': 'success',
            'data': bucket_details
        }
        logger.info("◀ RESPONSE 200: %s", json.dumps(response_data))
        return jsonify(response_data), 200

    except Exception as e:
        logger.exception("◀ RESPONSE 500 — Error in /bucket")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


listen_port = os.getenv('X_ZOHO_CATALYST_LISTEN_PORT', 9000)
app.run(host='0.0.0.0', port=listen_port)
