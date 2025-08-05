from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo,
    Update,
)
import asyncio
import redis
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

bot_token = '8038936358:AAF-YxpGmXnoDLHG2sljx3fx79mFye9rwzY'
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
    if data:
        return json.loads(data)
    return {
        "sections": {
            "علوم الحي": {
                "message_text": "مرحباً في قسم علوم الحي، اختر موضوعاً:",
                "keyboard_type": "reply",
                "buttons": [
                    {"label": "مقدمة عن الخلية", "action": "send_text", "content": "الخلية هي الوحدة الأساسية للحياة.", "row": 0, "col": 0},
                    {"label": "أنواع الخلايا", "action": "send_text", "content": "هناك خلايا حيوانية ونباتية.", "row": 0, "col": 1},
                    {"label": "صورة خلية", "action": "send_photo", "content": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Eukaryotic_cell_structure_ar.svg/1200px-Eukaryotic_cell_structure_ar.svg.png", "row": 1, "col": 0},
                    {"label": "فيديو عن الخلية", "action": "send_video", "content": "https://file-examples-com.github.io/uploads/2017/04/file_example_MP4_480_1_5MG.mp4", "row": 1, "col": 1},
                    {"label": "موقع علمي", "action": "url_button", "url": "https://ar.wikipedia.org/wiki/%D8%AE%D9%84%D9%8A%D8%A9", "row": 2, "col": 0},
                    {"label": "زر تعديل", "action": "edit_message", "content": "تم التعديل من قسم علوم الحي", "row": 3, "col": 0},
                    {
                        "label": "زر إرسال نص مع أزرار متقدمة",
                        "action": "send_text_with_inline_keyboard",
                        "content": "رسالة نصية مع أزرار متقدمة:",
                        "row": 3,
                        "col": 1,
                        "inline_buttons": [
                            {"label": "زر 1", "callback": "custom_1", "tg_action": "send_message", "tg_args": {"text": "تم الضغط على زر 1"}},
                            {"label": "زر 2 إرسال صورة", "callback": "custom_2", "tg_action": "send_photo", "tg_args": {"photo": "https://i.imgur.com/ExdKOOz.png"}},
                            {"label": "زر رابط", "url": "https://telegram.org"},
                            {"label": "زر WebApp", "web_app_url": "https://google.com"},
                            {"label": "زر كود برمجي عادي", "callback": "run_python_code", "py_code": "result = 2 + 2"},
                            {"label": "زر كود bot", "callback": "run_bot_code", "bot_code": ["send_message", {"text": "الرسالة المرسلة من زر كود bot"}]}
                        ]
                    }
                ]
            }
        }
    }

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
        if btn["action"] == "url_button":
            continue
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

async def execute_py_code(py_code, chat_id):
    try:
        local_vars = {}
        exec(py_code, {}, local_vars)
        result = local_vars.get("result", "تم تنفيذ الكود بنجاح.")
        await bot.send_message(chat_id, f"نتيجة تنفيذ الكود: {result}")
    except Exception as e:
        await bot.send_message(chat_id, f"خطأ في تنفيذ الكود: {e}")

async def execute_bot_code(bot_code, chat_id):
    func_name, kwargs = bot_code
    func = getattr(bot, func_name, None)
    if func:
        try:
            await func(chat_id, **kwargs)
        except Exception as e:
            await bot.send_message(chat_id, f"حدث خطأ في تنفيذ إجراء البوت: {e}")
    else:
        await bot.send_message(chat_id, "إجراء البوت غير موجود.")

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
                    await bot.send_message(chat_id, btn["content"])
                elif action == "send_photo":
                    await bot.send_photo(chat_id, photo=btn["content"])
                elif action == "send_video":
                    await bot.send_video(chat_id, video=btn["content"])
                elif action == "send_document":
                    try:
                        with open(btn["content"], "rb") as f:
                            await bot.send_document(chat_id, f)
                    except:
                        await bot.send_message(chat_id, "لم يتم العثور على الملف لإرساله.")
                elif action == "edit_message":
                    await bot.send_message(chat_id, btn["content"])
                elif action == "url_button":
                    await bot.send_message(chat_id, f"زر برابط: {btn['url']}")
                elif action == "send_text_with_inline_keyboard":
                    kb_inline = create_inline_keyboard(btn.get("inline_buttons", []))
                    await bot.send_message(chat_id, btn["content"], reply_markup=kb_inline)
                return

@bot.callback_query_handler(func=lambda call: True)
async def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data_call = call.data
    data = get_data()

    if data_call == "go_back":
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="اختر القسم:", reply_markup=None)
        await bot.send_message(chat_id=chat_id, text="اختر القسم:", reply_markup=create_main_keyboard())
        await bot.answer_callback_query(call.id)
        return

    found = False
    for sec_data in data["sections"].values():
        for btn in sec_data["buttons"]:
            inline_buttons = btn.get("inline_buttons", [])
            for inline_btn in inline_buttons:
                if inline_btn.get("callback") == data_call:
                    found = True
                    py_code = inline_btn.get("py_code")
                    bot_code = inline_btn.get("bot_code")
                    if py_code:
                        await execute_py_code(py_code, chat_id)
                    elif bot_code:
                        await execute_bot_code(bot_code, chat_id)
                    await bot.answer_callback_query(call.id)
                    break
            if found:
                break
        if found:
            break

    if not found:
        await bot.answer_callback_query(call.id)

@app.get("/", response_class=HTMLResponse)
async def home():
    return "Bot is running..."

@app.post("/webhook")
async def webhook(request: Request):
    if request.headers.get('content-type') == 'application/json':
        json_string = await request.body()
        update = Update.de_json(json_string.decode('utf-8'))
        await bot.process_new_updates([update])
        return JSONResponse(content={'status': 'ok'})
    raise HTTPException(status_code=400, detail="Invalid content type")

@app.get("/webapp", response_class=HTMLResponse)
def webapp(request: Request):
    return templates.TemplateResponse("webapp.html", {"request": request})

@app.get("/get_data")
def api_get_data():
    data = get_data()
    return JSONResponse(content=data)

@app.post("/update_data")
async def api_update_data(request: Request):
    try:
        new_data = await request.json()
        if new_data:
            update_data(new_data)
            return JSONResponse(content={"status": "success", "message": "تم تحديث البيانات بنجاح."})
        return JSONResponse(content={"status": "error", "message": "بيانات غير صالحة"}), 400
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def set_webhook():
    webhook_url = "https://hanet-bot.vercel.app/webhook"
    await bot.set_webhook(url=webhook_url)

@app.on_event("startup")
async def on_startup():
    await set_webhook()
