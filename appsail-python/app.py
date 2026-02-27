from flask import Flask, jsonify, request
import zcatalyst_sdk
import os
import traceback

app = Flask(__name__)


@app.route('/')
def index():
    return 'Web App with Python Flask!'


@app.route('/bucket')
def get_bucket_details():
    try:
        catalyst_app = zcatalyst_sdk.initialize(req=request)
        stratus = catalyst_app.stratus()
        bucket = stratus.bucket('techgiants')
        bucket_details = bucket.get_details()
        return jsonify({
            'status': 'success',
            'data': bucket_details
        }), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


listen_port = os.getenv('X_ZOHO_CATALYST_LISTEN_PORT', 9000)
app.run(host='0.0.0.0', port=listen_port)
