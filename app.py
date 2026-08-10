# -*- coding: utf-8 -*-
import telebot
from telebot import types
import subprocess
import os
import zipfile
import tempfile
import shutil
import time
import psutil
import json
import threading
import re
import uuid 
import sys
import atexit
import signal
from datetime import datetime
from flask import Flask
from threading import Thread    

# ==================== CONFIG ====================
TOKEN = os.environ.get("TOKEN")
OWNER_ID = 8066849679
ADMIN_IDS = {8066849679}
ADMIN_CHANNEL_ID = -1003729608203  # your private admin channel id

FORCE_JOIN = {
    'channel': {'id': '@ETOFFICIALS', 'name': ' 📟 Main Channel'},
    'group': {'id': '@EVILXGC', 'name': ' ⭐ Main Group'}
}

# ==================== SETUP ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'user_scripts')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def cleanup_orphaned_processes():
    for root, dirs, files in os.walk(UPLOAD_DIR):
        for file in files:
            if file.endswith('.pid'):
                pid_path = os.path.join(root, file)
                try:
                    with open(pid_path, 'r') as f:
                        pid = int(f.read().strip())
                    try:
                        parent = psutil.Process(pid)
                        children = parent.children(recursive=True)
                        for child in children:
                            child.kill()
                        parent.kill()
                    except psutil.NoSuchProcess:
                        pass
                except Exception:
                    pass
                finally:
                    if os.path.exists(pid_path):
                        try: os.remove(pid_path)
                        except: pass

cleanup_orphaned_processes()

running_scripts = {}
bot_locked = False
user_temp_data = {}
pending_files = {}  # store file info temporarily
reject_waiting = {}

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# ==================== FLASK KEEP ALIVE ====================
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "✅ Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ==================== SAFE FUNCTIONS ====================
def safe_send(chat_id, text, reply_markup=None, parse_mode=None):
    try:
        return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        print(f"Send error: {e}")
        return None

# FIX: Added parse_mode argument which was missing but called everywhere
def safe_edit(chat_id, msg_id, text, reply_markup=None, parse_mode=None):
    try:
        return bot.edit_message_text(text, chat_id, msg_id, reply_markup=reply_markup, parse_mode=parse_mode)
    except:
        return None

def safe_callback(call_id, text=None, show_alert=False):
    try:
        if text:
            bot.answer_callback_query(call_id, text, show_alert=show_alert)
        else:
            bot.answer_callback_query(call_id)
    except:
        pass


MENU_COMMANDS = [
    '📤 UPLOAD FILE', '📂 MY SCRIPTS', '📦 INSTALL MODULE', '📊 STATS', 
    '⚡ BOT SPEED', '❓ HELP', '⚙️ SETTINGS & ADMIN', '👑 ADMIN PANEL'
]


def route_menu_command(message):
    text = message.text.strip() if message.text else ""
    if text == '📤 UPLOAD FILE': upload_prompt(message)
    elif text == '📂 MY SCRIPTS': list_scripts(message)
    elif text == '📦 INSTALL MODULE': install_module_prompt(message)
    elif text == '📊 STATS': show_stats(message)
    elif text == '⚡ BOT SPEED': bot_speed(message)
    elif text == '❓ HELP': show_help(message)
    elif text in ['⚙️ SETTINGS & ADMIN', '👑 ADMIN PANEL']: admin_panel(message)
    elif text.startswith('/start'): send_welcome(message)

def is_cancel_command(message):
    if not message.text:
        return False
    text = message.text.strip()
    if text.lower() == '/cancel' or text in MENU_COMMANDS or text.startswith('/start'):
        return True
    return False

# ==================== HELPER FUNCTIONS ====================
def get_user_dir(user_id):
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def get_user_scripts(user_id):
    user_dir = get_user_dir(user_id)
    scripts = []
    for f in os.listdir(user_dir):
        if f.endswith(('.py', '.js')):
            scripts.append(f)
    return scripts

def get_user_files_count(user_id):
    user_dir = get_user_dir(user_id)
    count = 0
    for root, dir, files in os.walk(user_dir):
        count += len([f for f in files if not f.endswith('.log')])
    return count

def get_all_users():
    users = []
    for d in os.listdir(UPLOAD_DIR):
        if os.path.isdir(os.path.join(UPLOAD_DIR, d)) and d.isdigit():
            users.append(int(d))
    return users

def get_total_files_system():
    count = 0
    for root, dir, files in os.walk(UPLOAD_DIR):
        count += len([f for f in files if not f.endswith('.log')])
    return count

def is_script_running(user_id, script_name):
    key = f"{user_id}_{script_name}"
    if key in running_scripts:
        proc = running_scripts[key].get('process')
        if proc and proc.poll() is None:
            return True
        else:
            del running_scripts[key]
    return False

def stop_script(user_id, script_name):
    key = f"{user_id}_{script_name}"
    user_dir = get_user_dir(user_id)
    pid_path = os.path.join(user_dir, f"{script_name}.pid")
    
    if key in running_scripts:
        proc = running_scripts[key].get('process')
        if proc:
            try:
                parent = psutil.Process(proc.pid)
                children = parent.children(recursive=True)
                for child in children:
                    child.terminate()
                parent.terminate()
                time.sleep(1)
                for child in children:
                    if child.is_running():
                        child.kill()
                if parent.is_running():
                    parent.kill()
            except:
                pass
        del running_scripts[key]
        if os.path.exists(pid_path):
            try: os.remove(pid_path)
            except: pass
        return True
    return False

def delete_user_script(user_id, script_name):
    user_dir = get_user_dir(user_id)
    script_path = os.path.join(user_dir, script_name)
    log_path = script_path.replace('.py', '.log').replace('.js', '.log')
    
    stop_script(user_id, script_name)
    
    deleted = []
    if os.path.exists(script_path):
        os.remove(script_path)
        deleted.append(script_name)
    if os.path.exists(log_path):
        os.remove(log_path)
    return deleted

def validate_script(script_path):
    if script_path.endswith('.py'):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, script_path, 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
    return True, None

def install_package(module_name, chat_id):
    try:
        msg = safe_send(chat_id, f"📦 Installing `{module_name}`...")
        if not msg: return False
        
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', module_name], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            safe_edit(chat_id, msg.message_id, f"✅ Successfully installed: `{module_name}`")
            return True
        else:
            safe_edit(chat_id, msg.message_id, f"❌ Failed to install: `{module_name}`")
            return False
    except Exception as e:
        safe_send(chat_id, f"❌ Error: {str(e)}")
        return False

def is_user_joined(user_id):
    try:
        channel_joined = False
        try:
            chat_member = bot.get_chat_member(FORCE_JOIN['channel']['id'], user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                channel_joined = True
        except:
            channel_joined = False
        
        group_joined = False
        try:
            chat_member = bot.get_chat_member(FORCE_JOIN['group']['id'], user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                group_joined = True
        except:
            group_joined = False
        
        return channel_joined and group_joined
    except:
        return False

# ==================== SUB-SERVICES ====================
def backup_task():
    while True:
        time.sleep(2 * 3600)  # 2 hours
        try:
            zip_filename = f"server_backup_{int(time.time())}.zip"
            zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(UPLOAD_DIR):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, UPLOAD_DIR)
                        zipf.write(file_path, arcname)
            
            with open(zip_path, 'rb') as f:
                bot.send_document(OWNER_ID, f, caption="📦 Automated 2-Hour Server Scripts Backup")
                
            os.remove(zip_path)
        except Exception as e:
            print(f"Backup task failed: {e}")

# ==================== SCRIPT RUNNERS ====================
import html


def kill_previous_instances(user_dir, script_name):
    # Kill any processes running from this script path
    script_path = os.path.join(user_dir, script_name)
    for p in psutil.process_iter(['pid', 'cmdline', 'cwd']):
        try:
            cmd = p.info.get('cmdline')
            cwd = p.info.get('cwd')
            if cmd and cwd:
                # If script path is in cmd or cwd matches user_dir
                if any(script_name in c for c in cmd) and cwd == user_dir:
                    try:
                        parent = psutil.Process(p.pid)
                        for child in parent.children(recursive=True):
                            child.kill()
                        parent.kill()
                    except:
                        pass
        except:
            pass

def run_python_script(script_path, user_id, script_name, chat_id):
    key = f"{user_id}_{script_name}"
    user_dir = get_user_dir(user_id)
    log_path = script_path.replace('.py', '.log')
    pid_path = f"{script_path}.pid"
    
    try:
        kill_previous_instances(user_dir, script_name)
        log_file = open(log_path, 'w', encoding='utf-8')
        process = subprocess.Popen(
            [sys.executable, "-u", script_path], cwd=user_dir, stdout=log_file, stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        with open(pid_path, 'w') as f:
            f.write(str(process.pid))
            
        running_scripts[key] = {'process': process, 'log_path': log_path, 'start_time': datetime.now(), 'log_file': log_file}
        safe_send(chat_id, f"✅ Script `{script_name}` started successfully!")
        
        def monitor():
            process.wait()
            log_file.close()
            if os.path.exists(pid_path):
                try: os.remove(pid_path)
                except: pass
            if key in running_scripts:
                del running_scripts[key]
                exit_code = process.returncode
                status = "successfully" if exit_code == 0 else f"with error (Code: {exit_code})"
                msg = f"🛑 Script `{script_name}` stopped {status}."
                
                if exit_code != 0:
                    try:
                        with open(log_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if lines:
                                last_lines = "".join(lines[-10:])
                                msg += f"\n\n<b>Last log output:</b>\n<pre>{html.escape(last_lines)}</pre>"
                    except:
                        pass
                
                safe_send(chat_id, msg, parse_mode="HTML")
        threading.Thread(target=monitor, daemon=True).start()
    except Exception as e:
        safe_send(chat_id, f"❌ Error: {str(e)}")

def run_js_script(script_path, user_id, script_name, chat_id):
    key = f"{user_id}_{script_name}"
    user_dir = get_user_dir(user_id)
    log_path = script_path.replace('.js', '.log')
    pid_path = f"{script_path}.pid"
    
    try:
        kill_previous_instances(user_dir, script_name)
        kill_previous_instances(user_dir, script_name)
        log_file = open(log_path, 'w', encoding='utf-8')
        process = subprocess.Popen(
            ['node', script_path], cwd=user_dir, stdout=log_file, stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        with open(pid_path, 'w') as f:
            f.write(str(process.pid))
            
        running_scripts[key] = {'process': process, 'log_path': log_path, 'start_time': datetime.now(), 'log_file': log_file}
        safe_send(chat_id, f"✅ JavaScript Script `{script_name}` started!")
        
        def monitor():
            process.wait()
            log_file.close()
            if os.path.exists(pid_path):
                try: os.remove(pid_path)
                except: pass
            if key in running_scripts:
                del running_scripts[key]
                exit_code = process.returncode
                status = "successfully" if exit_code == 0 else f"with error (Code: {exit_code})"
                msg = f"🛑 Script `{script_name}` stopped {status}."
                
                if exit_code != 0:
                    try:
                        with open(log_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if lines:
                                last_lines = "".join(lines[-10:])
                                msg += f"\n\n<b>Last log output:</b>\n<pre>{html.escape(last_lines)}</pre>"
                    except:
                        pass
                
                safe_send(chat_id, msg, parse_mode="HTML")
        threading.Thread(target=monitor, daemon=True).start()
    except FileNotFoundError:
        safe_send(chat_id, "❌ Node.js is not installed!")
    except Exception as e:
        safe_send(chat_id, f"❌ Error: {str(e)}")

# ==================== BEAUTIFUL MENUS ====================
def main_menu(user_id):
    """Beautiful main menu with emojis and design"""
    is_admin = user_id in ADMIN_IDS or user_id == OWNER_ID
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Row 1
    markup.add(
        types.KeyboardButton("📤 UPLOAD FILE"),
        types.KeyboardButton("📂 MY SCRIPTS")
    )
    
    # Row 2
    markup.add(
        types.KeyboardButton("📦 INSTALL MODULE"),
        types.KeyboardButton("📊 STATS")
    )
    
    # Row 3
    markup.add(
        types.KeyboardButton("⚡ BOT SPEED"),
        types.KeyboardButton("❓ HELP")
    )
    
    # Admin buttons
    if is_admin:
        markup.add(
            types.KeyboardButton("⚙️ SETTINGS & ADMIN")
        )
    
    return markup

def force_join_menu():
    """Force join menu design"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"📢 JOIN {FORCE_JOIN['channel']['name']}", url=f"https://t.me/{FORCE_JOIN['channel']['id'].replace('@', '')}"),
        types.InlineKeyboardButton(f"👥 JOIN {FORCE_JOIN['group']['name']}", url=f"https://t.me/{FORCE_JOIN['group']['id'].replace('@', '')}"),
        types.InlineKeyboardButton("✅ VERIFY MEMBERSHIP", callback_data="check_join")
    )
    return markup

def script_control_menu(user_id, script_name, is_running):
    """Script control buttons design"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if is_running:
        markup.add(
            types.InlineKeyboardButton("🛑 STOP", callback_data=f"stop_{user_id}_{script_name}"),
            types.InlineKeyboardButton("📄 VIEW LOGS", callback_data=f"logs_{user_id}_{script_name}")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("▶️ START", callback_data=f"start_{user_id}_{script_name}"),
            types.InlineKeyboardButton("🗑️ DELETE", callback_data=f"delete_{user_id}_{script_name}"),
            types.InlineKeyboardButton("📄 VIEW LOGS", callback_data=f"logs_{user_id}_{script_name}")
        )
    
    markup.add(types.InlineKeyboardButton("🔙 BACK TO SCRIPTS", callback_data="back_to_scripts"))
    return markup

def admin_panel_menu():
    """Admin panel design"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 BOT STATS", callback_data="admin_stats"),
        types.InlineKeyboardButton("👥 ALL USERS", callback_data="all_users"),
        types.InlineKeyboardButton("📁 MANAGE FILES", callback_data="manage_files"),
        types.InlineKeyboardButton("▶️ RUNNING SCRIPTS", callback_data="admin_running_scripts"),
        types.InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("✉️ MSG USER", callback_data="admin_msg_user"),
        types.InlineKeyboardButton("🔒 LOCK BOT", callback_data="lock_bot"),
        types.InlineKeyboardButton("🔓 UNLOCK BOT", callback_data="unlock_bot"),
        types.InlineKeyboardButton("🗑️ CLEAN LOGS", callback_data="clean_logs"),
        types.InlineKeyboardButton("❌ CLOSE", callback_data="admin_close")
    )
    return markup


# ==================== BOT COMMANDS ====================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    user_name = message.from_user.first_name

    import html

    # Check if new user
    user_dir_path = os.path.join(UPLOAD_DIR, str(user_id))
    is_new_user = not os.path.exists(user_dir_path)

    if is_new_user:
        os.makedirs(user_dir_path, exist_ok=True)

        raw_username = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else "No Username"
        )

        safe_u_name = html.escape(user_name)
        safe_uname = html.escape(raw_username)
        is_premium = (
            "Yes"
            if getattr(message.from_user, 'is_premium', False)
            else "No"
        )

        notify_markup = types.InlineKeyboardMarkup()
        notify_markup.add(
            types.InlineKeyboardButton(
                "Talk to User",
                url=f"tg://user?id={user_id}"
            )
        )

        notify_text = (
            f"🆕 <b>New User Started Bot</b>\n\n"
            f"👤 <b>Name:</b> {safe_u_name}\n"
            f"📛 <b>Username:</b> {safe_uname}\n"
            f"🆔 <b>Chat ID:</b> <code>{user_id}</code>\n"
            f"💎 <b>Premium User:</b> {is_premium}"
        )

        safe_send(
            ADMIN_CHANNEL_ID,
            notify_text,
            reply_markup=notify_markup,
            parse_mode='HTML'
        )

    # Force Join Check
    if not is_user_joined(user_id):
        welcome_text = (
            "<b>🤖 SCRIPT HOSTING BOT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ <b>Welcome {html.escape(user_name)}!</b> ✨\n\n"
            "⚠️ <b>IMPORTANT NOTICE:</b>\n"
            "You must join our channel and group to use this bot.\n\n"
            f"📢 Channel: <b>{FORCE_JOIN['channel']['name']}</b>\n"
            f"👥 Group: <b>{FORCE_JOIN['group']['name']}</b>\n\n"
            "<i>After joining, click the verify button below.</i>"
        )

        safe_send(
            message.chat.id,
            welcome_text,
            reply_markup=force_join_menu(),
            parse_mode="HTML"
        )
        return

    scripts = get_user_scripts(user_id)
    running_count = sum(
        1 for s in scripts
        if is_script_running(user_id, s)
    )

    welcome_text = (
        "<b>🤖 SCRIPT HOSTING BOT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ <b>VERIFIED USER</b>\n\n"
        f"👤 <b>Name:</b> {html.escape(user_name)}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
        "📊 <b>YOUR STATISTICS:</b>\n"
        " ├ 📁 Total Scripts: <b>{total_scripts}</b>\n"
        " ├ 🟢 Running: <b>{running_count}</b>\n"
        " └ 🔴 Stopped: <b>{stopped_count}</b>\n\n"
        "<i>💡 Use the buttons below to manage your scripts.</i>"
    ).format(
        total_scripts=len(scripts),
        running_count=running_count,
        stopped_count=len(scripts) - running_count
    )

    safe_send(
        message.chat.id,
        welcome_text,
        reply_markup=main_menu(user_id),
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    user_id = call.from_user.id

    if is_user_joined(user_id):
        safe_callback(
            call.id,
            "✅ Verification Successful!",
            True
        )

        try:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass

        send_welcome(call.message)

    else:
        safe_callback(
            call.id,
            "❌ Please join both channel and group first!",
            True
        )
        
# ==================== FILE UPLOAD ====================
@bot.message_handler(func=lambda message: message.text == '📤 UPLOAD FILE' and message.chat.type == 'private')
def upload_prompt(message):
    user_id = message.from_user.id
    
    if not is_user_joined(user_id):
        send_welcome(message)
        return
    
    if bot_locked and user_id not in ADMIN_IDS:
        safe_send(message.chat.id, "🔒 Bot is locked. Please try later.")
        return
    
    safe_send(
        message.chat.id,
        "<b>📤 UPLOAD WORKSPACE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please send your script or archive file directly here.\n\n"
        "<b>✅ Supported formats:</b>\n"
        " ├ <code>.py</code>  (Python)\n"
        " ├ <code>.js</code>  (Node.js)\n"
        " └ <code>.zip</code> (Auto-extractable Archive)\n\n"
        "⚠️ <b>Max upload size:</b> 20MB",
        parse_mode="HTML"
    )

@bot.message_handler(content_types=['document'])
def handle_upload(message):
    if message.chat.type != 'private':
        return
    
    user_id = message.from_user.id
    
    if not is_user_joined(user_id):
        send_welcome(message)
        return
    
    if bot_locked and user_id not in ADMIN_IDS:
        safe_send(message.chat.id, "🔒 Bot is locked. Please try later.")
        return
    
    doc = message.document
    file_name = doc.file_name
    
    if not any(file_name.endswith(ext) for ext in ['.py', '.js', '.zip']):
        safe_send(message.chat.id, "❌ Only .py, .js, or .zip files are allowed!")
        return
    
    if doc.file_size > 20 * 1024 * 1024:
        safe_send(message.chat.id, "❌ File too large! Max size is 20MB.")
        return
    
    status_msg = safe_send(message.chat.id, f"⏳ Downloading `{file_name}`...")
    if not status_msg: return
    
    try:
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        # TEMP SAVE
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file_name)

        with open(file_path, 'wb') as f:
            f.write(downloaded)

        short_id = str(uuid.uuid4())[:8]

        pending_files[short_id] = {
            "user_id": user_id,
            "file_name": file_name,
            "file_path": file_path,
            "file_id": message.document.file_id  # keep original here
            }

        # USER MESSAGE
        safe_edit(message.chat.id, status_msg.message_id,
                  f"⏳ File `{file_name}` is under ai detection.\nOnce it will be approved , you will be notified..",
                  )

        # ADMIN MESSAGE
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{short_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{short_id}")
        )

        admin_msg = bot.send_document(
            ADMIN_CHANNEL_ID,
            message.document.file_id,
            caption=f"New file\nUser: {user_id}\nFile: {file_name}",
            reply_markup=markup
            )
        pending_files[short_id]["admin_msg_id"] = admin_msg.message_id

    except Exception as e:
        safe_edit(message.chat.id, status_msg.message_id, f"❌ Error: {str(e)}")

        
#==============APPROVE FILE BUTTON======================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_file(call):
    short_id = call.data.split("_")[1]

    if short_id not in pending_files:
        safe_callback(call.id, "❌ File expired or not found!", True)
        return

    data = pending_files[short_id]

    user_id = data["user_id"]
    file_name = data["file_name"]
    temp_path = data["file_path"]
    admin_msg_id = data.get("admin_msg_id")

    # validate python file
    if file_name.endswith('.py'):
        is_valid, error = validate_script(temp_path)
        if not is_valid:
            bot.send_message(user_id, f"❌ Syntax Error:\n{error}")
            os.remove(temp_path)
            del pending_files[short_id]
            safe_callback(call.id, "❌ Invalid script!", True)
            return

    user_dir = get_user_dir(user_id)
    final_path = os.path.join(user_dir, file_name)

    if file_name.endswith('.zip'):
        try:
            import zipfile
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                # Check for malicious paths
                for name in zip_ref.namelist():
                    if '..' in name or name.startswith('/'):
                        raise Exception("Invalid ZIP structure")
                
                extract_folder = user_dir
                zip_ref.extractall(extract_folder)
                
                # Auto-detect main script
                main_script = None
                for ext in ['.py', '.js']:
                    if os.path.exists(os.path.join(extract_folder, f"main{ext}")):
                        main_script = f"main{ext}"
                        break
                    if os.path.exists(os.path.join(extract_folder, f"index{ext}")):
                        main_script = f"index{ext}"
                        break
                    if os.path.exists(os.path.join(extract_folder, f"app{ext}")):
                        main_script = f"app{ext}"
                        break
                
                if main_script:
                    bot.send_message(user_id, f"✅ Extracted ZIP. Found <code>{main_script}</code> as entry point.", parse_mode="HTML")
                else:
                    bot.send_message(user_id, "⚠️ Extracted ZIP, but couldn't auto-detect main script (e.g., main.py, index.js).")

        except Exception as e:
            bot.send_message(user_id, f"❌ Failed to extract ZIP: {e}")
            os.remove(temp_path)
            del pending_files[short_id]
            safe_callback(call.id, "❌ ZIP failure!", True)
            return
            
        os.remove(temp_path)
    else:
        shutil.move(temp_path, final_path)

    # cleanup temp folder
    temp_dir = os.path.dirname(temp_path)
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Update channel message to remove buttons and show confirmation
    if admin_msg_id:
        try:
            bot.edit_message_caption(
                caption=f"✅ Approved\nUser: {user_id}\nFile: {file_name}",
                chat_id=ADMIN_CHANNEL_ID,
                message_id=admin_msg_id,
                reply_markup=None
            )
        except Exception:
            pass

    del pending_files[short_id]

    bot.send_message(user_id,
        f"✅ Your file `{file_name}` is approved!\nNow check MY SCRIPTS.")

    safe_callback(call.id, "✅ Approved")

#==================REJECT FILE BUTTON=========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_file(call):
    short_id = call.data.split("_")[1]

    if short_id not in pending_files:
        safe_callback(call.id, "❌ File not found!", True)
        return

    admin_id = call.from_user.id

    reject_waiting[admin_id] = short_id

    bot.send_message(admin_id, "✍️ Send rejection reason:")
    safe_callback(call.id)

@bot.message_handler(func=lambda m: m.from_user.id in reject_waiting)
def handle_reject_reason(message):
    admin_id = message.from_user.id
    short_id = reject_waiting[admin_id]

    if is_cancel_command(message):
        bot.send_message(admin_id, "❌ Rejection cancelled.")
        if message.text in MENU_COMMANDS:
            route_menu_command(message)
        del reject_waiting[admin_id]
        return

    if short_id not in pending_files:
        bot.send_message(admin_id, "❌ File not found or expired.")
        del reject_waiting[admin_id]
        return

    reason = message.text
    data = pending_files[short_id]

    user_id = data["user_id"]
    file_name = data["file_name"]
    temp_path = data["file_path"]
    admin_msg_id = data.get("admin_msg_id")

    # delete file
    if os.path.exists(temp_path):
        temp_dir = os.path.dirname(temp_path)
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Update channel message to remove buttons and show reason
    if admin_msg_id:
        try:
            bot.edit_message_caption(
                caption=f"❌ Rejected\nUser: {user_id}\nFile: {file_name}\nReason: {reason}",
                chat_id=ADMIN_CHANNEL_ID,
                message_id=admin_msg_id,
                reply_markup=None
            )
        except Exception:
            pass

    del pending_files[short_id]
    del reject_waiting[admin_id]

    try:
        bot.send_message(user_id,
            f"❌ File `{file_name}` rejected.\n\n📌 Reason:\n{reason}")

    except:
        pass

    bot.send_message(admin_id, "✅ Rejection sent successfully.")

# ==================== MY SCRIPTS ====================
@bot.message_handler(func=lambda message: message.text == '📂 MY SCRIPTS' and message.chat.type == 'private')
def list_scripts(message):
    user_id = message.from_user.id
    
    if not is_user_joined(user_id):
        send_welcome(message)
        return
    
    scripts = get_user_scripts(user_id)
    
    if not scripts:
        safe_send(message.chat.id, "📂 No scripts found.\n\nUse 'UPLOAD FILE' to add scripts.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for script in sorted(scripts):
        status = "🟢" if is_script_running(user_id, script) else "🔴"
        markup.add(types.InlineKeyboardButton(f"{status} {script}", callback_data=f"script_{user_id}_{script}"))
    
    safe_send(
        message.chat.id,
        "<b>📂 YOUR SCRIPTS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Total: <b>{len(scripts)}</b> scripts\n\n"
        "🟢 = <b>Running</b>  |  🔴 = <b>Stopped</b>\n\n"
        "<i>Click on a script to manage it.</i>",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('script_'))
def handle_script_callback(call):
    _, user_id, script_name = call.data.split('_', 2)
    user_id = int(user_id)
    current_user = call.from_user.id
    
    if current_user != user_id and current_user not in ADMIN_IDS:
        safe_callback(call.id, "❌ You can only control your own scripts!", True)
        return
    
    is_running = is_script_running(user_id, script_name)
    safe_callback(call.id)
    
    status_text = "🟢 RUNNING" if is_running else "🔴 STOPPED"
    
    safe_edit(call.message.chat.id, call.message.message_id,
        "<b>📄 SCRIPT CONTROL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📁 <b>Name:</b> <code>{script_name}</code>\n"
        f"📊 <b>Status:</b> <b>{status_text}</b>\n\n"
        "<i>Choose an action below:</i>",
        reply_markup=script_control_menu(user_id, script_name, is_running),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('start_'))
def start_script_cmd(call):
    _, user_id, script_name = call.data.split('_', 2)
    user_id = int(user_id)
    
    if call.from_user.id != user_id and call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Permission denied!", True)
        return
    
    user_dir = get_user_dir(user_id)
    script_path = os.path.join(user_dir, script_name)
    
    if not os.path.exists(script_path):
        safe_callback(call.id, "❌ Script not found!", True)
        return
    
    if is_script_running(user_id, script_name):
        safe_callback(call.id, "⚠️ Script is already running!", True)
        return
    
    safe_callback(call.id, "🚀 Starting script...")
    
    if script_name.endswith('.py'):
        threading.Thread(target=run_python_script, args=(script_path, user_id, script_name, call.message.chat.id), daemon=True).start()
    else:
        threading.Thread(target=run_js_script, args=(script_path, user_id, script_name, call.message.chat.id), daemon=True).start()
    
    time.sleep(1)
    fake_msg = call.message
    fake_msg.from_user = call.from_user
    list_scripts(fake_msg)

@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
def stop_script_cmd(call):
    _, user_id, script_name = call.data.split('_', 2)
    user_id = int(user_id)
    
    if call.from_user.id != user_id and call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Permission denied!", True)
        return
    
    if stop_script(user_id, script_name):
        safe_callback(call.id, "🛑 Script stopped!")
    else:
        safe_callback(call.id, "⚠️ Script was not running!", True)
    
    time.sleep(0.5)

    fake_msg = call.message
    fake_msg.from_user = call.from_user
    list_scripts(fake_msg)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_script_cmd(call):
    _, user_id, script_name = call.data.split('_', 2)
    user_id = int(user_id)
    
    if call.from_user.id != user_id and call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Permission denied!", True)
        return
    
    delete_user_script(user_id, script_name)
    safe_callback(call.id, f"🗑️ Deleted: {script_name}")
    safe_send(call.message.chat.id, f"✅ Deleted `{script_name}`")
    
    time.sleep(0.5)

    fake_msg = call.message
    fake_msg.from_user = call.from_user
    list_scripts(fake_msg)

@bot.callback_query_handler(func=lambda call: call.data.startswith('logs_'))
def view_logs_cmd(call):
    _, user_id, script_name = call.data.split('_', 2)
    user_id = int(user_id)
    
    if call.from_user.id != user_id and call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Permission denied!", True)
        return
    
    user_dir = get_user_dir(user_id)
    log_path = os.path.join(user_dir, script_name.replace('.py', '.log').replace('.js', '.log'))
    
    if not os.path.exists(log_path):
        safe_callback(call.id, "📝 No logs found yet!", True)
        return
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        if not log_content.strip():
            log_content = "(Log is empty)"
        
        if len(log_content) > 4000:
            log_content = "...\n" + log_content[-3500:]
        
        safe_send(call.message.chat.id, f"📝 LOGS for {script_name}:\n\n{log_content}")
        safe_callback(call.id)
    except Exception as e:
        safe_send(call.message.chat.id, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_scripts')
def back_to_scripts_cmd(call):
    safe_callback(call.id)
    fake_msg = call.message
    fake_msg.from_user = call.from_user
    list_scripts(fake_msg)

# ==================== INSTALL MODULE ====================
@bot.message_handler(func=lambda message: message.text == '📦 INSTALL MODULE' and message.chat.type == 'private')
def install_module_prompt(message):
    user_id = message.from_user.id
    
    if not is_user_joined(user_id):
        send_welcome(message)
        return
    
    if bot_locked and user_id not in ADMIN_IDS:
        safe_send(message.chat.id, "🔒 Bot is locked. Please try later.")
        return
    
    msg = safe_send(
        message.chat.id,
        "<b>📦 INSTALL MODULE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Send the module name to install.\n\n"
        "📝 <b>Examples:</b>\n"
        " ├ <code>requests</code>\n"
        " ├ <code>pillow</code>\n"
        " ├ <code>numpy</code>\n"
        " └ <code>telebot</code>\n\n"
        "<i>Send /cancel to cancel.</i>",
        parse_mode="HTML"
    )
    if msg:
        bot.register_next_step_handler(msg, process_install_module)

def process_install_module(message):
    if is_cancel_command(message):
        safe_send(message.chat.id, "❌ Installation cancelled.")
        if message.text in MENU_COMMANDS:
            route_menu_command(message)
        return
    
    module_name = message.text.strip()
    install_package(module_name, message.chat.id)

# ==================== STATISTICS ====================
@bot.message_handler(func=lambda message: message.text == '📊 STATS' and message.chat.type == 'private')
def show_stats(message):
    user_id = message.from_user.id
    
    if not is_user_joined(user_id):
        send_welcome(message)
        return
    
    scripts = get_user_scripts(user_id)
    running = sum(1 for s in scripts if is_script_running(user_id, s))
    pending = sum(1 for v in pending_files.values() if v['user_id'] == user_id)
    total_files = get_user_files_count(user_id)
    
    stats_text = (
        "<b>📊 STATISTICS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 <b>USER STATISTICS:</b>\n"
        f" ├ 📁 Active Scripts: <b>{len(scripts)}</b>\n"
        f" ├ 📝 Total Files: <b>{total_files}</b>\n"
        f" ├ ⏳ Pending Configs: <b>{pending}</b>\n"
        f" ├ 🟢 Running: <b>{running}</b>\n"
        f" └ 🔴 Stopped: <b>{len(scripts) - running}</b>\n\n"
        "💻 <b>SYSTEM INFO:</b>\n"
        f" ├ 🐍 Python: <code>{sys.version.split()[0]}</code>\n"
        f" └ 💻 Platform: <code>{sys.platform}</code>"
    )
    safe_send(message.chat.id, stats_text, parse_mode="HTML")

# ==================== BOT SPEED ====================
@bot.message_handler(func=lambda message: message.text == '⚡ BOT SPEED' and message.chat.type == 'private')
def bot_speed(message):
    user_id = message.from_user.id
    
    if not is_user_joined(user_id):
        send_welcome(message)
        return
    
    start = time.time()
    msg = safe_send(message.chat.id, "🏓 Pinging...")
    end = time.time()
    
    latency = round((end - start) * 1000, 2)
    
    speed_text = (
        "<b>⚡ SERVER PERFORMANCE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📡 <b>Response Time:</b> <code>{latency} ms</code>\n"
        "✅ <b>Status:</b> Online\n\n"
        "🟢 <i>All systems operational.</i>"
    )
    if msg:
        safe_edit(message.chat.id, msg.message_id, speed_text, parse_mode="HTML")

# ==================== HELP ====================
@bot.message_handler(func=lambda message: message.text == '❓ HELP' and message.chat.type == 'private')
def show_help(message):
    user_id = message.from_user.id
    
    if not is_user_joined(user_id):
        send_welcome(message)
        return
    
    help_text = (
        "<b>❓ HELP & GUIDE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📤 <b>UPLOAD FILE:</b>\n"
        " • Send .py, .js, or .zip files directly.\n"
        " • ZIP files wait for manual admin approval.\n\n"
        "📂 <b>MY SCRIPTS:</b>\n"
        " • View all your approved scripts.\n"
        " • Start, Stop, Delete, or view App logs.\n\n"
        "📦 <b>INSTALL MODULE:</b>\n"
        " • Install Python packages (e.g. <code>requests</code>).\n\n"
        "📊 <b>STATISTICS:</b>\n"
        " • View system and script analytics.\n\n"
        "────────────────────────────\n"
        "📢 Support: @EVILTALKS"
    )
    safe_send(message.chat.id, help_text, parse_mode="HTML")

#==================== ADMIN PANEL ====================
@bot.message_handler(func=lambda message: message.text in ['👑 ADMIN PANEL', '⚙️ SETTINGS & ADMIN'] and message.chat.type == 'private')
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS and message.from_user.id != OWNER_ID:
        safe_send(message.chat.id, "❌ Admin access required!")
        return
    
    safe_send(
        message.chat.id,
        "<b>⚙️ SETTINGS & ADMIN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome to the control panel Admin!\n\n"
        "<i>Select an administrative task below:</i>",
        reply_markup=admin_panel_menu(),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    total_users = len(get_all_users())
    total_scripts = sum(len(get_user_scripts(u)) for u in get_all_users())
    total_system_files = get_total_files_system()
    running = len(running_scripts)
    
    stats = (
        "<b>📊 ADMIN BOT STATISTICS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👥 <b>USERS:</b>\n"
        f" ├ Total Users: <b>{total_users}</b>\n"
        f" ├ Total Scripts: <b>{total_scripts}</b>\n"
        f" ├ Total System Files: <b>{total_system_files}</b>\n"
        f" └ Running Scripts: <b>{running}</b>\n\n"
        "💻 <b>SYSTEM:</b>\n"
        f" ├ Python: <code>{sys.version.split()[0]}</code>\n"
        f" └ Platform: <code>{sys.platform}</code>"
    )
    safe_callback(call.id)
    safe_edit(call.message.chat.id, call.message.message_id, stats, reply_markup=admin_panel_menu(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "all_users")
def all_users_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    users = get_all_users()
    
    if not users:
        safe_edit(call.message.chat.id, call.message.message_id, "No users found.", reply_markup=admin_panel_menu())
        return
    
    user_list = "<b>👥 ALL SYSTEM USERS</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, user_id in enumerate(users, 1):
        scripts = len(get_user_scripts(user_id))
        user_list += f"<b>{i}.</b> <code>{user_id}</code>  -  📁 {scripts} scripts\n"
    
    if len(user_list) > 4000:
        user_list = user_list[:3500] + "\n... <i>(truncated)</i>"
    
    safe_callback(call.id)
    safe_edit(call.message.chat.id, call.message.message_id, user_list, reply_markup=admin_panel_menu(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "manage_files")
def manage_files_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    users = get_all_users()
    
    if not users:
        safe_edit(call.message.chat.id, call.message.message_id, "No users found.", reply_markup=admin_panel_menu())
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for user_id in users:
        script_count = len(get_user_scripts(user_id))
        markup.add(types.InlineKeyboardButton(f"👤 User {user_id} ({script_count} scripts)", callback_data=f"view_user_{user_id}"))
    
    markup.add(types.InlineKeyboardButton("🔙 BACK", callback_data="admin_back"))
    
    safe_callback(call.id)
    safe_edit(call.message.chat.id, call.message.message_id, "<b>📁 MANAGE USER FILES</b>\n━━━━━━━━━━━━━━━━━━━━\n\n<i>Select a user:</i>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_user_'))
def view_user_scripts_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    user_id = int(call.data.split('_')[2])
    scripts = get_user_scripts(user_id)
    
    if not scripts:
        safe_callback(call.id, "No scripts found!", True)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for script in scripts:
        status = "🟢" if is_script_running(user_id, script) else "🔴"
        markup.add(types.InlineKeyboardButton(f"{status} {script}", callback_data=f"admin_delete_{user_id}_{script}"))
    
    markup.add(types.InlineKeyboardButton("🔙 BACK", callback_data="manage_files"))
    
    safe_callback(call.id)
    safe_edit(call.message.chat.id, call.message.message_id, f"<b>👤 USER {user_id} SCRIPTS</b>\n━━━━━━━━━━━━━━━━━━━━\n\n<i>Select a script to delete:</i>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_delete_'))
def admin_delete_script_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    parts = call.data.split('_')
    user_id = int(parts[2])
    script_name = '_'.join(parts[3:])
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ YES", callback_data=f"confirm_delete_{user_id}_{script_name}"),
        types.InlineKeyboardButton("❌ NO", callback_data=f"view_user_{user_id}")
    )
    
    safe_callback(call.id)
    safe_edit(call.message.chat.id, call.message.message_id, f"<b>⚠️ CONFIRM DELETION</b>\n━━━━━━━━━━━━━━━━━━━━\n\n👤 <b>User:</b> <code>{user_id}</code>\n📝 <b>Script:</b> <code>{script_name}</code>\n\nAre you absolutely sure?", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_delete_'))
def confirm_delete_script_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    parts = call.data.split('_')
    user_id = int(parts[2])
    script_name = '_'.join(parts[3:])
    
    delete_user_script(user_id, script_name)
    safe_callback(call.id, f"✅ Deleted: {script_name}", True)
    
    try:
        bot.send_message(user_id, f"⚠️ Admin has deleted your script: {script_name}")
    except:
        pass
    
    view_user_scripts_callback(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_close")
def admin_close_callback(call):
    if call.from_user.id in ADMIN_IDS or call.from_user.id == OWNER_ID:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

@bot.callback_query_handler(func=lambda call: call.data == "admin_running_scripts")
def admin_running_scripts(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    if not running_scripts:
        safe_edit(call.message.chat.id, call.message.message_id, "<b>▶️ RUNNING SCRIPTS</b>\n━━━━━━━━━━━━━━━━━━━━\n\nNo scripts are currently running.", reply_markup=admin_panel_menu(), parse_mode="HTML")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    text = "<b>▶️ RUNNING SCRIPTS</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for key, data in running_scripts.items():
        parts = key.split('_', 1)
        uid = parts[0]
        sname = parts[1]
        uptime_secs = int((datetime.now() - data['start_time']).total_seconds())
        text += f"👤 <code>{uid}</code> | 💻 <code>{sname}</code> | ⏱️ {uptime_secs}s\n"
        markup.add(types.InlineKeyboardButton(f"🛑 Stop: {sname} ({uid})", callback_data=f"stop_{uid}_{sname}"))
        
    markup.add(types.InlineKeyboardButton("🔙 BACK", callback_data="admin_back"))
    safe_callback(call.id)
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_msg_user")
def admin_msg_user_prompt(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    safe_callback(call.id)
    msg = safe_send(call.message.chat.id, "<b>✉️ SEND DIRECT MESSAGE</b>\n━━━━━━━━━━━━━━━━━━━━\n\nReply to this with the <code>USER_ID</code> you want to message.\n\n<i>Send /cancel to cancel.</i>", parse_mode="HTML")
    if msg:
        bot.register_next_step_handler(msg, process_msg_user_id)

def process_msg_user_id(message):
    if message.from_user.id not in ADMIN_IDS:
        return
        
    if is_cancel_command(message):
        safe_send(message.chat.id, "❌ Cancelled.")
        if message.text in MENU_COMMANDS:
            route_menu_command(message)
        return
        
    target_id = message.text.strip()
    if not target_id.isdigit():
        safe_send(message.chat.id, "❌ Invalid USER_ID. It must be a number.")
        return
        
    msg = safe_send(message.chat.id, f"📝 Sending message to <code>{target_id}</code>.\n\nNow, send me the message text:\n<i>Send /cancel to cancel.</i>", parse_mode="HTML")

    if msg:
        bot.register_next_step_handler(msg, process_msg_user_text, target_id)
def process_msg_user_text(message, target_id):
    if message.from_user.id not in ADMIN_IDS:
        return
        
    if is_cancel_command(message):
        safe_send(message.chat.id, "❌ Cancelled.")
        if message.text in MENU_COMMANDS:
            route_menu_command(message)
        return
        
    try:
        bot.send_message(int(target_id), f"<b>📬 MESSAGE FROM ADMIN:</b>\n━━━━━━━━━━━━━━━━━━━━\n\n{message.text}", parse_mode="HTML")

        safe_send(message.chat.id, f"✅ Message sent successfully to <code>{target_id}</code>.", parse_mode="HTML")
    except Exception as e:
        safe_send(message.chat.id, f"❌ Failed to send message: {e}")
@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back_callback(call):
    safe_callback(call.id)
    admin_panel(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def broadcast_prompt(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    safe_callback(call.id)
    msg = safe_send(call.message.chat.id, "<b>📢 SYSTEM BROADCAST</b>\n━━━━━━━━━━━━━━━━━━━━\n\nSend the message you want to broadcast to all users:\n\n<i>Send /cancel to cancel.</i>", parse_mode="HTML")
    if msg:
        bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    if is_cancel_command(message):
        safe_send(message.chat.id, "❌ Broadcast cancelled.")
        if message.text in MENU_COMMANDS:
            route_menu_command(message)
        return
    
    users = get_all_users()
    sent = 0
    failed = 0
    
    status_msg = safe_send(message.chat.id, f"📢 Broadcasting to {len(users)} users...")
    
    for user_id in users:
        try:
            bot.send_message(int(user_id), f"<b>📢 SYSTEM ANNOUNCEMENT:</b>\n━━━━━━━━━━━━━━━━━━━━\n\n{message.text}", parse_mode="HTML")

            sent += 1
        except:
            failed += 1
        time.sleep(0.1)
    
    if status_msg:
        safe_edit(message.chat.id, status_msg.message_id, f"<b>✅ Broadcast Complete!</b>\n━━━━━━━━━━━━━━━━━━━━\n✅ Delivered: <b>{sent}</b>\n❌ Failed: <b>{failed}</b>", parse_mode="HTML")
@bot.callback_query_handler(func=lambda call: call.data == "clean_logs")
def clean_logs_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    deleted = 0
    for user_dir in os.listdir(UPLOAD_DIR):
        user_path = os.path.join(UPLOAD_DIR, user_dir)
        if os.path.isdir(user_path):
            for file in os.listdir(user_path):
                if file.endswith('.log'):
                    try:
                        os.remove(os.path.join(user_path, file))
                        deleted += 1
                    except:
                        pass
    
    safe_callback(call.id, f"✅ Cleaned {deleted} log files!", True)
    safe_edit(call.message.chat.id, call.message.message_id, f"<b>🗑️ LOG CLEANUP REPORT</b>\n━━━━━━━━━━━━━━━━━━━━\n\n✅ Cleaned up <b>{deleted}</b> log files.\n\n<i>Returning to admin menu...</i>", reply_markup=admin_panel_menu(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "lock_bot")
def lock_bot_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    global bot_locked
    bot_locked = True
    safe_callback(call.id, "🔒 Bot locked!", True)
    safe_edit(call.message.chat.id, call.message.message_id, "<b>🔒 SYSTEM LOCKED</b>\n━━━━━━━━━━━━━━━━━━━━\n\nNormal operations paused.", reply_markup=admin_panel_menu(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "unlock_bot")
def unlock_bot_callback(call):
    if call.from_user.id not in ADMIN_IDS:
        safe_callback(call.id, "❌ Admin only!", True)
        return
    
    global bot_locked
    bot_locked = False
    safe_callback(call.id, "🔓 Bot unlocked!", True)
    safe_edit(call.message.chat.id, call.message.message_id, "<b>🔓 SYSTEM UNLOCKED</b>\n━━━━━━━━━━━━━━━━━━━━\n\nOperations resumed normally.", reply_markup=admin_panel_menu(), parse_mode="HTML")


# ==================== DEFAULT HANDLER ====================
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    if message.chat.type != 'private':
        return
    
    if not is_user_joined(message.from_user.id):
        send_welcome(message)
        return
    
    if bot_locked and message.from_user.id not in ADMIN_IDS:
        safe_send(message.chat.id, "🔒 Bot is locked. Please try later.")
        return
    
    safe_send(message.chat.id, "❓ Unknown command. Please use the buttons below.", reply_markup=main_menu(message.from_user.id))

# ==================== CLEANUP ====================
# FIX: The key splitting here was expecting 3 items instead of 2
def cleanup():
    print("Shutting down, stopping all scripts...")
    for key in list(running_scripts.keys()):
        try:
            user_id, script_name = key.split('_', 1)
            stop_script(int(user_id), script_name)
        except:
            pass

atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda s, f: cleanup())

# ==================== MAIN ====================
if __name__ == '__main__':
    print("=" * 60)
    print("🤖 SCRIPT HOSTING BOT STARTED")
    print(f"📁 Upload directory: {UPLOAD_DIR}")
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"📢 Force Join: {FORCE_JOIN['channel']['id']}")
    print(f"👥 Force Join: {FORCE_JOIN['group']['id']}")
    print("=" * 60)
    
    keep_alive()
    
    # Start the background task for ziplog backups
    threading.Thread(target=backup_task, daemon=True).start()
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"Error: {e}")
            print("Reconnecting in 5 seconds...")
            time.sleep(5)
