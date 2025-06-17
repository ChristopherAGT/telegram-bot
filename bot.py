import logging
import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Carga variables de entorno
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
admin_ids_env = os.getenv("ADMIN_ID", "")
# Permite múltiples admin separados por coma, o solo uno
ADMIN_IDS = [int(i.strip()) for i in admin_ids_env.split(",") if i.strip().isdigit()]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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

        tz = pytz.timezone('America/Guatemala')
        fecha_expiracion = (datetime.now(tz) + timedelta(days=dias)).strftime("%Y-%m-%d")

        # Crear usuario SSH
        resultado_useradd = subprocess.run(
            ["useradd", "-e", fecha_expiracion, "-M", "-s", "/bin/false", usuario],
            capture_output=True, text=True
        )
        if resultado_useradd.returncode != 0:
            raise Exception(f"useradd error: {resultado_useradd.stderr.strip()}")

        resultado_chpasswd = subprocess.run(
            f"echo '{usuario}:{password}' | chpasswd", shell=True,
            capture_output=True, text=True
        )
        if resultado_chpasswd.returncode != 0:
            raise Exception(f"chpasswd error: {resultado_chpasswd.stderr.strip()}")

        # Añadir MaxSessions si no existe para evitar duplicados
        with open("/etc/ssh/sshd_config", "r") as f:
            sshd_conf = f.read()

        maxsessions_line = f"MaxSessions {conexiones}"
        if maxsessions_line not in sshd_conf:
            with open("/etc/ssh/sshd_config", "a") as f:
                f.write(f"\n{maxsessions_line}\n")

            # Recargar sshd para aplicar cambios
            subprocess.run(["systemctl", "reload", "sshd"])

        await update.message.reply_text(
            f"✅ Usuario SSH creado:\n\n"
            f"👤 Usuario: `{usuario}`\n"
            f"🔑 Contraseña: `{password}`\n"
            f"📅 Expira: `{fecha_expiracion}`\n"
            f"🔌 Conexiones: `{conexiones}`",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error al crear el usuario: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crear", crear))
    print("🤖 Bot en funcionamiento...")
    app.run_polling()
