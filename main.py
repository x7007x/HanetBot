# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Update
import redis
import json
import os
import random

app = FastAPI()
bot_token = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
bot = AsyncTeleBot(bot_token)

r = redis.Redis(
    host='redis-17683.c263.us-east-1-2.ec2.redns.redis-cloud.com',
    port=17683,
    decode_responses=True,
    username="default",
    password="LszSeLOwYQd6A6nGeinRuY0TrJlRR9nx",
)

def get_data():
    raw = r.get("bot_core")
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
                    "label": "أرسل ملف",
                    "action": "send_document",
                    "document": "https://file-examples-com.github.io/uploads/2017/10/file_example_PDF_1MB.pdf",
                    "inline_keyboard": []
                }
            ]
        }
        r.set("bot_core", json.dumps(default))
        return default
    return json.loads(raw)

def update_data(data):
    r.set("bot_core", json.dumps(data))

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
    d = get_data()
    await bot.send_message(msg.chat.id, d["start_message"], reply_markup=create_reply_keyboard())

@bot.message_handler(func=lambda m: True)
async def general_handler(msg):
    text = msg.text
    d = get_data()
    for btn in d["reply_buttons"]:
        if btn["label"] == text:
            chat_id = msg.chat.id
            if btn["action"] == "send_random_text":
                txt = random.choice(btn["texts"]) if "texts" in btn else "نص ثابت"
                if btn.get("inline_keyboard"):
                    kb = create_inline_keyboard(btn["inline_keyboard"])
                    await bot.send_message(chat_id, txt, reply_markup=kb)
                else:
                    await bot.send_message(chat_id, txt)
                return
            if btn["action"] == "send_random_photo":
                photo = random.choice(btn["photos"]) if "photos" in btn else None
                if photo:
                    if btn.get("inline_keyboard"):
                        kb = create_inline_keyboard(btn["inline_keyboard"])
                        await bot.send_photo(chat_id, photo=photo, reply_markup=kb)
                    else:
                        await bot.send_photo(chat_id, photo=photo)
                return
            if btn["action"] == "send_video":
                vid = btn.get("video")
                if vid:
                    if btn.get("inline_keyboard"):
                        kb = create_inline_keyboard(btn["inline_keyboard"])
                        await bot.send_video(chat_id, video=vid, reply_markup=kb)
                    else:
                        await bot.send_video(chat_id, video=vid)
                return
            if btn["action"] == "send_document":
                doc = btn.get("document")
                if doc:
                    if btn.get("inline_keyboard"):
                        kb = create_inline_keyboard(btn["inline_keyboard"])
                        await bot.send_document(chat_id, document=doc, reply_markup=kb)
                    else:
                        await bot.send_document(chat_id, document=doc)
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

@app.get("/", response_class=HTMLResponse)
async def control_panel():
    return html

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

html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>لوحة تحكم البوت</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-4 font-sans">
  <h1 class="text-2xl font-bold mb-4">لوحة تحكم البوت</h1>
  <div class="mb-4">
    <label class="block font-semibold mb-1" for="startMessage">نص رسالة البدء:</label>
    <textarea id="startMessage" rows="3" class="w-full p-2 border rounded"></textarea>
  </div>
  <div class="mb-4">
    <h2 class="font-semibold mb-2">أزرار لوحة الرد:</h2>
    <div id="buttonsContainer" class="space-y-2 max-h-96 overflow-y-auto border p-2 rounded bg-white"></div>
    <button id="addBtn" class="mt-2 px-4 py-2 bg-green-500 rounded text-white">+ إضافة زر جديد</button>
  </div>
  <button id="saveBtn" class="px-6 py-2 bg-blue-600 text-white rounded">حفظ التغييرات</button>
  <div id="msg" class="mt-4 text-green-600 font-semibold"></div>
<script>
let data = null;
async function fetchData(){
  let res = await fetch('/api/data');
  data = await res.json();
  document.getElementById('startMessage').value = data.start_message;
  renderButtons();
}
function renderButtons(){
  const container = document.getElementById('buttonsContainer');
  container.innerHTML = '';
  data.reply_buttons.forEach((btn,i)=>{
    const div = document.createElement('div');
    div.className = 'border rounded p-2 bg-gray-50';
    div.innerHTML = `
      <input type="text" class="border p-1 w-1/3 ml-2 rounded" placeholder="النص الظاهر على الزر" value="${btn.label}"/>
      <select class="actionSel border p-1 rounded ml-2">
        <option value="send_random_text"${btn.action==='send_random_text'?' selected':''}>ارسال نص عشوائي</option>
        <option value="send_random_photo"${btn.action==='send_random_photo'?' selected':''}>ارسال صورة عشوائية</option>
        <option value="send_video"${btn.action==='send_video'?' selected':''}>ارسال فيديو</option>
        <option value="send_document"${btn.action==='send_document'?' selected':''}>ارسال ملف</option>
      </select>
      <button class="delBtn bg-red-500 text-white px-2 rounded ml-2">حذف</button>
      <div class="mt-2 details"></div>
    `;
    container.appendChild(div);

    const labelInput = div.querySelector('input[type=text]');
    const actionSel = div.querySelector('select.actionSel');
    const delBtn = div.querySelector('button.delBtn');
    const details = div.querySelector('.details');

    function renderDetails(){
      let html = '';
      if(actionSel.value==='send_random_text'){
        let texts = btn.texts || [];
        html += '<label>النصوص العشوائية (افصل بين كل نص بسطر جديد):</label><br>';
        html += `<textarea class="textsArea border p-1 rounded w-full" rows="4">${texts.join("\\n")}</textarea>`;
        html += '<br><label>زرار لوحة مفاتيح إن وجدت (اختياري): JSON مثال: [{"label":"زر", "url":"http://..."}, {"label":"زر2","callback":"data"}]</label><br>'
        let ikb = btn.inline_keyboard ? JSON.stringify(btn.inline_keyboard,null,2) : '[]';
        html += `<textarea class="inlineKbArea border p-1 rounded w-full" rows="3">${ikb}</textarea>`;
      } else if(actionSel.value==='send_random_photo'){
        let photos = btn.photos || [];
        html += '<label>روابط الصور (افصل بين كل رابط بسطر جديد):</label><br>';
        html += `<textarea class="photosArea border p-1 rounded w-full" rows="3">${photos.join("\\n")}</textarea>`;
        html += '<br><label>زرار لوحة مفاتيح إن وجدت (اختياري): JSON مثال: [{"label":"زر", "url":"http://..."}, {"label":"زر2","callback":"data"}]</label><br>'
        let ikb = btn.inline_keyboard ? JSON.stringify(btn.inline_keyboard,null,2) : '[]';
        html += `<textarea class="inlineKbArea border p-1 rounded w-full" rows="3">${ikb}</textarea>`;
      } else if(actionSel.value==='send_video'){
        let vid = btn.video || '';
        html += '<label>رابط الفيديو:</label><br>';
        html += `<input type="text" class="videoInput border p-1 rounded w-full" value="${vid}"/>`;
        html += '<br><label>زرار لوحة مفاتيح إن وجدت (اختياري): JSON مثال: [{"label":"زر", "url":"http://..."}, {"label":"زر2","callback":"data"}]</label><br>'
        let ikb = btn.inline_keyboard ? JSON.stringify(btn.inline_keyboard,null,2) : '[]';
        html += `<textarea class="inlineKbArea border p-1 rounded w-full" rows="3">${ikb}</textarea>`;
      } else if(actionSel.value==='send_document'){
        let doc = btn.document || '';
        html += '<label>رابط الملف:</label><br>';
        html += `<input type="text" class="docInput border p-1 rounded w-full" value="${doc}"/>`;
        html += '<br><label>زرار لوحة مفاتيح إن وجدت (اختياري): JSON مثال: [{"label":"زر", "url":"http://..."}, {"label":"زر2","callback":"data"}]</label><br>'
        let ikb = btn.inline_keyboard ? JSON.stringify(btn.inline_keyboard,null,2) : '[]';
        html += `<textarea class="inlineKbArea border p-1 rounded w-full" rows="3">${ikb}</textarea>`;
      }
      details.innerHTML = html;

      if(actionSel.value==='send_random_text'){
        details.querySelector('.textsArea').addEventListener('input', e => {
          btn.texts = e.target.value.split('\\n').filter(t=>t.trim());
        });
      }
      if(actionSel.value==='send_random_photo'){
        details.querySelector('.photosArea').addEventListener('input', e => {
          btn.photos = e.target.value.split('\\n').filter(t=>t.trim());
        });
      }
      if(actionSel.value==='send_video'){
        details.querySelector('.videoInput').addEventListener('input', e => {
          btn.video = e.target.value.trim();
        });
      }
      if(actionSel.value==='send_document'){
        details.querySelector('.docInput').addEventListener('input', e => {
          btn.document = e.target.value.trim();
        });
      }
      const inlineKbArea = details.querySelector('.inlineKbArea');
      if(inlineKbArea){
        inlineKbArea.addEventListener('input', e => {
          try {
            const val = JSON.parse(e.target.value);
            if(Array.isArray(val)) btn.inline_keyboard = val;
          }catch{}
        });
      }
    }
    labelInput.addEventListener('input', e => {
      btn.label = e.target.value;
    });
    actionSel.addEventListener('change', e => {
      btn.action = e.target.value;
      renderDetails();
    });
    delBtn.addEventListener('click', () => {
      data.reply_buttons.splice(i,1);
      renderButtons();
    });
    renderDetails();
  });
}
document.getElementById('addBtn').addEventListener('click', ()=>{
  data.reply_buttons.push({
    label: 'زر جديد',
    action: 'send_random_text',
    texts: ["مثال نص 1", "مثال نص 2"],
    inline_keyboard: []
  });
  renderButtons();
});
document.getElementById('saveBtn').addEventListener('click', async () => {
  data.start_message = document.getElementById('startMessage').value;
  try {
    let res = await fetch('/api/data', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(data)
    });
    if(res.ok){
      document.getElementById('msg').innerText = 'تم حفظ التغييرات بنجاح';
    } else {
      document.getElementById('msg').innerText = 'حدث خطأ أثناء الحفظ';
    }
  } catch {
    document.getElementById('msg').innerText = 'حدث خطأ أثناء الحفظ';
  }
});
fetchData();
</script>
</body>
</html>
