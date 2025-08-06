from fastapi import FastAPI, Request, Response
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
import redis
import json
import random
import telebot.types

TOKEN = "8038936358:AAF-YxpGmXnoDLHG2sljx3fx79mFye9rwzY"
bot = AsyncTeleBot(TOKEN)
r = redis.from_url(
    'redis://default:LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx@redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com:17683'
)
app = FastAPI()


def build_inline_keyboard(inline_kbd_data):
    if not inline_kbd_data:
        return None
    inline_keyboard = InlineKeyboardMarkup()
    for row in inline_kbd_data:
        buttons = []
        for b in row:
            t = b.get("type")
            text = b.get("text")
            if t == "url":
                buttons.append(InlineKeyboardButton(text=text, url=b.get("value")))
            elif t == "callback_data":
                buttons.append(InlineKeyboardButton(text=text, callback_data=b.get("value")))
            elif t == "switch_inline_query":
                buttons.append(InlineKeyboardButton(text=text, switch_inline_query=b.get("value")))
            elif t == "switch_inline_query_current_chat":
                buttons.append(InlineKeyboardButton(text=text, switch_inline_query_current_chat=b.get("value")))
            elif t == "web_app":
                url = b.get("value", {}).get("url")
                if url:
                    buttons.append(InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url)))
                else:
                    buttons.append(InlineKeyboardButton(text=text, callback_data=text))
            else:
                buttons.append(InlineKeyboardButton(text=text, callback_data=text))
        inline_keyboard.row(*buttons)
    return inline_keyboard


@app.post("/webhook")
async def webhook(request: Request):
    update_json = await request.json()
    update = telebot.types.Update.de_json(update_json)
    await bot.process_new_updates([update])
    return Response(status_code=200)


@bot.message_handler(commands=['start', 'help'])
async def start_help(message):
    try:
        raw = r.get("bot_data")
        if not raw:
            await bot.send_message(message.chat.id, "No data found.")
            return
        data = json.loads(raw)
        msg = data.get("start_message", "Welcome!")
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [KeyboardButton(btn["label"]) for btn in data.get("main_keyboard", [])]
        keyboard.add(*buttons)
        await bot.send_message(message.chat.id, msg, reply_markup=keyboard)
    except Exception as e:
        await bot.send_message(message.chat.id, f"Error: {e}")


@bot.message_handler(func=lambda m: True)
async def all_messages(message):
    try:
        raw = r.get("bot_data")
        if not raw:
            await bot.send_message(message.chat.id, "No data found.")
            return
        data = json.loads(raw)
        mk = data.get("main_keyboard", [])
        label = message.text
        item = next((x for x in mk if x["label"] == label), None)
        if not item:
            await bot.send_message(message.chat.id, "Unknown command or button")
            return
        chosen = random.choice(item.get("content", []))
        inline_keyboard = build_inline_keyboard(item.get("inline_keyboard", []))
        action = item.get("action")
        method = getattr(bot, action, None)
        if not callable(method):
            await bot.send_message(message.chat.id, "Unknown action")
            return
        kwargs = dict(chosen)
        if inline_keyboard:
            kwargs["reply_markup"] = inline_keyboard
        await method(message.chat.id, **kwargs)
    except Exception as e:
        await bot.send_message(message.chat.id, f"Error: {e}")


@app.get("/ping")
async def ping():
    return {"status": "ok"}


# Preload bot data into Redis synchronously - run once before or deploy-time
data = {
    "start_message": "Hello",
    "main_keyboard": [
        {
            "label": "button 1",
            "action": "send_message",
            "content": [{"text": "Hello ¹"}, {"text": "Hello ²"}],
            "inline_keyboard": [
                [
                    {"text": "URL Button", "type": "url", "value": "https://t.me"},
                    {"text": "Callback Button", "type": "callback_data", "value": "callback_1"},
                ],
                [
                    {"text": "Switch Inline Query", "type": "switch_inline_query", "value": "query"},
                    {"text": "Switch Inline Query Current Chat", "type": "switch_inline_query_current_chat", "value": "query_current"},
                ],
                [{"text": "WebApp Button", "type": "web_app", "value": {"url": "https://yourwebappurl.com"}}],
            ],
        },
        {
            "label": "button 2",
            "action": "send_photo",
            "content": [
                {"photo": "https://files.catbox.moe/wfnud7.jpg", "caption": "Caption 1"},
                {"photo": "https://files.catbox.moe/i6dj6j.jpg", "caption": "Caption 2"},
            ],
            "inline_keyboard": [],
        },
    ],
}
r.set("bot_data", json.dumps(data))
