import logging
import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# Cargar variables de entorno
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN_ID"))]

# Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Verifica si el usuario es admin
def es_admin(user_id):
    return user_id in ADMIN_IDS

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bienvenido. Usa /crear para crear un usuario SSH.")

# Comando /crear
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
        fecha_expiracion = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")

        # Crear usuario SSH en el sistema
        subprocess.run(["useradd", "-e", fecha_expiracion, "-M", "-s", "/bin/false", usuario])
        subprocess.run(f"echo '{usuario}:{password}' | chpasswd", shell=True)
        subprocess.run(f"echo 'MaxSessions {conexiones}' >> /etc/ssh/sshd_config", shell=True)

        await update.message.reply_text(
            f"✅ Usuario SSH creado:\n\n👤 Usuario: `{usuario}`\n🔑 Contraseña: `{password}`\n📅 Expira: `{fecha_expiracion}`\n🔌 Conexiones: `{conexiones}`",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error al crear el usuario: {e}")

# Inicializar bot
if __name__ == '__main__':
    scheduler = AsyncIOScheduler(timezone=pytz.UTC)

    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .scheduler(scheduler) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crear", crear))

    print("🤖 Bot en funcionamiento...")
    app.run_polling()  # Este inicia el scheduler automáticamente
