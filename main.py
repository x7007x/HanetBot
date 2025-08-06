from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Update
import redis
import json
import os
import random

app = FastAPI()
bot_token = "8038936358:AAF-YxpGmXnoDLHG2sljx3fx79mFye9rwzY"
bot = AsyncTeleBot(bot_token)

r = redis.Redis(
    host='redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17683,
    decode_responses=True,
    username="default",
    password="LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx",
)

DATA_KEY = "bot_core"
STATS_KEY = "bot_stats"

def get_data():
    raw = r.get(DATA_KEY)
    if not raw:
        default = {
            "start_message": "أهلاً بك في البوت! اختر زراً لبدء تجربة الرسائل العشوائية.",
            "reply_buttons": [
                {
                    "label": "رسالة نصية عشوائية",
                    "action": "send_random_text",
                    "texts": [
                        "هذه رسالة نصية عشوائية ١",
                        "رسالة نصية مختلفة ٢",
                        "نص عشوائي ٣"
                    ],
                    "inline_keyboard": []
                },
                {
                    "label": "رسالة نصية ثابتة مع رابط",
                    "action": "send_fixed_text",
                    "text": "زوروا موقعنا: https://example.com",
                    "inline_keyboard": [
                        {"label": "زيارة الموقع", "url": "https://example.com"}
                    ]
                },
                {
                    "label": "أرسل صورة عشوائية",
                    "action": "send_random_photo",
                    "photos": [
                        "https://placekitten.com/400/300",
                        "https://placebear.com/400/300"
                    ],
                    "inline_keyboard": [
                        {"label": "زيارة موقع", "url": "https://example.com"},
                        {"label": "فتح ويب اب", "web_app_url": "https://tailwindcss.com"},
                        {"label": "زر رجوع", "callback": "go_back"}
                    ]
                },
                {
                    "label": "أرسل فيديو ثابت",
                    "action": "send_video",
                    "video": "http://techslides.com/demos/sample-videos/small.mp4",
                    "inline_keyboard": []
                },
                {
                    "label": "أرسل ملف PDF",
                    "action": "send_document",
                    "document": "https://file-examples-com.github.io/uploads/2017/10/file_example_PDF_1MB.pdf",
                    "inline_keyboard": []
                },
                {
                    "label": "أرسل ملف صوت",
                    "action": "send_audio",
                    "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                    "inline_keyboard": []
                },
                {
                    "label": "أرسل ملصق ثابت",
                    "action": "send_sticker",
                    "sticker": "CAACAgIAAxkBAAEIYtdjkhc3-rD14LvNk8W1sFGXhQzRsAAC1gADVp29CtL1PC1dLEZQHwQ",
                    "inline_keyboard": []
                }
            ]
        }
        r.set(DATA_KEY, json.dumps(default))
        return default
    return json.loads(raw)

def update_data(data):
    r.set(DATA_KEY, json.dumps(data))

def increment_stat(field:str):
    r.hincrby(STATS_KEY, field, 1)

def get_stats():
    stats = r.hgetall(STATS_KEY)
    # تأكد من تحويل القيم لأعداد صحيحية أو 0
    return {k: int(v) for k, v in stats.items()} if stats else {}

def create_reply_keyboard():
    data = get_data()
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for btn in data["reply_buttons"]:
        kb.add(btn["label"])
    return kb

def create_inline_keyboard(buttons):
    kb = InlineKeyboardMarkup()
    for b in buttons:
        if "url" in b:
            kb.add(InlineKeyboardButton(text=b["label"], url=b["url"]))
        elif "web_app_url" in b:
            kb.add(InlineKeyboardButton(text=b["label"], web_app=WebAppInfo(url=b["web_app_url"])))
        else:
            kb.add(InlineKeyboardButton(text=b["label"], callback_data=b["callback"]))
    return kb

@bot.message_handler(commands=['start'])
async def start_handler(msg):
    increment_stat("start_count")
    d = get_data()
    await bot.send_message(msg.chat.id, d["start_message"], reply_markup=create_reply_keyboard())

@bot.message_handler(func=lambda m: True)
async def general_handler(msg):
    increment_stat("message_count")
    text = msg.text
    d = get_data()
    for btn in d["reply_buttons"]:
        if btn["label"] == text:
            chat_id = msg.chat.id
            action = btn.get("action")

            if action == "send_random_text":
                txt = random.choice(btn["texts"]) if "texts" in btn else "نص ثابت"
                if btn.get("inline_keyboard"):
                    kb = create_inline_keyboard(btn["inline_keyboard"])
                    await bot.send_message(chat_id, txt, reply_markup=kb)
                else:
                    await bot.send_message(chat_id, txt)
                return

            if action == "send_fixed_text":
                txt = btn.get("text", "نص ثابت")
                if btn.get("inline_keyboard"):
                    kb = create_inline_keyboard(btn["inline_keyboard"])
                    await bot.send_message(chat_id, txt, reply_markup=kb)
                else:
                    await bot.send_message(chat_id, txt)
                return

            if action == "send_random_photo":
                photo = random.choice(btn["photos"]) if "photos" in btn else None
                if photo:
                    if btn.get("inline_keyboard"):
                        kb = create_inline_keyboard(btn["inline_keyboard"])
                        await bot.send_photo(chat_id, photo=photo, reply_markup=kb)
                    else:
                        await bot.send_photo(chat_id, photo=photo)
                return

            if action == "send_video":
                vid = btn.get("video")
                if vid:
                    if btn.get("inline_keyboard"):
                        kb = create_inline_keyboard(btn["inline_keyboard"])
                        await bot.send_video(chat_id, video=vid, reply_markup=kb)
                    else:
                        await bot.send_video(chat_id, video=vid)
                return

            if action == "send_document":
                doc = btn.get("document")
                if doc:
                    if btn.get("inline_keyboard"):
                        kb = create_inline_keyboard(btn["inline_keyboard"])
                        await bot.send_document(chat_id, document=doc, reply_markup=kb)
                    else:
                        await bot.send_document(chat_id, document=doc)
                return

            if action == "send_audio":
                audio = btn.get("audio")
                if audio:
                    if btn.get("inline_keyboard"):
                        kb = create_inline_keyboard(btn["inline_keyboard"])
                        await bot.send_audio(chat_id, audio=audio, reply_markup=kb)
                    else:
                        await bot.send_audio(chat_id, audio=audio)
                return

            if action == "send_sticker":
                sticker = btn.get("sticker")
                if sticker:
                    await bot.send_sticker(chat_id, sticker=sticker)
                return

@bot.callback_query_handler(func=lambda call: True)
async def callback_handler(call):
    if call.data == "go_back":
        d = get_data()
        await bot.edit_message_text(d["start_message"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=create_reply_keyboard())
    await bot.answer_callback_query(call.id)

@app.post("/webhook")
async def webhook(request: Request):
    if request.headers.get('content-type') == 'application/json':
        data = await request.body()
        update = Update.de_json(data.decode('utf-8'))
        await bot.process_new_updates([update])
        return JSONResponse({"status": "ok"})
    raise HTTPException(400, "Invalid content-type")

@app.get("/api/data")
async def api_get_data():
    return get_data()

@app.post("/api/data")
async def api_post_data(request: Request):
    try:
        new_data = await request.json()
        update_data(new_data)
        return {"status":"success"}
    except Exception:
        raise HTTPException(400, "Invalid JSON")

@app.get("/api/stats")
async def api_get_stats():
    return get_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
