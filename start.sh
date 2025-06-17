#!/bin/bash

# ╔════════════════════════════════════════════════════════╗
# ║           🤖 CONFIGURADOR AUTOMÁTICO DE BOT           ║
# ╚════════════════════════════════════════════════════════╝

set -e

echo -e "\n🔧 Verificando dependencias básicas..."
command -v git >/dev/null || { echo "❌ Git no está instalado. Instálalo con: sudo apt install git -y"; exit 1; }
command -v python3 >/dev/null || { echo "❌ Python3 no está instalado. Instálalo con: sudo apt install python3 -y"; exit 1; }
command -v pip3 >/dev/null || { echo "❌ pip3 no está instalado. Instálalo con: sudo apt install python3-pip -y"; exit 1; }

echo -e "\n📥 Clonando el repositorio..."
git clone https://github.com/ChristopherAGT/telegram-bot.git
cd telegram-bot

echo -e "\n📦 Instalando dependencias..."
pip3 install -r requirements.txt

echo -e "\n🛠️ Solicitando datos necesarios para enlazar el bot:\n"
read -p "🔑 Ingresa tu TOKEN del bot de Telegram: " BOT_TOKEN
read -p "🧑‍💻 Ingresa tu ID de administrador de Telegram: " ADMIN_ID

echo -e "\n📝 Creando archivo .env..."
cat <<EOF > .env
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID
EOF

echo -e "\n🚀 Iniciando el bot..."
python3 bot.py
