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

ADMINS = [5719372657, 6383967261]

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
                    from pyrogram.types import WebAppInfo
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
    user_id = message.from_user.id
    is_new_user = not r.sismember("Users", user_id)

    if is_new_user:
        r.sadd("Users", user_id)
        user_info = {
            "id": user_id,
            "username": message.from_user.username or "",
            "first_name": message.from_user.first_name or "",
            "last_name": message.from_user.last_name or "",
        }
        user_count = r.scard("Users")
        notif = f"""تم تسجيل مستخدم جديد 🤖

• الاسم ← {user_info['first_name']} {user_info['last_name']}
• المعرف ← @{user_info['username'] if user_info['username'] else 'لا يوجد'}
• الايدي ← {user_info['id']}

عدد المستخدمين اصبح ( {user_count} )"""
        for admin_id in ADMINS:
            try:
                await client.send_message(admin_id, notif)
            except Exception:
                pass

    if user_id in ADMINS:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("فتح لوحة التحكم", web_app=WebAppInfo(url="https://hanet-bot.vercel.app/webapp"))],
            [InlineKeyboardButton("عدد المستخدمين", callback_data="show_stats"), InlineKeyboardButton("بدء اذاعة", callback_data="start_broadcast")]
        ])
        await message.reply("- واجهة تحكم الادمن -", reply_markup=keyboard)
        # return

    data_raw = r.get("bot_data")
    if not data_raw:
        return await message.reply_text("لا توجد بيانات في الريديز")

    data = json.loads(data_raw)
    start_message = data.get("start_message", "")
    main_keyboard = data.get("main_keyboard", [])
    buttons = [KeyboardButton(btn["label"]) for btn in main_keyboard]
    keyboard = ReplyKeyboardMarkup(
        [buttons[i:i + 2] for i in range(0, len(buttons), 2)],
        resize_keyboard=True
    )
    await message.reply_text(start_message, reply_markup=keyboard)

@app.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in ADMINS:
        await callback_query.answer("غير مصرح لك باستعمال هذه الخاصية", show_alert=True)
        return

    data = callback_query.data

    if data == "show_stats":
        user_count = r.scard("Users")
        await callback_query.answer(f"عدد المستخدمين المسجلين ( {user_count} )", show_alert=True)
        return

    elif data == "start_broadcast":
        if r.get(f"Action{user_id}") == "broadcasting":
            await callback_query.answer("الاذاعة شغالة اصلا\n ارسل رسالة او الغاء للايقاف", show_alert=True)
            return

        r.set(f"Action{user_id}", "broadcasting")
        await callback_query.answer("تم تفعيل الاذاعة", show_alert=True)
        await callback_query.message.edit_text("ارسل الرسالة التي تريد اذاعتها للجميع\n\nلإلغاء الاذاعة ارسل 'الغاء'")
        return

@app.on_message(filters.text & filters.user(ADMINS))
async def broadcast_handler(client, message):
    user_id = message.from_user.id
    current_action = r.get(f"Action{user_id}")

    if message.text.strip() == "الغاء" and current_action == "broadcasting":
        r.delete(f"Action{user_id}")
        await message.reply("✅")
        return

    if current_action == "broadcasting":
        r.delete(f"Action{user_id}")
        sent_count = 0
        fail_count = 0

        for u_id in r.smembers("Users"):
            try:
                await client.send_message(u_id, message.text)
                sent_count += 1
            except Exception:
                fail_count += 1

        await message.reply(f"تم ارسال الرسالة الى ( {sent_count} ) مستخدم\nفشل الارسال لـ( {fail_count} ) مستخدم")
        return

@app.on_message(filters.text)
async def handle_buttons(client, message):
    user_id = message.from_user.id

    if user_id in ADMINS and r.get(f"Action{user_id}") == "broadcasting":
        return

    data_raw = r.get("bot_data")
    if not data_raw:
        return await message.reply_text("لا توجد بيانات في الريديز")

    data = json.loads(data_raw)
    main_keyboard = data.get("main_keyboard", [])
    label = message.text
    item = next((x for x in main_keyboard if x["label"] == label), None)

    if not item:
        return await message.reply_text("امر او زر غير معروف")

    action = item.get("action")
    content = item.get("content", [])
    inline_kbd_data = item.get("inline_keyboard", [])
    inline_keyboard = build_inline_keyboard(inline_kbd_data)

    if not content:
        return await message.reply_text("لا يوجد محتوى للارسال")

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
        return await message.reply_text("اجراء غير معروف")

    kwargs = dict(chosen)
    if inline_keyboard:
        kwargs["reply_markup"] = inline_keyboard

    await method(message.chat.id, **kwargs)

if __name__ == "__main__":
    app.run()
