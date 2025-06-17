from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from dotenv import load_dotenv
from datetime import datetime, timedelta
import subprocess
import logging
import os
import pytz  # <--- Importante

# Cargar variables del .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN_ID"))]

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Zona horaria compatible con pytz
TIMEZONE = pytz.timezone("America/Guatemala")


def es_admin(user_id):
    return user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bienvenido. Usa /crear para crear un usuario SSH.")


async def crear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not es_admin(user_id):
        await update.message.reply_text("🚫 No tienes permiso para usar este comando.")
        return

    try:
        args = context.args
        if len(args) != 4:
            await update.message.reply_text(
                "❗ Uso correcto: `/crear usuario contraseña días conexiones`",
                parse_mode='Markdown'
            )
            return

        usuario = args[0]
        password = args[1]
        dias = int(args[2])
        conexiones = int(args[3])
        fecha_expiracion = (datetime.now(TIMEZONE) + timedelta(days=dias)).strftime("%Y-%m-%d")

        subprocess.run(["useradd", "-e", fecha_expiracion, "-M", "-s", "/bin/false", usuario], check=True)
        subprocess.run(f"echo '{usuario}:{password}' | chpasswd", shell=True, check=True)

        with open("/etc/ssh/sshd_config", "a") as ssh_config:
            ssh_config.write(f"\nMatch User {usuario}\n    MaxSessions {conexiones}\n")

        subprocess.run("systemctl restart sshd", shell=True)

        await update.message.reply_text(
            f"✅ Usuario SSH creado:\n\n👤 Usuario: `{usuario}`\n🔑 Contraseña: `{password}`\n📅 Expira: `{fecha_expiracion}`\n🔌 Conexiones: `{conexiones}`",
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error al crear el usuario:\n`{str(e)}`", parse_mode='Markdown')


if __name__ == "__main__":
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    # Scheduler con zona horaria pytz
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.start()

    app = ApplicationBuilder().token(BOT_TOKEN).scheduler(scheduler).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crear", crear))

    print("🤖 Bot en funcionamiento...")
    app.run_polling()
