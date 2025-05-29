from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# >>> Trage hier deine echten Capital.com-API-Daten ein (niemals öffentlich teilen!) <<<
API_KEY = "elvswWKiE4RmZ4Mt"
API_PASS = "Daisy1234!"
CAPITAL_COM_API_BASE = "https://api-capital.backend-capital.com"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook empfangen:", data)
    
    # Auslesen der Parameter aus TradingView-Alert
    signal = data.get("signal")
    symbol = data.get("symbol", "BTC/USD")
    volume = data.get("volume", 0.01)

    # Capital.com: Session/Login aufbauen
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

    # Order vorbereiten
    order_type = "BUY" if signal and signal.upper() == "BUY" else "SELL"
    order_payload = {
        "market": symbol,
        "direction": order_type,
        "size": volume,
        "orderType": "MARKET",
        "currencyCode": "USD"
    }

    # Order senden
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

