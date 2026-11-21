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

XARAKTER = """
Sening isming Alpomish. Sen O'zbekistonda yaratilgan aqlli, hazilkash va ko'p qirrali sun'iy intellektsan.
Har doim o'zbek tilida, do'stona, aniq va tushunarli javob ber. Seni Usmon yaratgan.
"""

chatlar = {}
foydalanuvchilar = set() # Botga kirgan odamlar ro'yxati

def menyu_tugmalari():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔄 Yangi suhbat", "ℹ️ Imkoniyatlarim")
    return markup

def chatni_olish(user_id):
    if user_id not in chatlar:
        chatlar[user_id] = client.chats.create(
            model="gemini-3.1-flash-lite",
            config=gemini_types.GenerateContentConfig(system_instruction=XARAKTER)
        )
    return chatlar[user_id]

if bot:
    @bot.message_handler(commands=['start'])
    def salomlashish(xabar):
        foydalanuvchilar.add(xabar.chat.id)
        chatlar.pop(xabar.chat.id, None)
        bot.send_message(
            xabar.chat.id,
            "Assalomu alaykum! Men **Alpomish**man — yangilangan super versiya!\n\n"
            "✍️ Matn yozing\n"
            "📸 Rasm yuboring (misol yechaman yoki tahlil qilaman)\n"
            "🎙️ Ovozli xabar yuboring (eshitib javob beraman)",
            parse_mode="Markdown",
            reply_markup=menyu_tugmalari()
        )

    @bot.message_handler(commands=['stat'])
    def statistika(xabar):
        bot.reply_to(xabar, f"📊 **Bot statistikasi:**\n\nFaol foydalanuvchilar soni: **{len(foydalanuvchilar)} ta**", parse_mode="Markdown")

    # 1. RASMLARNI KO'RISH VA TAHLIL QILISH
    @bot.message_handler(content_types=['photo'])
    def rasm_tahlili(xabar):
        foydalanuvchilar.add(xabar.chat.id)
        bot.send_chat_action(xabar.chat.id, 'typing')
        try:
            file_info = bot.get_file(xabar.photo[-1].file_id)
            rasm_baytlari = bot.download_file(file_info.file_path)
            izoh = xabar.caption if xabar.caption else "Bu rasmda nima tasvirlangan? O'zbek tilida batafsil tushuntirib ber."

            javob = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=[
                    gemini_types.Part.from_bytes(data=rasm_baytlari, mime_type="image/jpeg"),
                    izoh
                ],
                config=gemini_types.GenerateContentConfig(system_instruction=XARAKTER)
            )
            bot.reply_to(xabar, javob.text)
        except Exception as e:
            bot.reply_to(xabar, "Rasmni tahlil qilishda biroz xatolik bo'ldi, qayta yuborib ko'ring!")

    # 2. OVOZLI XABARLARNI ESHITISH VA JAVOB BERISH
    @bot.message_handler(content_types=['voice'])
    def ovoz_tahlili(xabar):
        foydalanuvchilar.add(xabar.chat.id)
        bot.send_chat_action(xabar.chat.id, 'typing')
        try:
            file_info = bot.get_file(xabar.voice.file_id)
            ovoz_baytlari = bot.download_file(file_info.file_path)

            javob = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=[
                    gemini_types.Part.from_bytes(data=ovoz_baytlari, mime_type="audio/ogg"),
                    "Foydalanuvchining ovozli xabarini tingla va unga o'zbek tilida aqlli javob ber."
                ],
                config=gemini_types.GenerateContentConfig(system_instruction=XARAKTER)
            )
            bot.reply_to(xabar, javob.text)
        except Exception as e:
            bot.reply_to(xabar, "Ovozli xabarni eshitishda biroz xatolik bo'ldi, qayta yuboring!")

    # 3. MATNLI XABARLAR VA TUGMALAR
    @bot.message_handler(func=lambda message: True)
    def javob_berish(xabar):
        user_id = xabar.chat.id
        foydalanuvchilar.add(user_id)
        matn = xabar.text

        if matn == "🔄 Yangi suhbat":
            chatlar.pop(user_id, None)
            bot.reply_to(xabar, "Xotira tozalandi! Yangi mavzuda suhbatlashamiz.")
            return

        if matn == "ℹ️ Imkoniyatlarim":
            bot.reply_to(
                xabar,
                "Men Usmon yaratgan **Alpomish AI** man:\n"
                "• Istalgan savolga javob beraman va suhbatni eslab qolaman\n"
                "• Yuborgan rasmlaringizni ko'rib tahlil qilaman\n"
                "• Ovozli xabarlaringizni eshitib javob qaytaraman",
                parse_mode="Markdown"
            )
            return

        bot.send_chat_action(user_id, 'typing')
        try:
            chat = chatni_olish(user_id)
            javob = chat.send_message(matn)
            bot.reply_to(xabar, javob.text)
        except Exception as e:
            bot.reply_to(xabar, "Biroz bandman, qayta yozib ko'ring!")

@app.route('/webhook', methods=['POST'])
def getMessage():
    if bot:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def home():
    return "Alpomish Super AI 24/7 ishlamoqda!", 200

def avtomatik_ulash():
    time.sleep(3)
    if bot:
        server_url = os.environ.get("RENDER_EXTERNAL_URL", "https://onrender.com")
        bot.remove_webhook()
        bot.set_webhook(url=f"{server_url}/webhook")

if __name__ == "__main__":
    threading.Thread(target=avtomatik_ulash).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
