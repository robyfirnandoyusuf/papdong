from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import mysql.connector
import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from contextlib import contextmanager

load_dotenv()

token = os.getenv('TOKEN') #ISI TOKEN BOT
# conn = mysql.connector.connect(
#     host='localhost',
#     port='3306',
#     user=os.getenv('MYSQL_USER'),
#     password=os.getenv('MYSQL_PASS'),
#     database=os.getenv('MYSQL_DB')
# )
@contextmanager
def db_cursor(commit=False, buffered=False):
    conn = mysql.connector.connect(
        host='localhost',
        port='3306',
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASS'),
        database=os.getenv('MYSQL_DB')
    )
    try:
        if (buffered == False):
            with conn.cursor() as cursor:
                yield cursor
                if commit:
                    conn.commit()
        else:
            with conn.cursor(buffered=True) as cursor:
                yield cursor
                if commit:
                    conn.commit()
    finally:
        conn.close()

# URL = input('url >')
URL = os.getenv('URL')
def validate_url(url):
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])

def remove_double_whitespace(text):
    words = text.split()
    new_text = " ".join(words)

    return new_text


def start(update, ctx):
    """Send a message when the command /start is issued."""
    print(update.message.chat)
    # log to DB
    with db_cursor(commit=True) as cur:
        # Check if the username already exists
        cur.execute("SELECT COUNT(*) FROM `users` WHERE `username` = %s;", [update.message.chat.username])
        result = cur.fetchone()
        username_exists = result[0] > 0
        print(username_exists)
        if not username_exists:
            # Insert the new record
            cur.execute("INSERT INTO `users` (`username`, `name`, `created_at`) VALUES (%s, %s, %s);", [
                update.message.chat.username,
                update.message.chat.first_name or "" + ' ' + update.message.chat.last_name or "",
                datetime.datetime.now()
            ])
        
    update.message.reply_text("""
Selamat datang di PAP Dong.\n

*Cara pakai:*\n
1. /papdong#*URL*.
*Contoh:* /papdong#https://inet.detik.com/cyberlife/d-6762090/google-buka-kursus-ai-generatif-gratis-untuk-talenta-digital-indonesia\n
2. Supaya lebih meyakinkan, Anda bisa mengkustom tag meta (supaya ketika dishare ke WA / FB maka judul dan desc berubah).
*Contoh:* /papdong#https://inet.detik.com/cyberlife/d-6762090/google-buka-kursus-ai-generatif-gratis-untuk-talenta-digital-indonesia#DETIK.COM Berbagi Hadiah#Dapatkan Saldo Dana Sebanyak Mungkin di sekitarmu dengan mengeklik 'izinkan'.\n
3. Gunakan Skill Social Engineering (Soceng) Anda sebagus mungkin.\n

Happy Spying !\n
*Follow IG: @your.online.clown*😊
""", parse_mode=ParseMode.MARKDOWN)
    
def papdong(update, ctx):
    global URL
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT * FROM `users` WHERE `username` = %s;", [update.message.chat.username])
        result = cur.fetchone()
        user_id = result[0]
        
        msg = remove_double_whitespace(str(update.message.text))
        try:
            url = msg.split('#')[1].strip()
        except IndexError:
            url = ''
            
        try:
            meta_title = msg.split('#')[2].strip()
        except IndexError:
            meta_title = ''
            
        try:
            meta_desc = msg.split('#')[3].strip()
        except IndexError:
            meta_desc = ''
            
        try:
            meta_image = msg.split('#')[4].strip()
        except IndexError:
            meta_image = ''
        
        is_valid_url = validate_url(url)

        if is_valid_url:
            cur.execute("SELECT COUNT(*) FROM `urls` WHERE `url` = %s and user_id = %s;", [url, user_id])
            result_url = cur.fetchone()
            url_exists = result_url[0] <= 0
            
            if url_exists:
                cur.execute("INSERT INTO `urls` (`user_id`, `chat_id`, `url`, meta_title, meta_desc, meta_image, `created_at`) VALUES (%s, %s, %s, %s,%s,%s,%s);", [
                    user_id,
                    update.message.chat_id,
                    url,
                    meta_title,
                    meta_desc,
                    meta_image,
                    datetime.datetime.now()
                ])
            else:
                update_query = "UPDATE `urls` SET `meta_title` = %s, `meta_desc` = %s, `meta_image` = %s WHERE `url` = %s AND user_id = %s;"
                update_values = [meta_title, meta_desc, meta_image, url, user_id]
                cur.execute(update_query, update_values)

            text = "URL Berhasil dibuat: \n`"+URL+"?article="+url+"&userId="+str(user_id)+"`"
            update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text('URL Gagal dibuat!\nPastikan commandmu benar: /papdong#*URL-nya*#meta title (opsional)#meta desc (opsional)', parse_mode=ParseMode.MARKDOWN)
        
        
def main():
    """Start the bot."""
    
    print("Bot Started!")

    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("papdong", papdong))

    # Start the Bot
    updater.start_polling()
    updater.idle()


main()