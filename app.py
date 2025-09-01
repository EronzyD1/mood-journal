import os
import json
import uuid
from datetime import datetime

import requests
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

from config import Config
from models import get_db, User, Entry, Payment

load_dotenv()

db = get_db()

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

HF_API_URL = "https://api-inference.huggingface.co/models/{}"

# ---------- Helpers ----------

def ensure_user():
    if "user_id" not in session:
        session["user_id"] = uuid.uuid4().hex
        session.permanent = True
    user = User.query.get(session["user_id"])
    if not user:
        user = User(id=session["user_id"], is_pro=False)
        db.session.add(user)
        db.session.commit()
    return user


def call_huggingface(model: str, text: str):
    headers = {"Authorization": f"Bearer {app.config['HF_API_KEY']}"} if app.config['HF_API_KEY'] else {}
    url = HF_API_URL.format(model)
    try:
        resp = requests.post(url, headers=headers, json={"inputs": text}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Normalized structure: list of dicts with label/score
        # Some models return [[{label,score}...]]; flatten if needed
        if isinstance(data, list) and len(data) and isinstance(data[0], list):
            data = data[0]
        scores = {item["label"].lower(): float(item["score"]) for item in data}
        top_label = max(scores, key=scores.get)
        top_score = scores[top_label]
        return top_label, top_score, scores
    except Exception:
        # Fallback (super naive):
        lowered = text.lower()
        heur = {
            "joy": any(k in lowered for k in ["happy", "great", "excited", "joy", "good"]),
            "sadness": any(k in lowered for k in ["sad", "down", "blue", "cry", "lonely"]),
            "anger": any(k in lowered for k in ["angry", "mad", "furious", "rage"]),
            "fear": any(k in lowered for k in ["worried", "scared", "anxious", "afraid"]),
            "love": any(k in lowered for k in ["love", "grateful", "thankful"]),
        }
        scores = {k: (1.0 if v else 0.0) for k, v in heur.items()}
        top_label = max(scores, key=scores.get)
        return top_label, scores[top_label], scores


# ---------- Routes ----------

@app.before_request
def load_user():
    ensure_user()


@app.route("/")
def index():
    return render_template(
        "index.html",
        flw_public_key=app.config["FLW_PUBLIC_KEY"],
        amount=app.config["SUBSCRIPTION_AMOUNT"],
        currency=app.config["SUBSCRIPTION_CURRENCY"],
    )


@app.route("/entry", methods=["POST"])
def add_entry():
    user = ensure_user()
    text = (request.form.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "Text is required"}), 400

    label, score, scores = call_huggingface(app.config["HF_MODEL"], text)

    e = Entry(
        user_id=user.id,
        text=text,
        top_emotion=label,
        top_score=score,
        scores_json=json.dumps(scores),
    )
    db.session.add(e)
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "entry": {
                "id": e.id,
                "created_at": e.created_at.isoformat(),
                "top_emotion": e.top_emotion,
                "top_score": e.top_score,
                "scores": scores,
            },
        }
    )


@app.route("/data")
def data():
    user = ensure_user()
    rows = Entry.query.filter_by(user_id=user.id).order_by(Entry.created_at.asc()).all()
    out = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "top_emotion": r.top_emotion,
                "top_score": r.top_score,
                "scores": json.loads(r.scores_json or "{}"),
            }
        )
    return jsonify({"ok": True, "entries": out})


@app.route("/user/status")
def user_status():
    user = ensure_user()
    now = datetime.utcnow()
    is_pro = bool(user.pro_until and user.pro_until > now)
    return jsonify(
        {
            "ok": True,
            "is_pro": is_pro,
            "email": user.email,
            "pro_until": user.pro_until.isoformat() if user.pro_until else None,
        }
    )


@app.route("/user/email", methods=["POST"])
def set_email():
    user = ensure_user()
    email = (request.form.get("email") or "").strip()
    if not email:
        return jsonify({"ok": False, "error": "Email required"}), 400
    existing = User.query.filter_by(email=email).first()
    if existing and existing.id != user.id:
        session["user_id"] = existing.id
        user = existing
    else:
        user.email = email
    db.session.commit()
    return jsonify({"ok": True, "email": user.email})


# ---------- Payments (Flutterwave) ----------

@app.route("/subscribe/txref")
def make_txref():
    user = ensure_user()
    tx_ref = f"mj-{user.id}-{uuid.uuid4().hex[:8]}"
    p = Payment(
        user_id=user.id,
        tx_ref=tx_ref,
        status="initialized",
        amount=app.config["SUBSCRIPTION_AMOUNT"],
        currency=app.config["SUBSCRIPTION_CURRENCY"],
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"ok": True, "tx_ref": tx_ref})


@app.route("/payment/verify", methods=["POST"])
def verify_payment():
    user = ensure_user()
    data = request.get_json(force=True)
    flw_tx_id = str(data.get("transaction_id"))
    tx_ref = data.get("tx_ref")
    if not (flw_tx_id and tx_ref):
        return jsonify({"ok": False, "error": "Missing transaction data"}), 400

    url = f"https://api.flutterwave.com/v3/transactions/{flw_tx_id}/verify"
    headers = {"Authorization": f"Bearer {app.config['FLW_SECRET_KEY']}"}
    r = requests.get(url, headers=headers, timeout=30)
    try:
        payload = r.json()
    except Exception:
        payload = {"raw": r.text}

    status_ok = False
    amount_ok = False
    currency_ok = False

    if isinstance(payload, dict) and payload.get("status") == "success":
        data = payload.get("data", {})
        status_ok = data.get("status") == "successful"
        amount_ok = float(data.get("amount", 0)) >= float(app.config["SUBSCRIPTION_AMOUNT"])
        currency_ok = data.get("currency") == app.config["SUBSCRIPTION_CURRENCY"]
        tx_ref_matches = data.get("tx_ref") == tx_ref
    else:
        data = {}
        tx_ref_matches = False

    p = Payment.query.filter_by(tx_ref=tx_ref).first()
    if not p:
        p = Payment(user_id=user.id, tx_ref=tx_ref)
        db.session.add(p)

    p.flw_tx_id = flw_tx_id
    p.raw_json = json.dumps(payload)

    if status_ok and amount_ok and currency_ok and tx_ref_matches:
        p.status = "successful"
        u = User.query.get(user.id)
        u.activate_pro(app.config["SUBSCRIPTION_DURATION_DAYS"])
        db.session.commit()
        return jsonify({"ok": True, "message": "Payment verified. PRO activated."})
    else:
        p.status = "failed"
        db.session.commit()
        return jsonify(
            {"ok": False, "error": "Verification failed", "payload": payload}
        ), 400


@app.route("/webhook/flutterwave", methods=["POST"])
def flutterwave_webhook():
    secret = app.config["FLW_WEBHOOK_SECRET"]
    incoming = request.headers.get("verif-hash")
    if not secret or incoming != secret:
        return "", 401

    event = request.get_json(silent=True) or {}
    data = event.get("data", {})
    flw_tx_id = data.get("id") or data.get("txid")
    tx_ref = data.get("tx_ref")
    if flw_tx_id and tx_ref:
        with app.test_request_context(
            "/payment/verify",
            method="POST",
            json={"transaction_id": flw_tx_id, "tx_ref": tx_ref},
        ):
            verify_payment()
        return "ok", 200

    return "ok", 200


# ---------- CLI ----------

@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
