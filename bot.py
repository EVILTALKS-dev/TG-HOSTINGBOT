# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════╗
# ║         JEXXY CLOUD BOT — Premium Edition           ║
# ║      Owner/Dev: @JEXXYNOIRMYATTITUDE                ║
# ╚══════════════════════════════════════════════════════╝

# --- JEXXY dependency bootstrap (runs before third-party imports) ---
import os as _bootstrap_os
import sys as _bootstrap_sys
import subprocess as _bootstrap_subprocess
import importlib.util as _bootstrap_importlib

_BOOTSTRAP_DIR = _bootstrap_os.path.join(_bootstrap_os.path.abspath(_bootstrap_os.path.dirname(__file__)), ".jexxy_packages")
_bootstrap_os.makedirs(_BOOTSTRAP_DIR, exist_ok=True)
if _BOOTSTRAP_DIR not in _bootstrap_sys.path:
    _bootstrap_sys.path.insert(0, _BOOTSTRAP_DIR)

def _ensure_bootstrap_package(module_name, package_name):
    try:
        if _bootstrap_importlib.find_spec(module_name) is not None:
            return True
    except Exception:
        pass
    try:
        env = _bootstrap_os.environ.copy()
        home = _bootstrap_os.path.join(_BOOTSTRAP_DIR, ".home")
        cache = _bootstrap_os.path.join(_BOOTSTRAP_DIR, ".cache")
        userbase = _bootstrap_os.path.join(_BOOTSTRAP_DIR, ".userbase")
        for _d in (home, cache, userbase):
            _bootstrap_os.makedirs(_d, exist_ok=True)
        env.update({"HOME": home, "PIP_CACHE_DIR": cache, "PYTHONUSERBASE": userbase,
                    "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PIP_NO_INPUT": "1"})
        result = _bootstrap_subprocess.run(
            [_bootstrap_sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
             "--no-input", "--upgrade", "--target", _BOOTSTRAP_DIR, package_name],
            env=env, stdout=_bootstrap_subprocess.PIPE, stderr=_bootstrap_subprocess.STDOUT,
            text=True, timeout=600
        )
        if result.returncode != 0:
            print(f"[JEXXY] Failed to install {package_name}:\n{result.stdout[-2000:]}")
            return False
        _bootstrap_importlib.invalidate_caches()
        return True
    except Exception as _e:
        print(f"[JEXXY] Dependency bootstrap error for {package_name}: {_e}")
        return False

# These are required by the hosting bot itself. Uploaded-file dependencies
# are handled later by ensure_python_dependencies().
_BOOTSTRAP_DEPS = {
    "telebot": "pyTelegramBotAPI",
    "psutil": "psutil",
    "requests": "requests",
    "flask": "Flask",
}
for _mod, _pkg in _BOOTSTRAP_DEPS.items():
    if not _ensure_bootstrap_package(_mod, _pkg):
        raise RuntimeError(f"Required dependency '{_mod}' is unavailable. Install package '{_pkg}' and restart.")

# --- End JEXXY dependency bootstrap ---

import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import hashlib
import mimetypes
import struct
import random
import ast
import importlib.util

# --- Flask Keep Alive ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "⚡ EvilHosts — Online & Blazing"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Flask Keep-Alive server started.")
# --- End Flask Keep Alive ---

# ══════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════
TOKEN          = '8843932282:AAF8Vzm9yTlh0IeMLRwKbP-0G8wMbYOq4Go'
OWNER_ID       = 8066849679
ADMIN_ID       = 8066849679
YOUR_USERNAME  = '@EVILTALKS'
BOT_NAME       = "EVIL HOSTS BOT"
BOT_USERNAME   = "@EvilHostsBot"
CREDIT         = "𝗘𝘃𝗶𝗹𝘁𝗮𝗹𝗸𝘀"

# Credits config
FREE_CREDITS      = 2       # credits given to every new user
REFERRAL_BONUS    = 5       # credits referrer earns per successful referral
UPLOAD_COST       = 1       # credits consumed per file upload

# Welcome video
WELCOME_VIDEO_URL = 'https://t.me/EVILTALKSBOTKALIYEVIDEOS/2'

# Folder setup
BASE_DIR         = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR  = os.path.join(BASE_DIR, 'upload_bots')
DATA_DIR         = os.path.join(BASE_DIR, 'jexxy_data')
DATABASE_PATH    = os.path.join(DATA_DIR, 'bot_data.db')

os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# --- Telegram formatting safety ---
# Telegram's legacy Markdown parser rejects filenames, logs and user-provided
# errors containing unmatched _, *, `, [, etc.  Keep the premium formatting,
# but automatically retry the same message as plain text when entity parsing
# fails. This prevents a bad filename/runtime log from breaking the hosting flow.
def _is_entity_parse_error(exc):
    text = str(exc).lower()
    return ('can\'t parse entities' in text or 'cant parse entities' in text
            or 'parse entities' in text)

def _safe_wrap_method(obj, method_name):
    original = getattr(obj, method_name)
    def wrapped(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except Exception as exc:
            if not _is_entity_parse_error(exc) or kwargs.get('parse_mode') is None:
                raise
            retry_kwargs = dict(kwargs)
            retry_kwargs.pop('parse_mode', None)
            return original(*args, **retry_kwargs)
    setattr(obj, method_name, wrapped)

for _method in ('send_message', 'send_photo', 'send_video', 'send_document',
                'edit_message_text', 'edit_message_caption'):
    try:
        _safe_wrap_method(bot, _method)
    except Exception:
        pass

# --- Runtime state ---
bot_scripts       = {}
user_credits_cache = {}   # {user_id: int}  in-memory cache
user_files        = {}    # {user_id: [(file_name, file_type), ...]}
active_users      = set()
admin_ids         = {OWNER_ID}
bot_locked        = False

# ══════════════════════════════════════════════════════
#  AUTO-REACTION POOL
# ══════════════════════════════════════════════════════
REACTION_POOL = ['🔥', '⚡', '🤩', '🎉', '💯', '🏆', '👍', '❤️', '🤣', '💀', '😎', '🥳']

def auto_react(message):
    """Fire a random emoji reaction on any message — silently."""
    try:
        emoji = random.choice(REACTION_POOL)
        # ReactionTypeEmoji available in pyTelegramBotAPI >= 4.14
        reaction = types.ReactionTypeEmoji(emoji)
        bot.set_message_reaction(
            message.chat.id, message.message_id,
            [reaction], is_big=False
        )
    except Exception:
        pass  # older API version or not supported — no crash

# ══════════════════════════════════════════════════════
#  MALWARE DETECTION
# ══════════════════════════════════════════════════════
MALWARE_SIGNATURES = [
    b'MZ', b'\x7fELF', b'\xfe\xed\xfa', b'\xce\xfa\xed\xfe', b'PK', b'Rar!',
]
ENCRYPTED_FILE_INDICATORS = [
    b'openssl', b'encrypted', b'cipher', b'AES', b'DES', b'RSA', b'GPG', b'PGP',
]
SUSPICIOUS_KEYWORDS = [
    b'ransomware', b'trojan', b'virus', b'malware', b'backdoor',
    b'exploit', b'payload', b'botnet', b'keylogger', b'rootkit',
]

def get_file_type(file_content):
    signatures = {
        b'\x7fELF':      'application/x-executable',
        b'MZ':           'application/x-dosexec',
        b'\xfe\xed\xfa': 'application/x-mach-binary',
        b'\xce\xfa\xed\xfe': 'application/x-mach-binary',
        b'PK':           'application/zip',
        b'Rar!':         'application/x-rar',
    }
    for sig, mime in signatures.items():
        if file_content.startswith(sig):
            return mime
    return 'application/octet-stream'

def is_suspicious_file(file_content, file_name):
    file_lower = file_name.lower()
    suspicious_ext = [
        '.exe', '.dll', '.bat', '.cmd', '.scr', '.com', '.pif',
        '.application', '.gadget', '.msi', '.msp', '.hta', '.cpl',
        '.msc', '.jar', '.bin', '.deb', '.rpm', '.apk', '.app',
        '.dmg', '.iso', '.img'
    ]
    if any(file_lower.endswith(e) for e in suspicious_ext):
        return True, f"Suspicious file extension: {file_name}"
    for sig in MALWARE_SIGNATURES:
        if file_content.startswith(sig):
            return True, "Malware signature detected"
    sample = file_content[:4096]
    for ind in ENCRYPTED_FILE_INDICATORS:
        if ind in sample:
            return True, f"Encrypted indicator: {ind.decode('utf-8', errors='ignore')}"
    sample_text = sample.decode('utf-8', errors='ignore').lower()
    for kw in SUSPICIOUS_KEYWORDS:
        if kw.decode('utf-8').lower() in sample_text:
            return True, f"Suspicious keyword: {kw.decode('utf-8')}"
    try:
        ftype = get_file_type(sample)
        if ftype in ['application/x-dosexec', 'application/x-executable', 'application/x-mach-binary']:
            return True, f"Executable detected: {ftype}"
    except Exception:
        pass
    return False, "File passed scan"

def scan_file(file_content, file_name, user_id):
    if user_id == OWNER_ID:
        return True, "Owner bypass"
    ok, reason = is_suspicious_file(file_content, file_name)
    if ok:
        logger.warning(f"🚨 Blocked {file_name} from {user_id}: {reason}")
        return False, f"Security block: {reason}"
    return True, "Clean"

# ══════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════
DB_LOCK = threading.Lock()

def init_db():
    logger.info(f"Initializing DB at: {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS active_users
                     (user_id INTEGER PRIMARY KEY)''')
        # User files
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
                     (user_id INTEGER, file_name TEXT, file_type TEXT,
                      PRIMARY KEY (user_id, file_name))''')
        # Admins
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY)''')
        # Credits system — replaces old subscriptions
        c.execute('''CREATE TABLE IF NOT EXISTS credits
                     (user_id INTEGER PRIMARY KEY,
                      amount INTEGER DEFAULT 2,
                      referred_by INTEGER DEFAULT NULL,
                      referral_code TEXT DEFAULT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS credit_transactions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      admin_id INTEGER,
                      action TEXT NOT NULL,
                      amount INTEGER NOT NULL,
                      balance_after INTEGER,
                      created_at TEXT NOT NULL)''')
        # Owner is always an admin; additional admins persist across restarts.
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        # Owner gets infinite marker — we handle in code, but store 999999 in DB
        c.execute('INSERT OR IGNORE INTO credits (user_id, amount) VALUES (?, ?)', (OWNER_ID, 999999))
        conn.commit()
        conn.close()
        logger.info("DB ready.")
    except Exception as e:
        logger.error(f"DB init error: {e}", exc_info=True)

def load_data():
    logger.info("Loading data from DB...")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        # Load files
        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for user_id, fn, ft in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((fn, ft))
        # Load active users
        c.execute('SELECT user_id FROM active_users')
        active_users.update(uid for (uid,) in c.fetchall())
        # Load admins
        c.execute('SELECT user_id FROM admins')
        admin_ids.update(uid for (uid,) in c.fetchall())
        # Load credits
        c.execute('SELECT user_id, amount FROM credits')
        for uid, amt in c.fetchall():
            user_credits_cache[uid] = amt
        conn.close()
        logger.info(f"Loaded: {len(active_users)} users | {len(admin_ids)} admins | {len(user_credits_cache)} credit records")
    except Exception as e:
        logger.error(f"Data load error: {e}", exc_info=True)

init_db()
load_data()

# ══════════════════════════════════════════════════════
#  CREDITS FUNCTIONS
# ══════════════════════════════════════════════════════
def get_credits(user_id: int):
    """Returns float('inf') for owner/admin, else int from cache/DB."""
    if user_id == OWNER_ID or user_id in admin_ids:
        return float('inf')
    return user_credits_cache.get(user_id, 0)

def _set_credits_db(user_id: int, amount: int):
    amount = max(0, int(amount))
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute(
                'INSERT INTO credits (user_id, amount) VALUES (?, ?) '
                'ON CONFLICT(user_id) DO UPDATE SET amount=excluded.amount',
                (user_id, amount)
            )
            conn.commit()
            user_credits_cache[user_id] = amount
            return amount
        except Exception as e:
            logger.error(f"_set_credits_db: {e}")
            return user_credits_cache.get(user_id, 0)
        finally:
            conn.close()

def _record_credit_transaction(user_id, admin_id, action, amount, balance_after):
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            try:
                conn.execute(
                    'INSERT INTO credit_transactions '
                    '(user_id, admin_id, action, amount, balance_after, created_at) '
                    'VALUES (?,?,?,?,?,?)',
                    (user_id, admin_id, action, int(amount),
                     None if balance_after == float('inf') else int(balance_after),
                     datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
                conn.commit()
            finally:
                conn.close()
    except Exception as e:
        logger.warning(f"Credit audit log failed: {e}")

def add_credits(user_id: int, amount: int, admin_id=None, action='add'):
    amount = int(amount)
    if amount <= 0:
        raise ValueError('Amount must be positive')
    if user_id == OWNER_ID or user_id in admin_ids:
        # Admins/owner are unlimited; keep an audit entry but do not inflate DB.
        _record_credit_transaction(user_id, admin_id, action, amount, float('inf'))
        return float('inf')
    with DB_LOCK:
        current = int(user_credits_cache.get(user_id, 0))
        new_balance = current + amount
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute(
                'INSERT INTO credits (user_id, amount) VALUES (?, ?) '
                'ON CONFLICT(user_id) DO UPDATE SET amount=excluded.amount',
                (user_id, new_balance)
            )
            conn.commit()
            user_credits_cache[user_id] = new_balance
        finally:
            conn.close()
    _record_credit_transaction(user_id, admin_id, action, amount, new_balance)
    return new_balance

def deduct_credit(user_id: int) -> bool:
    if user_id == OWNER_ID or user_id in admin_ids:
        return True  # unlimited
    with DB_LOCK:
        current = int(user_credits_cache.get(user_id, 0))
        if current <= 0:
            return False
        new_balance = current - 1
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute(
                'INSERT INTO credits (user_id, amount) VALUES (?, ?) '
                'ON CONFLICT(user_id) DO UPDATE SET amount=excluded.amount',
                (user_id, new_balance)
            )
            conn.commit()
            user_credits_cache[user_id] = new_balance
        finally:
            conn.close()
    _record_credit_transaction(user_id, None, 'upload', 1, new_balance)
    return True

def init_user_credits(user_id: int, referred_by: int = None):
    """Give FREE_CREDITS to a brand-new user and optionally handle referral."""
    if user_id in user_credits_cache:
        return  # already initialized
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            ref_code = f"ref_{user_id}"
            conn.execute(
                'INSERT OR IGNORE INTO credits (user_id, amount, referred_by, referral_code) VALUES (?,?,?,?)',
                (user_id, FREE_CREDITS, referred_by, ref_code)
            )
            conn.commit()
            user_credits_cache[user_id] = FREE_CREDITS
        except Exception as e:
            logger.error(f"init_user_credits: {e}")
        finally:
            conn.close()
    # Pay referral bonus if referred by someone valid
    if referred_by and referred_by != user_id:
        add_credits(referred_by, REFERRAL_BONUS)
        try:
            bot.send_message(
                referred_by,
                f"🎁 *Referral Bonus!*\n\n"
                f"Someone joined using your link!\n"
                f"✅ +{REFERRAL_BONUS} credits added to your account.\n"
                f"💰 New balance: `{get_credits(referred_by)}`",
                parse_mode='Markdown'
            )
        except Exception:
            pass

def get_referral_code(user_id: int) -> str:
    return f"ref_{user_id}"

# ══════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════
def get_user_folder(user_id):
    folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

def get_user_file_count(user_id):
    return len(user_files.get(user_id, []))

def is_bot_running(owner_id, file_name):
    key = f"{owner_id}_{file_name}"
    info = bot_scripts.get(key)
    if info and info.get('process'):
        try:
            proc = psutil.Process(info['process'].pid)
            running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not running:
                _close_log(info)
                bot_scripts.pop(key, None)
            return running
        except psutil.NoSuchProcess:
            _close_log(info)
            bot_scripts.pop(key, None)
        except Exception as e:
            logger.error(f"Process check {key}: {e}")
    return False

def _close_log(info):
    lf = info.get('log_file')
    if lf and hasattr(lf, 'close') and not lf.closed:
        try: lf.close()
        except: pass

def kill_process_tree(process_info):
    _close_log(process_info)
    proc = process_info.get('process')
    if not proc or not hasattr(proc, 'pid') or not proc.pid:
        return
    try:
        parent = psutil.Process(proc.pid)
        kids   = parent.children(recursive=True)
        for kid in kids:
            try: kid.terminate()
            except: pass
        psutil.wait_procs(kids, timeout=1)
        for kid in kids:
            try: kid.kill()
            except: pass
        try:
            parent.terminate()
            parent.wait(timeout=1)
        except psutil.TimeoutExpired:
            try: parent.kill()
            except: pass
        except psutil.NoSuchProcess:
            pass
    except psutil.NoSuchProcess:
        pass
    except Exception as e:
        logger.error(f"kill_process_tree: {e}", exc_info=True)

def get_user_status_str(user_id: int) -> str:
    if user_id == OWNER_ID:    return "👑 Owner"
    if user_id in admin_ids:   return "🛡️ Admin"
    credits = get_credits(user_id)
    if credits > 10:           return "💎 Premium"
    if credits > 0:            return "⭐ User"
    return "🆓 Free"

# ══════════════════════════════════════════════════════
#  AUTO PACKAGE INSTALLATION
# ══════════════════════════════════════════════════════
TELEGRAM_MODULES = {
    'telebot': 'pyTelegramBotAPI', 'telegram': 'python-telegram-bot',
    'python_telegram_bot': 'python-telegram-bot', 'aiogram': 'aiogram',
    'pyrogram': 'pyrogram', 'telethon': 'telethon', 'telethon.sync': 'telethon',
    'telepot': 'telepot', 'tgcrypto': 'tgcrypto', 'bs4': 'beautifulsoup4',
    'requests': 'requests', 'httpx': 'httpx', 'pillow': 'Pillow',
    'cv2': 'opencv-python', 'yaml': 'PyYAML', 'dotenv': 'python-dotenv',
    'dateutil': 'python-dateutil', 'pandas': 'pandas', 'numpy': 'numpy',
    'flask': 'Flask', 'django': 'Django', 'sqlalchemy': 'SQLAlchemy',
    'psutil': 'psutil', 'urllib3': 'urllib3', 'lxml': 'lxml',
    'cryptography': 'cryptography', 'jwt': 'PyJWT', 'dns': 'dnspython',
    'qrcode': 'qrcode', 'PIL': 'Pillow', 'yaml': 'PyYAML',
    # stdlib — no install needed
    'asyncio': None, 'json': None, 'datetime': None, 'os': None, 'sys': None,
    're': None, 'time': None, 'math': None, 'random': None, 'logging': None,
    'threading': None, 'subprocess': None, 'zipfile': None, 'tempfile': None,
    'shutil': None, 'sqlite3': None, 'atexit': None, 'pathlib': None,
    'typing': None, 'collections': None, 'itertools': None, 'functools': None,
    'hashlib': None, 'uuid': None, 'base64': None, 'secrets': None,
    'signal': None, 'socket': None, 'ssl': None, 'statistics': None,
    'timeit': None, 'traceback': None, 'contextlib': None, 'dataclasses': None,
    'enum': None, 'string': None, 'csv': None, 'io': None, 'copy': None,
    'glob': None, 'platform': None, 'subprocess': None, 'configparser': None,
}


def _top_level_module(name):
    return (name or '').split('.')[0].strip()


def detect_imports(script_path):
    """Read imports without executing the uploaded script."""
    found = set()
    try:
        source = open(script_path, 'r', encoding='utf-8', errors='ignore').read()
        tree = ast.parse(source, filename=script_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(_top_level_module(alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module:
                if not node.level:
                    found.add(_top_level_module(node.module))
    except Exception as e:
        logger.warning(f"Import scan failed for {script_path}: {e}")
    return sorted(x for x in found if x)


def module_is_available(module_name):
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
        return False


def _dependency_dir(user_folder):
    """Writable, per-user package directory. Never install into /.local or system paths."""
    path = os.path.join(user_folder, '.packages')
    os.makedirs(path, exist_ok=True)
    return path


def _pip_env(user_folder):
    """Build a pip environment that stays completely inside the user's writable folder."""
    env = os.environ.copy()
    home = os.path.join(user_folder, '.home')
    cache = os.path.join(user_folder, '.cache', 'pip')
    userbase = os.path.join(user_folder, '.local')
    for path in (home, cache, userbase):
        os.makedirs(path, exist_ok=True)
    env['HOME'] = home
    env['PIP_CACHE_DIR'] = cache
    env['PYTHONUSERBASE'] = userbase
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    env['PIP_NO_INPUT'] = '1'
    package_dir = _dependency_dir(user_folder)
    old_pp = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = package_dir + (os.pathsep + user_folder + (os.pathsep + old_pp if old_pp else '') if user_folder else (os.pathsep + old_pp if old_pp else ''))
    return env, package_dir


def _pip_command(user_folder, args):
    """pip command that installs only into our writable .packages directory."""
    _, package_dir = _pip_env(user_folder)
    return [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
            '--no-input', '--upgrade', '--target', package_dir] + list(args)


def pip_install_package(pkg, user_folder=None, message=None):
    if not pkg or not user_folder:
        return False
    try:
        env, package_dir = _pip_env(user_folder)
        if message:
            bot.reply_to(message, f"🐍 Installing `{pkg}`...", parse_mode='Markdown')
        r = subprocess.run(
            _pip_command(user_folder, [pkg]),
            cwd=user_folder, env=env,
            capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=600
        )
        if r.returncode == 0:
            if package_dir not in sys.path:
                sys.path.insert(0, package_dir)
            importlib.invalidate_caches()
            if message:
                bot.reply_to(message, f"✅ `{pkg}` installed locally.", parse_mode='Markdown')
            return True
        err = (r.stderr or r.stdout or 'unknown pip error').strip()
        logger.error(f"pip install {pkg} failed: {err[-4000:]}")
        if message:
            bot.reply_to(message, f"❌ Install failed for `{pkg}`:\n```\n{err[-2200:]}\n```", parse_mode='Markdown')
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"pip install timeout: {pkg}")
        if message:
            bot.reply_to(message, f"❌ Install timeout: `{pkg}`", parse_mode='Markdown')
        return False
    except Exception as e:
        logger.error(f"pip install error {pkg}: {e}", exc_info=True)
        if message:
            bot.reply_to(message, f"❌ Install error `{pkg}`: {e}")
        return False


def install_requirements(user_folder, message=None):
    req_path = os.path.join(user_folder, 'requirements.txt')
    if not os.path.isfile(req_path):
        return True
    try:
        env, package_dir = _pip_env(user_folder)
        if package_dir not in sys.path:
            sys.path.insert(0, package_dir)
        importlib.invalidate_caches()
        if message:
            bot.reply_to(message, "📦 Installing `requirements.txt` into private package storage...", parse_mode='Markdown')
        r = subprocess.run(
            _pip_command(user_folder, ['-r', req_path]),
            cwd=user_folder, env=env,
            capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=900
        )
        if r.returncode == 0:
            importlib.invalidate_caches()
            if message:
                bot.reply_to(message, "✅ Requirements installed.", parse_mode='Markdown')
            return True
        err = (r.stderr or r.stdout or 'unknown pip error').strip()
        logger.error(f"requirements.txt failed: {err[-5000:]}")
        if message:
            bot.reply_to(message, f"❌ `requirements.txt` failed:\n```\n{err[-2200:]}\n```", parse_mode='Markdown')
        return False
    except subprocess.TimeoutExpired:
        if message: bot.reply_to(message, "❌ requirements.txt installation timed out.")
        return False
    except Exception as e:
        logger.error(f"requirements install error: {e}", exc_info=True)
        if message: bot.reply_to(message, f"❌ Requirements error: {e}")
        return False


def ensure_python_dependencies(script_path, user_folder, message=None):
    """Install requirements/missing imports into a writable per-user directory."""
    env, package_dir = _pip_env(user_folder)
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)
    importlib.invalidate_caches()

    if not install_requirements(user_folder, message):
        return False

    missing = []
    for mod in detect_imports(script_path):
        if TELEGRAM_MODULES.get(mod) is None:
            continue
        if module_is_available(mod):
            continue
        missing.append(mod)

    packages = []
    seen = set()
    for mod in missing:
        pkg = TELEGRAM_MODULES.get(mod, mod)
        if pkg and pkg not in seen:
            packages.append((mod, pkg)); seen.add(pkg)

    for mod, pkg in packages:
        logger.info(f"Missing dependency detected: {mod} -> {pkg}")
        if not pip_install_package(pkg, user_folder, message):
            return False

    importlib.invalidate_caches()
    still_missing = [m for m in detect_imports(script_path)
                     if TELEGRAM_MODULES.get(m) is not None and not module_is_available(m)]
    if still_missing:
        logger.error(f"Dependencies still missing: {still_missing}")
        if message:
            bot.reply_to(message, "❌ Missing Python modules after install: " + ', '.join(still_missing))
        return False
    return True

def attempt_install_pip(module_name, message):
    pkg = TELEGRAM_MODULES.get(_top_level_module(module_name), module_name)
    return pip_install_package(pkg, BASE_DIR, message)

# ══════════════════════════════════════════════════════
#  SCRIPT RUNNERS
# ══════════════════════════════════════════════════════
def _read_log_tail(log_path, limit=5000):
    try:
        if not os.path.exists(log_path):
            return "(no log file)"
        with open(log_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - limit), os.SEEK_SET)
            data = f.read(limit)
        text = data.decode('utf-8', errors='replace').strip()
        return text[-limit:] if text else "(empty log)"
    except Exception as e:
        return f"(could not read log: {e})"


def _monitor_python_process(key, process, log_path, msg_obj, file_name):
    """Confirm startup and immediately report runtime crashes instead of false 'running'."""
    time.sleep(3.0)
    rc = process.poll()
    if rc is None:
        logger.info(f"{file_name} startup OK, PID={process.pid}")
        return

    info = bot_scripts.get(key)
    if info:
        _close_log(info)
        bot_scripts.pop(key, None)
    reason = _read_log_tail(log_path, 4500)
    text = (
        f"❌ `{file_name}` stopped during startup. Exit code: `{rc}`\n\n"
        f"📜 *Runtime log:*\n```\n{reason[:3500]}\n```"
    )
    try:
        bot.reply_to(msg_obj, text, parse_mode='Markdown')
    except Exception:
        logger.error(text)


def run_script(script_path, owner_id, user_folder, file_name, msg_obj, attempt=1):
    max_attempts = 2
    if attempt > max_attempts:
        bot.reply_to(msg_obj, f"❌ `{file_name}` failed after {max_attempts} attempts.", parse_mode='Markdown')
        return
    key = f"{owner_id}_{file_name}"
    try:
        if not os.path.exists(script_path):
            bot.reply_to(msg_obj, f"❌ Script `{file_name}` not found."); return

        # IMPORTANT: py_compile only checks syntax. It does NOT detect missing imports.
        # Install requirements + all missing imports before starting the real process.
        if attempt == 1:
            if not ensure_python_dependencies(script_path, user_folder, msg_obj):
                return

        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = open(log_path, 'w', encoding='utf-8', errors='ignore')
        si = None; cf = 0
        if os.name == 'nt':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE

        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        package_dir = _dependency_dir(user_folder)
        env['HOME'] = os.path.join(user_folder, '.home')
        env['PIP_CACHE_DIR'] = os.path.join(user_folder, '.cache', 'pip')
        env['PYTHONUSERBASE'] = os.path.join(user_folder, '.local')
        old_pythonpath = env.get('PYTHONPATH', '')
        paths = [package_dir, user_folder]
        if old_pythonpath:
            paths.append(old_pythonpath)
        env['PYTHONPATH'] = os.pathsep.join(paths)

        process = subprocess.Popen(
            [sys.executable, '-u', script_path], cwd=user_folder,
            stdout=log_file, stderr=log_file, stdin=subprocess.PIPE,
            startupinfo=si, creationflags=cf, env=env,
            encoding='utf-8', errors='ignore'
        )
        bot_scripts[key] = {
            'process': process, 'log_file': log_file, 'log_path': log_path,
            'file_name': file_name, 'chat_id': msg_obj.chat.id,
            'script_owner_id': owner_id, 'start_time': datetime.now(),
            'user_folder': user_folder, 'type': 'py', 'script_key': key
        }
        bot.reply_to(msg_obj, f"🚀 Starting `{file_name}`... PID: `{process.pid}`", parse_mode='Markdown')
        threading.Thread(
            target=_monitor_python_process,
            args=(key, process, log_path, msg_obj, file_name),
            daemon=True
        ).start()
    except Exception as e:
        if key in bot_scripts:
            kill_process_tree(bot_scripts[key]); bot_scripts.pop(key, None)
        bot.reply_to(msg_obj, f"❌ Python error: {e}")

def run_js_script(script_path, owner_id, user_folder, file_name, msg_obj, attempt=1):
    max_attempts = 2
    if attempt > max_attempts:
        bot.reply_to(msg_obj, f"❌ `{file_name}` failed after {max_attempts} attempts.", parse_mode='Markdown')
        return
    key = f"{owner_id}_{file_name}"
    try:
        if not os.path.exists(script_path):
            bot.reply_to(msg_obj, f"❌ `{file_name}` not found."); return
        if attempt == 1:
            check_proc = None
            try:
                check_proc = subprocess.Popen(
                    ['node', script_path], cwd=user_folder,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding='utf-8', errors='ignore'
                )
                _, stderr = check_proc.communicate(timeout=5)
                if check_proc.returncode != 0 and stderr:
                    m = re.search(r"Cannot find module '(.+?)'", stderr)
                    if m:
                        mod = m.group(1).strip().strip("'\"")
                        if not mod.startswith('.') and not mod.startswith('/'):
                            if attempt_install_npm(mod, user_folder, msg_obj):
                                time.sleep(2)
                                threading.Thread(
                                    target=run_js_script,
                                    args=(script_path, owner_id, user_folder, file_name, msg_obj, attempt+1)
                                ).start()
                            return
                    bot.reply_to(msg_obj, f"❌ JS error:\n```\n{stderr[:500]}\n```", parse_mode='Markdown')
                    return
            except subprocess.TimeoutExpired:
                if check_proc and check_proc.poll() is None:
                    check_proc.kill(); check_proc.communicate()
            except FileNotFoundError:
                bot.reply_to(msg_obj, "❌ Node.js not found. Install it first."); return
            except Exception as e:
                bot.reply_to(msg_obj, f"❌ JS pre-check error: {e}"); return
            finally:
                if check_proc and check_proc.poll() is None:
                    check_proc.kill(); check_proc.communicate()
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = open(log_path, 'w', encoding='utf-8', errors='ignore')
        process = subprocess.Popen(
            ['node', script_path], cwd=user_folder,
            stdout=log_file, stderr=log_file, stdin=subprocess.PIPE,
            encoding='utf-8', errors='ignore'
        )
        bot_scripts[key] = {
            'process': process, 'log_file': log_file, 'file_name': file_name,
            'chat_id': msg_obj.chat.id, 'script_owner_id': owner_id,
            'start_time': datetime.now(), 'user_folder': user_folder,
            'type': 'js', 'script_key': key
        }
        bot.reply_to(msg_obj, f"✅ `{file_name}` running! PID: `{process.pid}`", parse_mode='Markdown')
    except Exception as e:
        if key in bot_scripts:
            kill_process_tree(bot_scripts[key]); del bot_scripts[key]
        bot.reply_to(msg_obj, f"❌ JS error: {e}")

# ══════════════════════════════════════════════════════
#  DATABASE OPERATIONS
# ══════════════════════════════════════════════════════
def save_user_file(user_id, file_name, file_type='py'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute(
                'INSERT OR REPLACE INTO user_files VALUES (?,?,?)',
                (user_id, file_name, file_type)
            )
            conn.commit()
            if user_id not in user_files: user_files[user_id] = []
            user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
            user_files[user_id].append((file_name, file_type))
        except Exception as e: logger.error(f"save_user_file: {e}")
        finally: conn.close()

def remove_user_file_db(user_id, file_name):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute('DELETE FROM user_files WHERE user_id=? AND file_name=?', (user_id, file_name))
            conn.commit()
            if user_id in user_files:
                user_files[user_id] = [f for f in user_files[user_id] if f[0] != file_name]
                if not user_files[user_id]: del user_files[user_id]
        except Exception as e: logger.error(f"remove_user_file_db: {e}")
        finally: conn.close()

def add_active_user(user_id):
    active_users.add(user_id)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute('INSERT OR IGNORE INTO active_users VALUES (?)', (user_id,))
            conn.commit()
        except Exception as e: logger.error(f"add_active_user: {e}")
        finally: conn.close()

def add_admin_db(admin_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute('INSERT OR IGNORE INTO admins VALUES (?)', (admin_id,))
            conn.commit()
            admin_ids.add(admin_id)
        except Exception as e: logger.error(f"add_admin_db: {e}")
        finally: conn.close()

def remove_admin_db(admin_id):
    if admin_id == OWNER_ID: return False
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        removed = False
        try:
            conn.execute('DELETE FROM admins WHERE user_id=?', (admin_id,))
            conn.commit()
            removed = True
            admin_ids.discard(admin_id)
        except Exception as e: logger.error(f"remove_admin_db: {e}")
        finally: conn.close()
        return removed

# ══════════════════════════════════════════════════════
#  FILE HANDLERS
# ══════════════════════════════════════════════════════
def handle_zip_file(content, zip_name, message):
    user_id = message.from_user.id
    user_folder = get_user_folder(user_id)
    if user_id != OWNER_ID:
        ok, reason = scan_file(content, zip_name, user_id)
        if not ok:
            bot.reply_to(message, f"🚨 Blocked: {reason}"); return
    tmp = None
    try:
        tmp = tempfile.mkdtemp(prefix=f"user_{user_id}_zip_")
        zip_path = os.path.join(tmp, zip_name)
        with open(zip_path, 'wb') as f: f.write(content)
        with zipfile.ZipFile(zip_path, 'r') as zr:
            if user_id != OWNER_ID:
                sus_ext = ['.exe', '.dll', '.bat', '.cmd', '.scr', '.com']
                for m in zr.infolist():
                    if any(m.filename.lower().endswith(e) for e in sus_ext):
                        bot.reply_to(message, f"🚨 ZIP has suspicious file: {m.filename}"); return
                    mp = os.path.abspath(os.path.join(tmp, m.filename))
                    if not mp.startswith(os.path.abspath(tmp)):
                        raise zipfile.BadZipFile(f"Path traversal: {m.filename}")
            zr.extractall(tmp)
        # Find the script root
        target = tmp
        root_files = os.listdir(target)
        if not any(f.endswith(('.py', '.js')) for f in root_files):
            for root, dirs, files in os.walk(tmp):
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('__')]
                if any(f.endswith(('.py', '.js')) for f in files):
                    target = root; break
        if target != tmp:
            for item in os.listdir(target):
                s = os.path.join(target, item); d = os.path.join(tmp, item)
                if os.path.exists(d):
                    shutil.rmtree(d) if os.path.isdir(d) else os.remove(d)
                shutil.move(s, d)
        items   = os.listdir(tmp)
        py_files = [f for f in items if f.endswith('.py')]
        js_files = [f for f in items if f.endswith('.js')]
        req_file = 'requirements.txt' if 'requirements.txt' in items else None
        pkg_json = 'package.json'     if 'package.json'      in items else None
        if req_file:
            req_src = os.path.join(tmp, req_file)
            req_dst = os.path.join(user_folder, 'requirements.txt')
            shutil.copy2(req_src, req_dst)
            if not install_requirements(user_folder, message):
                return
        if pkg_json:
            bot.reply_to(message, "🔄 Installing npm deps...")
            subprocess.run(
                ['npm', 'install'], cwd=tmp,
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
        main_py = next((f for f in py_files if f in ('main.py', 'bot.py', 'app.py', 'index.py')), None)
        if not main_py and py_files: main_py = py_files[0]
        main_js = next((f for f in js_files if f in ('main.js', 'bot.js', 'app.js', 'index.js')), None)
        if not main_js and js_files: main_js = js_files[0]
        if main_py:
            dst = os.path.join(user_folder, main_py)
            shutil.copy2(os.path.join(tmp, main_py), dst)
            for item in os.listdir(tmp):
                if item != main_py:
                    s = os.path.join(tmp, item); d = os.path.join(user_folder, item)
                    if os.path.isdir(s): shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        try: shutil.copy2(s, d)
                        except Exception: pass
            handle_py_file(dst, user_id, user_folder, main_py, message)
        elif main_js:
            dst = os.path.join(user_folder, main_js)
            shutil.copy2(os.path.join(tmp, main_js), dst)
            for item in os.listdir(tmp):
                if item != main_js:
                    s = os.path.join(tmp, item); d = os.path.join(user_folder, item)
                    if os.path.isdir(s): shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        try: shutil.copy2(s, d)
                        except Exception: pass
            handle_js_file(dst, user_id, user_folder, main_js, message)
        else:
            bot.reply_to(message, "❌ No `.py` or `.js` file found in ZIP.")
    except zipfile.BadZipFile as e:
        bot.reply_to(message, f"❌ Invalid ZIP: {e}")
    except Exception as e:
        bot.reply_to(message, f"❌ ZIP error: {e}")
    finally:
        if tmp and os.path.exists(tmp):
            try: shutil.rmtree(tmp)
            except: pass

def handle_js_file(path, owner_id, folder, name, msg):
    save_user_file(owner_id, name, 'js')
    threading.Thread(target=run_js_script, args=(path, owner_id, folder, name, msg)).start()

def handle_py_file(path, owner_id, folder, name, msg):
    save_user_file(owner_id, name, 'py')
    threading.Thread(target=run_script, args=(path, owner_id, folder, name, msg)).start()

# ══════════════════════════════════════════════════════
#  SEND COMMAND / LOGS
# ══════════════════════════════════════════════════════
def send_to_process_init(message):
    user_id = message.from_user.id
    running = [
        (k, v) for k, v in bot_scripts.items()
        if (user_id == v['script_owner_id'] or user_id in admin_ids)
        and is_bot_running(v['script_owner_id'], v['file_name'])
    ]
    if not running:
        bot.reply_to(message, "❌ No running scripts."); return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, info in running:
        markup.add(types.InlineKeyboardButton(
            f"{info['file_name']} (UID: {info['script_owner_id']})",
            callback_data=f'sendcmd_select_{key}'
        ))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='send_command'))
    bot.reply_to(message, "📝 Select script:", reply_markup=markup)

def process_send_command(message, script_key):
    if script_key not in bot_scripts:
        bot.reply_to(message, "❌ Script no longer running."); return
    info = bot_scripts[script_key]
    try:
        proc = info['process']
        if proc and proc.poll() is None:
            proc.stdin.write(message.text + '\n')
            proc.stdin.flush()
            bot.reply_to(message, f"✅ Sent to `{info['file_name']}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ `{info['file_name']}` not running.", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def view_all_logs(message):
    user_id = message.from_user.id
    folder  = get_user_folder(user_id)
    logs = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.endswith('.log'):
                p = os.path.join(folder, f)
                logs.append((f, os.path.getsize(p), p))
    if not logs:
        bot.reply_to(message, "📜 No log files yet."); return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for lf, sz, _ in sorted(logs):
        markup.add(types.InlineKeyboardButton(
            f"{lf} ({sz/1024:.1f} KB)", callback_data=f'viewlog_{user_id}_{lf}'
        ))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='send_command'))
    bot.reply_to(message, "📜 *Your Logs:*", reply_markup=markup, parse_mode='Markdown')

def send_log_file(message, log_path, log_filename):
    try:
        if os.path.getsize(log_path) > 50 * 1024 * 1024:
            bot.reply_to(message, "❌ Log too large (>50 MB)."); return
        with open(log_path, 'rb') as f:
            bot.send_document(message.chat.id, f, caption=f"📜 {log_filename}")
    except Exception as e:
        bot.reply_to(message, f"❌ Log send error: {e}")

# ══════════════════════════════════════════════════════
#  MENU BUILDERS — PREMIUM UI
# ══════════════════════════════════════════════════════
def create_main_menu_inline(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('📤 Upload File',  callback_data='upload'),
        types.InlineKeyboardButton('📂 My Files',     callback_data='check_files'),
    )
    markup.add(
        types.InlineKeyboardButton('⚡ Speed Test',   callback_data='speed'),
        types.InlineKeyboardButton('📊 Statistics',   callback_data='stats'),
    )
    markup.add(
        types.InlineKeyboardButton('💎 My Credits',   callback_data='my_credits'),
        types.InlineKeyboardButton('🔗 Refer Friends', callback_data='refer'),
    )
    markup.add(
        types.InlineKeyboardButton('📤 Send Command', callback_data='send_command'),
    )
    if user_id in admin_ids:
        markup.add(
            types.InlineKeyboardButton('💳 Credits Panel', callback_data='credits_panel'),
            types.InlineKeyboardButton('📢 Broadcast',     callback_data='broadcast'),
        )
        markup.add(
            types.InlineKeyboardButton('🔒 Lock Bot' if not bot_locked else '🔓 Unlock Bot',
                callback_data='lock_bot' if not bot_locked else 'unlock_bot'),
            types.InlineKeyboardButton('🟢 Run All',       callback_data='run_all_scripts'),
        )
        markup.add(
            types.InlineKeyboardButton('👑 Admin Panel',   callback_data='admin_panel'),
        )
    markup.add(
        types.InlineKeyboardButton(f'💬 Contact — {CREDIT}',
            url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}')
    )
    return markup

def create_reply_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    is_admin = user_id in admin_ids
    if is_admin:
        rows = [
            ["📤 Upload File",   "📂 My Files"],
            ["⚡ Speed Test",    "📊 Statistics"],
            ["💎 My Credits",   "🔗 Refer Friends"],
            ["💳 Credits Panel", "📢 Broadcast"],
            ["🔒 Lock Bot",     "🟢 Run All Scripts"],
            ["📤 Send Command", "👑 Admin Panel"],
            ["📞 Contact Owner"],
        ]
    else:
        rows = [
            ["📤 Upload File",  "📂 My Files"],
            ["⚡ Speed Test",   "📊 Statistics"],
            ["💎 My Credits",  "🔗 Refer Friends"],
            ["📤 Send Command", "📞 Contact Owner"],
        ]
    for row in rows:
        markup.add(*[types.KeyboardButton(t) for t in row])
    return markup

def create_control_buttons(owner_id, file_name, is_running=True):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_running:
        markup.row(
            types.InlineKeyboardButton("🔴 Stop",    callback_data=f'stop_{owner_id}_{file_name}'),
            types.InlineKeyboardButton("🔄 Restart", callback_data=f'restart_{owner_id}_{file_name}'),
        )
        markup.row(
            types.InlineKeyboardButton("🗑️ Delete",  callback_data=f'delete_{owner_id}_{file_name}'),
            types.InlineKeyboardButton("📜 Logs",    callback_data=f'logs_{owner_id}_{file_name}'),
        )
    else:
        markup.row(
            types.InlineKeyboardButton("🟢 Start",     callback_data=f'start_{owner_id}_{file_name}'),
            types.InlineKeyboardButton("🗑️ Delete",    callback_data=f'delete_{owner_id}_{file_name}'),
        )
        markup.row(
            types.InlineKeyboardButton("📜 View Logs", callback_data=f'logs_{owner_id}_{file_name}'),
        )
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='check_files'))
    return markup

def create_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('➕ Add Admin',    callback_data='add_admin'),
        types.InlineKeyboardButton('➖ Remove Admin', callback_data='remove_admin'),
    )
    markup.row(types.InlineKeyboardButton('📋 List Admins', callback_data='list_admins'))
    markup.row(types.InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
    return markup

def create_credits_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('➕ Add Credits',    callback_data='add_credits_init'),
        types.InlineKeyboardButton('➖ Remove Credits', callback_data='remove_credits_init'),
    )
    markup.row(types.InlineKeyboardButton('🔍 Check Credits', callback_data='check_credits_init'))
    markup.row(types.InlineKeyboardButton('📜 Credit History', callback_data='credit_history'))
    markup.row(types.InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
    return markup

def create_send_command_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton('📝 Send to Process', callback_data='send_to_process'),
        types.InlineKeyboardButton('🗂️ View All Logs',   callback_data='view_all_logs'),
    )
    markup.row(types.InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
    return markup

# ══════════════════════════════════════════════════════
#  LOGIC FUNCTIONS
# ══════════════════════════════════════════════════════
def _logic_send_welcome(message, referrer_id=None):
    user_id  = message.from_user.id
    chat_id  = message.chat.id
    name     = message.from_user.first_name or "User"
    username = message.from_user.username or "Not set"

    if bot_locked and user_id not in admin_ids:
        bot.send_message(chat_id, "⚠️ Bot is currently locked by admin."); return

    # Register user & handle referral
    is_new = user_id not in active_users
    if is_new:
        add_active_user(user_id)
        init_user_credits(user_id, referred_by=referrer_id)
        join_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            bot.send_message(
                OWNER_ID,
                f"⚡ *New User Alert!*\n\n"
                f"👤 Name: `{name}`\n"
                f"✳️ Username: @{username}\n"
                f"🆔 ID: `{user_id}`\n"
                f"🕐 Time: `{join_time}`\n"
                f"🔗 Referred by: `{referrer_id or 'None'}`",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Owner notify failed: {e}")
    else:
        # Ensure credits entry exists even for returning users
        init_user_credits(user_id)

    credits    = get_credits(user_id)
    credits_str = "∞" if credits == float('inf') else str(credits)
    status     = get_user_status_str(user_id)
    file_count = get_user_file_count(user_id)
    ref_code   = get_referral_code(user_id)
    bot_link   = f"https://t.me/{BOT_USERNAME.lstrip('@')}?start={ref_code}"

    welcome_text = (
        f"╔══════════════════════╗\n"
        f"║   ⚡ {BOT_NAME} ⚡   ║\n"
        f"╚══════════════════════╝\n\n"
        f"👋 Welcome, *{name}*!\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Username: `@{username}`\n"
        f"🔰 Status: {status}\n"
        f"💎 Credits: `{credits_str}`\n"
        f"📁 Files Hosted: `{file_count}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 Host Python & JS bots here.\n"
        f"Upload `.py`, `.js`, or `.zip` archives.\n\n"
        f"🔗 *Your Referral Link:*\n"
        f"`{bot_link}`\n"
        f"Refer friends → get *+{REFERRAL_BONUS} credits* each!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Dev: {CREDIT}"
    )

    reply_kb = create_reply_keyboard(user_id)
    try:
        bot.send_video(
            chat_id, WELCOME_VIDEO_URL,
            caption=welcome_text,
            reply_markup=reply_kb,
            parse_mode='Markdown'
        )
    except Exception:
        bot.send_message(chat_id, welcome_text, reply_markup=reply_kb, parse_mode='Markdown')

def _logic_upload_file(message):
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot locked. Cannot accept files."); return
    credits = get_credits(user_id)
    if credits == float('inf'):
        bot.reply_to(message, "📤 Send your `.py`, `.js`, or `.zip` file now.", parse_mode='Markdown')
        return
    if credits <= 0:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🔗 Get Credits via Referral', callback_data='refer'))
        markup.add(types.InlineKeyboardButton(f'💬 Contact Owner', url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}'))
        bot.reply_to(
            message,
            "❌ *No credits left!*\n\n"
            "Ways to get more credits:\n"
            f"• 🔗 Refer friends → *+{REFERRAL_BONUS} credits* each\n"
            f"• 💬 Contact the owner to refill\n",
            reply_markup=markup, parse_mode='Markdown'
        )
        return
    bot.reply_to(
        message,
        f"📤 Send your `.py`, `.js`, or `.zip` file now.\n"
        f"💎 You have `{credits}` credit(s). This upload costs `1`.",
        parse_mode='Markdown'
    )

def _logic_check_files(message):
    user_id = message.from_user.id
    files   = user_files.get(user_id, [])
    if not files:
        bot.reply_to(message, "📂 No files uploaded yet."); return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fn, ft in sorted(files):
        icon = "🟢" if is_bot_running(user_id, fn) else "🔴"
        markup.add(types.InlineKeyboardButton(f"{icon} {fn} [{ft}]", callback_data=f'file_{user_id}_{fn}'))
    bot.reply_to(message, "📂 *Your Files* — tap to manage:", reply_markup=markup, parse_mode='Markdown')

def _logic_bot_speed(message):
    t0   = time.time()
    wait = bot.reply_to(message, "⏱️ Pinging...")
    try:
        ms  = round((time.time() - t0) * 1000, 2)
        uid = message.from_user.id
        lvl = get_user_status_str(uid)
        text = (
            f"⚡ *Speed Report*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📶 Ping: `{ms} ms`\n"
            f"🚦 Bot: {'🔒 Locked' if bot_locked else '🟢 Online'}\n"
            f"👤 You: {lvl}\n"
            f"━━━━━━━━━━━━━━━"
        )
        bot.edit_message_text(text, message.chat.id, wait.message_id, parse_mode='Markdown')
    except Exception as e:
        bot.edit_message_text(f"❌ Speed test failed: {e}", message.chat.id, wait.message_id)

def _logic_statistics(message):
    user_id = message.from_user.id
    running_total = sum(
        1 for v in bot_scripts.values()
        if is_bot_running(v['script_owner_id'], v['file_name'])
    )
    user_running = sum(
        1 for v in bot_scripts.values()
        if v['script_owner_id'] == user_id and is_bot_running(user_id, v['file_name'])
    )
    text = (
        f"📊 *JexxyCloud Stats*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: `{len(active_users)}`\n"
        f"📁 Total Files: `{sum(len(v) for v in user_files.values())}`\n"
        f"🟢 Active Scripts: `{running_total}`\n"
        f"🤖 Your Scripts: `{user_running}`\n"
    )
    if user_id in admin_ids:
        text += f"🔒 Bot Lock: `{'On' if bot_locked else 'Off'}`\n"
        text += f"💎 Credit Records: `{len(user_credits_cache)}`\n"
    text += f"━━━━━━━━━━━━━━━\nDev: {CREDIT}"
    bot.reply_to(message, text, parse_mode='Markdown')

def _logic_my_credits(message):
    user_id = message.from_user.id
    credits = get_credits(user_id)
    credits_str = "∞ (Unlimited)" if credits == float('inf') else str(credits)
    status  = get_user_status_str(user_id)
    ref_code = get_referral_code(user_id)
    bot_link = f"https://t.me/{BOT_USERNAME.lstrip('@')}?start={ref_code}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔗 Share Referral Link', url=bot_link))
    markup.add(types.InlineKeyboardButton(f'💬 Refill Credits — {CREDIT}', url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}'))
    bot.reply_to(
        message,
        f"💎 *Your Credit Balance*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔰 Status: {status}\n"
        f"💰 Credits: `{credits_str}`\n\n"
        f"📌 *How to earn more:*\n"
        f"• Share referral link → `+{REFERRAL_BONUS}` per join\n"
        f"• Contact owner to refill\n\n"
        f"🔗 Your referral link:\n`{bot_link}`\n"
        f"━━━━━━━━━━━━━━━",
        reply_markup=markup, parse_mode='Markdown'
    )

def _logic_refer(message):
    user_id  = message.from_user.id
    ref_code = get_referral_code(user_id)
    bot_link = f"https://t.me/{BOT_USERNAME.lstrip('@')}?start={ref_code}"
    markup   = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔗 Share This Link', url=bot_link))
    bot.reply_to(
        message,
        f"🔗 *Your Referral Link*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"`{bot_link}`\n\n"
        f"📌 For every friend who joins using your link:\n"
        f"✅ You earn *+{REFERRAL_BONUS} credits*\n"
        f"✅ They get *{FREE_CREDITS} free credits* to start\n\n"
        f"Share & stack that bag! 💰",
        reply_markup=markup, parse_mode='Markdown'
    )

def _logic_contact_owner(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f'💬 DM {CREDIT}', url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}'))
    bot.reply_to(message, "📞 Tap below to reach the developer:", reply_markup=markup)

def _logic_credits_panel(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin only."); return
    bot.reply_to(message, "💳 *Credits Manager*", reply_markup=create_credits_panel(), parse_mode='Markdown')

def _logic_broadcast_init(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin only."); return
    msg = bot.reply_to(message, "📢 Send your broadcast message. /cancel to abort.")
    bot.register_next_step_handler(msg, process_broadcast_message)

def _logic_toggle_lock_bot(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin only."); return
    global bot_locked
    bot_locked = not bot_locked
    status = "🔒 Locked" if bot_locked else "🟢 Unlocked"
    bot.reply_to(message, f"Bot is now *{status}*.", parse_mode='Markdown')

def _logic_admin_panel(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin only."); return
    bot.reply_to(message, "👑 *Admin Panel*", reply_markup=create_admin_panel(), parse_mode='Markdown')

def _logic_run_all_scripts(moc):
    if isinstance(moc, types.Message):
        uid = moc.from_user.id; msg_for_script = moc
        reply = lambda t, **kw: bot.reply_to(moc, t, **kw)
    else:
        uid = moc.from_user.id
        bot.answer_callback_query(moc.id)
        msg_for_script = moc.message
        reply = lambda t, **kw: bot.send_message(moc.message.chat.id, t, **kw)
    if uid not in admin_ids:
        reply("⚠️ Admin only."); return
    reply("⏳ Starting all stopped scripts...")
    started = 0; skipped = 0
    for tuid, files in dict(user_files).items():
        folder = get_user_folder(tuid)
        for fname, ftype in files:
            if is_bot_running(tuid, fname): continue
            fpath = os.path.join(folder, fname)
            if not os.path.exists(fpath): skipped += 1; continue
            try:
                fn = run_script if ftype == 'py' else run_js_script
                threading.Thread(target=fn, args=(fpath, tuid, folder, fname, msg_for_script)).start()
                started += 1; time.sleep(0.5)
            except Exception as e:
                logger.error(f"Run all error {fname}: {e}"); skipped += 1
    reply(f"✅ Done! Started: `{started}` | Skipped: `{skipped}`", parse_mode='Markdown')

def _logic_send_command(message):
    if bot_locked and message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot locked."); return
    bot.reply_to(message, "📤 *Send Command*", reply_markup=create_send_command_menu(), parse_mode='Markdown')

# ══════════════════════════════════════════════════════
#  BROADCAST
# ══════════════════════════════════════════════════════
def process_broadcast_message(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin only."); return
    if message.text and message.text.lower() == '/cancel':
        bot.reply_to(message, "Broadcast cancelled."); return
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_broadcast_{message.message_id}"),
        types.InlineKeyboardButton("❌ Cancel",  callback_data="cancel_broadcast")
    )
    preview = (message.text or "(media)")[:800]
    bot.reply_to(
        message,
        f"📢 Broadcast to *{len(active_users)}* users?\n\n```\n{preview}\n```",
        reply_markup=markup, parse_mode='Markdown'
    )

def handle_confirm_broadcast(call):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Admin only.", show_alert=True); return
    try:
        orig = call.message.reply_to_message
        if not orig: raise ValueError("Original not found.")
        text = photo = video = caption = None
        if orig.text:    text  = orig.text
        elif orig.photo: photo = orig.photo[-1].file_id; caption = orig.caption
        elif orig.video: video = orig.video.file_id;     caption = orig.caption
        else: raise ValueError("Unsupported media.")
        bot.answer_callback_query(call.id, "🚀 Broadcasting...")
        bot.edit_message_text(f"📢 Broadcasting to {len(active_users)} users...",
                              call.message.chat.id, call.message.message_id)
        threading.Thread(
            target=execute_broadcast,
            args=(text, photo, video, caption, call.message.chat.id)
        ).start()
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {e}", call.message.chat.id, call.message.message_id)

def handle_cancel_broadcast(call):
    bot.answer_callback_query(call.id, "Broadcast cancelled.")
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

def execute_broadcast(text, photo, video, caption, admin_cid):
    sent = failed = blocked = 0
    users = list(active_users)
    for i, uid in enumerate(users):
        try:
            if text:  bot.send_message(uid, text, parse_mode='Markdown')
            elif photo: bot.send_photo(uid, photo, caption=caption, parse_mode='Markdown' if caption else None)
            elif video: bot.send_video(uid, video, caption=caption, parse_mode='Markdown' if caption else None)
            sent += 1
        except telebot.apihelper.ApiTelegramException as e:
            s = str(e).lower()
            if any(x in s for x in ["blocked", "deactivated", "not found", "kicked"]):
                blocked += 1
            elif "flood" in s or "too many" in s:
                m = re.search(r"retry after (\d+)", s)
                wait = int(m.group(1)) + 1 if m else 5
                time.sleep(wait)
                try:
                    if text:  bot.send_message(uid, text, parse_mode='Markdown')
                    elif photo: bot.send_photo(uid, photo, caption=caption)
                    elif video: bot.send_video(uid, video, caption=caption)
                    sent += 1
                except: failed += 1
            else: failed += 1
        except Exception: failed += 1
        if (i + 1) % 25 == 0: time.sleep(1.5)
        elif i % 5 == 0:      time.sleep(0.2)
    result = (
        f"📢 *Broadcast Complete!*\n"
        f"✅ Sent: `{sent}` | ❌ Failed: `{failed}` | 🚫 Blocked: `{blocked}`\n"
        f"👥 Total: `{len(users)}`"
    )
    try: bot.send_message(admin_cid, result, parse_mode='Markdown')
    except Exception as e: logger.error(f"Broadcast result error: {e}")

# ══════════════════════════════════════════════════════
#  BUTTON TEXT MAP
# ══════════════════════════════════════════════════════
BUTTON_MAP = {
    "📤 Upload File":    _logic_upload_file,
    "📂 My Files":       _logic_check_files,
    "⚡ Speed Test":     _logic_bot_speed,
    "📊 Statistics":     _logic_statistics,
    "💎 My Credits":     _logic_my_credits,
    "🔗 Refer Friends":  _logic_refer,
    "📤 Send Command":   _logic_send_command,
    "📞 Contact Owner":  _logic_contact_owner,
    "💳 Credits Panel":  _logic_credits_panel,
    "📢 Broadcast":      _logic_broadcast_init,
    "🔒 Lock Bot":       _logic_toggle_lock_bot,
    "🟢 Run All Scripts":_logic_run_all_scripts,
    "👑 Admin Panel":    _logic_admin_panel,
}

# ══════════════════════════════════════════════════════
#  COMMAND & TEXT HANDLERS
# ══════════════════════════════════════════════════════
@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    # Handle referral deep link: /start ref_USERID
    referrer_id = None
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        if param.startswith('ref_'):
            try:
                rid = int(param[4:])
                if rid != message.from_user.id:
                    referrer_id = rid
            except ValueError:
                pass
    _logic_send_welcome(message, referrer_id=referrer_id)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['mycredits'])
def cmd_mycredits(message):
    _logic_my_credits(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['refer'])
def cmd_refer(message):
    _logic_refer(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['addcredits'])
def cmd_addcredits(message):
    """Admin: /addcredits USER_ID AMOUNT"""
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin only."); return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "Usage: `/addcredits USER_ID AMOUNT`", parse_mode='Markdown'); return
    try:
        uid = int(parts[1]); amount = int(parts[2])
        if amount <= 0: raise ValueError("Amount must be positive")
        add_credits(uid, amount, admin_id=message.from_user.id, action='admin_add')
        new_bal = get_credits(uid)
        bot.reply_to(message, f"✅ Added `{amount}` credits to `{uid}`.\nNew balance: `{new_bal}`", parse_mode='Markdown')
        try:
            bot.send_message(uid,
                f"🎉 *Credits Added!*\n\n"
                f"✅ +`{amount}` credits from admin.\n"
                f"💰 New balance: `{new_bal}`",
                parse_mode='Markdown'
            )
        except: pass
    except (ValueError, IndexError) as e:
        bot.reply_to(message, f"⚠️ Error: {e}")
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['status'])
def cmd_status(message):
    _logic_statistics(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['ping'])
def cmd_ping(message):
    t0  = time.time()
    msg = bot.reply_to(message, "🏓 Pong!")
    lat = round((time.time() - t0) * 1000, 2)
    bot.edit_message_text(f"🏓 Pong! `{lat} ms`", message.chat.id, msg.message_id, parse_mode='Markdown')
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['uploadfile'])
def cmd_upload(m):
    _logic_upload_file(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['checkfiles'])
def cmd_check(m):
    _logic_check_files(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['speed'])
def cmd_speed(m):
    _logic_bot_speed(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['stats'])
def cmd_stats(m):
    _logic_statistics(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['sendcommand'])
def cmd_sendcmd(m):
    _logic_send_command(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['contact'])
def cmd_contact(m):
    _logic_contact_owner(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['lock'])
def cmd_lock(m):
    _logic_toggle_lock_bot(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['runall'])
def cmd_runall(m):
    _logic_run_all_scripts(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['admin'])
def cmd_admin(m):
    _logic_admin_panel(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(func=lambda m: m.text in BUTTON_MAP)
def handle_buttons(message):
    fn = BUTTON_MAP.get(message.text)
    if fn: fn(message)
    threading.Thread(target=auto_react, args=(message,)).start()

# ══════════════════════════════════════════════════════
#  FILE UPLOAD HANDLER
# ══════════════════════════════════════════════════════
@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    threading.Thread(target=auto_react, args=(message,)).start()

    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot locked."); return

    # Credit check
    credits = get_credits(user_id)
    if credits != float('inf') and credits <= 0:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🔗 Get Credits', callback_data='refer'))
        markup.add(types.InlineKeyboardButton(f'💬 Contact Owner', url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}'))
        bot.reply_to(
            message,
            f"❌ *No credits!*\n\n"
            f"Refer friends to earn credits or contact the owner.",
            reply_markup=markup, parse_mode='Markdown'
        )
        return

    doc = message.document
    if not doc:
        bot.reply_to(message, "❌ No document found."); return

    fname_orig = doc.file_name or 'uploaded_file'
    lower_name = fname_orig.lower()
    allowed = lower_name.endswith(('.py', '.js', '.zip')) or lower_name == 'requirements.txt'
    if not allowed:
        bot.reply_to(
            message,
            f"❌ Only `.py`, `.js`, `.zip`, or `requirements.txt` allowed.\n"
            f"Got: `{fname_orig}`",
            parse_mode='Markdown'
        )
        return

    if doc.file_size > 50 * 1024 * 1024:
        bot.reply_to(message, "❌ File too large (>50 MB)."); return

    try:
        file_info = bot.get_file(doc.file_id)
        content   = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.reply_to(message, f"❌ Download failed: {e}"); return

    user_folder = get_user_folder(user_id)
    fname       = fname_orig

    if fname.lower().endswith('.zip'):
        # Deduct credit BEFORE processing
        if not deduct_credit(user_id):
            bot.reply_to(message, "❌ Failed to deduct credit."); return
        new_bal = get_credits(user_id)
        bal_str = "∞" if new_bal == float('inf') else str(new_bal)
        bot.reply_to(message, f"📦 Processing ZIP... Credits remaining: `{bal_str}`", parse_mode='Markdown')
        handle_zip_file(content, fname, message)
        return

    # Security scan
    if user_id != OWNER_ID:
        ok, reason = scan_file(content, fname, user_id)
        if not ok:
            bot.reply_to(message, f"🚨 Blocked: {reason}"); return

    # Reserve/deduct credit before writing so a zero-credit user cannot leave an orphan file.
    if not deduct_credit(user_id):
        bot.reply_to(message, "❌ No credits left. Refer friends or contact the owner to get credits.")
        return

    # Save file. If storage fails, restore the consumed credit for normal users.
    dest = os.path.join(user_folder, fname)
    try:
        with open(dest, 'wb') as f:
            f.write(content)
    except Exception as e:
        if user_id != OWNER_ID and user_id not in admin_ids:
            add_credits(user_id, 1, action='upload_refund')
        bot.reply_to(message, f"❌ File save failed: {e}")
        return
    new_bal = get_credits(user_id)
    bal_str = "∞" if new_bal == float('inf') else str(new_bal)
    bot.reply_to(message, f"💾 File saved. Credits remaining: `{bal_str}`\n⚙️ Starting...", parse_mode='Markdown')

    if fname.lower().endswith('.py'):
        handle_py_file(dest, user_id, user_folder, fname, message)
    elif fname.lower().endswith('.js'):
        handle_js_file(dest, user_id, user_folder, fname, message)
    elif fname.lower() == 'requirements.txt':
        # Install immediately into the private writable package directory; do not execute the text file.
        if install_requirements(user_folder, message):
            bot.reply_to(message, "✅ `requirements.txt` saved and installed. Now upload/start your `.py` or `.js` bot.", parse_mode='Markdown')

# ══════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ══════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data    = call.data

    if bot_locked and user_id not in admin_ids and data not in ['speed', 'stats', 'my_credits', 'refer', 'back_to_main']:
        bot.answer_callback_query(call.id, "⚠️ Bot locked.", show_alert=True); return

    try:
        if   data == 'upload':              upload_callback(call)
        elif data == 'check_files':         check_files_callback(call)
        elif data.startswith('file_'):      file_control_callback(call)
        elif data.startswith('start_'):     start_bot_callback(call)
        elif data.startswith('stop_'):      stop_bot_callback(call)
        elif data.startswith('restart_'):   restart_bot_callback(call)
        elif data.startswith('delete_'):    delete_bot_callback(call)
        elif data.startswith('logs_'):      logs_bot_callback(call)
        elif data == 'speed':               speed_callback(call)
        elif data == 'stats':               stats_callback(call)
        elif data == 'my_credits':          my_credits_callback(call)
        elif data == 'refer':               refer_callback(call)
        elif data == 'back_to_main':        back_to_main_callback(call)
        elif data == 'send_command':        send_command_callback(call)
        elif data == 'send_to_process':     send_to_process_callback(call)
        elif data.startswith('sendcmd_select_'): sendcmd_select_callback(call)
        elif data == 'view_all_logs':       view_all_logs_callback(call)
        elif data.startswith('viewlog_'):   viewlog_callback(call)
        elif data == 'credits_panel':       _admin_cb(call, credits_panel_callback)
        elif data == 'add_credits_init':    _admin_cb(call, add_credits_init_callback)
        elif data == 'remove_credits_init': _admin_cb(call, remove_credits_init_callback)
        elif data == 'check_credits_init':  _admin_cb(call, check_credits_init_callback)
        elif data == 'credit_history':       _admin_cb(call, credit_history_callback)
        elif data == 'broadcast':           _admin_cb(call, broadcast_init_callback)
        elif data == 'lock_bot':            _admin_cb(call, lock_bot_callback)
        elif data == 'unlock_bot':          _admin_cb(call, unlock_bot_callback)
        elif data == 'run_all_scripts':     _admin_cb(call, run_all_scripts_callback)
        elif data == 'admin_panel':         _admin_cb(call, admin_panel_callback)
        elif data == 'add_admin':           _owner_cb(call, add_admin_init_callback)
        elif data == 'remove_admin':        _owner_cb(call, remove_admin_init_callback)
        elif data == 'list_admins':         _admin_cb(call, list_admins_callback)
        elif data.startswith('confirm_broadcast_'): handle_confirm_broadcast(call)
        elif data == 'cancel_broadcast':    handle_cancel_broadcast(call)
        else:
            bot.answer_callback_query(call.id, "Unknown action.")
    except Exception as e:
        logger.error(f"Callback '{data}' for {user_id}: {e}", exc_info=True)
        try: bot.answer_callback_query(call.id, "Error.", show_alert=True)
        except: pass

def _admin_cb(call, fn):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Admin only.", show_alert=True); return
    fn(call)

def _owner_cb(call, fn):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "⚠️ Owner only.", show_alert=True); return
    fn(call)

# ══════════════════════════════════════════════════════
#  CALLBACK IMPLEMENTATIONS
# ══════════════════════════════════════════════════════
def upload_callback(call):
    user_id = call.from_user.id
    credits = get_credits(user_id)
    if credits != float('inf') and credits <= 0:
        bot.answer_callback_query(call.id, "❌ No credits left! Refer friends or contact owner.", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    credits_str = "∞" if credits == float('inf') else str(credits)
    bot.send_message(
        call.message.chat.id,
        f"📤 Send your `.py`, `.js`, `.zip`, or `requirements.txt` file.\n💎 Credits: `{credits_str}`",
        parse_mode='Markdown'
    )

def check_files_callback(call):
    user_id = call.from_user.id
    files   = user_files.get(user_id, [])
    if not files:
        bot.answer_callback_query(call.id, "⚠️ No files yet.", show_alert=True)
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='back_to_main'))
            bot.edit_message_text("📂 No files uploaded yet.",
                call.message.chat.id, call.message.message_id, reply_markup=markup)
        except: pass
        return
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fn, ft in sorted(files):
        icon = "🟢" if is_bot_running(user_id, fn) else "🔴"
        markup.add(types.InlineKeyboardButton(f"{icon} {fn} [{ft}]", callback_data=f'file_{user_id}_{fn}'))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='back_to_main'))
    try:
        bot.edit_message_text("📂 *Your Files:*",
            call.message.chat.id, call.message.message_id,
            reply_markup=markup, parse_mode='Markdown')
    except telebot.apihelper.ApiTelegramException as e:
        if "not modified" not in str(e): logger.error(f"check_files CB: {e}")

def file_control_callback(call):
    try:
        _, oid_str, fname = call.data.split('_', 2)
        oid = int(oid_str); uid = call.from_user.id
        if not (uid == oid or uid in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return
        files = user_files.get(oid, [])
        if not any(f[0] == fname for f in files):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); return
        bot.answer_callback_query(call.id)
        running = is_bot_running(oid, fname)
        ft      = next((f[1] for f in files if f[0] == fname), '?')
        status  = "🟢 Running" if running else "🔴 Stopped"
        try:
            bot.edit_message_text(
                f"⚙️ *{fname}* `[{ft}]`\nOwner: `{oid}` | Status: {status}",
                call.message.chat.id, call.message.message_id,
                reply_markup=create_control_buttons(oid, fname, running),
                parse_mode='Markdown'
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "not modified" not in str(e): raise
    except Exception as e:
        logger.error(f"file_control CB: {e}")
        bot.answer_callback_query(call.id, "Error.", show_alert=True)

def start_bot_callback(call):
    try:
        _, oid_str, fname = call.data.split('_', 2)
        oid = int(oid_str); uid = call.from_user.id
        if not (uid == oid or uid in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return
        files = user_files.get(oid, [])
        fi = next((f for f in files if f[0] == fname), None)
        if not fi:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); return
        ft = fi[1]; folder = get_user_folder(oid); fpath = os.path.join(folder, fname)
        if not os.path.exists(fpath):
            bot.answer_callback_query(call.id, "⚠️ File missing. Re-upload.", show_alert=True)
            remove_user_file_db(oid, fname); return
        if is_bot_running(oid, fname):
            bot.answer_callback_query(call.id, "⚠️ Already running.", show_alert=True); return
        bot.answer_callback_query(call.id, f"▶️ Starting {fname}...")
        fn = run_script if ft == 'py' else run_js_script
        threading.Thread(target=fn, args=(fpath, oid, folder, fname, call.message)).start()
        time.sleep(3.5)
        running = is_bot_running(oid, fname)
        status  = "🟢 Running" if running else "🟡 Starting..."
        try:
            bot.edit_message_text(
                f"⚙️ *{fname}* `[{ft}]`\nStatus: {status}",
                call.message.chat.id, call.message.message_id,
                reply_markup=create_control_buttons(oid, fname, running),
                parse_mode='Markdown'
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "not modified" not in str(e): raise
    except Exception as e:
        logger.error(f"start_bot CB: {e}")
        bot.answer_callback_query(call.id, "Error starting.", show_alert=True)

def stop_bot_callback(call):
    try:
        _, oid_str, fname = call.data.split('_', 2)
        oid = int(oid_str); uid = call.from_user.id
        if not (uid == oid or uid in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return
        files = user_files.get(oid, [])
        fi = next((f for f in files if f[0] == fname), None)
        if not fi:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); return
        ft = fi[1]; key = f"{oid}_{fname}"
        if not is_bot_running(oid, fname):
            bot.answer_callback_query(call.id, "⚠️ Not running.", show_alert=True); return
        bot.answer_callback_query(call.id, f"⏹️ Stopping {fname}...")
        info = bot_scripts.get(key)
        if info: kill_process_tree(info)
        bot_scripts.pop(key, None)
        try:
            bot.edit_message_text(
                f"⚙️ *{fname}* `[{ft}]`\nStatus: 🔴 Stopped",
                call.message.chat.id, call.message.message_id,
                reply_markup=create_control_buttons(oid, fname, False),
                parse_mode='Markdown'
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "not modified" not in str(e): raise
    except Exception as e:
        logger.error(f"stop_bot CB: {e}")
        bot.answer_callback_query(call.id, "Error stopping.", show_alert=True)

def restart_bot_callback(call):
    try:
        _, oid_str, fname = call.data.split('_', 2)
        oid = int(oid_str); uid = call.from_user.id
        if not (uid == oid or uid in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return
        files = user_files.get(oid, [])
        fi = next((f for f in files if f[0] == fname), None)
        if not fi:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); return
        ft = fi[1]; folder = get_user_folder(oid); fpath = os.path.join(folder, fname)
        if not os.path.exists(fpath):
            bot.answer_callback_query(call.id, "⚠️ File missing. Re-upload.", show_alert=True)
            remove_user_file_db(oid, fname); return
        bot.answer_callback_query(call.id, f"🔄 Restarting {fname}...")
        key = f"{oid}_{fname}"
        if is_bot_running(oid, fname):
            info = bot_scripts.get(key)
            if info: kill_process_tree(info)
            bot_scripts.pop(key, None)
            time.sleep(1.5)
        fn = run_script if ft == 'py' else run_js_script
        threading.Thread(target=fn, args=(fpath, oid, folder, fname, call.message)).start()
        time.sleep(3.5)
        running = is_bot_running(oid, fname)
        status  = "🟢 Running" if running else "🟡 Starting..."
        try:
            bot.edit_message_text(
                f"⚙️ *{fname}* `[{ft}]`\nStatus: {status}",
                call.message.chat.id, call.message.message_id,
                reply_markup=create_control_buttons(oid, fname, running),
                parse_mode='Markdown'
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "not modified" not in str(e): raise
    except Exception as e:
        logger.error(f"restart CB: {e}")
        bot.answer_callback_query(call.id, "Error restarting.", show_alert=True)

def delete_bot_callback(call):
    try:
        _, oid_str, fname = call.data.split('_', 2)
        oid = int(oid_str); uid = call.from_user.id
        if not (uid == oid or uid in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return
        if not any(f[0] == fname for f in user_files.get(oid, [])):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); return
        bot.answer_callback_query(call.id, f"🗑️ Deleting {fname}...")
        key = f"{oid}_{fname}"
        if is_bot_running(oid, fname):
            info = bot_scripts.get(key)
            if info: kill_process_tree(info)
            bot_scripts.pop(key, None)
        folder = get_user_folder(oid)
        for p in [
            os.path.join(folder, fname),
            os.path.join(folder, f"{os.path.splitext(fname)[0]}.log")
        ]:
            try:
                if os.path.exists(p): os.remove(p)
            except OSError as e: logger.error(f"Delete {p}: {e}")
        remove_user_file_db(oid, fname)
        try:
            bot.edit_message_text(
                f"🗑️ `{fname}` deleted.",
                call.message.chat.id, call.message.message_id,
                parse_mode='Markdown'
            )
        except: pass
    except Exception as e:
        logger.error(f"delete CB: {e}")
        bot.answer_callback_query(call.id, "Error deleting.", show_alert=True)

def logs_bot_callback(call):
    try:
        _, oid_str, fname = call.data.split('_', 2)
        oid = int(oid_str); uid = call.from_user.id
        if not (uid == oid or uid in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return
        if not any(f[0] == fname for f in user_files.get(oid, [])):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); return
        log_path = os.path.join(get_user_folder(oid), f"{os.path.splitext(fname)[0]}.log")
        if not os.path.exists(log_path):
            bot.answer_callback_query(call.id, "⚠️ No logs yet.", show_alert=True); return
        bot.answer_callback_query(call.id)
        size = os.path.getsize(log_path)
        if size == 0:
            content = "(Empty)"
        elif size > 100 * 1024:
            with open(log_path, 'rb') as f:
                f.seek(-100 * 1024, os.SEEK_END); raw = f.read()
            content = "(Last 100 KB)\n...\n" + raw.decode('utf-8', errors='ignore')
        else:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        if len(content) > 4000: content = "...\n" + content[-3900:]
        if not content.strip(): content = "(Empty)"
        bot.send_message(
            call.message.chat.id,
            f"📜 *Logs — `{fname}`*:\n```\n{content}\n```",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"logs CB: {e}")
        bot.answer_callback_query(call.id, "Error fetching logs.", show_alert=True)

def speed_callback(call):
    uid = call.from_user.id; cid = call.message.chat.id
    t0  = time.time()
    try:
        bot.edit_message_text("⏱️ Testing...", cid, call.message.message_id)
        ms  = round((time.time() - t0) * 1000, 2)
        lvl = get_user_status_str(uid)
        text = (
            f"⚡ *Speed Report*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📶 Ping: `{ms} ms`\n"
            f"🚦 Bot: {'🔒 Locked' if bot_locked else '🟢 Online'}\n"
            f"👤 You: {lvl}\n"
            f"━━━━━━━━━━━━━━━"
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, cid, call.message.message_id,
                              reply_markup=create_main_menu_inline(uid), parse_mode='Markdown')
    except Exception as e:
        bot.answer_callback_query(call.id, "Error.", show_alert=True)

def stats_callback(call):
    bot.answer_callback_query(call.id)
    _logic_statistics(call.message)

def my_credits_callback(call):
    bot.answer_callback_query(call.id)
    _logic_my_credits(call.message)

def refer_callback(call):
    bot.answer_callback_query(call.id)
    _logic_refer(call.message)

def back_to_main_callback(call):
    uid = call.from_user.id
    credits = get_credits(uid)
    credits_str = "∞" if credits == float('inf') else str(credits)
    status = get_user_status_str(uid)
    files  = get_user_file_count(uid)
    text   = (
        f"⚡ *{BOT_NAME}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👋 {call.from_user.first_name}\n"
        f"🆔 `{uid}` | 🔰 {status}\n"
        f"💎 Credits: `{credits_str}`\n"
        f"📁 Files: `{files}`\n"
        f"━━━━━━━━━━━━━━━"
    )
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=create_main_menu_inline(uid), parse_mode='Markdown')
    except telebot.apihelper.ApiTelegramException as e:
        if "not modified" not in str(e): logger.error(f"back_to_main: {e}")

def send_command_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("📤 *Send Command*", call.message.chat.id, call.message.message_id,
                              reply_markup=create_send_command_menu(), parse_mode='Markdown')
    except Exception as e: logger.error(f"send_command CB: {e}")

def send_to_process_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📝 Type your command:")
    bot.register_next_step_handler(msg, send_to_process_init)

def sendcmd_select_callback(call):
    key = call.data.replace('sendcmd_select_', '')
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"📝 Command for `{key}`:", parse_mode='Markdown')
    bot.register_next_step_handler(msg, lambda m: process_send_command(m, key))

def view_all_logs_callback(call):
    bot.answer_callback_query(call.id)
    view_all_logs(call.message)

def viewlog_callback(call):
    try:
        _, uid_str, lf = call.data.split('_', 2)
        uid = int(uid_str); req = call.from_user.id
        if not (req == uid or req in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return
        lpath = os.path.join(get_user_folder(uid), lf)
        if not os.path.exists(lpath):
            bot.answer_callback_query(call.id, "❌ Log not found.", show_alert=True); return
        bot.answer_callback_query(call.id, "📜 Sending...")
        send_log_file(call.message, lpath, lf)
    except Exception as e:
        logger.error(f"viewlog CB: {e}")
        bot.answer_callback_query(call.id, "Error.", show_alert=True)

# Credits Panel Callbacks
def credits_panel_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("💳 *Credits Manager*",
            call.message.chat.id, call.message.message_id,
            reply_markup=create_credits_panel(), parse_mode='Markdown')
    except Exception as e: logger.error(f"credits panel CB: {e}")

def add_credits_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        "💳 Enter: `USER_ID AMOUNT`\n/cancel to abort.", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_add_credits)

def process_add_credits(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⚠️ Admin only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        parts = message.text.split()
        if len(parts) != 2: raise ValueError("Format: USER_ID AMOUNT")
        uid = int(parts[0]); amount = int(parts[1])
        if amount <= 0: raise ValueError("Amount must be positive")
        add_credits(uid, amount, admin_id=message.from_user.id, action='admin_add')
        new_bal = get_credits(uid)
        bot.reply_to(message, f"✅ Added `{amount}` credits to `{uid}`.\nBalance: `{new_bal}`", parse_mode='Markdown')
        try:
            bot.send_message(uid,
                f"🎉 *Credits Added!*\n+`{amount}` credits by admin.\n💰 Balance: `{new_bal}`",
                parse_mode='Markdown')
        except: pass
    except ValueError as e:
        msg = bot.reply_to(message, f"⚠️ {e}. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_add_credits)

def remove_credits_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        "💳 Enter: `USER_ID AMOUNT`\n/cancel to abort.", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_remove_credits)

def process_remove_credits(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⚠️ Admin only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        parts = message.text.split()
        if len(parts) != 2: raise ValueError("Format: USER_ID AMOUNT")
        uid = int(parts[0]); amount = int(parts[1])
        current = user_credits_cache.get(uid, 0)
        new_bal = max(0, current - amount)
        if uid == OWNER_ID or uid in admin_ids:
            raise ValueError("Cannot remove credits from an Admin/Owner")
        _set_credits_db(uid, new_bal)
        _record_credit_transaction(uid, message.from_user.id, 'admin_remove', amount, new_bal)
        bot.reply_to(message, f"✅ Removed `{amount}` from `{uid}`. New balance: `{new_bal}`", parse_mode='Markdown')
    except ValueError as e:
        msg = bot.reply_to(message, f"⚠️ {e}. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_remove_credits)

def check_credits_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        "💳 Enter User ID to check. /cancel to abort.")
    bot.register_next_step_handler(msg, process_check_credits)

def process_check_credits(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "⚠️ Admin only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        uid = int(message.text.strip())
        credits = get_credits(uid)
        credits_str = "∞ (Admin/Owner)" if credits == float('inf') else str(credits)
        status  = get_user_status_str(uid)
        bot.reply_to(message,
            f"💎 Credits for `{uid}`:\n"
            f"Balance: `{credits_str}`\n"
            f"Status: {status}",
            parse_mode='Markdown')
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Invalid ID. /cancel to abort.")
        bot.register_next_step_handler(msg, process_check_credits)

def credit_history_callback(call):
    bot.answer_callback_query(call.id)
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        rows = conn.execute(
            'SELECT user_id, admin_id, action, amount, balance_after, created_at '
            'FROM credit_transactions ORDER BY id DESC LIMIT 12'
        ).fetchall()
        conn.close()
        if not rows:
            text = "📜 *Credit History*\n\nNo transactions yet."
        else:
            lines = ["📜 *Credit History*", ""]
            for uid, aid, action, amount, balance, created in rows:
                bal = "∞" if balance is None else str(balance)
                who = "System" if aid is None else str(aid)
                lines.append(f"• `{uid}` — *{action}* `{amount}` | Bal: `{bal}` | By: `{who}`")
                lines.append(f"  🕐 {created}")
            text = "\n".join(lines)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=create_credits_panel(), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"credit history CB: {e}")
        try: bot.answer_callback_query(call.id, "Could not load history.", show_alert=True)
        except: pass

# Lock / Unlock / Broadcast / Admin panel callbacks
def lock_bot_callback(call):
    global bot_locked; bot_locked = True
    bot.answer_callback_query(call.id, "🔒 Bot locked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                       reply_markup=create_main_menu_inline(call.from_user.id))
    except: pass

def unlock_bot_callback(call):
    global bot_locked; bot_locked = False
    bot.answer_callback_query(call.id, "🟢 Bot unlocked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                       reply_markup=create_main_menu_inline(call.from_user.id))
    except: pass

def run_all_scripts_callback(call): _logic_run_all_scripts(call)

def broadcast_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📢 Send broadcast message. /cancel to abort.")
    bot.register_next_step_handler(msg, process_broadcast_message)

def admin_panel_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("👑 *Admin Panel*", call.message.chat.id, call.message.message_id,
                              reply_markup=create_admin_panel(), parse_mode='Markdown')
    except Exception as e: logger.error(f"admin panel CB: {e}")

def add_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        "👑 Enter Telegram User ID to promote.\n/cancel to abort.")
    bot.register_next_step_handler(msg, process_add_admin_id)

def process_add_admin_id(message):
    if message.from_user.id != OWNER_ID: bot.reply_to(message, "⚠️ Owner only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        nid = int(message.text.strip())
        if nid == OWNER_ID: bot.reply_to(message, "⚠️ Already owner."); return
        if nid in admin_ids: bot.reply_to(message, f"⚠️ `{nid}` already admin.", parse_mode='Markdown'); return
        add_admin_db(nid)
        bot.reply_to(message, f"✅ `{nid}` promoted to Admin.", parse_mode='Markdown')
        try: bot.send_message(nid, "🎉 You are now an Admin of JexxyCloudBot!")
        except: pass
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Invalid ID. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_add_admin_id)

def remove_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "👑 Enter Admin ID to demote. /cancel to abort.")
    bot.register_next_step_handler(msg, process_remove_admin_id)

def process_remove_admin_id(message):
    if message.from_user.id != OWNER_ID: bot.reply_to(message, "⚠️ Owner only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        rid = int(message.text.strip())
        if rid == OWNER_ID: bot.reply_to(message, "⚠️ Cannot demote owner."); return
        if rid not in admin_ids: bot.reply_to(message, f"⚠️ `{rid}` not admin.", parse_mode='Markdown'); return
        if remove_admin_db(rid):
            bot.reply_to(message, f"✅ Admin `{rid}` removed.", parse_mode='Markdown')
            try: bot.send_message(rid, "ℹ️ Admin access revoked.")
            except: pass
        else:
            bot.reply_to(message, f"❌ Failed to remove `{rid}`.", parse_mode='Markdown')
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Invalid ID. /cancel to abort.")
        bot.register_next_step_handler(msg, process_remove_admin_id)

def list_admins_callback(call):
    bot.answer_callback_query(call.id)
    lines = "\n".join(f"• `{a}` {'👑 Owner' if a == OWNER_ID else '🛡️ Admin'}" for a in sorted(admin_ids))
    try:
        bot.edit_message_text(
            f"👑 *Admin List:*\n\n{lines or '(none)'}",
            call.message.chat.id, call.message.message_id,
            reply_markup=create_admin_panel(), parse_mode='Markdown'
        )
    except Exception as e: logger.error(f"list_admins CB: {e}")

# ══════════════════════════════════════════════════════
#  CLEANUP & MAIN
# ══════════════════════════════════════════════════════
def cleanup():
    logger.warning("Shutting down — killing all scripts...")
    for key in list(bot_scripts.keys()):
        if key in bot_scripts:
            kill_process_tree(bot_scripts[key])
    logger.warning("Cleanup done.")

atexit.register(cleanup)

if __name__ == '__main__':
    logger.info(
        f"\n{'═'*50}\n"
        f"  ⚡ {BOT_NAME}\n"
        f"  Dev    : {CREDIT}\n"
        f"  Bot    : {BOT_USERNAME}\n"
        f"  Owner  : {OWNER_ID}\n"
        f"  Python : {sys.version.split()[0]}\n"
        f"{'═'*50}"
    )
    keep_alive()
    logger.info("🚀 Polling started...")
    while True:
        try:
            bot.infinity_polling(logger_level=logging.INFO, timeout=60, long_polling_timeout=30)
        except requests.exceptions.ReadTimeout:
            logger.warning("ReadTimeout — retry in 5s..."); time.sleep(5)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"ConnectionError: {e} — retry in 15s..."); time.sleep(15)
        except Exception as e:
            logger.critical(f"💥 Polling crash: {e}", exc_info=True)
            time.sleep(30)
        finally:
            time.sleep(1)
