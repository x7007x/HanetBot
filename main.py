from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)
from telebot import types
from telebot import asyncio_filters
from telebot.util import async_dec
import redis.asyncio as redis
from telebot import types
from telebot.types import Update
import json
from threading import Thread
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8038936358:AAF-YxpGmXnoDLHG2sljx3fx79mFye9rwzY")

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com"),
    port=int(os.getenv("REDIS_PORT", "17683")),
    decode_responses=True,
    username=os.getenv("REDIS_USERNAME", "default"),
    password=os.getenv("REDIS_PASSWORD", "LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx"),
)

bot = AsyncTeleBot(BOT_TOKEN)
app = FastAPI()

DATA_KEY = "telegram_bot_data"

async def get_data():
    data = await r.get(DATA_KEY)
    if data:
        return json.loads(data)
    return {"sections": {}}

async def set_data(data):
    await r.set(DATA_KEY, json.dumps(data, ensure_ascii=False))

@bot.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    data = await get_data()
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for sec_name in data.get("sections", {}).keys():
        kb.add(KeyboardButton(sec_name))
    await bot.send_message(message.chat.id, "مرحبا! اختر القسم:", reply_markup=kb)

@bot.message_handler(func=lambda m: True)
async def generic_message_handler(message: types.Message):
    chat_id = message.chat.id
    text = message.text
    data = await get_data()
    sections = data.get("sections", {})

    if text == "رجوع":
        kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for sec_name in sections.keys():
            kb.add(KeyboardButton(sec_name))
        await bot.send_message(chat_id, "اختر القسم:", reply_markup=kb)
        return

    if text in sections:
        sec = sections[text]
        kb_type = sec.get("keyboard_type", "reply")
        msg_text = sec.get("message_text", "")
        buttons = sec.get("buttons", [])
        if kb_type == "reply":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            max_row = max([b.get("row", 0) for b in buttons], default=0)
            rows = [[] for _ in range(max_row + 1)]
            for btn in buttons:
                if btn["action"] != "url_button":
                    rows[btn.get("row", 0)].append(btn["label"])
            for row in rows:
                kb.row(*row)
            kb.row("رجوع")
            await bot.send_message(chat_id, msg_text, reply_markup=kb)
            return

    for secv in sections.values():
        if secv.get("keyboard_type") != "reply":
            continue
        for btn in secv.get("buttons", []):
            if btn["label"] == text:
                action = btn.get("action")
                content = btn.get("content")
                if action == "send_text":
                    await bot.send_message(chat_id, content)
                elif action == "send_photo":
                    await bot.send_photo(chat_id, photo=content)
                elif action == "send_video":
                    await bot.send_video(chat_id, video=content)
                elif action == "send_document":
                    try:
                        with open(content, "rb") as f:
                            await bot.send_document(chat_id, f)
                    except:
                        await bot.send_message(chat_id, "لم يتم العثور على الملف لإرساله.")
                elif action == "edit_message":
                    await bot.send_message(chat_id, content)
                elif action == "url_button":
                    await bot.send_message(chat_id, f"زر برابط: {btn['url']}")
                elif action == "send_text_with_inline_keyboard":
                    kb_inline = InlineKeyboardMarkup()
                    for b in btn.get("inline_buttons", []):
                        if "url" in b:
                            kb_inline.add(InlineKeyboardButton(b["label"], url=b["url"]))
                        elif "web_app_url" in b:
                            kb_inline.add(InlineKeyboardButton(b["label"], web_app=WebAppInfo(b["web_app_url"])))
                        else:
                            kb_inline.add(InlineKeyboardButton(b["label"], callback_data=b["callback"]))
                    await bot.send_message(chat_id, content, reply_markup=kb_inline)
                return

@bot.callback_query_handler(func=lambda call: True)
async def callback_query_handler(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data_call = call.data
    if data_call == "go_back":
        data = await get_data()
        kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for sec_name in data.get("sections", {}).keys():
            kb.add(KeyboardButton(sec_name))
        await bot.edit_message_text("اختر القسم:", chat_id=chat_id, message_id=message_id, reply_markup=None)
        await bot.send_message(chat_id, "اختر القسم:", reply_markup=kb)
        await bot.answer_callback_query(call.id)
        return
    data = await get_data()
    found = False
    for secv in data.get("sections", {}).values():
        buttons = secv.get("buttons", [])
        for btn in buttons:
            inline_buttons = btn.get("inline_buttons", [])
            for inline_btn in inline_buttons:
                if inline_btn.get("callback") == data_call:
                    found = True
                    py_code = inline_btn.get("py_code")
                    bot_code = inline_btn.get("bot_code")
                    if py_code:
                        local_vars = {}
                        try:
                            exec(py_code, {}, local_vars)
                            result = local_vars.get("result", "تم تنفيذ الكود بنجاح.")
                            await bot.send_message(chat_id, f"نتيجة تنفيذ الكود: {result}")
                        except Exception as e:
                            await bot.send_message(chat_id, f"خطأ في تنفيذ الكود: {e}")
                        await bot.answer_callback_query(call.id)
                        return
                    if bot_code:
                        func_name, kwargs = bot_code
                        func = getattr(bot, func_name, None)
                        if func:
                            try:
                                await func(chat_id, **kwargs)
                            except Exception as e:
                                await bot.send_message(chat_id, f"خطأ في تنفيذ إجراء البوت: {e}")
                        else:
                            await bot.send_message(chat_id, "إجراء البوت غير موجود.")
                        await bot.answer_callback_query(call.id)
                        return
    await bot.answer_callback_query(call.id)

@app.get("/")
async def alive(request: Request):
    return {"status": "alive"}

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        request_body_dict = await request.json()
        update = Update.de_json(request_body_dict)
        await bot.process_new_updates([update])
        return JSONResponse(content={"ok": True}, status_code=200)
    except Exception:
        return JSONResponse(content={"ok": False, "error": "Error processing webhook"}, status_code=500)

@app.get("/webapp", response_class=HTMLResponse)
async def webapp(request: Request):
    with open("templates/webapp.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/data")
async def get_data_route():
    data = await get_data()
    return data

@app.post("/data")
async def post_data_route(req: Request):
    body = await req.json()
    await set_data(body)
    return {"status": "success"}
