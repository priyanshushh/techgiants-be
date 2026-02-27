from flask import Flask, jsonify, request
from flask_cors import CORS
import zcatalyst_sdk
import requests as http_requests
import os
import logging
import json

app = Flask(__name__)
CORS(app, origins=["https://techgiants-rgcz-vrlomksv.onslate.in/"])

# ── Logger setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("catalyst-app")

# ── QuickML LLM Config ──────────────────────────────────────
QUICKML_URL     = "https://api.catalyst.zoho.in/quickml/v2/project/31294000000018673/llm/chat"
QUICKML_MODEL   = "crm-di-qwen_text_14b-fp8-it"
CATALYST_ORG    = "60066171561"

FINANCE_SYSTEM_PROMPT = (
    "You are an expert financial analyst and advisor. "
    "Provide accurate, data-driven insights on finance topics including "
    "stock markets, investments, banking, taxation, financial planning, "
    "risk management, and economic trends. "
    "Be concise, factual, and use financial terminology appropriately. "
    "When relevant, mention potential risks and disclaimers. "
    "Do not provide personalized financial advice — instead offer general guidance."
)


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


# ══════════════════════════════════════════════════════════════════════════════
#  CHAT ENDPOINT — Zoho Catalyst QuickML LLM
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/chat', methods=['POST'])
def chat():
    # ── Log incoming request ─────────────────────────────────
    logger.info("▶ REQUEST  %s %s", request.method, request.path)
    logger.info("  Headers: %s", json.dumps(dict(request.headers)))

    try:
        # ── Parse & validate input ───────────────────────────
        body = request.get_json(force=True) or {}
        logger.info("  Body   : %s", json.dumps(body))

        prompt = (body.get("prompt") or "").strip()
        if not prompt:
            return jsonify({
                "status": "error",
                "message": "prompt is required in request body"
            }), 400

        # ── Allow optional overrides from request body ───────
        temperature = body.get("temperature", 0.7)
        max_tokens  = body.get("max_tokens", 512)
        top_p       = body.get("top_p", 0.9)
        top_k       = body.get("top_k", 50)

        # ── Build QuickML request ────────────────────────────
        quickml_headers = {
            "Content-Type":  "application/json",
            "CATALYST-ORG":  CATALYST_ORG,
        }

        quickml_payload = {
            "prompt":        prompt,
            "model":         QUICKML_MODEL,
            "system_prompt": FINANCE_SYSTEM_PROMPT,
            "temperature":   temperature,
            "max_tokens":    max_tokens,
            "top_p":         top_p,
            "top_k":         top_k,
            "best_of":       1,
        }

        logger.info("  → QuickML payload: %s", json.dumps(quickml_payload))

        # ── Call QuickML API ─────────────────────────────────
        llm_response = http_requests.post(
            QUICKML_URL,
            json=quickml_payload,
            headers=quickml_headers,
            timeout=60,
        )

        logger.info("  ← QuickML status: %s", llm_response.status_code)
        logger.info("  ← QuickML body  : %s", llm_response.text[:2000])

        llm_data = llm_response.json()

        if llm_response.status_code != 200:
            return jsonify({
                "status":  "error",
                "message": "QuickML API error",
                "details": llm_data,
            }), llm_response.status_code

        # ── Return success ───────────────────────────────────
        response_data = {
            "status":   "success",
            "model":    QUICKML_MODEL,
            "prompt":   prompt,
            "response": llm_data,
        }
        logger.info("◀ RESPONSE 200: %s", json.dumps(response_data)[:2000])
        return jsonify(response_data), 200

    except Exception as e:
        logger.exception("◀ RESPONSE 500 — Error in /chat")
        return jsonify({
            "status":  "error",
            "message": str(e)
        }), 500


listen_port = os.getenv('X_ZOHO_CATALYST_LISTEN_PORT', 9000)
app.run(host='0.0.0.0', port=listen_port)

