import telebot
import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from telebot import types

API_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = 7864985805 # Senin Telegram ID'n buraya güvenle tanımlandı!
bot = telebot.TeleBot(API_TOKEN)

# Veritabanı kurulumu
conn = sqlite3.connect('vpn_users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, expiry TEXT)''')
conn.commit()

# Web sunucusu (Render için)
app = Flask(__name__)
@app.route('/')
def home(): return "Bot 7/24 aktif!"
def run(): app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
Thread(target=run).start()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("👤 Profilim"), types.KeyboardButton("👑 Admin Paneli"))
    bot.send_message(message.chat.id, "VPN Paneline hoş geldin!", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "👑 Admin Paneli")
def admin_panel(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        bot.send_message(message.chat.id, "Admin Komutları:\n/ekle [ID] [Gün] \n/liste")
    else:
        bot.send_message(message.chat.id, "Yetkiniz yok!")

@bot.message_handler(commands=['ekle'])
def add_user(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        try:
            parts = message.text.split()
            uid, days = parts[1], int(parts[2])
            expiry = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (uid, expiry))
            conn.commit()
            bot.reply_to(message, f"Kullanıcı {uid} eklendi. Bitiş: {expiry}")
        except: 
            bot.reply_to(message, "Hata! Kullanım: /ekle [ID] [Gün]")

@bot.message_handler(commands=['liste'])
def list_users(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        cursor.execute("SELECT * FROM users")
        bot.reply_to(message, "Kullanıcılar:\n" + str(cursor.fetchall()))

bot.infinity_polling()
