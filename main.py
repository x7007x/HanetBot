from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    WebAppInfo,
    Update
)
import redis
import json
import os

app = FastAPI()
bot_token = os.getenv('BOT_TOKEN', '8038936358:AAF-YxpGmXnoDLHG2sljx3fx79mFye9rwzY')
bot = AsyncTeleBot(bot_token)

r = redis.Redis(
    host='redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17683,
    decode_responses=True,
    username="default",
    password="LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx",
)

def get_data(key="bot_data"):
    data = r.get(key)
    return json.loads(data) if data else {"sections": {}}

def update_data(new_data, key="bot_data"):
    r.set(key, json.dumps(new_data))

def create_main_keyboard():
    data = get_data()
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for section_name in data["sections"]:
        kb.add(KeyboardButton(text=section_name))
    return kb

def create_section_keyboard(section_name):
    data = get_data()
    buttons = data["sections"][section_name]["buttons"]
    max_row = max(btn.get("row", 0) for btn in buttons)
    rows = [[] for _ in range(max_row + 1)]
    for btn in buttons:
        rows[btn.get("row", 0)].append(btn["label"])
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for row_buttons in rows:
        kb.row(*row_buttons)
    kb.row("رجوع")
    return kb

def create_inline_keyboard(inline_buttons):
    kb = InlineKeyboardMarkup()
    for btn in inline_buttons:
        if "url" in btn:
            kb.add(InlineKeyboardButton(text=btn["label"], url=btn["url"]))
        elif "web_app_url" in btn:
            kb.add(InlineKeyboardButton(text=btn["label"], web_app=WebAppInfo(url=btn["web_app_url"])))
        else:
            kb.add(InlineKeyboardButton(text=btn["label"], callback_data=btn["callback"]))
    return kb

@bot.message_handler(commands=['start'])
async def start_handler(message):
    await bot.send_message(message.chat.id, "أهلاً! اختر القسم:", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda m: m.text in get_data()["sections"])
async def section_handler(message):
    sec = message.text
    data = get_data()
    text = data["sections"][sec]["message_text"]
    kb = create_section_keyboard(sec)
    await bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "رجوع")
async def go_back_handler(message):
    await bot.send_message(message.chat.id, "اختر القسم:", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda m: True)
async def section_buttons_handler(message):
    chat_id = message.chat.id
    text = message.text
    data = get_data()
    
    for sec_name, sec_data in data["sections"].items():
        for btn in sec_data["buttons"]:
            if btn["label"] == text:
                action = btn["action"]
                
                if action == "send_text":
                    if "inline_buttons" in btn:
                        kb = create_inline_keyboard(btn["inline_buttons"])
                        await bot.send_message(chat_id, btn["content"], reply_markup=kb)
                    else:
                        await bot.send_message(chat_id, btn["content"])
                
                elif action == "send_photo":
                    if "inline_buttons" in btn:
                        kb = create_inline_keyboard(btn["inline_buttons"])
                        await bot.send_photo(chat_id, photo=btn["content"], reply_markup=kb)
                    else:
                        await bot.send_photo(chat_id, photo=btn["content"])
                
                elif action == "send_video":
                    if "inline_buttons" in btn:
                        kb = create_inline_keyboard(btn["inline_buttons"])
                        await bot.send_video(chat_id, video=btn["content"], reply_markup=kb)
                    else:
                        await bot.send_video(chat_id, video=btn["content"])
                
                elif action == "send_document":
                    if "inline_buttons" in btn:
                        kb = create_inline_keyboard(btn["inline_buttons"])
                        await bot.send_document(chat_id, document=btn["content"], reply_markup=kb)
                    else:
                        await bot.send_document(chat_id, document=btn["content"])
                
                elif action == "edit_message":
                    await bot.send_message(chat_id, btn["content"])
                
                return

@bot.callback_query_handler(func=lambda call: True)
async def callback_handler(call):
    await bot.answer_callback_query(call.id)

@app.post("/webhook")
async def webhook(request: Request):
    if request.headers.get('content-type') == 'application/json':
        json_string = await request.body()
        update = Update.de_json(json_string.decode('utf-8'))
        await bot.process_new_updates([update])
        return JSONResponse(content={'status': 'ok'})
    raise HTTPException(status_code=400, detail="Invalid content type")

@app.get("/get_data")
def api_get_data():
    return JSONResponse(content=get_data())

@app.post("/update_data")
async def api_update_data(request: Request):
    try:
        new_data = await request.json()
        if new_data:
            update_data(new_data)
            return JSONResponse(content={"status": "success", "message": "تم تحديث البيانات بنجاح."})
        return JSONResponse(content={"status": "error", "message": "بيانات غير صالحة"}, status_code=400)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
