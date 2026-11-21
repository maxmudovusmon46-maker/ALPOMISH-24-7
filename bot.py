import os
import threading
import time
from flask import Flask, request
import telebot
from telebot import types
from google import genai
from google.genai import types as gemini_types

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_KALIT = os.environ.get("GEMINI_KALIT", "").strip()

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False) if TELEGRAM_TOKEN else None
client = genai.Client(api_key=GEMINI_KALIT) if GEMINI_KALIT else None
app = Flask(__name__)

TEZKOR_MODEL = "gemini-3.1-flash-lite"

ROL_NOMLARI = {
    "universal": "🧠 Universal AI",
    "english": "🇬🇧 Ingliz tili ustozi",
    "coder": "💻 Dasturchi",
    "teacher": "📚 Maktab ustozi"
}

ROL_MATNLARI = {
    "universal": "Sening isming Alpomish. O'zbek tilida aqlli, qisqa va do'stona javob ber. Seni Usmon yaratgan.",
    "english": "Sen tajribali ingliz tili o'qituvchisisiz. Foydalanuvchiga ingliz tilini o'zbek tilida oson tushuntir, xatolarini to'g'rila.",
    "coder": "Sen kuchli Python va dasturlash mutaxassisisiz. Kodlarni aniq, tushunarli va o'zbek tilida tushuntirib ber.",
    "teacher": "Sen mehribon ustozsan. Matematika, fizika va boshqa fanlardan misollarni qadamma-qadam yechib tushuntir."
}

xotira_bazasi = {}
joriy_rol = {}
foydalanuvchilar = set()

def inline_menyu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🧠 Universal AI", callback_data="rol_universal"),
        types.InlineKeyboardButton("🇬🇧 Ingliz tili", callback_data="rol_english"),
        types.InlineKeyboardButton("💻 Dasturchi", callback_data="rol_coder"),
        types.InlineKeyboardButton("📚 Maktab ustozi", callback_data="rol_teacher")
    )
    markup.add(types.InlineKeyboardButton("🔄 Suhbatni yangilash", callback_data="yangi_suhbat"))
    return markup

def tezkor_javob_olish(user_id, yangi_matn):
    rol_kodi = joriy_rol.get(user_id, "universal")
    xarakter = ROL_MATNLARI.get(rol_kodi, ROL_MATNLARI["universal"])
    tarix = xotira_bazasi.get(user_id, [])
    
    tarix.append(gemini_types.Content(role="user", parts=[gemini_types.Part.from_text(text=yangi_matn)]))
    if len(tarix) > 6:
        tarix = tarix[-6:]

    javob = client.models.generate_content(
        model=TEZKOR_MODEL,
        contents=tarix,
        config=gemini_types.GenerateContentConfig(
            system_instruction=xarakter
        )
    )
    
    tarix.append(gemini_types.Content(role="model", parts=[gemini_types.Part.from_text(text=javob.text)]))
    xotira_bazasi[user_id] = tarix[-6:]
    return javob.text

if bot:
    @bot.message_handler(commands=['start', 'mode'])
    def salomlashish(xabar):
        foydalanuvchilar.add(xabar.chat.id)
        xotira_bazasi.pop(xabar.chat.id, None)
        matn = (
            "✨ **ALPOMISH AI (Tezkor versiya)** ✨\n\n"
            "Assalomu alaykum! Men sizning shaxsiy sun'iy intellekt yordamchingizman.\n\n"
            "📸 **Rasm** yuboring — tahlil qilaman\n"
            "🎙️ **Ovoz** yuboring — eshitib javob beraman\n"
            "✍️ **Savol** yozing — bir soniyada javob olasiz\n\n"
            "👇 *Quyidan menga kerakli rolni tanlang:*"
        )
        bot.send_message(xabar.chat.id, matn, parse_mode="Markdown", reply_markup=inline_menyu())

    @bot.message_handler(commands=['new'])
    def yangi_suhbat_cmd(xabar):
        xotira_bazasi.pop(xabar.chat.id, None)
        bot.reply_to(xabar, "🧹 **Suhbat xotirasi tozalandi!** Yangi mavzuda yozishingiz mumkin.", parse_mode="Markdown")

    @bot.message_handler(commands=['stat'])
    def statistika(xabar):
        bot.reply_to(xabar, f"📊 **Statistika:**\n👥 Foydalanuvchilar: **{len(foydalanuvchilar)} ta**", parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: True)
    def tugma_bosilganda(call):
        user_id = call.message.chat.id
        if call.data.startswith("rol_"):
            tanlangan = call.data.replace("rol_", "")
            joriy_rol[user_id] = tanlangan
            xotira_bazasi.pop(user_id, None)
            rol_nomi = ROL_NOMLARI.get(tanlangan, "🧠 Universal AI")
            bot.answer_callback_query(call.id, f"{rol_nomi} rejimi yoqildi!")
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=f"✅ Tanlangan rejim: **{rol_nomi}**\n\nEndi savolingizni yozing, rasm yoki ovoz yuboring:",
                parse_mode="Markdown",
                reply_markup=inline_menyu()
            )
        elif call.data == "yangi_suhbat":
            xotira_bazasi.pop(user_id, None)
            bot.answer_callback_query(call.id, "Xotira tozalandi!")
            bot.send_message(user_id, "🧹 **Xotira tozalandi!** Yangi savolingizni yozing:", parse_mode="Markdown")

    @bot.message_handler(content_types=['photo'])
    def rasm_tahlili(xabar):
        user_id = xabar.chat.id
        foydalanuvchilar.add(user_id)
        bot.send_chat_action(user_id, 'typing')
        rol_kodi = joriy_rol.get(user_id, "universal")
        xarakter = ROL_MATNLARI.get(rol_kodi, ROL_MATNLARI["universal"])
        try:
            file_info = bot.get_file(xabar.photo[-1].file_id)
            rasm_baytlari = bot.download_file(file_info.file_path)
            izoh = xabar.caption if xabar.caption else "Bu rasmda nima tasvirlangan? O'zbek tilida batafsil tushuntirib ber."
            javob = client.models.generate_content(
                model=TEZKOR_MODEL,
                contents=[gemini_types.Part.from_bytes(data=rasm_baytlari, mime_type="image/jpeg"), izoh],
                config=gemini_types.GenerateContentConfig(system_instruction=xarakter)
            )
            bot.reply_to(xabar, f"🖼 **Rasm tahlili:**\n\n{javob.text}", parse_mode="Markdown")
        except Exception:
            bot.reply_to(xabar, "⚠️ Rasmni tahlil qilishda xatolik bo'ldi, qayta yuboring.")

    @bot.message_handler(content_types=['voice'])
    def ovoz_tahlili(xabar):
        user_id = xabar.chat.id
        foydalanuvchilar.add(user_id)
        bot.send_chat_action(user_id, 'typing')
        rol_kodi = joriy_rol.get(user_id, "universal")
        xarakter = ROL_MATNLARI.get(rol_kodi, ROL_MATNLARI["universal"])
        try:
            file_info = bot.get_file(xabar.voice.file_id)
            ovoz_baytlari = bot.download_file(file_info.file_path)
            javob = client.models.generate_content(
                model=TEZKOR_MODEL,
                contents=[gemini_types.Part.from_bytes(data=ovoz_baytlari, mime_type="audio/ogg"), "Ovozli xabarni tingla va o'zbek tilida javob ber."],
                config=gemini_types.GenerateContentConfig(system_instruction=xarakter)
            )
            bot.reply_to(xabar, f"🎙️ **Ovozli xabarga javob:**\n\n{javob.text}", parse_mode="Markdown")
        except Exception:
            bot.reply_to(xabar, "⚠️ Ovozli xabarni eshitishda xatolik bo'ldi.")

    @bot.message_handler(func=lambda message: True)
    def javob_berish(xabar):
        user_id = xabar.chat.id
        foydalanuvchilar.add(user_id)
        bot.send_chat_action(user_id, 'typing')
        try:
            natija = tezkor_javob_olish(user_id, xabar.text)
            bot.reply_to(xabar, natija)
        except Exception as e:
            bot.reply_to(xabar, f"Xatolik: {str(e)[:120]}")

@app.route('/webhook', methods=['POST'])
def getMessage():
    if bot:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def home():
    return "Alpomish Tezkor AI 24/7 ishlamoqda!", 200

def avtomatik_ulash():
    time.sleep(3)
    if bot:
        server_url = os.environ.get("RENDER_EXTERNAL_URL", "https://onrender.com")
        bot.remove_webhook()
        bot.set_webhook(url=f"{server_url}/webhook")

if __name__ == "__main__":
    threading.Thread(target=avtomatik_ulash).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
