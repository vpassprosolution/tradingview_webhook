import logging
import json
import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from aiogram import Bot

# ✅ Load environment variables
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Please check your Railway environment variables.")

# ✅ Initialize FastAPI
app = FastAPI()

# ✅ Logging setup
logging.basicConfig(level=logging.INFO)

# ✅ Initialize bot
bot = Bot(token=BOT_TOKEN)

# ✅ Subscription file
SUBSCRIPTION_FILE = "subscribed_users.json"

# ✅ Load subscribed users
def load_subscriptions():
    if os.path.exists(SUBSCRIPTION_FILE):
        try:
            with open(SUBSCRIPTION_FILE, "r") as file:
                return set(json.load(file))
        except json.JSONDecodeError:
            logging.error("⚠️ Error decoding JSON. Resetting subscriptions.")
            return set()
    return set()

# ✅ Save subscribed users
def save_subscriptions(users):
    with open(SUBSCRIPTION_FILE, "w") as file:
        json.dump(list(users), file)

subscribed_users = load_subscriptions()

# ✅ TradingView Webhook Endpoint
@app.post("/tradingview")
async def tradingview_alert(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "📩 VPASS PRO GOT SIGNAL!")

        # ✅ Check if there are subscribed users
        if not subscribed_users:
            logging.info("⚠️ No subscribed users to send the signal.")
            return {"status": "no_subscribers"}

        # ✅ Send message to subscribed users
        for user in subscribed_users:
            try:
                await bot.send_message(chat_id=user, text=message)
                logging.info(f"✅ Sent signal to {user}")
            except Exception as e:
                logging.error(f"❌ Failed to send message to {user}: {e}")

        return {"status": "success", "message": "Signal sent to subscribers"}

    except Exception as e:
        logging.error(f"❌ Error in TradingView webhook: {e}")
        return {"status": "error", "message": str(e)}

# ✅ Subscribe User to TradingView Alerts
@app.post("/subscribe")
async def subscribe_user(request: Request):
    try:
        data = await request.json()
        user_id = str(data.get("user_id"))  # Ensure user_id is a string

        if not user_id:
            return {"status": "error", "message": "Missing user_id"}

        subscribed_users.add(user_id)
        save_subscriptions(subscribed_users)

        return {"status": "success", "message": f"User {user_id} subscribed"}

    except Exception as e:
        logging.error(f"❌ Error subscribing user: {e}")
        return {"status": "error", "message": str(e)}

# ✅ Unsubscribe User from TradingView Alerts
@app.post("/unsubscribe")
async def unsubscribe_user(request: Request):
    try:
        data = await request.json()
        user_id = str(data.get("user_id"))  # Ensure user_id is a string

        if not user_id:
            return {"status": "error", "message": "Missing user_id"}

        if user_id in subscribed_users:
            subscribed_users.remove(user_id)
            save_subscriptions(subscribed_users)
            return {"status": "success", "message": f"User {user_id} unsubscribed"}
        else:
            return {"status": "error", "message": "User not found in subscription list"}

    except Exception as e:
        logging.error(f"❌ Error unsubscribing user: {e}")
        return {"status": "error", "message": str(e)}

# ✅ Run FastAPI Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
