🤖 Script Hosting Telegram Bot

A powerful Telegram bot built with Python that allows users to upload, manage, start, stop, and monitor Python and JavaScript scripts.

✨ Features

- 📤 Upload ".py", ".js", and ".zip" files
- 🤖 Run Python scripts
- 🟨 Run JavaScript/Node.js scripts
- ▶️ Start uploaded scripts
- 🛑 Stop running scripts
- 🗑️ Delete scripts
- 📄 View script logs
- 📦 Install Python modules
- 📊 User statistics
- ⚡ Bot speed checker
- 👑 Admin panel
- 👥 User management
- 📢 Broadcast messages
- ✉️ Send messages to users
- 🔒 Lock and unlock the bot
- 🧹 Clean log files
- 📦 Automatic backup system
- 🗂️ ZIP file extraction
- 🔐 Force join system
- 🌐 Flask health-check endpoint for hosting platforms

---

🛠️ Requirements

- Python 3.10+
- Node.js (required for running ".js" scripts)

Install the Python dependencies:

pip install -r requirements.txt

"requirements.txt"

pyTelegramBotAPI
Flask
psutil

---

🔐 Configuration

For security, use environment variables for your Telegram bot token.

Set the following environment variable:

TOKEN=YOUR_TELEGRAM_BOT_TOKEN

Then use this in "app.py":

TOKEN = os.environ.get("TOKEN")

Configure your admin settings:

OWNER_ID = YOUR_TELEGRAM_ID
ADMIN_IDS = {YOUR_TELEGRAM_ID}
ADMIN_CHANNEL_ID = YOUR_ADMIN_CHANNEL_ID

---

🚀 Deploy on Render

1. Upload to GitHub

Create a new GitHub repository and upload:

app.py
requirements.txt
README.md

2. Create a Render Web Service

Go to Render and create a new Web Service.

Connect your GitHub repository and use these settings:

Build Command

pip install -r requirements.txt

Start Command

python app.py

Environment Variables

Add:

Key| Value
"TOKEN"| Your Telegram Bot Token

Then deploy the service.

---

🌐 Health Check

The bot includes a Flask web server.

Visit your Render URL to check whether the bot is online:

https://your-service-name.onrender.com/

Expected response:

✅ Bot is Running!

---

📁 Supported Files

File Type| Description
".py"| Python scripts
".js"| JavaScript / Node.js scripts
".zip"| ZIP archives

Maximum upload size:

20 MB

---

📋 Bot Commands & Features

📤 Upload File

Users can upload supported script files directly to the bot.

📂 My Scripts

Users can:

- View uploaded scripts
- Start scripts
- Stop scripts
- Delete scripts
- View logs

📦 Install Module

Users can request Python packages to be installed.

Examples:

requests
pillow
numpy

📊 Statistics

Displays:

- Total scripts
- Running scripts
- Stopped scripts
- Total files
- Python version
- Platform information

---

👑 Admin Features

Admins can:

- 📊 View bot statistics
- 👥 View all users
- 📁 Manage user files
- ▶️ View running scripts
- 📢 Broadcast messages
- ✉️ Message users directly
- 🔒 Lock the bot
- 🔓 Unlock the bot
- 🗑️ Clean logs

---

⚠️ Important Hosting Notes

- Render services may restart or redeploy.
- Local files may not persist without persistent storage.
- Do not store your Telegram bot token directly in a public GitHub repository.
- Regenerate your token immediately if it has been exposed publicly.
- JavaScript script execution requires Node.js to be available in the hosting environment.

---

📜 License

This project is for educational and personal use.

Use it responsibly and secure your server properly before allowing untrusted users to upload and execute code.

---

❤️ Support

If you found this project useful, consider giving the repository a ⭐!

Made with ❤️ using Python & Telegram Bot API
