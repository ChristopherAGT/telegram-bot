import logging
import os
import subprocess
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🕒 Zona horaria Guatemala (pytz requerida por apscheduler)
TIMEZONE = pytz.timezone("America/Guatemala")

# Carga variables de entorno
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN_ID"))]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def es_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido. Usa /crear para crear un usuario SSH:\n"
        "`/crear usuario contraseña días conexiones`",
        parse_mode='Markdown'
    )

async def crear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_admin(update.effective_user.id):
        return await update.message.reply_text("🚫 No tienes permiso para usar este comando.")
    args = context.args
    if len(args) != 4:
        return await update.message.reply_text(
            "❗ Uso correcto: `/crear usuario contraseña días conexiones`",
            parse_mode='Markdown'
        )
    usuario, password = args[0], args[1]
    dias, conexiones = int(args[2]), int(args[3])
    fecha = (datetime.now(TIMEZONE) + timedelta(days=dias)).strftime("%Y-%m-%d")
    try:
        subprocess.run(["useradd", "-e", fecha, "-M", "-s", "/bin/false", usuario], check=True)
        subprocess.run(f"echo '{usuario}:{password}' | chpasswd", shell=True, check=True)
        with open("/etc/ssh/sshd_config", "a") as f:
            f.write(f"\nMatch User {usuario}\n  MaxSessions {conexiones}\n")
        subprocess.run("systemctl restart sshd", shell=True)
        await update.message.reply_text(
            f"✅ Usuario SSH creado:\n"
            f"👤 `{usuario}`\n🔑 `{password}`\n📅 `{fecha}`\n🔌 `{conexiones}` conexiones",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode='Markdown')

if __name__ == "__main__":
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.start()

    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .scheduler(scheduler) \
        .build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crear", crear))

    print("🤖 Bot en funcionamiento...")
    app.run_polling()
