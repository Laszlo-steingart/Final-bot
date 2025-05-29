from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get("CAPITALCOM_API_KEY")
API_PASS = os.environ.get("CAPITALCOM_API_PASS")
CAPITAL_COM_API_BASE = "https://api-capital.backend-capital.com"

# <<< HIER: Deinen Epic festlegen (z.B. BTCUSD) >>>
DEFAULT_EPIC = "BTCUSD"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook empfangen:", data)
    
    # Werte aus TradingView Strategy Alert Message
    signal = data.get("strategy_order_action")
    contracts = data.get("strategy_order_contracts", 0.01)  # Standardvolumen

    if not signal:
        return jsonify({"error": "No 'strategy_order_action' in alert message"}), 400

    epic = DEFAULT_EPIC

    # Session/Login bei Capital.com
    s = requests.Session()
    login_res = s.post(
        CAPITAL_COM_API_BASE + "/api/v1/session",
        json={
            "identifier": API_KEY,
            "password": API_PASS
        },
        headers={"X-CAP-API-KEY": API_KEY}
    )
    if login_res.status_code != 200:
        return jsonify({"error": "Login failed", "details": login_res.text}), 400

    # Order-Daten zusammenstellen
    order_type = "BUY" if signal.lower() == "buy" else "SELL"
    order_payload = {
        "market": epic,
        "direction": order_type,
        "size": contracts,
        "orderType": "MARKET",
        "currencyCode": "USD"
    }

    # Order an Capital.com senden
    order_res = s.post(
        CAPITAL_COM_API_BASE + "/api/v1/orders",
        json=order_payload,
        headers={"X-CAP-API-KEY": API_KEY}
    )

    if order_res.status_code == 200:
        return jsonify({"status": "Order placed", "order": order_res.json()}), 200
    else:
        return jsonify({"error": "Order failed", "details": order_res.text}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

