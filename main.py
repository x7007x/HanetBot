from pyrogram import Client, filters
from pyrogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
import asyncio
import redis
import json
import random

API_ID = 24638506
API_HASH = "43899b1fabd74d939033175b11d499a4"
BOT_TOKEN = "8038936358:AAF-YxpGmXnoDLHG2sljx3fx79mFye9rwzY"

r = redis.Redis(
    host='redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17683,
    decode_responses=True,
    username="default",
    password="LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx",
)

app = Client("mybot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

def build_inline_keyboard(inline_kbd_data):
    if not inline_kbd_data:
        return None
    buttons = []
    for row in inline_kbd_data:
        btn_row = []
        for b in row:
            btn_type = b.get("type")
            text = b.get("text")
            if btn_type == "url":
                btn_row.append(InlineKeyboardButton(text=text, url=b.get("value")))
            elif btn_type == "callback_data":
                btn_row.append(InlineKeyboardButton(text=text, callback_data=b.get("value")))
            elif btn_type == "switch_inline_query":
                btn_row.append(InlineKeyboardButton(text=text, switch_inline_query=b.get("value")))
            elif btn_type == "switch_inline_query_current_chat":
                btn_row.append(InlineKeyboardButton(text=text, switch_inline_query_current_chat=b.get("value")))
            elif btn_type == "web_app":
                web_app_data = b.get("value", {})
                url = web_app_data.get("url")
                if url:
                    web_app_obj = WebAppInfo(url=url)
                    btn_row.append(InlineKeyboardButton(text=text, web_app=web_app_obj))
                else:
                    btn_row.append(InlineKeyboardButton(text=text, callback_data=text))
            else:
                btn_row.append(InlineKeyboardButton(text=text, callback_data=text))
        buttons.append(btn_row)
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command(["start", "help"]))
async def send_welcome(client, message):
    if message.from_user.id in [5719372657, 6383967261]:
        keyboard = InlineKeyboardMarkup(InlineKeyboardButton(text="اضغط هنا", web_app=WebAppInfo(url="https://hanet-bot.vercel.app/webapp")))
        await message.reply_text("- Control panel By Ahmed Negm", reply_markup=keyboard)

    data_raw = r.get("bot_data")
    if not data_raw:
        return await message.reply_text("No data found in redis.")

    data = json.loads(data_raw)
    start_message = data.get("start_message", "")
    main_keyboard = data.get("main_keyboard", [])
    buttons = [KeyboardButton(btn["label"]) for btn in main_keyboard]
    keyboard = ReplyKeyboardMarkup(
        [buttons[i:i+2] for i in range(0, len(buttons), 2)],
        resize_keyboard=True
    )
    await message.reply_text(start_message, reply_markup=keyboard)

@app.on_message(filters.text)
async def handle_buttons(client, message):
    data_raw = r.get("bot_data")
    if not data_raw:
        return await message.reply_text("No data found in redis.")

    data = json.loads(data_raw)
    main_keyboard = data.get("main_keyboard", [])
    label = message.text
    item = next((x for x in main_keyboard if x["label"] == label), None)

    if not item:
        return await message.reply_text("Unknown command or button")

    action = item.get("action")
    content = item.get("content", [])
    inline_kbd_data = item.get("inline_keyboard", [])
    inline_keyboard = build_inline_keyboard(inline_kbd_data)

    if not content:
        return await message.reply_text("No content to send")

    chosen = random.choice(content)

    send_methods = {
        "send_message": client.send_message,
        "send_photo": client.send_photo,
        "send_document": client.send_document,
        "send_audio": client.send_audio,
        "send_video": client.send_video,
    }
    method = send_methods.get(action)
    if not method:
        return await message.reply_text("Unknown action")

    kwargs = dict(chosen)
    if inline_keyboard:
        kwargs["reply_markup"] = inline_keyboard

    await method(message.chat.id, **kwargs)

if __name__ == "__main__":
    asyncio.run(app.run())
