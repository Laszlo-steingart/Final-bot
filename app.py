from flask import Flask, request, jsonify
import requests
import os
import pyotp
import traceback

app = Flask(__name__)

API_KEY = os.environ.get("CAPITALCOM_API_KEY")
API_PASS = os.environ.get("CAPITALCOM_API_PASS")
CAPITALCOM_2FA_SECRET = os.environ.get("CAPITALCOM_2FA_SECRET")
CAPITALCOM_USERNAME = os.environ.get("CAPITALCOM_USERNAME")
CAPITAL_COM_API_BASE = "https://api-capital.backend-capital.com"
DEFAULT_EPIC = "BTCUSD"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook empfangen:", data)

    try:
        signal = data.get("strategy_order_action")
        contracts = data.get("strategy_order_contracts", 0.01)
        if not signal:
            print("ERROR: Kein strategy_order_action im Alert")
            return jsonify({"error": "No 'strategy_order_action' in alert message"}), 400

        epic = DEFAULT_EPIC

        # 2FA TOTP generieren
        totp = pyotp.TOTP(CAPITALCOM_2FA_SECRET)
        one_time_passcode = totp.now()

        # Login an Capital.com mit Username, Passwort, 2FA, API-Key
        s = requests.Session()
        login_payload = {
            "identifier": CAPITALCOM_USERNAME,
            "password": API_PASS,
            "oneTimePasscode": one_time_passcode
        }
        login_headers = {
            "X-CAP-API-KEY": API_KEY
        }
        print("Login-Payload:", login_payload)
        login_res = s.post(
            CAPITAL_COM_API_BASE + "/api/v1/session",
            json=login_payload,
            headers=login_headers
        )
        print("Login-Status:", login_res.status_code)
        print("Login-Response:", login_res.text)

        if login_res.status_code != 200:
            return jsonify({"error": "Login failed", "details": login_res.text}), 400

        order_type = "BUY" if signal.lower() == "buy" else "SELL"
        order_payload = {
            "market": epic,
            "direction": order_type,
            "size": float(contracts),
            "orderType": "MARKET",
            "currencyCode": "USD"
        }
        order_headers = {
            "X-CAP-API-KEY": API_KEY
        }
        print("Order-Payload:", order_payload)
        order_res = s.post(
            CAPITAL_COM_API_BASE + "/api/v1/orders",
            json=order_payload,
            headers=order_headers
        )
        print("Order-Status:", order_res.status_code)
        print("Order-Response:", order_res.text)

        if order_res.status_code == 200:
            return jsonify({"status": "Order placed", "order": order_res.json()}), 200
        else:
            return jsonify({"error": "Order failed", "details": order_res.text}), 400

    except Exception as e:
        print("EXCEPTION:", str(e))
        print(traceback.format_exc())
        return jsonify({"error": "Exception", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

