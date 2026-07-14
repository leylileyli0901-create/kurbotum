import telebot # Büyük 'I' harfi küçük 'i' olarak düzeltildi!
import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from telebot import types

API_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = 6573624235 # Senin Telegram ID'n
bot = telebot.TeleBot(API_TOKEN)

# Veritabanı kurulumu
conn = sqlite3.connect('vpn_v2.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, expiry TEXT, config TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS vpn_stock (id INTEGER PRIMARY KEY AUTOINCREMENT, config TEXT, used INTEGER DEFAULT 0)''')
conn.commit()

# Web sunucusu (Render için)
app = Flask(__name__)
@app.route('/')
def home(): return "Bot 7/24 aktif!"
def run(): app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
Thread(target=run).start()

@bot.message_handler(commands=['start'])
def start(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("👤 Profilim"), types.KeyboardButton("👑 Admin Paneli"))
        bot.send_message(message.chat.id, "VPN Paneline hoş geldin!", reply_markup=markup)
    except Exception as e:
        print(f"Start hatasi: {e}")

@bot.message_handler(func=lambda message: message.text == "👑 Admin Paneli")
def admin_panel(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        try:
            cursor.execute("SELECT COUNT(*) FROM vpn_stock WHERE used = 0")
            stock_count = cursor.fetchone()[0]
            
            menu_text = (
                f"👑 *Admin Paneli*\n"
                f"📦 Boştaki VPN Stok Sayısı: *{stock_count}*\n\n"
                f"🔧 *Komutlar:*\n"
                f"🔹 `/stok_ekle [VPN_Kodu]` -> Depoya çalışan kod ekler.\n"
                f"🔹 `/ekle [ID] [Gün]` -> Depodan otomatik kod seçip kullanıcıya tanımlar.\n"
                f"🔹 `/liste` -> Kayıtlı üyeleri listeler."
            )
            bot.send_message(message.chat.id, menu_text, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(message.chat.id, f"Hata oluştu: {str(e)}")
    else:
        bot.send_message(message.chat.id, "Yetkiniz yok!")

@bot.message_handler(func=lambda message: message.text == "👤 Profilim")
def user_profile(message):
    try:
        uid = str(message.from_user.id)
        cursor.execute("SELECT expiry, config FROM users WHERE id = ?", (uid,))
        result = cursor.fetchone()
        
        if result:
            expiry_str, config = result
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            
            if datetime.now().date() <= expiry_date.date():
                bot.send_message(
                    message.chat.id, 
                    f"👤 *Profil Bilgileriniz*\n\n"
                    f"📅 *Son Kullanma Tarihi:* {expiry_str}\n\n"
                    f"🔑 *VPN Bağlantı Kodunuz (Üzerine dokunarak kopyalayabilirsiniz):*\n`{config}`",
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(message.chat.id, "❌ VPN süreniz dolmuş! Lütfen yöneticiyle iletişime geçin.")
        else:
            bot.send_message(message.chat.id, "❌ Kayıtlı üyeliğiniz bulunamadı. Lütfen yöneticiyle iletişime geçin.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Profil hatasi: {e}")

@bot.message_handler(commands=['stok_ekle'])
def add_stock(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(message, "Hata! Kullanım: `/stok_ekle vless://...`", parse_mode="Markdown")
                return
            
            vpn_code = parts[1]
            cursor.execute("INSERT INTO vpn_stock (config) VALUES (?)", (vpn_code,))
            conn.commit()
            bot.reply_to(message, "✅ Çalışan VPN kodu başarıyla depoya eklendi!")
        except Exception as e:
            bot.reply_to(message, f"Hata oluştu: {str(e)}")

# Burası yarım kalmıştı, tamamen tamamlandı!
@bot.message_handler(commands=['ekle'])
def add_user(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        try:
            parts = message.text.split()
            if len(parts) < 3:
                bot.reply_to(message, "Hata! Kullanım: `/ekle [ID] [Gün]`", parse_mode="Markdown")
                return
            
            uid = parts[1]
            days = int(parts[2])
            
            cursor.execute("SELECT id, config FROM vpn_stock WHERE used = 0 LIMIT 1")
            stock_item = cursor.fetchone()
            
            if not stock_item:
                bot.reply_to(message, "⚠️ Depoda hiç çalışan VPN kodu kalmamış! Lütfen önce `/stok_ekle` ile kod yükleyin.")
                return
            
            stock_id, vpn_config = stock_item
            expiry = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (uid, expiry, vpn_config))
            cursor.execute("UPDATE vpn_stock SET used = 1 WHERE id = ?", (stock_id,))
            conn.commit()
            
            bot.reply_to(
                message, 
                f"✅ Kullanıcı {uid} başarıyla eklendi!\n"
                f"📅 Bitiş Tarihi: {expiry}\n"
                f"🔑 Depodan otomatik olarak 1 adet VPN kodu atanıp teslim edildi."
            )
        except Exception as e: 
            bot.reply_to(message, f"Hata oluştu: {str(e)}")

@bot.message_handler(commands=['liste'])
def list_users(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        try:
            cursor.execute("SELECT * FROM users")
            bot.reply_to(message, "Kullanıcılar:\n" + str(cursor.fetchall()))
        except Exception as e:
            bot.reply_to(message, f"Liste hatasi: {e}")

# Botun çökmesini engelleyen ve sürekli çalışmasını sağlayan döngü
bot.infinity_polling(timeout=10, long_polling_timeout=5)
