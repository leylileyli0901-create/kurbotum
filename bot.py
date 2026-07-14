import telebot
import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from telebot import types

API_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = 123456789 # Buraya kendi Telegram ID'ni yaz!
bot = telebot.TeleBot(API_TOKEN)

# Veritabanı kurulumu
conn = sqlite3.connect('vpn_users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, username TEXT, expiry_date TEXT)''')
conn.commit()

# --- WEB SUNUCUSU (Render için) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot 7/24 ayakta!"
def run(): app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
Thread(target=run).start()

# --- MENÜ VE KOMUTLAR ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("👤 Profilim"), types.KeyboardButton("👑 Admin Paneli"))
    bot.send_message(message.chat.id, "VPN Paneline hoş geldin!", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "👑 Admin Paneli")
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Admin Paneli:\n/ekle [ID] [Gün] - Kullanıcı ekle\n/liste - Kullanıcıları gör")
    else:
        bot.send_message(message.chat.id, "Bu yetkiniz yok!")

@bot.message_handler(commands=['ekle'])
def add_user(message):
    if message.from_user.id == ADMIN_ID:7864985805
        parts = message.text.split()
        user_id, days = parts[1], int(parts[2])
        expiry = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (user_id, "Kullanıcı", expiry))
        conn.commit()
        bot.reply_to(message, f"Kullanıcı {user_id} için {days} günlük erişim tanımlandı. Bitiş: {expiry}")

@bot.message_handler(commands=['liste'])
def list_users(message):
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    bot.reply_to(message, str(users))

bot.infinity_polling()
