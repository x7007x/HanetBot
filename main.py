from fastapi import FastAPI, Request, Response
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import redis.asyncio as redis
import json
import random
import telebot.types

TOKEN = "8038936358:AAF-YxpGmXnoDLHG2sljx3fx79mFye9rwzY"
bot = AsyncTeleBot(TOKEN)

r = None
app = FastAPI()

def build_inline_keyboard(inline_kbd_data):
    if not inline_kbd_data:
        return None

    inline_keyboard = InlineKeyboardMarkup()
    for row in inline_kbd_data:
        buttons = []
        for b in row:
            btn_type = b.get("type")
            text = b.get("text")
            if btn_type == "url":
                buttons.append(InlineKeyboardButton(text=text, url=b.get("value")))
            elif btn_type == "callback_data":
                buttons.append(InlineKeyboardButton(text=text, callback_data=b.get("value")))
            elif btn_type == "switch_inline_query":
                buttons.append(InlineKeyboardButton(text=text, switch_inline_query=b.get("value")))
            elif btn_type == "switch_inline_query_current_chat":
                buttons.append(InlineKeyboardButton(text=text, switch_inline_query_current_chat=b.get("value")))
            elif btn_type == "web_app":
                web_app_data = b.get("value", {})
                url = web_app_data.get("url")
                if url:
                    web_app_obj = WebAppInfo(url=url)
                    buttons.append(InlineKeyboardButton(text=text, web_app=web_app_obj))
                else:
                    buttons.append(InlineKeyboardButton(text=text, callback_data=text))
            else:
                buttons.append(InlineKeyboardButton(text=text, callback_data=text))
        inline_keyboard.row(*buttons)
    return inline_keyboard

@app.on_event("startup")
async def startup_event():
    global r
    r = redis.from_url(
        'redis://default:LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx@redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com:17683'
    )

@app.on_event("shutdown")
async def shutdown_event():
    await r.close()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    json_update = await request.json()
    update = telebot.types.Update.de_json(json_update)
    await bot.process_new_updates([update])
    return Response(status_code=200)

@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    try:
        data_raw = await r.get("bot_data")
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
        data_raw = await r.get("bot_data")
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

data = {
    "start_message": "Hello",
    "main_keyboard": [
        {
            "label": "button 1",
            "action": "send_message",
            "content": [
                {"text": "Hello ¹"},
                {"text": "Hello ²"}
            ],
            "inline_keyboard": [
                [
                    {"text": "URL Button", "type": "url", "value": "https://t.me"},
                    {"text": "Callback Button", "type": "callback_data", "value": "callback_1"}
                ],
                [
                    {"text": "Switch Inline Query", "type": "switch_inline_query", "value": "query"},
                    {"text": "Switch Inline Query Current Chat", "type": "switch_inline_query_current_chat", "value": "query_current"}
                ],
                [
                    {"text": "WebApp Button", "type": "web_app", "value": {"url": "https://yourwebappurl.com"}}
                ]
            ]
        },
        {
            "label": "button 2",
            "action": "send_photo",
            "content": [
                {"photo": "https://files.catbox.moe/wfnud7.jpg", "caption": "Caption 1"},
                {"photo": "https://files.catbox.moe/i6dj6j.jpg", "caption": "Caption 2"}
            ],
            "inline_keyboard": []
        }
    ]
}

@app.on_event("startup")
async def set_redis_data():
    await r.ping()
