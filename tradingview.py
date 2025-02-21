import logging
import os
import json
from fastapi import FastAPI, Request
import uvicorn
import httpx
from dotenv import load_dotenv

# ✅ Load bot token
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ✅ Load TradingView Webhook API
app = FastAPI()

SUBSCRIPTION_FILE = "subscribed_users.json"

# ✅ Load subscribed users
def load_subscriptions():
    if os.path.exists(SUBSCRIPTION_FILE):
        with open(SUBSCRIPTION_FILE, "r") as file:
            return set(json.load(file))
    return set()

subscribed_users = load_subscriptions()

@app.post("/tradingview")
async def tradingview_alert(request: Request):
    """Receives alerts from TradingView and sends them to subscribed users."""
    try:
        data = await request.json()
        message = data.get("message", "📩 VPASS PRO GOT SIGNAL")

        for user in subscribed_users:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(TELEGRAM_API_URL, json={"chat_id": user, "text": message})
            except Exception as e:
                logging.error(f"❌ Failed to send message to {user}: {e}")

        return {"status": "success"}
    except Exception as e:
        logging.error(f"❌ Error receiving TradingView alert: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
