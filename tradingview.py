import logging
import json
import os
import asyncio
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ✅ Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

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
    """Loads subscribers from file"""
    if os.path.exists(SUBSCRIPTION_FILE):
        try:
            with open(SUBSCRIPTION_FILE, "r") as file:
                return set(json.load(file))
        except (json.JSONDecodeError, FileNotFoundError):
            logging.error("⚠️ Error loading subscriptions. Resetting file.")
            return set()
    return set()

# ✅ Save subscribed users
def save_subscriptions():
    """Saves subscribers to file"""
    try:
        with open(SUBSCRIPTION_FILE, "w") as file:
            json.dump(list(subscribed_users), file)
    except Exception as e:
        logging.error(f"❌ Error saving subscriptions: {e}")

# ✅ Initialize subscriptions
subscribed_users = load_subscriptions()

# ✅ Function to send AI signal with buttons
async def send_signal(user, message):
    try:
        # ✅ Add "🚫 Unsubscribe" & "🔄 Start Again" Buttons
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🚫 Unsubscribe", callback_data=f"unsubscribe_signal_{user}")],
                [InlineKeyboardButton(text="🔄 Start Again", callback_data="show_main_buttons")]
            ]
        )

        # ✅ Send AI Signal Alert with Buttons
        await bot.send_message(chat_id=user, text=message, reply_markup=keyboard)
        logging.info(f"✅ Sent signal to {user}")

    except Exception as e:
        logging.error(f"❌ Failed to send message to {user}: {e}")

# ✅ TradingView Webhook Endpoint
@app.post("/tradingview")
async def tradingview_alert(request: Request):
    try:
        # ✅ Read the request JSON
        data = await request.json()
        
        # ✅ Validate JSON structure
        if not data or "message" not in data:
            logging.error(f"❌ Invalid request: {data}")
            return {"status": "error", "message": "Invalid JSON format or missing 'message' field"}

        message = data["message"]
        logging.info(f"📩 Received TradingView Alert: {message}")

        # ✅ Check if there are subscribed users
        if not subscribed_users:
            logging.info("⚠️ No subscribed users to send the signal.")
            return {"status": "no_subscribers"}

        # ✅ Send message to subscribed users asynchronously
        tasks = [send_signal(user, message) for user in subscribed_users]
        await asyncio.gather(*tasks)

        return {"status": "success", "message": "Signal sent to subscribers"}

    except json.JSONDecodeError:
        logging.error("❌ Received an invalid JSON request from TradingView.")
        return {"status": "error", "message": "Invalid JSON format"}

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

        if user_id in subscribed_users:
            return {"status": "error", "message": "User already subscribed"}

        subscribed_users.add(user_id)
        save_subscriptions()

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
            save_subscriptions()
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
