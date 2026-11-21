import os
import threading
import time
from flask import Flask, request
import telebot
from google import genai
from google.genai import types as gemini_types

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_KALIT = os.environ.get("GEMINI_KALIT", "").strip()

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
client = genai.Client(api_key=GEMINI_KALIT)
app = Flask(__name__)

XARAKTER = "Sening isming Alpomish. O'zbek tilida aqlli, qisqa va do'stona javob ber. Seni Usmon yaratgan."
chatlar = {}

@bot.message_handler(commands=['start'])
def salomlashish(xabar):
    chatlar[xabar.chat.id] = client.chats.create(
        model="gemini-3.1-flash-lite",
        config=gemini_types.GenerateContentConfig(system_instruction=XARAKTER)
    )
    bot.reply_to(xabar, "Assalomu alaykum! Men Alpomishman. Menga istalgan savolingizni yozing!")

@bot.message_handler(func=lambda message: True)
def javob_berish(xabar):
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
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def home():
    return "Alpomish 24/7 ishlamoqda!", 200

# Bot ishga tushganidan 3 soniya o'tib o'zi avtomatik Telegram'ga ulanadi
def avtomatik_ulash():
    time.sleep(3)
    bot.remove_webhook()
    bot.set_webhook(url="https://onrender.com")
    print("Webhook avtomatik ulandi!")

if __name__ == "__main__":
    threading.Thread(target=avtomatik_ulash).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
