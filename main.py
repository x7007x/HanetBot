from fastapi import FastAPI, Request, Response
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import redis
import json
import random
import telebot.types

TOKEN = "8038936358:AAF-YxpGmXnoDLHG2sljx3fx79mFye9rwzY"
bot = AsyncTeleBot(TOKEN)

# Initialize redis synchronously at module level
r = redis.from_url(
    'redis://default:LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx@redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com:17683'
)

app = FastAPI()

# Remove or comment out startup and shutdown event handlers

@app.post("/webhook")
async def telegram_webhook(request: Request):
    json_update = await request.json()
    update = telebot.types.Update.de_json(json_update)
    await bot.process_new_updates([update])
    return Response(status_code=200)

@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    try:
        data_raw = r.get("bot_data")  # removed await
        if not data_raw:
            await bot.send_message(message.chat.id, "No data found in redis.")
            return
        data = json.loads(data_raw)
        start_message = data.get("start_message", "No 🙂‍↔️")
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = []
        for btn in data.get("main_keyboard", []):
            buttons.append(KeyboardButton(btn["label"]))
        keyboard.add(*buttons)
        await bot.send_message(message.chat.id, start_message, reply_markup=keyboard)
    except Exception as e:
        await bot.send_message(message.chat.id, f"err: {str(e)}")

@bot.message_handler(func=lambda m: True)
async def handle_buttons(message):
    try:
        data_raw = r.get("bot_data")  # removed await
        if not data_raw:
            await bot.send_message(message.chat.id, "No data found in redis.")
            return
        data = json.loads(data_raw)
        main_keyboard = data.get("main_keyboard", [])
        label = message.text
        item = None
        for x in main_keyboard:
            if x["label"] == label:
                item = x
                break
        if not item:
            await bot.send_message(message.chat.id, "Unknown command or button")
            return
        action = item.get("action")
        content = item.get("content", [])
        inline_kbd_data = item.get("inline_keyboard", [])
        inline_keyboard = build_inline_keyboard(inline_kbd_data)
        if not content:
            await bot.send_message(message.chat.id, "No content to send")
            return
        chosen = random.choice(content)
        method = getattr(bot, action, None)
        if not callable(method):
            await bot.send_message(message.chat.id, "Unknown action")
            return
        kwargs = dict(chosen)
        if inline_keyboard:
            kwargs["reply_markup"] = inline_keyboard
        await method(message.chat.id, **kwargs)
    except Exception as e:
        await bot.send_message(message.chat.id, f"err: {str(e)}")

# If you want you can just remove the following event, or at least remove await
# @app.on_event("startup")
# async def set_redis_data():
#     r.ping()
