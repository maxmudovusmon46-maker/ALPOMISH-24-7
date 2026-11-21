import os
import telebot
from google import genai
from google.genai import types as gemini_types

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KALIT = os.environ.get("GEMINI_KALIT")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_KALIT)

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

print("Alpomish 24/7 rejimda ishga tushdi!")
bot.infinity_polling()
