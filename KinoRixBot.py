import os
import json
import mysql.connector
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
API_KEY = "7957856186:AAFsX6n1Vs4JCOBHY4cg14ljkfNqFl34fAo"
BOT_USERNAME = "@ZeroRisk0"
UMIDJON = 8071548274
OWNERS = [UMIDJON]
ADMINS_FILE = "admin/admins.txt"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "kinorix",
    "password": "Kinorix",
    "database": "x_u_15359_kinorix",
    "charset": "utf8mb4",
}

# Initialize database connection
db = mysql.connector.connect(**DB_CONFIG)
cursor = db.cursor(dictionary=True)

# Set timezone
os.environ["TZ"] = "Asia/Tashkent"
try:
    from time import tzset
    tzset()
except ImportError:
    pass

# Utility functions
def ensure_directories():
    os.makedirs("admin", exist_ok=True)
    os.makedirs("admin/links", exist_ok=True)
    os.makedirs("admin/zayavka", exist_ok=True)

def delete_folder(path):
    if os.path.isdir(path):
        for item in os.listdir(path):
            if item not in [".", ".."]:
                delete_folder(os.path.join(path, item))
        os.rmdir(path)
    elif os.path.isfile(path):
        os.remove(path)
    return False

def get_name(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    try:
        chat = context.bot.get_chat(user_id)
        return chat.first_name or chat.title
    except:
        return "Unknown"

def get_chat_member(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        return context.bot.get_chat_member(chat_id, user_id)
    except:
        return None

def get_chat_admins(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        admins = context.bot.get_chat_administrators(chat_id)
        return True
    except:
        return False

def joinchat(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        with open("admin/kanal.txt", "r", encoding="utf-8") as f:
            channels = f.read().strip().split("\n")
    except FileNotFoundError:
        return True

    if not channels or channels == [""]:
        return True

    keyboard = []
    uns = False
    for channel_id in channels:
        if not channel_id:
            continue
        try:
            with open(f"admin/links/{channel_id}", "r", encoding="utf-8") as f:
                url = f.read().strip()
            chat = context.bot.get_chat(channel_id)
            title = chat.title
            member = get_chat_member(channel_id, user_id, context)
            status = member.status if member else "left"

            if status == "left":
                with open(f"admin/zayavka/{channel_id}", "r", encoding="utf-8") as f:
                    zayavka = f.read()
                if str(user_id) in zayavka:
                    status = "member"
                else:
                    status = "left"

            if status in ["creator", "administrator", "member"]:
                keyboard.append([InlineKeyboardButton(f"✅ {title}", url=url)])
            else:
                keyboard.append([InlineKeyboardButton(f"❌ {title}", url=url)])
                uns = True
        except:
            return True

    keyboard.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if uns:
        context.bot.send_message(
            chat_id=user_id,
            text="❌ <b>Botdan to'liq foydalanish uchun quyidagi kanallarimizga obuna bo'ling!</b>",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
        return False
    return True

# Database initialization
def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(256),
            file_id VARCHAR(256),
            film_name VARCHAR(256),
            film_date VARCHAR(256)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            kino VARCHAR(256),
            kino2 VARCHAR(256)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_id (
            uid INT AUTO_INCREMENT PRIMARY KEY,
            id VARCHAR(256),
            step VARCHAR(256),
            ban VARCHAR(256),
            lastmsg VARCHAR(256),
            sana VARCHAR(256)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS texts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            start VARCHAR(256)
        )
    """)
    cursor.execute("""
        INSERT IGNORE INTO texts (id, start) VALUES (
            1,
            '8J+RiyBBc3NhbG9tdSBhbGF5a3VtIHtuYW1lfSAgYm90aW1pemdhIHx1c2gga2VsaWJzaXouCgrinI3wn4+7IEtpbm8ga29kaW5pIHl1Ym9yaW5nLg=='
        )
    """)
    cursor.execute("INSERT IGNORE INTO settings (kino, kino2) VALUES ('0', '0')")
    db.commit()

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not joinchat(user_id, context):
        return

    cursor.execute("SELECT * FROM user_id WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    now = datetime.now().strftime("%d.%m.%Y | %H:%M")
    if user:
        cursor.execute("UPDATE user_id SET sana = %s WHERE id = %s", (now, user_id))
    else:
        cursor.execute(
            "INSERT INTO user_id (id, step, sana, ban) VALUES (%s, '0', %s, '0')",
            (user_id, now),
        )
    db.commit()

    cursor.execute("SELECT start FROM texts WHERE id = 1")
    start_text = cursor.fetchone()["start"]
    start_text = (
        base64.b64decode(start_text)
        .decode("utf-8")
        .replace("{name}", f"<a href='tg://user?id={user_id}'>{get_name(user_id, context)}</a>")
        .replace("{time}", now)
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Kodlarni qidirish", url=f"https://t.me/{context.bot_data['kino']}")]
    ])
    await update.message.reply_text(start_text, parse_mode="HTML", reply_markup=keyboard)
    cursor.execute("UPDATE user_id SET lastmsg = 'start', step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.message.delete()
    user_id = query.from_user.id
    if joinchat(user_id, context):
        cursor.execute("SELECT start FROM texts WHERE id = 1")
        start_text = cursor.fetchone()["start"]
        now = datetime.now().strftime("%d.%m.%Y | %H:%M")
        start_text = (
            base64.b64decode(start_text)
            .decode("utf-8")
            .replace("{name}", f"<a href='tg://user?id={user_id}'>{get_name(user_id, context)}</a>")
            .replace("{time}", now)
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔎 Kodlarni qidirish", url=f"https://t.me/{context.bot_data['kino']}")]
        ])
        await query.message.reply_text(start_text, parse_mode="HTML", reply_markup=keyboard)
        cursor.execute("UPDATE user_id SET lastmsg = 'start', step = '0' WHERE id = %s", (user_id,))
        db.commit()

async def dev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not joinchat(user_id, context):
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨‍💻 Bot dasturchisi", url="https://t.me/alimov_ak")],
        [InlineKeyboardButton("🔁 Boshqa botlar", url="https://t.me/alimov_ak")],
    ])
    await update.message.reply_text(
        "👨‍💻 <b>Botimiz dasturchisi: @alimov_ak</b>\n\n<i>🤖 Sizga ham shu kabi botlar kerak bo‘lsa bizga buyurtma berishingiz mumkin. Sifatli botlar tuzib beramiz.</i>\n\n<b>📊 Na’munalar:</b> @alimov_ak",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'start', step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not joinchat(user_id, context):
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Kino kodlarini qidirish", url=f"https://t.me/{context.bot_data['kino']}")]
    ])
    await update.message.reply_text(
        "<b>📊 Botimiz buyruqlari:</b>\n/start - Botni yangilash ♻️\n/rand - Tasodifiy film 🍿\n/dev - Bot dasturchisi 👨‍💻\n/help - Bot buyruqlari 🔁\n\n<b>🤖 Ushbu bot orqali kinolarni osongina qidirib topishingiz va yuklab olishingiz mumkin. Kinoni yuklash uchun kino kodini yuborishingiz kerak. Barcha kino kodlari pastdagi kanalda jamlangan.</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'start', step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([
        ["📊 Statistika"],
        ["🎬 Kino qo'shish", "🗑️ Kino o'chirish"],
        ["👨‍💼 Adminlar", "💬 Kanallar"],
        ["🔴 Blocklash", "🟢 Blockdan olish"],
        ["✍️ Post xabar", "📬 Forward xabar"],
        ["⬇️ Panelni Yopish"],
    ], resize_keyboard=True)
    await update.message.reply_text(
        "<b>👨🏻‍💻 Boshqaruv paneliga xush kelibsiz.</b>\n\n<i>Nimani o'zgartiramiz?</i>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'panel', step = '0' WHERE id = %s", (user_id,))
    db.commit()
    if os.path.exists("film.txt"):
        os.remove("film.txt")

async def close_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    await update.message.reply_text(
        "<b>🚪 Panelni tark etdingiz unga /panel yoki /admin xabarini yuborib kirishingiz mumkin.\n\nYangilash /start</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'start', step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text("<b>🎬 Kinoni yuboring:</b>", parse_mode="HTML", reply_markup=keyboard)
    cursor.execute("UPDATE user_id SET step = 'movie' WHERE id = %s", (user_id,))
    db.commit()

async def handle_movie_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "movie":
        return
    video = update.message.video
    file_id = video.file_id
    file_name = video.file_name or "unknown"
    with open("file.id", "w") as f:
        f.write(file_id)
    with open("file.name", "w") as f:
        f.write(base64.b64encode(file_name.encode()).decode())
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text("<b>🎬 Kinoni malumotini yuboring:</b>", parse_mode="HTML", reply_markup=keyboard)
    cursor.execute("UPDATE user_id SET step = 'caption' WHERE id = %s", (user_id,))
    db.commit()

async def handle_movie_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "caption":
        return
    text = update.message.text
    with open("film.caption", "w") as f:
        f.write(base64.b64encode(text.encode()).decode())
    file_id = open("file.id", "r").read()
    with open("admin/rek.txt", "r") as f:
        reklama = f.read().replace("%kino%", context.bot_data["kino"]).replace("%admin%", BOT_USERNAME)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎞️ Kanalga yuborish", callback_data="channel")]])
    await update.message.reply_video(
        video=file_id,
        caption=f"<b>{text}</b>\n\n<b>{reklama}</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.message.delete()
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await query.message.reply_text(
        "<b>📝 Post uchun video yoki rasm yuboring:</b>", parse_mode="HTML", reply_markup=keyboard
    )
    cursor.execute("UPDATE user_id SET step = 'post' WHERE id = %s", (user_id,))
    db.commit()

async def handle_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "post":
        return
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Yuborish", callback_data="sms")]])
    if update.message.video:
        file_id = update.message.video.file_id
        with open("post.video", "w") as f:
            f.write(file_id)
        with open("post.type", "w") as f:
            f.write("video")
        await update.message.reply_video(
            video=file_id, caption="<b>✅ Qabul qilindi.</b>", parse_mode="HTML", reply_markup=keyboard
        )
        cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
        db.commit()
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        with open("post.photo", "w") as f:
            f.write(file_id)
        with open("post.type", "w") as f:
            f.write("photo")
        await update.message.reply_photo(
            photo=file_id, caption="<b>✅ Qabul qilindi.</b>", parse_mode="HTML", reply_markup=keyboard
        )
        cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
        db.commit()
    else:
        await update.message.reply_text("<b>⚠️ Hatolik yuzberdi video yoki rasm yuboring!</b>", parse_mode="HTML")

async def sms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    with open("file.id", "r") as f:
        film_id = f.read()
    with open("file.name", "r") as f:
        file_name = base64.b64decode(f.read()).decode()
    with open("film.caption", "r") as f:
        film_caption = base64.b64decode(f.read()).decode()
    cursor.execute("SELECT kino FROM settings WHERE id = 1")
    code = int(cursor.fetchone()["kino"]) + 1
    cursor.execute(
        "INSERT INTO data (id, file_name, file_id, film_name, film_date) VALUES (%s, %s, %s, %s, %s)",
        (code, file_name, film_id, film_caption, datetime.now().strftime("%d.%m.%Y")),
    )
    cursor.execute("UPDATE settings SET kino = %s WHERE id = 1", (code,))
    db.commit()
    post_type = open("post.type", "r").read()
    kino_channel = context.bot_data["kino"]
    with open("admin/rek.txt", "r") as f:
        reklama = f.read().replace("%kino%", kino_channel).replace("%admin%", BOT_USERNAME)
    try:
        if post_type == "video":
            video = open("post.video", "r").read()
            message = await context.bot.send_video(
                chat_id=f"@{kino_channel}",
                video=video,
                caption=f"🎬 <b>Kino kodi:</b> <code>{code}</code>\n\n<b> ✅ <b>Aynan shu videoni kinosi to'liq xolda @{BOT_USERNAME} ga joylandi !</b>\n\n⚠️ Filmni yuklab olish uchun Botimizga kiring va kodni kiriting ! \n\n📎 Bot manzili: @{BOT_USERNAME}</b>",
                parse_mode="HTML",
            )
            message_id = message.message_id
            await query.message.delete()
            await query.message.reply_text(
                f"✅ <b>@{kino_channel} kanaliga yuborildi! \n\n🔢 Kino kodi: <code>{code}</code>\n\n👀 <a href='https://t.me/{kino_channel}/{message_id}'>Ko‘rish</a></b>",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
            )
        elif post_type == "photo":
            photo = open("post.photo", "r").read()
            message = await context.bot.send_photo(
                chat_id=f"@{kino_channel}",
                photo=photo,
                caption=f"🎬 <b>Kino kodi:</b> <code>{code}</code>\n\n<b>✅ Ushbu videoni kinosini botga joyladik, botga kino kodini yuboring va kinoni yuklab oling. \n\n📎 Bot manzili:</b> @{BOT_USERNAME},",
                parse_mode="HTML",
            )
            message_id = message.message_id
            await query.message.delete()
            await query.message.reply_text(
                f"✅ <b>@{kino_channel} kanaliga yuborildi! \n\n🎬 Kino kodi: <code>{code}</code>\n\n👀 <a href='https://t.me/{kino_channel}/{message_id}'>Ko‘rish</a></b>",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
            )
        for file in ["file.id", "file.name", "film.caption", "post.type", "post.video", "post.photo"]:
            if os.path.exists(file):
                os.remove(file)
    except Exception as e:
        await query.message.reply_text(f"<b>⚠️ Kanalga post yuborishda hatolik yuzberdi!</b>\n{e}", parse_mode="HTML")
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def delete_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text(
        "<b>🗑️ Kino o'chirish uchun menga kino kodini yuboring:</b>", parse_mode="HTML", reply_markup=keyboard
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'deleteMovie', step = 'movie-remove' WHERE id = %s", (user_id,))
    db.commit()

async def handle_delete_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "movie-remove":
        return
    text = update.message.text
    cursor.execute("SELECT * FROM data WHERE id = %s", (text,))
    row = cursor.fetchone()
    if row:
        cursor.execute("DELETE FROM data WHERE id = %s", (text,))
        cursor.execute("SELECT kino2 FROM settings WHERE id = 1")
        kino2 = int(cursor.fetchone()["kino2"]) + 1
        cursor.execute("UPDATE settings SET kino2 = %s WHERE id = 1", (kino2,))
        db.commit()
        await update.message.reply_text(f"🗑️ {text} <b>raqamli kino olib tashlandi!</b>", parse_mode="HTML")
        cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
        db.commit()
    else:
        await update.message.reply_text(f"📛 {text} <b>mavjud emas!</b>\n\n🔄 Qayta urinib ko'ring:", parse_mode="HTML")

async def set_movie_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text(
        "<b>💡 Kino kanal havolasini yuboring!\n\nNa'muna: @ULoyihalar</b>", parse_mode="HTML", reply_markup=keyboard
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'movie_chan', step = 'movie_chan' WHERE id = %s", (user_id,))
    db.commit()

async def handle_movie_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "movie_chan":
        return
    text = update.message.text
    try:
        chat = await context.bot.get_chat(text)
        nn_id = chat.id
        with open("admin/kino.txt", "w") as f:
            f.write(str(nn_id))
        context.bot_data["kino"] = text.lstrip("@")
        await update.message.reply_text(
            f"<b>✅ {text} ({str(nn_id).replace('-100','')}) ga o‘zgartirildi.</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
        )
        cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
        db.commit()
    except Exception as e:
        await update.message.reply_text(f"<b>⚠️ Xatolik: {e}</b>", parse_mode="HTML")

async def set_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text(
        "<b>📈 Reklamani yuboring!\n\nNa'muna:</b> <pre>@%kino% kanali uchun maxsus joylandi!</pre>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'ads_set', step = 'ads_set' WHERE id = %s", (user_id,))
    db.commit()

async def handle_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "ads_set":
        return
    text = update.message.text
    with open("admin/rek.txt", "w") as f:
        f.write(text)
    await update.message.reply_text(
        f"<b>✅ {text} ga o'zgartirildi.</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([
        ["🔷 Kanal ulash", "🔶 Kanal uzish"],
        ["💡 Kino kanal", "📈 Reklama"],
        ["🟩 Majburish a'zolik"],
        ["◀️ Orqaga"],
    ], resize_keyboard=True)
    await update.message.reply_text(
        f"<b>🔰 Kanallar bo'limi:\n🆔 Admin: {user_id}</b>", parse_mode="HTML", reply_markup=keyboard
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'channels' WHERE id = %s", (user_id,))
    db.commit()

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text(
        "<b>Majbur obuna ulamoqchi bo'lgan kanaldan (forward) shaklida habar olib yuboring.</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'channelsAdd', step = 'channel-add' WHERE id = %s", (user_id,))
    db.commit()

async def handle_channel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "channel-add":
        return
    forward_from_chat = update.message.forward_from_chat
    if not forward_from_chat:
        await update.message.reply_text(
            "<b>Majbur obuna ulamoqchi bo'lgan kanaldan (forward) shaklida habar olib yuboring.</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
        )
        return
    channel_id = forward_from_chat.id
    channel_name = (await context.bot.get_chat(channel_id)).title
    if not get_chat_admins(channel_id, context):
        await update.message.reply_text(
            "<b>⚠️ Bot ushbu kanalda admin emas</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
        )
        return
    with open("admin/kanal.txt", "a") as f:
        f.write(f"\n{channel_id}" if os.path.exists("admin/kanal.txt") else f"{channel_id}")
    with open("admin/channel.id", "w") as f:
        f.write(str(channel_id))
    await update.message.reply_text(
        f"<b>✅ {channel_name} - qabul qilindi, endi havola kiriting!</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = 'url' WHERE id = %s", (user_id,))
    db.commit()

async def handle_channel_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "url":
        return
    text = update.message.text
    channel_id = open("admin/channel.id", "r").read()
    with open(f"admin/links/{channel_id}", "w") as f:
        f.write(text)
    os.remove("admin/channel.id")
    await update.message.reply_text(
        "<b>✅ Qabul qilindi!</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    delete_folder("admin/links")
    delete_folder("admin/zayavka")
    if os.path.exists("admin/kanal.txt"):
        os.remove("admin/kanal.txt")
    await update.message.reply_text(
        "<b>✅ Kanallar uzildi.</b>", parse_mode="HTML", reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'deleteChan' WHERE id = %s", (user_id,))
    db.commit()

async def mandatory_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    channels = open("admin/kanal.txt", "r").read() if os.path.exists("admin/kanal.txt") else ""
    await update.message.reply_text(
        f"<b>🟩 Majburish a'zolik kanallari:</b>\n\n{channels}",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'channels' WHERE id = %s", (user_id,))
    db.commit()

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text(
        f"<b>Foydalanuvchi ID raqamini kiriting:</b>\n\n<i>M-n: {user_id}</i>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'addblock', step = 'blocklash' WHERE id = %s", (user_id,))
    db.commit()

async def handle_block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "blocklash":
        return
    text = update.message.text
    cursor.execute("UPDATE user_id SET ban = '1' WHERE id = %s", (text,))
    db.commit()
    await update.message.reply_text(
        f"<b>✅ {text} blocklandi!</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text(
        f"<b>Foydalanuvchi ID raqamini kiriting:</b>\n\n<i>M-n: {user_id}</i>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'deleteBlock', step = 'blockdanolish' WHERE id = %s", (user_id,))
    db.commit()

async def handle_unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "blockdanolish":
        return
    text = update.message.text
    cursor.execute("UPDATE user_id SET ban = '0' WHERE id = %s", (text,))
    db.commit()
    await update.message.reply_text(
        f"<b>✅ {text} blockdan olindi!</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def post_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text(
        "<b>Xabaringizni yuboring:</b>", parse_mode="HTML", reply_markup=keyboard
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'post_msg', step = 'post_send' WHERE id = %s", (user_id,))
    db.commit()

async def handle_post_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "post_send":
        return
    message_id = update.message.message_id
    sent = 0
    failed = 0
    msg = await update.message.reply_text(
        "✅ <b>Xabar yuborish boshlandi!</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("SELECT id FROM user_id")
    users = cursor.fetchall()
    for user in users:
        try:
            await context.bot.copy_message(
                chat_id=user["id"], from_chat_id=user_id, message_id=message_id
            )
            sent += 1
        except:
            failed += 1
            cursor.execute("UPDATE user_id SET sana = 'tark' WHERE id = %s", (user["id"],))
        await msg.edit_text(
            f"✅ <b>Yuborildi:</b> {sent}taga\n❌ <b>Yuborilmadi:</b> {failed}taga",
            parse_mode="HTML",
        )
    db.commit()
    await msg.delete()
    now = datetime.now().strftime("%H:%M | %d.%m.%Y")
    await update.message.reply_text(
        f"💡 <b>Xabar yuborish tugatildi.\n\n</b>✅ <b>Yuborildi:</b> {sent}taga\n❌ <b>Yuborilmadi:</b> {failed}taga\n\n<b>⏰ Soat: {now}</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await update.message.reply_text(
        "<b>Xabaringizni yuboring:</b>", parse_mode="HTML", reply_markup=keyboard
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'post_msg', step = 'forward_send' WHERE id = %s", (user_id,))
    db.commit()

async def handle_forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "forward_send":
        return
    message_id = update.message.message_id
    sent = 0
    failed = 0
    msg = await update.message.reply_text(
        "✅ <b>Xabar yuborish boshlandi!</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("SELECT id FROM user_id")
    users = cursor.fetchall()
    for user in users:
        try:
            await context.bot.forward_message(
                chat_id=user["id"], from_chat_id=user_id, message_id=message_id
            )
            sent += 1
        except:
            failed += 1
            cursor.execute("UPDATE user_id SET sana = 'tark' WHERE id = %s", (user["id"],))
        await msg.edit_text(
            f"✅ <b>Yuborildi:</b> {sent}taga\n❌ <b>Yuborilmadi:</b> {failed}taga",
            parse_mode="HTML",
        )
    db.commit()
    await msg.delete()
    now = datetime.now().strftime("%H:%M | %d.%m.%Y")
    await update.message.reply_text(
        f"💡 <b>Xabar yuborish tugatildi.\n\n</b>✅ <b>Yuborildi:</b> {sent}taga\n❌ <b>Yuborilmadi:</b> {failed}taga\n\n<b>⏰ Soat: {now}</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    cursor.execute("SELECT COUNT(*) as count FROM user_id")
    total_users = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) as count FROM user_id WHERE sana = 'tark'")
    tark_users = cursor.fetchone()["count"]
    active_users = total_users - tark_users
    cursor.execute("SELECT COUNT(*) as count FROM data")
    total_movies = cursor.fetchone()["count"]
    cursor.execute("SELECT kino, kino2 FROM settings WHERE id = 1")
    settings = cursor.fetchone()
    code = settings["kino"]
    deleted = settings["kino2"]
    ping = os.getloadavg()[2]
    await update.message.reply_text(
        f"""
💡 <b>O'rtacha yuklanish:</b> <code>{ping}</code>

• <b>Jami a’zolar:</b> {total_users} ta
• <b>Tark etgan a’zolar:</b> {tark_users} ta
• <b>Faol a’zolar:</b> {active_users} ta
—————————————
• <b>Faol kinolar:</b> {total_movies} ta
• <b>O‘chirilgan kinolar:</b> {deleted} ta
• <b>Barcha kinolar:</b> {code} ta
""",
        parse_mode="HTML",
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'stat' WHERE id = %s", (user_id,))
    db.commit()

async def admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Yangi admin qo'shish", callback_data="add-admin")],
        [
            InlineKeyboardButton("📑 Ro'yxat", callback_data="list-admin"),
            InlineKeyboardButton("🗑 O'chirish", callback_data="remove"),
        ],
    ])
    await update.message.reply_text(
        "👇🏻 <b>Quyidagilardan birini tanlang:</b>", parse_mode="HTML", reply_markup=keyboard
    )
    cursor.execute("UPDATE user_id SET lastmsg = 'admins' WHERE id = %s", (user_id,))
    db.commit()

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    admins_list = open(ADMINS_FILE, "r").read() if os.path.exists(ADMINS_FILE) else ""
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Orqaga", callback_data="admins")]])
    await query.message.edit_text(
        f"<b>👮 Adminlar ro'yxati:</b>\n\n{admins_list}", parse_mode="HTML", reply_markup=keyboard
    )

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id != UMIDJON:
        return
    await query.message.delete()
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await query.message.reply_text(
        "<b>Kerakli iD raqamni kiriting:</b>", parse_mode="HTML", reply_markup=keyboard
    )
    cursor.execute("UPDATE user_id SET step = 'add-admin' WHERE id = %s", (user_id,))
    db.commit()

async def handle_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != UMIDJON:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "add-admin":
        return
    text = update.message.text
    if not text.isdigit() or int(text) == UMIDJON:
        await update.message.reply_text("<b>Kerakli iD raqamni kiriting:</b>", parse_mode="HTML")
        return
    with open(ADMINS_FILE, "a") as f:
        f.write(f"\n{text}")
    await update.message.reply_text(
        f"✅ <b>{text} endi bot admini.</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id != UMIDJON:
        return
    await query.message.delete()
    keyboard = ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    await query.message.reply_text(
        "<b>Kerakli iD raqamni kiriting:</b>", parse_mode="HTML", reply_markup=keyboard
    )
    cursor.execute("UPDATE user_id SET step = 'remove-admin' WHERE id = %s", (user_id,))
    db.commit()

async def handle_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != UMIDJON:
        return
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if step != "remove-admin":
        return
    text = update.message.text
    if not text.isdigit() or int(text) == UMIDJON:
        await update.message.reply_text("<b>Kerakli iD raqamni kiriting:</b>", parse_mode="HTML")
        return
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r") as f:
            admins = f.read()
        admins = admins.replace(f"{text}\n", "").replace(f"\n{text}", "").replace(text, "")
        with open(ADMINS_FILE, "w") as f:
            f.write(admins)
    await update.message.reply_text(
        f"✅ <b>{text} endi botda admin emas.</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def handle_movie_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT lastmsg, ban FROM user_id WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if user["ban"] == "1":
        return
    if user["lastmsg"] != "start":
        return
    text = update.message.text
    if text.startswith("/start "):
        text = text.split(" ")[1]
    elif text == "/rand":
        cursor.execute("SELECT COUNT(*) as count FROM data")
        text = str(random.randint(1, cursor.fetchone()["count"]))
    if not joinchat(user_id, context):
        return
    if not text.isdigit():
        await update.message.reply_text("<b>📛 Faqat raqamlardan foydalaning!</b>", parse_mode="HTML")
        return
    cursor.execute("SELECT * FROM data WHERE id = %s", (text,))
    row = cursor.fetchone()
    if not row:
        await update.message.reply_text(f"📛 {text} <b>kodli kino mavjud emas!</b>", parse_mode="HTML")
        return
    fname = base64.b64decode(row["film_name"]).decode()
    file_id = row["file_id"]
    with open("admin/rek.txt", "r") as f:
        reklama = f.read().replace("%kino%", context.bot_data["kino"]).replace("%admin%", BOT_USERNAME)
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("↗️ Do'stlarga ulashish", url=f"https://t.me/share/url/?url=https://t.me/{BOT_USERNAME}?start={text}")],
        [InlineKeyboardButton("🔎 Boshqa kodlar", url=f"https://t.me/{context.bot_data['kino']}")],
    ])
    await update.message.reply_video(
        video=file_id, caption=f"<b>{fname}</b>\n\n{reklama}", parse_mode="HTML", reply_markup=keyboard
    )

async def chat_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.chat_join_request.chat.id
    user_id = update.chat_join_request.from_user.id
    if update.chat_join_request.chat.type in ["channel", "supergroup"]:
        try:
            with open(f"admin/zayavka/{chat_id}", "r") as f:
                zayavka = f.read()
        except FileNotFoundError:
            zayavka = ""
        if str(user_id) not in zayavka:
            with open(f"admin/zayavka/{chat_id}", "a") as f:
                f.write(f"\n{user_id}")

async def chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.my_chat_member.from_user.id
    status = update.my_chat_member.new_chat_member.status
    if status == "kicked":
        cursor.execute("UPDATE user_id SET sana = 'tark' WHERE id = %s", (user_id,))
        db.commit()

async def texts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("1", callback_data="text=start")]])
    await update.message.reply_text(
        "<b>📑 Matnlar:</b>\n\n1. /start - uchun matn.", parse_mode="HTML", reply_markup=keyboard
    )

async def handle_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    if not data.startswith("text="):
        return
    field = data.split("=")[1]
    cursor.execute(f"SELECT {field} FROM texts WHERE id = 1")
    text = cursor.fetchone()[field]
    text_decoded = base64.b64decode(text).decode()
    await query.message.delete()
    if field == "start":
        await query.message.reply_text("<pre>{name}</pre> - Foydalanuvchi ismi", parse_mode="HTML")
    await query.message.reply_text(f"<code>{text_decoded}</code>", parse_mode="HTML")
    await query.message.reply_text(
        "<b>Yangi matn kiriting.</b>", parse_mode="HTML", reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True)
    )
    cursor.execute("UPDATE user_id SET step = %s WHERE id = %s", (f"text={field}", user_id))
    db.commit()

async def handle_text_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT step FROM user_id WHERE id = %s", (user_id,))
    step = cursor.fetchone()["step"]
    if not step.startswith("text="):
        return
    field = step.split("=")[1]
    text = update.message.text
    encoded_text = base64.b64encode(text.encode()).decode()
    cursor.execute(f"UPDATE texts SET {field} = %s WHERE id = 1", (encoded_text,))
    db.commit()
    await update.message.reply_text(
        "<b>✅ Qabul qilindi.</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["◀️ Orqaga"]], resize_keyboard=True),
    )
    cursor.execute("UPDATE user_id SET step = '0' WHERE id = %s", (user_id,))
    db.commit()

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = OWNERS + (open(ADMINS_FILE, "r").read().strip().split("\n") if os.path.exists(ADMINS_FILE) else [])
    if user_id not in [int(x) for x in admins if x.isdigit()]:
        return
    text = update.message.text
    if text.startswith("/set "):
        value = text.split(" ")[1]
        cursor.execute("UPDATE settings SET kino = %s WHERE id = 1", (value,))
        db.commit()
    elif text.startswith("/set2 "):
        value = text.split(" ")[1]
        cursor.execute("UPDATE settings SET kino2 = %s WHERE id = 1", (value,))
        db.commit()

def main():
    ensure_directories()
    init_db()
    app = Application.builder().token(API_KEY).build()

    # Initialize bot data
    kino_id = open("admin/kino.txt", "r").read().strip() if os.path.exists("admin/kino.txt") else ""
    if kino_id:
        app.bot_data["kino"] = app.bot.get_chat(kino_id).username.lstrip("@")
    else:
        app.bot_data["kino"] = "Unknown"

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dev", dev))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler(["panel", "a", "admin", "p"], panel))
    app.add_handler(MessageHandler(filters.Regex("⬇️ Panelni Yopish"), close_panel))
    app.add_handler(MessageHandler(filters.Regex("🎬 Kino qo'shish"), add_movie))
    app.add_handler(MessageHandler(filters.VIDEO & filters.ChatType.PRIVATE, handle_movie_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_movie_caption, block=False))
    app.add_handler(CallbackQueryHandler(channel_callback, pattern="channel"))
    app.add_handler(MessageHandler(filters.Regex("🗑️ Kino o'chirish"), delete_movie))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_delete_movie, block=False))
    app.add_handler(MessageHandler(filters.Regex("💡 Kino kanal"), set_movie_channel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_movie_channel, block=False))
    app.add_handler(MessageHandler(filters.Regex("📈 Reklama"), set_ads))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_ads, block=False))
    app.add_handler(MessageHandler(filters.Regex("💬 Kanallar"), channels))
    app.add_handler(MessageHandler(filters.Regex("🔷 Kanal ulash"), add_channel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_channel_add, block=False))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_channel_url, block=False))
    app.add_handler(MessageHandler(filters.Regex("🔶 Kanal uzish"), remove_channel))
    app.add_handler(MessageHandler(filters.Regex("🟩 Majburish a'zolik"), mandatory_channels))
    app.add_handler(MessageHandler(filters.Regex("🔴 Blocklash"), block_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_block_user, block=False))
    app.add_handler(MessageHandler(filters.Regex("🟢 Blockdan olish"), unblock_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_unblock_user, block=False))
    app.add_handler(MessageHandler(filters.Regex("✍️ Post xabar"), post_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_post_message, block=False))
    app.add_handler(MessageHandler(filters.Regex("📬 Forward xabar"), forward_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_forward_message, block=False))
    app.add_handler(MessageHandler(filters.Regex("📊 Statistika"), stats))
    app.add_handler(MessageHandler(filters.Regex("👨‍💼 Adminlar"), admins))
    app.add_handler(CallbackQueryHandler(list_admins, pattern="list-admin"))
    app.add_handler(CallbackQueryHandler(add_admin, pattern="add-admin"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_add_admin, block=False))
    app.add_handler(CallbackQueryHandler(remove_admin, pattern="remove"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_remove_admin, block=False))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_movie_code))
    app.add_handler(ChatJoinRequestHandler(chat_join_request))
    app.add_handler(ChatMemberHandler(chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.Regex("📝 Matnlar"), texts))
    app.add_handler(CallbackQueryHandler(handle_text_callback, pattern=r"text="))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^(?!◀️ Orqaga$).*$"), handle_text_update, block=False))
    app.add_handler(CommandHandler(["set", "set2"], set_command))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="check"))

    app.run_polling()

if __name__ == "__main__":
    import base64
    import random
    main()