import os
import threading
import time
from flask import Flask, request
import telebot
from google import genai
from google.genai import types as gemini_types

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_KALIT = os.environ.get("GEMINI_KALIT", "").strip()

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False) if TELEGRAM_TOKEN else None
client = genai.Client(api_key=GEMINI_KALIT) if GEMINI_KALIT else None
app = Flask(__name__)

XARAKTER = "Sening isming Alpomish. O'zbek tilida aqlli, qisqa va do'stona javob ber. Seni Usmon yaratgan."
chatlar = {}

if bot:
    @bot.message_handler(commands=['start'])
    def salomlashish(xabar):
        if not client:
            bot.reply_to(xabar, "Xato: Render Environment bo'limida GEMINI_KALIT kiritilmagan!")
            return
        chatlar[xabar.chat.id] = client.chats.create(
            model="gemini-3.1-flash-lite",
            config=gemini_types.GenerateContentConfig(system_instruction=XARAKTER)
        )
        bot.reply_to(xabar, "Assalomu alaykum! Men Alpomishman. Menga istalgan savolingizni yozing!")

    @bot.message_handler(func=lambda message: True)
    def javob_berish(xabar):
        if not client:
            bot.reply_to(xabar, "Xato: Render Environment bo'limida GEMINI_KALIT kiritilmagan!")
            return
        user_id = xabar.chat.id
        bot.send_chat_action(user_id, 'typing')
        
        if user_id not in chatlar:
            chatlar[user_id] = client.chats.create(
                model="gemini-3.1-flash-lite",
                config=gemini_types.GenerateContentConfig(system_instruction=XARAKTER)
            )
            
        try:
            javob = chatlar[user_id].send_message(xabar.text)
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
    return "Alpomish 24/7 ishlamoqda!", 200

def avtomatik_ulash():
    time.sleep(3)
    if bot:
        # Render bergan tashqi manzilni avtomatik oladi
        server_url = os.environ.get("RENDER_EXTERNAL_URL", "https://onrender.com")
        bot.remove_webhook()
        bot.set_webhook(url=f"{server_url}/webhook")
        print(f"Webhook ulandi: {server_url}/webhook")

if __name__ == "__main__":
    threading.Thread(target=avtomatik_ulash).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
