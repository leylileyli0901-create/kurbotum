import telebot
import requests
import os
from flask import Flask
from threading import Thread

# Token'ı Render panelinden güvenli bir şekilde çekeceğiz
API_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# Render botu uyutmasın diye minik bir web sunucusu
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 7/24 ayakta!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Merhaba! 7/24 Render sunucusunda çalışan botuma hoş geldin. Dolar kurunu öğrenmek için /dolar yazabilirsin.")

@bot.message_handler(commands=['dolar'])
def send_usd(message):
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
        try_rate = response['rates']['TRY']
        bot.reply_to(message, f"💵 Güncel Dolar Kuru: {try_rate} TL")
    except Exception as e:
        bot.reply_to(message, "Hata: Kur bilgisi şu an alınamadı.")

keep_alive()
print("Bot çalışıyor...")
bot.infinity_polling()
