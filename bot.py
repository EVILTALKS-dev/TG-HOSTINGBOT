# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════╗
# ║              EVIL HOST — Premium Edition            ║
# ║           Owner/Dev: @EVILTALKS                     ║
# ╚══════════════════════════════════════════════════════╝

# --- EVIL HOST dependency bootstrap (runs before third-party imports) ---
import os as _bootstrap_os
import sys as _bootstrap_sys
import subprocess as _bootstrap_subprocess
import importlib.util as _bootstrap_importlib
import importlib.metadata as _bootstrap_metadata

_BOOTSTRAP_DIR = _bootstrap_os.path.join(_bootstrap_os.path.abspath(_bootstrap_os.path.dirname(__file__)), ".evilhost_packages")
_bootstrap_os.makedirs(_BOOTSTRAP_DIR, exist_ok=True)
if _BOOTSTRAP_DIR not in _bootstrap_sys.path:
    _bootstrap_sys.path.insert(0, _BOOTSTRAP_DIR)

def _ensure_bootstrap_package(module_name, package_name):
    try:
        if _bootstrap_importlib.find_spec(module_name) is not None:
            if module_name == "telebot":
                try:
                    _v = _bootstrap_metadata.version("pyTelegramBotAPI")
                    _parts = tuple(int(x) for x in _v.split('.')[:3])
                    if _parts >= (4, 33, 0):
                        return True
                except Exception:
                    pass
            else:
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
            print(f"[EVIL HOST] Failed to install {package_name}:\n{result.stdout[-2000:]}")
            return False
        _bootstrap_importlib.invalidate_caches()
        return True
    except Exception as _e:
        print(f"[EVIL HOST] Dependency bootstrap error for {package_name}: {_e}")
        return False

_BOOTSTRAP_DEPS = {
    "telebot": "pyTelegramBotAPI>=4.33.0",
    "psutil": "psutil",
    "requests": "requests",
    "flask": "Flask",
}
for _mod, _pkg in _BOOTSTRAP_DEPS.items():
    if not _ensure_bootstrap_package(_mod, _pkg):
        raise RuntimeError(f"Required dependency '{_mod}' is unavailable. Install package '{_pkg}' and restart.")

# --- End EVIL HOST dependency bootstrap ---

import telebot
from html import escape as _html_escape
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
import uuid
from types import SimpleNamespace
import traceback
import platform
import contextlib

# --- Logger FIRST (fixes NameError in run_flask / scan_file) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)
logger = logging.getLogger(__name__)

# --- Flask Keep Alive ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "EVIL HOST Bot — Online & Blazing"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    try:
        app.run(host='0.0.0.0', port=port)
    except OSError as e:
        logger.warning(f"Keep-alive web server not started on port {port}: {e}")

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Flask Keep-Alive server started.")
# --- End Flask Keep Alive ---

# ══════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════
TOKEN          = '8843932282:AAGRejTsyr9msS0tdckQOd_dKUgXpTDV1qk'
OWNER_ID       = 8066849679
ADMIN_ID       = 8066849679
YOUR_USERNAME  = '@EVILTALKS'
BOT_NAME       = "𝗘𝘃𝗶𝗹 𝗛𝗼𝘀𝘁"
BOT_USERNAME   = "@EvilHostsBot"
CREDIT         = "@EVILTALKS"

def _pe(emoji_id, fallback="•"):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

PE_SIGNAL  = _pe("6239930832128056797", "⚡")
PE_WELCOME = _pe("4958832114540741368", "👋")
PE_WELCOME_TEXT = _pe("5244688958620710085", "✨")
PE_COMMANDS = _pe("6026239398650056451", "📋")
PE_FAST = _pe("5379879303439739169", "🚀")
PE_CREDITS = _pe("5823319287883896508", "💎")
PE_OWNER_ID = _pe("5798743308922523679", "👑")
PE_POWERED = _pe("5258093637450866522", "⚙️")
PE_ADMIN = _pe("6091259474025126934", "🛡️")
PE_ADMIN_ACTION = _pe("6129805886383723340", "🔧")
PE_USER_SEE = _pe("5774007681731795134", "👁️")
PE_BROADCAST = _pe("5388704211397522006", "📢")
PE_REDEEM = _pe("5294500065174365378", "🎟️")
PE_LOADING = _pe("5215579104807497179", "⏳")
PE_LOADING2 = _pe("5983299943417257042", "🔄")
PE_SUCCESS = _pe("5985652692142266021", "✅")

PE_OK = PE_SUCCESS
PE_DEV = PE_SIGNAL
PE_OWNER = PE_ADMIN
PE_VIEW = PE_USER_SEE
PE_TIME = PE_LOADING2
PE_PANEL = PE_ADMIN
PE_STATUS = PE_VIEW
PE_ACTION = PE_ADMIN_ACTION
PE_BRAND = PE_ADMIN
PE_DANCE = PE_ACTION
PE_STAR = PE_OK
PE_STAR2 = PE_VIEW
PE_STAR3 = PE_OWNER
PE_WAIT = PE_TIME

PREMIUM_BUTTON_IDS = {
    "ok": "5985652692142266021", "dev": "6239930832128056797",
    "owner": "6091259474025126934", "view": "5774007681731795134",
    "time": "5983299943417257042", "dance": "6129805886383723340",
    "star": "5985652692142266021", "star2": "5774007681731795134",
    "star3": "6091259474025126934", "wait": "5983299943417257042",
    "status": "5774007681731795134",
}

_InlineKeyboardButton = types.InlineKeyboardButton
_KeyboardButton = types.KeyboardButton

def premium_inline_button(text: str, callback_data: str = None, url: str = None, icon_key: str = "ok", style: str = None) -> types.InlineKeyboardButton:
    kwargs = {"text": text}
    if url:
        kwargs["url"] = url
    else:
        kwargs["callback_data"] = callback_data or "noop"
    emoji_id = PREMIUM_BUTTON_IDS.get(icon_key) or PREMIUM_BUTTON_IDS.get("ok")
    if style in {"primary", "success", "danger"}:
        kwargs["style"] = style
    try:
        return types.InlineKeyboardButton(icon_custom_emoji_id=emoji_id, **kwargs)
    except Exception:
        kwargs.pop("style", None)
        try:
            return types.InlineKeyboardButton(icon_custom_emoji_id=emoji_id, **kwargs)
        except Exception:
            return types.InlineKeyboardButton(**kwargs)

FREE_CREDITS      = 2
REFERRAL_BONUS    = 5
UPLOAD_COST       = 1

WELCOME_VIDEO_URL = ''  # t.me links don't work with send_video; leave empty to skip

BASE_DIR         = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR  = os.path.join(BASE_DIR, 'upload_bots')
DATA_DIR         = os.path.join(BASE_DIR, 'evilhost_data')
DATABASE_PATH    = os.path.join(DATA_DIR, 'bot_data.db')

os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

bot = telebot.TeleBot(TOKEN)

def _is_entity_parse_error(exc):
    text = str(exc).lower()
    return ("can't parse entities" in text or "cant parse entities" in text
            or "parse entities" in text or "entity_text_invalid" in text)

def _strip_tg_emoji(html_text: str) -> str:
    return re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', str(html_text))

def _safe_wrap_method(obj, method_name):
    original = getattr(obj, method_name)
    def wrapped(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except Exception as exc:
            if not _is_entity_parse_error(exc):
                raise
            retry_kwargs = dict(kwargs)
            if method_name == 'send_message':
                new_args = list(args)
                if len(new_args) >= 2:
                    new_args[1] = _strip_tg_emoji(new_args[1])
                elif 'text' in retry_kwargs:
                    retry_kwargs['text'] = _strip_tg_emoji(retry_kwargs['text'])
            elif method_name == 'edit_message_text':
                new_args = list(args)
                if new_args:
                    new_args[0] = _strip_tg_emoji(new_args[0])
                elif 'text' in retry_kwargs:
                    retry_kwargs['text'] = _strip_tg_emoji(retry_kwargs['text'])
            elif method_name in ('send_photo', 'send_video', 'send_document'):
                new_args = list(args)
                if len(new_args) >= 3 and new_args[2]:
                    new_args[2] = _strip_tg_emoji(new_args[2])
                elif 'caption' in retry_kwargs and retry_kwargs['caption']:
                    retry_kwargs['caption'] = _strip_tg_emoji(retry_kwargs['caption'])
            elif method_name == 'edit_message_caption':
                new_args = list(args)
                if new_args:
                    new_args[0] = _strip_tg_emoji(new_args[0])
                elif 'caption' in retry_kwargs and retry_kwargs['caption']:
                    retry_kwargs['caption'] = _strip_tg_emoji(retry_kwargs['caption'])
            else:
                new_args = list(args)
            return original(*new_args, **retry_kwargs)
    setattr(obj, method_name, wrapped)

for _method in ('send_message', 'send_photo', 'send_video', 'send_document',
                'edit_message_text', 'edit_message_caption'):
    try:
        _safe_wrap_method(bot, _method)
    except Exception:
        pass

_REPLY_CONTEXT = {}
_REPLY_CONTEXT_TTL = 20
_RAW_SEND_MESSAGE_BASE = bot.send_message
_RAW_SEND_VIDEO_BASE = bot.send_video
_RAW_SEND_DOCUMENT_BASE = bot.send_document
_RAW_SEND_PHOTO_BASE = bot.send_photo

def _set_reply_context(message):
    try:
        _REPLY_CONTEXT[int(message.chat.id)] = (int(message.message_id), time.time())
    except Exception:
        pass

def _reply_kwargs_for(chat_id, kwargs):
    out = dict(kwargs)
    if 'reply_to_message_id' not in out and 'reply_parameters' not in out:
        try:
            item = _REPLY_CONTEXT.get(int(chat_id))
            if item and (time.time() - item[1]) <= _REPLY_CONTEXT_TTL:
                out['reply_to_message_id'] = item[0]
        except Exception:
            pass
    return out

def _react_outgoing(result):
    try:
        if result is not None:
            threading.Thread(target=auto_react, args=(result,), daemon=True).start()
    except Exception:
        pass

def _send_message_reply_layer(*args, **kwargs):
    chat_id = args[0] if args else kwargs.get('chat_id')
    call_kwargs = _reply_kwargs_for(chat_id, kwargs)
    try:
        result = _RAW_SEND_MESSAGE_BASE(*args, **call_kwargs)
    except TypeError:
        call_kwargs.pop('reply_to_message_id', None)
        call_kwargs.pop('reply_parameters', None)
        result = _RAW_SEND_MESSAGE_BASE(*args, **call_kwargs)
    _react_outgoing(result)
    return result

def _send_media_reply_layer(raw_fn, *args, **kwargs):
    chat_id = args[0] if args else kwargs.get('chat_id')
    call_kwargs = _reply_kwargs_for(chat_id, kwargs)
    try:
        result = raw_fn(*args, **call_kwargs)
    except TypeError:
        call_kwargs.pop('reply_to_message_id', None)
        call_kwargs.pop('reply_parameters', None)
        result = raw_fn(*args, **call_kwargs)
    _react_outgoing(result)
    return result

def _send_video_reply_layer(*args, **kwargs):
    return _send_media_reply_layer(_RAW_SEND_VIDEO_BASE, *args, **kwargs)

def _send_document_reply_layer(*args, **kwargs):
    return _send_media_reply_layer(_RAW_SEND_DOCUMENT_BASE, *args, **kwargs)

def _send_photo_reply_layer(*args, **kwargs):
    return _send_media_reply_layer(_RAW_SEND_PHOTO_BASE, *args, **kwargs)

try:
    bot.send_message = _send_message_reply_layer
    bot.send_video = _send_video_reply_layer
    bot.send_document = _send_document_reply_layer
    bot.send_photo = _send_photo_reply_layer
except Exception:
    pass

_RAW_SEND_MESSAGE = bot.send_message

def _evil_premium_reply_to(message, text, *args, **kwargs):
    try:
        raw = str(text or '')
        markup = kwargs.get('reply_markup')
        parse_mode = kwargs.get('parse_mode') or 'HTML'
        _set_reply_context(message)
        if 'EVIL HOST BOT' in raw or '<blockquote>' in raw:
            return bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode=parse_mode)
        clean = re.sub(r'<[^>]+>', '', raw).replace('\r', '').strip()
        body = f"{PE_VIEW} <b>{_html_escape(clean[:5000])}</b>"
        return premium_send(message.chat.id, 'EVIL HOST RESPONSE', body, reply_markup=markup)
    except Exception:
        _set_reply_context(message)
        return bot.send_message(
            message.chat.id,
            re.sub(r'<[^>]+>', '', str(text or '')),
            reply_markup=kwargs.get('reply_markup'),
            parse_mode=kwargs.get('parse_mode'),
        )

try:
    bot.reply_to = _evil_premium_reply_to
except Exception:
    pass

# --- Runtime state ---
bot_scripts       = {}
user_credits_cache = {}
user_files        = {}
active_users      = set()
admin_ids         = {OWNER_ID}
bot_locked        = False

REACTION_POOL = ["🔥"]

def auto_react(message):
    try:
        react = getattr(bot, "set_message_reaction", None)
        reaction_cls = getattr(types, "ReactionTypeEmoji", None)
        if react and reaction_cls:
            emoji = random.choice(REACTION_POOL)
            react(chat_id=message.chat.id, message_id=message.message_id,
                  reaction=[reaction_cls(emoji=emoji)], is_big=False)
    except Exception:
        pass

try:
    _RAW_PROCESS_NEW_MESSAGES = bot.process_new_messages
    def _process_new_messages_with_context(messages):
        for _m in messages or []:
            try:
                _set_reply_context(_m)
                threading.Thread(target=auto_react, args=(_m,), daemon=True).start()
            except Exception:
                pass
        return _RAW_PROCESS_NEW_MESSAGES(messages)
    bot.process_new_messages = _process_new_messages_with_context
except Exception:
    pass

try:
    _RAW_PROCESS_NEW_CALLBACKS = bot.process_new_callback_query
    def _process_new_callback_query_with_context(callback_queries):
        for _call in callback_queries or []:
            try:
                if getattr(_call, 'message', None):
                    _set_reply_context(_call.message)
            except Exception:
                pass
        return _RAW_PROCESS_NEW_CALLBACKS(callback_queries)
    bot.process_new_callback_query = _process_new_callback_query_with_context
except Exception:
    pass

# ══════════════════════════════════════════════════════
#  MALWARE DETECTION
# ══════════════════════════════════════════════════════
MALWARE_SIGNATURES = [b'MZ', b'\x7fELF', b'\xfe\xed\xfa', b'\xce\xfa\xed\xfe', b'PK', b'Rar!']
ENCRYPTED_FILE_INDICATORS = [b'openssl', b'encrypted', b'cipher', b'AES', b'DES', b'RSA', b'GPG', b'PGP']
SUSPICIOUS_KEYWORDS = [b'ransomware', b'trojan', b'virus', b'malware', b'backdoor',
                       b'exploit', b'payload', b'botnet', b'keylogger', b'rootkit']

def get_file_type(file_content):
    signatures = {
        b'\x7fELF': 'application/x-executable',
        b'MZ': 'application/x-dosexec',
        b'\xfe\xed\xfa': 'application/x-mach-binary',
        b'\xce\xfa\xed\xfe': 'application/x-mach-binary',
        b'PK': 'application/zip',
        b'Rar!': 'application/x-rar',
    }
    for sig, mime in signatures.items():
        if file_content.startswith(sig):
            return mime
    return 'application/octet-stream'

def is_suspicious_file(file_content, file_name):
    file_lower = file_name.lower()
    suspicious_ext = ['.exe', '.dll', '.bat', '.cmd', '.scr', '.com', '.pif',
                      '.application', '.gadget', '.msi', '.msp', '.hta', '.cpl',
                      '.msc', '.jar', '.bin', '.deb', '.rpm', '.apk', '.app',
                      '.dmg', '.iso', '.img']
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
        logger.warning(f"Blocked {file_name} from {user_id}: {reason}")
        return False, f"Security block: {reason}"
    return True, "Clean"

# ══════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════
DB_LOCK = threading.Lock()

def init_db():
    logger.info(f"Initializing DB at: {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS active_users (user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
                     (user_id INTEGER, file_name TEXT, file_type TEXT,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
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
        c.execute('''CREATE TABLE IF NOT EXISTS hosted_processes
                     (user_id INTEGER NOT NULL,
                      file_name TEXT NOT NULL,
                      file_type TEXT NOT NULL,
                      enabled INTEGER DEFAULT 0,
                      updated_at TEXT NOT NULL,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS redeem_codes
                     (code TEXT PRIMARY KEY, amount INTEGER NOT NULL,
                      used_by INTEGER, created_at TEXT NOT NULL)''')
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
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
        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for user_id, fn, ft in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((fn, ft))
        c.execute('SELECT user_id FROM active_users')
        active_users.update(uid for (uid,) in c.fetchall())
        c.execute('SELECT user_id FROM admins')
        admin_ids.update(uid for (uid,) in c.fetchall())
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
        return True
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
    if user_id in user_credits_cache:
        return
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
    if referred_by and referred_by != user_id:
        add_credits(referred_by, REFERRAL_BONUS)
        try:
            bot.send_message(
                referred_by,
                f" *Referral Bonus!*\n\n"
                f"Someone joined using your link!\n"
                f" +{REFERRAL_BONUS} credits added to your account.\n"
                f"New balance: `{get_credits(referred_by)}`",
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
        kids = parent.children(recursive=True)
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
    if user_id == OWNER_ID:    return f"{PE_STATUS} Owner"
    if user_id in admin_ids:   return f"{PE_STATUS} Admin"
    credits = get_credits(user_id)
    if credits > 10:           return f"{PE_STAR3} Premium"
    if credits > 0:            return f"{PE_STAR} User"
    return "Free"

# ══════════════════════════════════════════════════════
#  AUTO PACKAGE INSTALLATION
# ══════════════════════════════════════════════════════
TELEGRAM_MODULES = {
    'telebot': 'pyTelegramBotAPI>=4.33.0', 'telegram': 'python-telegram-bot',
    'python_telegram_bot': 'python-telegram-bot', 'aiogram': 'aiogram',
    'pyrogram': 'pyrogram', 'telethon': 'telethon', 'telethon.sync': 'telethon',
    'telepot': 'telepot', 'tgcrypto': 'tgcrypto', 'bs4': 'beautifulsoup4',
    'requests': 'requests', 'httpx': 'httpx', 'pillow': 'Pillow',
    'cv2': 'opencv-python', 'yaml': 'PyYAML', 'dotenv': 'python-dotenv',
    'dateutil': 'python-dateutil', 'pandas': 'pandas', 'numpy': 'numpy',
    'flask': 'Flask', 'django': 'Django', 'sqlalchemy': 'SQLAlchemy',
    'psutil': 'psutil', 'urllib3': 'urllib3', 'lxml': 'lxml',
    'cryptography': 'cryptography', 'jwt': 'PyJWT', 'dns': 'dnspython',
    'qrcode': 'qrcode', 'PIL': 'Pillow',
    'asyncio': None, 'json': None, 'datetime': None, 'os': None, 'sys': None,
    're': None, 'time': None, 'math': None, 'random': None, 'logging': None,
    'threading': None, 'subprocess': None, 'zipfile': None, 'tempfile': None,
    'shutil': None, 'sqlite3': None, 'atexit': None, 'pathlib': None,
    'typing': None, 'collections': None, 'itertools': None, 'functools': None,
    'hashlib': None, 'uuid': None, 'base64': None, 'secrets': None,
    'signal': None, 'socket': None, 'ssl': None, 'statistics': None,
    'timeit': None, 'traceback': None, 'contextlib': None, 'dataclasses': None,
    'enum': None, 'string': None, 'csv': None, 'io': None, 'copy': None,
    'glob': None, 'platform': None, 'configparser': None,
}

EXTRA_PYPI_MODULES = {
    'aiohttp': 'aiohttp', 'aiofiles': 'aiofiles', 'websockets': 'websockets',
    'discord': 'discord.py', 'discord_webhook': 'discord-webhook',
    'google': 'google-api-python-client', 'googleapiclient': 'google-api-python-client',
    'google_auth_oauthlib': 'google-auth-oauthlib', 'oauth2client': 'oauth2client',
    'sklearn': 'scikit-learn', 'multipart': 'python-multipart',
    'uvicorn': 'uvicorn', 'fastapi': 'fastapi', 'starlette': 'starlette',
    'pydantic': 'pydantic', 'jinja2': 'Jinja2', 'werkzeug': 'Werkzeug',
    'rich': 'rich', 'colorama': 'colorama', 'orjson': 'orjson',
    'redis': 'redis', 'pymongo': 'pymongo', 'motor': 'motor',
    'mysql': 'mysql-connector-python', 'psycopg2': 'psycopg2-binary',
    'aiosqlite': 'aiosqlite', 'peewee': 'peewee', 'tqdm': 'tqdm',
    'openpyxl': 'openpyxl', 'xlsxwriter': 'XlsxWriter',
    'docx': 'python-docx', 'pptx': 'python-pptx', 'reportlab': 'reportlab',
    'selectolax': 'selectolax',
}

def package_for_import(module_name):
    mod = _top_level_module(module_name)
    return TELEGRAM_MODULES.get(mod) or EXTRA_PYPI_MODULES.get(mod)

def dependency_cache_key(user_folder):
    return os.path.join(user_folder, '.packages', '.dependency_state.json')

def _load_dependency_state(user_folder):
    path = dependency_cache_key(user_folder)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _save_dependency_state(user_folder, data):
    path = dependency_cache_key(user_folder)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        logger.warning(f"Dependency state save failed: {e}")

def _top_level_module(name):
    return (name or '').split('.')[0].strip()

def detect_imports(script_path):
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
    path = os.path.join(user_folder, '.packages')
    os.makedirs(path, exist_ok=True)
    return path

def _pip_env(user_folder):
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
    parts = [package_dir, user_folder]
    if old_pp:
        parts.append(old_pp)
    env['PYTHONPATH'] = os.pathsep.join(parts)
    return env, package_dir

def _pip_command(user_folder, args):
    _, package_dir = _pip_env(user_folder)
    return [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
            '--no-input', '--upgrade', '--target', package_dir] + list(args)

def pip_install_package(pkg, user_folder=None, message=None):
    if not pkg or not user_folder:
        return False
    try:
        env, package_dir = _pip_env(user_folder)
        if message:
            bot.reply_to(message, f"Installing `{pkg}`...", parse_mode='Markdown')
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
                bot.reply_to(message, f" `{pkg}` installed locally.", parse_mode='Markdown')
            return True
        err = (r.stderr or r.stdout or 'unknown pip error').strip()
        logger.error(f"pip install {pkg} failed: {err[-4000:]}")
        if message:
            bot.reply_to(message, f"Install failed for `{pkg}`:\n```\n{err[-2200:]}\n```", parse_mode='Markdown')
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"pip install timeout: {pkg}")
        if message:
            bot.reply_to(message, f"Install timeout: `{pkg}`", parse_mode='Markdown')
        return False
    except Exception as e:
        logger.error(f"pip install error {pkg}: {e}", exc_info=True)
        if message:
            bot.reply_to(message, f"Install error `{pkg}`: {e}")
        return False

def attempt_install_npm(module_name, user_folder, message=None):
    """FIX: missing function. Install npm package into user's folder."""
    if not module_name:
        return False
    try:
        if message:
            bot.reply_to(message, f"Installing npm `{module_name}`...", parse_mode='Markdown')
        r = subprocess.run(
            ['npm', 'install', '--no-audit', '--no-fund', module_name],
            cwd=user_folder,
            capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=900
        )
        if r.returncode == 0:
            if message:
                bot.reply_to(message, f" npm `{module_name}` installed.", parse_mode='Markdown')
            return True
        err = (r.stderr or r.stdout or 'unknown npm error').strip()
        logger.error(f"npm install {module_name} failed: {err[-4000:]}")
        if message:
            bot.reply_to(message, f"npm install failed for `{module_name}`:\n```\n{err[-2200:]}\n```", parse_mode='Markdown')
        return False
    except FileNotFoundError:
        if message:
            bot.reply_to(message, "Node.js / npm not installed on this host.")
        return False
    except subprocess.TimeoutExpired:
        if message:
            bot.reply_to(message, f"npm install timeout: `{module_name}`", parse_mode='Markdown')
        return False
    except Exception as e:
        logger.error(f"npm install error {module_name}: {e}", exc_info=True)
        if message:
            bot.reply_to(message, f"npm install error `{module_name}`: {e}")
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
            bot.reply_to(message, "Installing `requirements.txt` into private package storage...", parse_mode='Markdown')
        r = subprocess.run(
            _pip_command(user_folder, ['-r', req_path]),
            cwd=user_folder, env=env,
            capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=900
        )
        if r.returncode == 0:
            importlib.invalidate_caches()
            if message:
                bot.reply_to(message, "Requirements installed.", parse_mode='Markdown')
            return True
        err = (r.stderr or r.stdout or 'unknown pip error').strip()
        logger.error(f"requirements.txt failed: {err[-5000:]}")
        if message:
            bot.reply_to(message, f" `requirements.txt` failed:\n```\n{err[-2200:]}\n```", parse_mode='Markdown')
        return False
    except subprocess.TimeoutExpired:
        if message: bot.reply_to(message, "requirements.txt installation timed out.")
        return False
    except Exception as e:
        logger.error(f"requirements install error: {e}", exc_info=True)
        if message: bot.reply_to(message, f"Requirements error: {e}")
        return False

def ensure_python_dependencies(script_path, user_folder, message=None):
    env, package_dir = _pip_env(user_folder)
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)
    importlib.invalidate_caches()
    if not install_requirements(user_folder, message):
        return False
    missing = []
    for mod in detect_imports(script_path):
        if module_is_available(mod):
            continue
        pkg = package_for_import(mod)
        if pkg:
            missing.append((mod, pkg))
    packages = []
    seen = set()
    for mod, pkg in missing:
        if pkg and pkg not in seen:
            packages.append((mod, pkg)); seen.add(pkg)
    state = _load_dependency_state(user_folder)
    for mod, pkg in packages:
        logger.info(f"Missing dependency detected: {mod} -> {pkg}")
        if not pip_install_package(pkg, user_folder, message):
            return False
        state[mod] = pkg
    _save_dependency_state(user_folder, state)
    importlib.invalidate_caches()
    still_missing = [m for m in detect_imports(script_path)
                     if package_for_import(m) and not module_is_available(m)]
    if still_missing:
        logger.error(f"Dependencies still missing: {still_missing}")
        if message:
            bot.reply_to(message, "Missing Python modules after install: " + ', '.join(still_missing))
        return False
    return True

def attempt_install_pip(module_name, message):
    pkg = TELEGRAM_MODULES.get(_top_level_module(module_name), module_name)
    return pip_install_package(pkg, BASE_DIR, message)

# ══════════════════════════════════════════════════════
#  PERSISTENT PROCESS SUPERVISOR
# ══════════════════════════════════════════════════════
SUPERVISOR_INTERVAL = 8
SUPERVISOR_MAX_BACKOFF = 300
_SUPERVISOR_STOP = threading.Event()
_SUPERVISOR_LOCK = threading.RLock()
_supervisor_failures = {}

def set_hosted_process_state(user_id, file_name, file_type, enabled):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute(
                '''INSERT INTO hosted_processes(user_id,file_name,file_type,enabled,updated_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(user_id,file_name) DO UPDATE SET
                     file_type=excluded.file_type,
                     enabled=excluded.enabled,
                     updated_at=excluded.updated_at''',
                (int(user_id), str(file_name), str(file_type), 1 if enabled else 0,
                 datetime.now().isoformat(timespec='seconds'))
            )
            conn.commit()
        finally:
            conn.close()
    if not enabled:
        _supervisor_failures.pop(f"{user_id}_{file_name}", None)

def remove_hosted_process_state(user_id, file_name):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute('DELETE FROM hosted_processes WHERE user_id=? AND file_name=?',
                         (int(user_id), str(file_name)))
            conn.commit()
        finally:
            conn.close()
    _supervisor_failures.pop(f"{user_id}_{file_name}", None)

def get_enabled_hosted_processes():
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            return conn.execute(
                'SELECT user_id,file_name,file_type FROM hosted_processes WHERE enabled=1'
            ).fetchall()
        finally:
            conn.close()

def _notify_supervisor_failure(info, reason):
    try:
        cid = info.get('chat_id')
        if cid:
            bot.send_message(cid,
                f"{PE_TIME} <b>HOST SUPERVISOR</b>\n"
                f"{PE_VIEW} <code>{_html_escape(info.get('file_name',''))}</code> exited.\n"
                f"{PE_STATUS} Auto-restart queued.\n\n"
                f"<pre>{_html_escape(reason[-1800:])}</pre>",
                parse_mode='HTML')
    except Exception:
        pass

def _launch_hosted_process(user_id, file_name, file_type, chat_id=None, notify=False):
    folder = get_user_folder(user_id)
    path = os.path.join(folder, file_name)
    if not os.path.isfile(path):
        logger.warning(f"Supervisor: missing hosted file {path}")
        return False
    class _Msg: pass
    msg = _Msg()
    msg.chat = SimpleNamespace(id=chat_id or user_id)
    msg.message_id = 0
    msg.from_user = SimpleNamespace(id=user_id)
    fn = run_script if file_type == 'py' else run_js_script
    try:
        threading.Thread(
            target=fn,
            args=(path, user_id, folder, file_name, msg),
            daemon=True,
            name=f"host-{user_id}-{file_name}"
        ).start()
        return True
    except Exception as e:
        logger.error(f"Supervisor launch failed: {e}", exc_info=True)
        return False

def _supervisor_loop():
    logger.info("Persistent hosting supervisor started.")
    while not _SUPERVISOR_STOP.wait(SUPERVISOR_INTERVAL):
        try:
            for uid, fname, ftype in get_enabled_hosted_processes():
                key = f"{uid}_{fname}"
                if is_bot_running(uid, fname):
                    _supervisor_failures.pop(key, None)
                    continue
                info = bot_scripts.get(key)
                if info and info.get('starting'):
                    continue
                state = _supervisor_failures.get(key, {'count': 0, 'next': 0})
                now = time.time()
                if now < state.get('next', 0):
                    continue
                state['count'] = state.get('count', 0) + 1
                delay = min(SUPERVISOR_MAX_BACKOFF, 2 ** min(state['count'], 8))
                state['next'] = now + delay
                _supervisor_failures[key] = state
                logger.warning(f"Supervisor restarting {key}; attempt={state['count']} backoff={delay}s")
                _launch_hosted_process(uid, fname, ftype, chat_id=uid, notify=(state['count'] > 1))
        except Exception:
            logger.error("Supervisor loop error", exc_info=True)

def start_persistent_supervisor():
    t = threading.Thread(target=_supervisor_loop, daemon=True, name="evilhost-host-supervisor")
    t.start()
    for uid, fname, ftype in get_enabled_hosted_processes():
        threading.Thread(
            target=_launch_hosted_process,
            args=(uid, fname, ftype, uid, False),
            daemon=True,
            name=f"recover-{uid}-{fname}"
        ).start()

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
    body = (
        f"{PE_TIME} <b>Startup failed</b>\n\n"
        f"{PE_VIEW} File : <code>{_html_escape(file_name)}</code>\n"
        f"{PE_STATUS} Exit code : <code>{rc}</code>\n\n"
        f"<pre>{_html_escape(reason[:3000])}</pre>"
    )
    text, markup = premium_card("DEPLOYMENT ERROR", body, copy_value=file_name, copy_label="COPY FILE NAME")
    try:
        bot.send_message(msg_obj.chat.id, text, reply_markup=markup, parse_mode='HTML')
    except Exception:
        logger.error(text)

def run_script(script_path, owner_id, user_folder, file_name, msg_obj, attempt=1):
    max_attempts = 2
    if attempt > max_attempts:
        bot.reply_to(msg_obj, f" `{file_name}` failed after {max_attempts} attempts.", parse_mode='Markdown')
        return
    key = f"{owner_id}_{file_name}"
    loading_msg = None
    try:
        if not os.path.exists(script_path):
            bot.reply_to(msg_obj, f"Script `{file_name}` not found."); return
        loading_msg = premium_loading(msg_obj.chat.id, "PYTHON DEPLOYMENT")
        if attempt == 1:
            if not ensure_python_dependencies(script_path, user_folder, msg_obj):
                premium_loading_done(msg_obj.chat.id, loading_msg, "DEPLOYMENT FAILED",
                                     f"{PE_TIME} <b>Dependency installation failed.</b>\n{PE_VIEW} Check the deployment log for details.")
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
            'starting': True,
            'file_name': file_name, 'chat_id': msg_obj.chat.id,
            'script_owner_id': owner_id, 'start_time': datetime.now(),
            'user_folder': user_folder, 'type': 'py', 'script_key': key
        }
        try:
            set_hosted_process_state(owner_id, file_name, 'py', True)
            premium_loading_done(
                msg_obj.chat.id, loading_msg, "PYTHON HOSTED",
                f"{PE_OK} <b>DEPLOYMENT SUCCESSFUL</b>\n\n"
                f"{PE_DEV} File : <code>{_html_escape(file_name)}</code>\n"
                f"{PE_VIEW} PID : <code>{process.pid}</code>\n"
                f"{PE_STATUS} Status : <b>STARTING</b>\n\n"
                f"{PE_OWNER} EVIL HOST • Python engine online",
                reply_markup=create_control_buttons(owner_id, file_name, False),
                copy_value=file_name, copy_label="COPY FILE NAME"
            )
        finally:
            info = bot_scripts.get(key)
            if info:
                info['starting'] = False
        threading.Thread(
            target=_monitor_python_process,
            args=(key, process, log_path, msg_obj, file_name),
            daemon=True
        ).start()
    except Exception as e:
        if key in bot_scripts:
            kill_process_tree(bot_scripts[key]); bot_scripts.pop(key, None)
        bot.reply_to(msg_obj, f"Python error: {e}")

def run_js_script(script_path, owner_id, user_folder, file_name, msg_obj, attempt=1):
    max_attempts = 2
    if attempt > max_attempts:
        bot.reply_to(msg_obj, f" `{file_name}` failed after {max_attempts} attempts.", parse_mode='Markdown')
        return
    key = f"{owner_id}_{file_name}"
    try:
        if not os.path.exists(script_path):
            bot.reply_to(msg_obj, f" `{file_name}` not found."); return
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
                    bot.reply_to(msg_obj, f"JS error:\n```\n{stderr[:500]}\n```", parse_mode='Markdown')
                    return
            except subprocess.TimeoutExpired:
                if check_proc and check_proc.poll() is None:
                    check_proc.kill(); check_proc.communicate()
            except FileNotFoundError:
                bot.reply_to(msg_obj, "Node.js not found. Install it first."); return
            except Exception as e:
                bot.reply_to(msg_obj, f"JS pre-check error: {e}"); return
            finally:
                if check_proc and check_proc.poll() is None:
                    check_proc.kill(); check_proc.communicate()
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = open(log_path, 'w', encoding='utf-8', errors='ignore')
        env = os.environ.copy()
        env['NODE_ENV'] = env.get('NODE_ENV', 'production')
        env['PYTHONUNBUFFERED'] = '1'
        process = subprocess.Popen(
            ['node', script_path], cwd=user_folder,
            stdout=log_file, stderr=log_file, stdin=subprocess.PIPE,
            encoding='utf-8', errors='ignore', env=env
        )
        bot_scripts[key] = {
            'process': process, 'log_file': log_file, 'file_name': file_name,
            'starting': False,
            'chat_id': msg_obj.chat.id, 'script_owner_id': owner_id,
            'start_time': datetime.now(), 'user_folder': user_folder,
            'type': 'js', 'script_key': key
        }
        set_hosted_process_state(owner_id, file_name, 'js', True)
        bot.reply_to(msg_obj, f" `{file_name}` running! PID: `{process.pid}`", parse_mode='Markdown')
    except Exception as e:
        if key in bot_scripts:
            kill_process_tree(bot_scripts[key]); del bot_scripts[key]
        bot.reply_to(msg_obj, f"JS error: {e}")

# ══════════════════════════════════════════════════════
#  DATABASE OPERATIONS
# ══════════════════════════════════════════════════════
def save_user_file(user_id, file_name, file_type='py'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute('INSERT OR REPLACE INTO user_files VALUES (?,?,?)',
                         (user_id, file_name, file_type))
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
            bot.reply_to(message, f"Blocked: {reason}"); return
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
                        bot.reply_to(message, f"ZIP has suspicious file: {m.filename}"); return
                    mp = os.path.abspath(os.path.join(tmp, m.filename))
                    if not mp.startswith(os.path.abspath(tmp)):
                        raise zipfile.BadZipFile(f"Path traversal: {m.filename}")
            zr.extractall(tmp)
        target = tmp
        root_files = sorted(os.listdir(target))
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
        items = sorted(os.listdir(tmp))
        py_files = [f for f in items if f.endswith('.py')]
        js_files = [f for f in items if f.endswith('.js')]
        req_file = 'requirements.txt' if 'requirements.txt' in items else None
        pkg_json = 'package.json' if 'package.json' in items else None
        if req_file:
            req_src = os.path.join(tmp, req_file)
            req_dst = os.path.join(user_folder, 'requirements.txt')
            shutil.copy2(req_src, req_dst)
            if not install_requirements(user_folder, message):
                return
        if pkg_json:
            shutil.copy2(os.path.join(tmp, pkg_json), os.path.join(user_folder, 'package.json'))
            npm_log = os.path.join(user_folder, 'npm-install.log')
            try:
                with open(npm_log, 'w', encoding='utf-8', errors='ignore') as nf:
                    r = subprocess.run(
                        ['npm', 'install', '--no-audit', '--no-fund'],
                        cwd=user_folder, stdout=nf, stderr=subprocess.STDOUT,
                        text=True, timeout=1200
                    )
                if r.returncode != 0:
                    bot.reply_to(message, "npm dependency installation failed. Check npm-install.log.")
                    return
            except FileNotFoundError:
                bot.reply_to(message, "Node.js/npm is not installed on this host.")
                return
            except subprocess.TimeoutExpired:
                bot.reply_to(message, "npm dependency installation timed out.")
                return
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
            bot.reply_to(message, "No `.py` or `.js` file found in ZIP.")
    except zipfile.BadZipFile as e:
        bot.reply_to(message, f"Invalid ZIP: {e}")
    except Exception as e:
        bot.reply_to(message, f"ZIP error: {e}")
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
        bot.reply_to(message, "No running scripts."); return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, info in running:
        markup.add(premium_inline_button(
            f"{info['file_name']} (UID: {info['script_owner_id']})",
            callback_data=f'sendcmd_select_{key}'
        ))
    markup.add(premium_inline_button("Back", callback_data='send_command'))
    bot.reply_to(message, "Select script:", reply_markup=markup)

def process_send_command(message, script_key):
    if script_key not in bot_scripts:
        bot.reply_to(message, "Script no longer running."); return
    info = bot_scripts[script_key]
    try:
        proc = info['process']
        if proc and proc.poll() is None:
            proc.stdin.write(message.text + '\n')
            proc.stdin.flush()
            bot.reply_to(message, f"Sent to `{info['file_name']}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, f" `{info['file_name']}` not running.", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

def view_all_logs(message):
    user_id = message.from_user.id
    folder = get_user_folder(user_id)
    logs = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.endswith('.log'):
                p = os.path.join(folder, f)
                logs.append((f, os.path.getsize(p), p))
    if not logs:
        bot.reply_to(message, "No log files yet."); return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for lf, sz, _ in sorted(logs):
        markup.add(premium_inline_button(
            f"{lf} ({sz/1024:.1f} KB)", callback_data=f'viewlog_{user_id}_{lf}'
        ))
    markup.add(premium_inline_button("Back", callback_data='send_command'))
    bot.reply_to(message, " *Your Logs:*", reply_markup=markup, parse_mode='Markdown')

def send_log_file(message, log_path, log_filename):
    try:
        if os.path.getsize(log_path) > 50 * 1024 * 1024:
            bot.reply_to(message, "Log too large (>50 MB)."); return
        with open(log_path, 'rb') as f:
            bot.send_document(message.chat.id, f, caption=f" {log_filename}")
    except Exception as e:
        bot.reply_to(message, f"Log send error: {e}")

# ══════════════════════════════════════════════════════
#  PREMIUM RESPONSE UI
# ══════════════════════════════════════════════════════
def premium_card(title, body, copy_value=None, copy_label="COPY CODE"):
    title = _html_escape(str(title))
    text = (
        f"{PE_BRAND}  <b>EVIL HOST BOT</b>\n"
        f"<b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{body}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_DEV} <b>@EVILTALKS</b>"
    )
    markup = None
    if copy_value is not None:
        markup = types.InlineKeyboardMarkup(row_width=1)
        try:
            markup.add(types.InlineKeyboardButton(
                copy_label,
                icon_custom_emoji_id=PREMIUM_BUTTON_IDS["ok"],
                style="success",
                copy_text=types.CopyTextButton(text=str(copy_value))
            ))
        except Exception:
            markup.add(premium_inline_button(copy_label, callback_data="copy_unavailable"))
    return text, markup

def premium_send(chat_id, title, body, *, reply_markup=None, copy_value=None, copy_label="COPY CODE", parse_mode="HTML"):
    text, copy_markup = premium_card(title, body, copy_value, copy_label)
    if reply_markup is not None and copy_markup is not None:
        for row in copy_markup.keyboard:
            reply_markup.keyboard.append(row)
        copy_markup = reply_markup
    elif reply_markup is not None:
        copy_markup = reply_markup
    return bot.send_message(chat_id, text, reply_markup=copy_markup, parse_mode=parse_mode)

def premium_reply(message, title, body, *, reply_markup=None, copy_value=None,
                  copy_label="COPY CODE"):
    try:
        return premium_send(message.chat.id, title, body,
                            reply_markup=reply_markup, copy_value=copy_value,
                            copy_label=copy_label, parse_mode="HTML")
    except Exception:
        return bot.send_message(message.chat.id, re.sub(r'<[^>]+>', '', str(body)))

def premium_loading(chat_id, title="PYTHON ENGINE", stages=None):
    if stages is None:
        stages = [
            ("INITIALIZING", 18),
            ("CHECKING FILE", 36),
            ("LOADING DEPENDENCIES", 58),
            ("BOOTING PYTHON", 78),
            ("VERIFYING PROCESS", 92),
            ("SYSTEM READY", 100),
        ]
    msg = None
    try:
        for i, (stage, pct) in enumerate(stages):
            filled = int(pct / 5)
            bar = "▰" * filled + "▱" * (20 - filled)
            body = (
                f"{PE_DEV} <b>{stage}</b>\n"
                f"<code>{bar}</code> <b>{pct}%</b>\n\n"
                f"{PE_VIEW} Engine : <code>PYTHON</code>\n"
                f"{PE_TIME} Stage  : <code>{i + 1}/{len(stages)}</code>\n"
                f"{PE_OK} EVIL HOST • <i>secure deployment</i>"
            )
            text, _ = premium_card(title, body)
            if msg is None:
                msg = bot.send_message(chat_id, text, parse_mode="HTML")
            else:
                try:
                    bot.edit_message_text(text, chat_id, msg.message_id, parse_mode="HTML")
                except Exception:
                    pass
            if i < len(stages) - 1:
                time.sleep(0.18)
    except Exception:
        pass
    return msg

def premium_loading_done(chat_id, loading_msg, title, body, reply_markup=None,
                         copy_value=None, copy_label="COPY CODE"):
    text, copy_markup = premium_card(title, body, copy_value, copy_label)
    markup = reply_markup
    if markup is None:
        markup = copy_markup
    elif copy_markup is not None:
        for row in copy_markup.keyboard:
            markup.keyboard.append(row)
    try:
        if loading_msg is not None:
            bot.edit_message_text(text, chat_id, loading_msg.message_id,
                                  reply_markup=markup, parse_mode="HTML")
            return loading_msg
    except Exception:
        pass
    return bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

def sync_user_files(user_id):
    folder = get_user_folder(user_id)
    disk = []
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if not os.path.isfile(path) or name.startswith('.') or name.endswith('.log'):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext == '.py': ft = 'py'
            elif ext == '.js': ft = 'js'
            elif ext == '.zip': ft = 'zip'
            elif name.lower() == 'requirements.txt': ft = 'txt'
            else: continue
            disk.append((name, ft))
    db_files = list(user_files.get(user_id, []))
    merged = {name: ft for name, ft in db_files}
    for name, ft in disk: merged[name] = ft
    valid = [(name, ft) for name, ft in merged.items() if os.path.isfile(os.path.join(folder, name))]
    user_files[user_id] = sorted(valid, key=lambda x: x[0].lower())
    for name, ft in valid:
        try: save_user_file(user_id, name, ft)
        except Exception: pass
    return user_files.get(user_id, [])

# ══════════════════════════════════════════════════════
#  MENU BUILDERS — PREMIUM UI
# ══════════════════════════════════════════════════════
def create_main_menu_inline(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        premium_inline_button('HOST FILE', callback_data='upload', icon_key='ok', style='success'),
        premium_inline_button('MY FILES', callback_data='check_files', icon_key='view', style='primary'),
    )
    markup.add(
        premium_inline_button('SPEED TEST', callback_data='speed', icon_key='time', style='primary'),
        premium_inline_button('STATISTICS', callback_data='stats', icon_key='status', style='primary'),
    )
    markup.add(
        premium_inline_button('MY CREDITS', callback_data='my_credits', icon_key='star', style='success'),
        premium_inline_button('REFER FRIENDS', callback_data='refer', icon_key='star3', style='primary'),
    )
    markup.add(
        premium_inline_button('SEND COMMAND', callback_data='send_command', icon_key='dev', style='primary'),
        premium_inline_button('CONTACT OWNER', url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}', icon_key='owner', style='success'),
    )
    if user_id in admin_ids:
        markup.add(
            premium_inline_button('CREDITS PANEL', callback_data='credits_panel', icon_key='star', style='primary'),
            premium_inline_button('BROADCAST', callback_data='broadcast', icon_key='star2', style='primary'),
        )
        markup.add(
            premium_inline_button('LOCK BOT' if not bot_locked else 'UNLOCK BOT',
                                  callback_data='lock_bot' if not bot_locked else 'unlock_bot',
                                  icon_key='admin', style='danger' if not bot_locked else 'success'),
            premium_inline_button('RUN ALL', callback_data='run_all_scripts', icon_key='ok', style='success'),
        )
        markup.add(
            premium_inline_button('ADMIN PANEL', callback_data='admin_panel', icon_key='admin', style='primary'),
        )
    markup.add(
        premium_inline_button('REFRESH PANEL', callback_data='back_to_main', icon_key='wait', style='primary')
    )
    return markup

def create_reply_keyboard(user_id):
    return create_main_menu_inline(user_id)

def create_control_buttons(owner_id, file_name, is_running=True):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_running:
        markup.row(
            premium_inline_button("Stop", callback_data=f'stop_{owner_id}_{file_name}'),
            premium_inline_button("Restart", callback_data=f'restart_{owner_id}_{file_name}'),
        )
        markup.row(
            premium_inline_button("Delete", callback_data=f'delete_{owner_id}_{file_name}'),
            premium_inline_button("Logs", callback_data=f'logs_{owner_id}_{file_name}'),
        )
    else:
        markup.row(
            premium_inline_button("Start", callback_data=f'start_{owner_id}_{file_name}'),
            premium_inline_button("Delete", callback_data=f'delete_{owner_id}_{file_name}'),
        )
        markup.row(
            premium_inline_button("View Logs", callback_data=f'logs_{owner_id}_{file_name}'),
        )
    markup.add(premium_inline_button("Back", callback_data='check_files'))
    return markup

def create_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        premium_inline_button('Add Credits', callback_data='add_credits_init'),
        premium_inline_button('Gen Redeem', callback_data='gen_redeem'),
    )
    markup.row(
        premium_inline_button('Add Admin', callback_data='add_admin'),
        premium_inline_button('User See', callback_data='user_see'),
    )
    markup.row(premium_inline_button('Broadcast', callback_data='broadcast'))
    markup.row(
        premium_inline_button('Remove Admin', callback_data='remove_admin'),
        premium_inline_button('List Admins', callback_data='list_admins'),
    )
    markup.row(premium_inline_button('Back', callback_data='back_to_main'))
    return markup

def create_credits_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        premium_inline_button('Add Credits', callback_data='add_credits_init'),
        premium_inline_button('Remove Credits', callback_data='remove_credits_init'),
    )
    markup.row(premium_inline_button('Check Credits', callback_data='check_credits_init'))
    markup.row(premium_inline_button('Credit History', callback_data='credit_history'))
    markup.row(premium_inline_button('Back', callback_data='back_to_main'))
    return markup

def create_send_command_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        premium_inline_button('Send to Process', callback_data='send_to_process'),
        premium_inline_button('View All Logs', callback_data='view_all_logs'),
    )
    markup.row(premium_inline_button('Back', callback_data='back_to_main'))
    return markup

# ══════════════════════════════════════════════════════
#  LOGIC FUNCTIONS
# ══════════════════════════════════════════════════════
def _logic_send_welcome(message, referrer_id=None):
    user_id = message.from_user.id
    chat_id = message.chat.id
    name = message.from_user.first_name or "User"
    username = message.from_user.username or "Not set"

    if bot_locked and user_id not in admin_ids:
        premium_send(chat_id, "BOT LOCKED", f"{PE_TIME} <b>The hosting panel is temporarily locked by the owner.</b>")
        return

    is_new = user_id not in active_users
    if is_new:
        add_active_user(user_id)
        init_user_credits(user_id, referred_by=referrer_id)
        join_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            owner_body = (
                f"{PE_DEV} <b>Name</b> : <code>{_html_escape(name)}</code>\n"
                f"{PE_OWNER} <b>Username</b> : <code>@{_html_escape(username)}</code>\n"
                f"{PE_OK} <b>ID</b> : <code>{user_id}</code>\n"
                f"{PE_TIME} <b>Time</b> : <code>{join_time}</code>\n"
                f"{PE_VIEW} <b>Referred by</b> : <code>{_html_escape(str(referrer_id or 'None'))}</code>"
            )
            owner_text, _ = premium_card("NEW USER ALERT", owner_body)
            bot.send_message(OWNER_ID, owner_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Owner notify failed: {e}")
    else:
        init_user_credits(user_id)

    credits = get_credits(user_id)
    credits_str = "UNLIMITED" if credits == float('inf') else str(credits)
    status = get_user_status_str(user_id)
    file_count = len(sync_user_files(user_id))
    ref_code = get_referral_code(user_id)
    bot_link = f"https://t.me/{BOT_USERNAME.lstrip('@')}?start={ref_code}"

    safe_name = _html_escape(str(name))
    safe_username = _html_escape(str(username))
    welcome_body = (
        f"{PE_WELCOME} <b>Welcome, {safe_name}!</b>\n"
        f"{PE_WELCOME_TEXT} <i>EVIL HOST — Premium Bot Hosting</i>\n\n"
        f"{PE_FAST} <b>Host your Telegram bots 24/7</b>\n"
        f"Upload your bot file, let EVIL HOST handle the setup, and keep your bot online without a PC.\n\n"
        f"{PE_COMMANDS} <b>Quick Commands</b>\n"
        f"• <code>/deploy</code> — Upload & deploy a bot\n"
        f"• <code>/mybots</code> — View & manage hosted bots\n"
        f"• <code>/logs</code> — Check runtime logs\n"
        f"• <code>/restart</code> — Restart a hosted bot\n"
        f"• <code>/stop</code> — Stop a hosted bot\n"
        f"• <code>/help</code> — Hosting help\n\n"
        f"{PE_CREDITS} <b>Your Credits:</b> <code>{credits_str}</code>\n"
        f"{PE_VIEW} <b>Hosted Files:</b> <code>{file_count}</code>\n"
        f"{PE_STATUS} <b>Status:</b> <b>{status}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_OWNER_ID} <b>Owner:</b> {_html_escape(YOUR_USERNAME)}\n"
        f"{PE_POWERED} <b>Owner ID:</b> <code>{OWNER_ID}</code>\n"
        f"{PE_POWERED} <b>Engine:</b> <code>Python + Telebot</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_SIGNAL} <i>Fast • Clean • 24/7 Hosting</i>"
    )
    welcome_text, _ = premium_card("PREMIUM HOSTING PANEL", welcome_body)
    main_markup = create_main_menu_inline(user_id)

    if WELCOME_VIDEO_URL:
        short_caption = f"EVIL HOST\nWelcome, {name}!\nPremium bot hosting panel is ready. Controls are below."
        try:
            try:
                bot.send_video(chat_id, WELCOME_VIDEO_URL, caption=short_caption, has_spoiler=True)
            except TypeError:
                bot.send_video(chat_id, WELCOME_VIDEO_URL, caption=short_caption)
        except Exception:
            pass

    try:
        bot.send_message(chat_id, welcome_text, reply_markup=main_markup, parse_mode='HTML')
    except Exception:
        bot.send_message(chat_id, re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', re.sub(r'<[^>]+>', '', welcome_text)), reply_markup=main_markup)

def _logic_upload_file(message):
    _set_reply_context(message)
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        premium_reply(message, "HOSTING LOCKED", f"{PE_TIME} <b>Hosting is temporarily locked by the owner.</b>")
        return
    credits = get_credits(user_id)
    if credits == float('inf'):
        premium_reply(message, "HOST FILE", f"{PE_OK} <b>Send your file now.</b>\n\n{PE_DEV} Accepted: <code>.py</code> <code>.js</code> <code>.zip</code>")
        return
    if credits <= 0:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(premium_inline_button('Get Credits via Referral', callback_data='refer'))
        markup.add(premium_inline_button('Contact Owner', url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}'))
        premium_reply(
            message, "CREDITS REQUIRED",
            f"{PE_TIME} <b>Your credit balance is empty.</b>\n\n"
            f"{PE_OK} Refer friends → <b>+{REFERRAL_BONUS} credits</b> each\n"
            f"{PE_OWNER} Contact the owner to refill.",
            reply_markup=markup,
        )
        return
    premium_reply(
        message, "HOST FILE",
        f"{PE_DEV} <b>Upload channel ready.</b>\n\n"
        f"{PE_OK} Send your <code>.py</code>, <code>.js</code> or <code>.zip</code> file now.\n"
        f"{PE_TIME} Balance: <code>{credits}</code> credit(s)\n"
        f"{PE_VIEW} Upload cost: <code>1 credit</code>",
    )

def _logic_check_files(message):
    _set_reply_context(message)
    user_id = message.from_user.id
    files = sync_user_files(user_id)
    if not files:
        text, kb = premium_card("MY FILES", f"{PE_VIEW} <b>No hosted files found.</b>\n\n{PE_OK} Upload a <code>.py</code>, <code>.js</code> or <code>.zip</code> file to begin.")
        bot.send_message(message.chat.id, text, reply_markup=create_main_menu_inline(user_id), parse_mode='HTML')
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for fn, ft in files:
        running = is_bot_running(user_id, fn)
        state = f"{PE_OK} RUNNING" if running else f"{PE_TIME} STOPPED"
        markup.add(premium_inline_button(f"{fn}  •  {ft.upper()}", callback_data=f'file_{user_id}_{fn}'))
    markup.add(premium_inline_button("BACK TO PANEL", callback_data='back_to_main'))
    body = f"{PE_VIEW} <b>{len(files)} hosted file(s)</b>\n{PE_OK} Select a file below to start, stop, restart, view logs or delete it.\n\n{PE_TIME} Status is checked live when you open a file."
    text, _ = premium_card("MY FILES", body, copy_value="EVIL HOST BOT")
    try:
        markup.keyboard.insert(0, [types.InlineKeyboardButton("COPY CODE", icon_custom_emoji_id=PREMIUM_BUTTON_IDS["ok"], style="success", copy_text=types.CopyTextButton(text="EVIL HOST BOT"))])
    except Exception:
        pass
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')

def _logic_bot_speed(message):
    _set_reply_context(message)
    t0 = time.time()
    wait = bot.reply_to(message, f"{PE_TIME} <b>Running secure speed test...</b>", parse_mode='HTML')
    try:
        ms = round((time.time() - t0) * 1000, 2)
        uid = message.from_user.id
        lvl = get_user_status_str(uid)
        body = (
            f"{PE_OK} <b>Ping</b> : <code>{ms} ms</code>\n"
            f"{PE_VIEW} <b>Bot</b> : <code>{'LOCKED' if bot_locked else 'ONLINE'}</code>\n"
            f"{PE_OWNER} <b>You</b> : {lvl}"
        )
        text, kb = premium_card("SPEED REPORT", body, copy_value=f"Ping: {ms} ms", copy_label="COPY REPORT")
        bot.edit_message_text(text, message.chat.id, wait.message_id, reply_markup=kb or create_main_menu_inline(uid), parse_mode='HTML')
    except Exception as e:
        bot.edit_message_text(f"{PE_TIME} <b>Speed test failed.</b>\n<code>{_html_escape(str(e))}</code>", message.chat.id, wait.message_id, parse_mode='HTML')

def _logic_statistics(message):
    _set_reply_context(message)
    user_id = message.from_user.id
    running_total = sum(1 for v in bot_scripts.values() if is_bot_running(v['script_owner_id'], v['file_name']))
    user_running = sum(1 for v in bot_scripts.values() if v['script_owner_id'] == user_id and is_bot_running(user_id, v['file_name']))
    body = (
        f"{PE_VIEW} <b>Total Users</b> : <code>{len(active_users)}</code>\n"
        f"{PE_DEV} <b>Total Files</b> : <code>{sum(len(v) for v in user_files.values())}</code>\n"
        f"{PE_OK} <b>Active Scripts</b> : <code>{running_total}</code>\n"
        f"{PE_TIME} <b>Your Scripts</b> : <code>{user_running}</code>\n"
    )
    if user_id in admin_ids:
        body += f"{PE_STATUS} <b>Bot Lock</b> : <code>{'ON' if bot_locked else 'OFF'}</code>\n"
        body += f"{PE_OK} <b>Credit Records</b> : <code>{len(user_credits_cache)}</code>\n"
    body += f"\n{PE_DEV} <b>DEV</b> : {_html_escape(CREDIT)}"
    premium_reply(message, "EVIL HOST STATISTICS", body)

def _logic_my_credits(message):
    _set_reply_context(message)
    user_id = message.from_user.id
    credits = get_credits(user_id)
    credits_str = "∞ (Unlimited)" if credits == float('inf') else str(credits)
    status = get_user_status_str(user_id)
    ref_code = get_referral_code(user_id)
    bot_link = f"https://t.me/{BOT_USERNAME.lstrip('@')}?start={ref_code}"
    markup = types.InlineKeyboardMarkup()
    markup.add(premium_inline_button('Share Referral Link', url=bot_link))
    markup.add(premium_inline_button(f'Refill Credits — {CREDIT}', url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}'))
    bot.reply_to(
        message,
        f" *Your Credit Balance*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Status: {status}\n"
        f"Credits: `{credits_str}`\n\n"
        f" *How to earn more:*\n"
        f"• Share referral link → `+{REFERRAL_BONUS}` per join\n"
        f"• Contact owner to refill\n\n"
        f"Your referral link:\n`{bot_link}`\n"
        f"━━━━━━━━━━━━━━━",
        reply_markup=markup, parse_mode='Markdown'
    )

def _logic_refer(message):
    _set_reply_context(message)
    user_id = message.from_user.id
    ref_code = get_referral_code(user_id)
    bot_link = f"https://t.me/{BOT_USERNAME.lstrip('@')}?start={ref_code}"
    markup = types.InlineKeyboardMarkup()
    markup.add(premium_inline_button('Share This Link', url=bot_link))
    bot.reply_to(
        message,
        f" *Your Referral Link*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"`{bot_link}`\n\n"
        f"For every friend who joins using your link:\n"
        f"You earn *+{REFERRAL_BONUS} credits*\n"
        f"They get *{FREE_CREDITS} free credits* to start\n\n"
        f"Share & stack that bag! ",
        reply_markup=markup, parse_mode='Markdown'
    )

def _logic_contact_owner(message):
    _set_reply_context(message)
    markup = types.InlineKeyboardMarkup()
    markup.add(premium_inline_button(f'DM {CREDIT}', url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}'))
    bot.reply_to(message, "Tap below to reach the developer:", reply_markup=markup)

def _logic_credits_panel(message):
    _set_reply_context(message)
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "Admin only."); return
    bot.reply_to(message, " *Credits Manager*", reply_markup=create_credits_panel(), parse_mode='Markdown')

def _logic_broadcast_init(message):
    _set_reply_context(message)
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "Admin only."); return
    msg = bot.reply_to(message, "Send your broadcast message. /cancel to abort.")
    bot.register_next_step_handler(msg, process_broadcast_message)

def _logic_toggle_lock_bot(message):
    _set_reply_context(message)
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "Admin only."); return
    global bot_locked
    bot_locked = not bot_locked
    status = "Locked" if bot_locked else "Unlocked"
    bot.reply_to(message, f"Bot is now *{status}*.", parse_mode='Markdown')

def _logic_admin_panel(message):
    _set_reply_context(message)
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "Admin only."); return
    bot.reply_to(message, " *Admin Panel*", reply_markup=create_admin_panel(), parse_mode='Markdown')

def _logic_run_all_scripts(moc):
    if isinstance(moc, types.Message):
        _set_reply_context(moc)
        uid = moc.from_user.id; msg_for_script = moc
        reply = lambda t, **kw: bot.reply_to(moc, t, **kw)
    else:
        uid = moc.from_user.id
        bot.answer_callback_query(moc.id)
        msg_for_script = moc.message
        reply = lambda t, **kw: bot.send_message(moc.message.chat.id, t, **kw)
    if uid not in admin_ids:
        reply("Admin only."); return
    reply("Starting all stopped scripts...")
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
    reply(f"Done! Started: `{started}` | Skipped: `{skipped}`", parse_mode='Markdown')

def _logic_send_command(message):
    _set_reply_context(message)
    if bot_locked and message.from_user.id not in admin_ids:
        bot.reply_to(message, "Bot locked."); return
    bot.reply_to(message, " *Send Command*", reply_markup=create_send_command_menu(), parse_mode='Markdown')

# ══════════════════════════════════════════════════════
#  BROADCAST
# ══════════════════════════════════════════════════════
def process_broadcast_message(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "Admin only."); return
    if message.text and message.text.lower() == '/cancel':
        bot.reply_to(message, "Broadcast cancelled."); return
    markup = types.InlineKeyboardMarkup()
    markup.row(
        premium_inline_button("Confirm", callback_data=f"confirm_broadcast_{message.message_id}"),
        premium_inline_button("Cancel", callback_data="cancel_broadcast")
    )
    preview = (message.text or "(media)")[:800]
    bot.reply_to(
        message,
        f"Broadcast to *{len(active_users)}* users?\n\n```\n{preview}\n```",
        reply_markup=markup, parse_mode='Markdown'
    )

def handle_confirm_broadcast(call):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "Admin only.", show_alert=True); return
    try:
        orig = call.message.reply_to_message
        if not orig: raise ValueError("Original not found.")
        text = photo = video = caption = None
        if orig.text: text = orig.text
        elif orig.photo: photo = orig.photo[-1].file_id; caption = orig.caption
        elif orig.video: video = orig.video.file_id; caption = orig.caption
        else: raise ValueError("Unsupported media.")
        bot.answer_callback_query(call.id, "Broadcasting...")
        bot.edit_message_text(f"Broadcasting to {len(active_users)} users...",
                              call.message.chat.id, call.message.message_id)
        threading.Thread(
            target=execute_broadcast,
            args=(text, photo, video, caption, call.message.chat.id)
        ).start()
    except Exception as e:
        bot.edit_message_text(f"Error: {e}", call.message.chat.id, call.message.message_id)

def handle_cancel_broadcast(call):
    bot.answer_callback_query(call.id, "Broadcast cancelled.")
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

def execute_broadcast(text, photo, video, caption, admin_cid):
    sent = failed = blocked = 0
    users = list(active_users)
    for i, uid in enumerate(users):
        try:
            if text: bot.send_message(uid, text, parse_mode='Markdown')
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
                    if text: bot.send_message(uid, text, parse_mode='Markdown')
                    elif photo: bot.send_photo(uid, photo, caption=caption)
                    elif video: bot.send_video(uid, video, caption=caption)
                    sent += 1
                except: failed += 1
            else: failed += 1
        except Exception: failed += 1
        if (i + 1) % 25 == 0: time.sleep(1.5)
        elif i % 5 == 0: time.sleep(0.2)
    result = (
        f" *Broadcast Complete!*\n"
        f"Sent: `{sent}` |  Failed: `{failed}` |  Blocked: `{blocked}`\n"
        f"Total: `{len(users)}`"
    )
    try: bot.send_message(admin_cid, result, parse_mode='Markdown')
    except Exception as e: logger.error(f"Broadcast result error: {e}")

# ══════════════════════════════════════════════════════
#  BUTTON TEXT MAP
# ══════════════════════════════════════════════════════
BUTTON_MAP = {
    "Upload File": _logic_upload_file, " HOST FILE": _logic_upload_file,
    "My Files": _logic_check_files, " MY FILES": _logic_check_files,
    "Speed Test": _logic_bot_speed, " SPEED TEST": _logic_bot_speed,
    "Statistics": _logic_statistics, " STATISTICS": _logic_statistics,
    "My Credits": _logic_my_credits, " MY CREDITS": _logic_my_credits,
    "Refer Friends": _logic_refer, " REFER FRIENDS": _logic_refer,
    "Send Command": _logic_send_command, " SEND COMMAND": _logic_send_command,
    "Contact Owner": _logic_contact_owner, " CONTACT OWNER": _logic_contact_owner,
    "Credits Panel": _logic_credits_panel, " CREDITS PANEL": _logic_credits_panel,
    "Broadcast": _logic_broadcast_init, " BROADCAST": _logic_broadcast_init,
    "Lock Bot": _logic_toggle_lock_bot, " LOCK BOT": _logic_toggle_lock_bot,
    "Unlock Bot": _logic_toggle_lock_bot, " UNLOCK BOT": _logic_toggle_lock_bot,
    "Run All Scripts": _logic_run_all_scripts, "▶️ RUN ALL": _logic_run_all_scripts,
    "Admin Panel": _logic_admin_panel, "🛡️ ADMIN PANEL": _logic_admin_panel,
}

# ══════════════════════════════════════════════════════
#  COMMAND & TEXT HANDLERS
# ══════════════════════════════════════════════════════
@bot.message_handler(commands=['menu', 'panel'])
def cmd_menu(message):
    _set_reply_context(message)
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        bot.send_message(
            message.chat.id,
            f"{PE_STATUS} <b>EVIL HOST</b>\n\n"
            f"{PE_OK} The bot is temporarily locked.\n"
            f"{PE_OWNER} Please contact the owner.",
            parse_mode='HTML'
        )
        return
    bot.send_message(
        message.chat.id,
        f"{PE_STAR} <b>EVIL HOST CONTROL DECK</b> {PE_STAR3}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{PE_OK} <b>HOST</b> • Upload & manage your bots\n"
        f"{PE_STAR2} <b>MANAGE</b> • Files • Processes • Logs\n"
        f"{PE_STATUS} <b>MONITOR</b> • Speed • Statistics\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Use the buttons below to control your hosting panel.</i>",
        reply_markup=create_main_menu_inline(user_id),
        parse_mode='HTML'
    )
    _set_reply_context(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
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
    _set_reply_context(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['mycredits'])
def cmd_mycredits(message):
    _logic_my_credits(message)
    _set_reply_context(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['refer'])
def cmd_refer(message):
    _logic_refer(message)
    _set_reply_context(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['addcredits'])
def cmd_addcredits(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "Admin only."); return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "Usage: `/addcredits USER_ID AMOUNT`", parse_mode='Markdown'); return
    try:
        uid = int(parts[1]); amount = int(parts[2])
        if amount <= 0: raise ValueError("Amount must be positive")
        add_credits(uid, amount, admin_id=message.from_user.id, action='admin_add')
        new_bal = get_credits(uid)
        bot.reply_to(message, f"Added `{amount}` credits to `{uid}`.\nNew balance: `{new_bal}`", parse_mode='Markdown')
        try:
            bot.send_message(uid,
                f" *Credits Added!*\n\n"
                f" +`{amount}` credits from admin.\n"
                f"New balance: `{new_bal}`",
                parse_mode='Markdown'
            )
        except: pass
    except (ValueError, IndexError) as e:
        bot.reply_to(message, f"Error: {e}")
    _set_reply_context(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['status'])
def cmd_status(message):
    _logic_statistics(message)
    _set_reply_context(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['ping'])
def cmd_ping(message):
    t0 = time.time()
    msg = bot.reply_to(message, "Pong!")
    lat = round((time.time() - t0) * 1000, 2)
    bot.edit_message_text(f"Pong! `{lat} ms`", message.chat.id, msg.message_id, parse_mode='Markdown')
    _set_reply_context(message)
    threading.Thread(target=auto_react, args=(message,)).start()

@bot.message_handler(commands=['uploadfile'])
def cmd_upload(m):
    _logic_upload_file(m)
    _set_reply_context(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['checkfiles'])
def cmd_check(m):
    _logic_check_files(m)
    _set_reply_context(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['speed'])
def cmd_speed(m):
    _logic_bot_speed(m)
    _set_reply_context(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['stats'])
def cmd_stats(m):
    _logic_statistics(m)
    _set_reply_context(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['sendcommand'])
def cmd_sendcmd(m):
    _logic_send_command(m)
    _set_reply_context(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['contact'])
def cmd_contact(m):
    _logic_contact_owner(m)
    _set_reply_context(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['lock'])
def cmd_lock(m):
    _logic_toggle_lock_bot(m)
    _set_reply_context(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['runall'])
def cmd_runall(m):
    _logic_run_all_scripts(m)
    _set_reply_context(m)
    threading.Thread(target=auto_react, args=(m,)).start()

@bot.message_handler(commands=['admin'])
def cmd_admin(m):
    _logic_admin_panel(m)
    _set_reply_context(m)
    threading.Thread(target=auto_react, args=(m,)).start()

def _normalize_menu_button(text):
    if not text:
        return None
    raw = str(text).strip()
    normalized = re.sub(r'^[^A-Za-z0-9]+', '', raw).strip()
    aliases = {
        'HOST FILE': 'Upload File',
        'MY FILES': 'My Files',
        'SPEED TEST': 'Speed Test',
        'STATISTICS': 'Statistics',
        'MY CREDITS': 'My Credits',
        'REFER FRIENDS': 'Refer Friends',
        'SEND COMMAND': 'Send Command',
        'CONTACT OWNER': 'Contact Owner',
        'CREDITS PANEL': 'Credits Panel',
        'BROADCAST': 'Broadcast',
        'LOCK BOT': 'Lock Bot',
        'UNLOCK BOT': 'Lock Bot',
        'RUN ALL': 'Run All Scripts',
        'ADMIN PANEL': 'Admin Panel',
    }
    return aliases.get(normalized) or BUTTON_MAP.get(raw)

@bot.message_handler(func=lambda m: _normalize_menu_button(m.text) is not None)
def handle_buttons(message):
    key = _normalize_menu_button(message.text)
    fn = BUTTON_MAP.get(key)
    if fn:
        fn(message)
    _set_reply_context(message)
    threading.Thread(target=auto_react, args=(message,), daemon=True).start()

@bot.message_handler(content_types=['text'], func=lambda m: True)
def _global_auto_reaction(message):
    _set_reply_context(message)
    threading.Thread(target=auto_react, args=(message,), daemon=True).start()

# ══════════════════════════════════════════════════════
#  SECURITY REVIEW / ADMIN APPROVAL QUEUE
# ══════════════════════════════════════════════════════
PENDING_APPROVAL_DIR = os.path.join(DATA_DIR, 'pending_approvals')
os.makedirs(PENDING_APPROVAL_DIR, exist_ok=True)

def _pending_paths(request_id):
    return (
        os.path.join(PENDING_APPROVAL_DIR, f'{request_id}.bin'),
        os.path.join(PENDING_APPROVAL_DIR, f'{request_id}.json')
    )

def queue_security_review(message, content, file_name, reason):
    request_id = uuid.uuid4().hex[:12]
    bin_path, meta_path = _pending_paths(request_id)
    try:
        with open(bin_path, 'wb') as f:
            f.write(content)
        meta = {
            'request_id': request_id,
            'user_id': int(message.from_user.id),
            'chat_id': int(message.chat.id),
            'file_name': file_name,
            'reason': str(reason),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        logger.error(f'Could not queue security review: {e}', exc_info=True)
        return False
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        premium_inline_button('APPROVE & HOST', callback_data=f'approve_pending_{request_id}'),
        premium_inline_button('REJECT', callback_data=f'reject_pending_{request_id}')
    )
    body = (
        f'{PE_DEV} <b>SECURITY REVIEW REQUIRED</b>\n\n'
        f'{PE_VIEW} File : <code>{_html_escape(file_name)}</code>\n'
        f'{PE_OWNER} User ID : <code>{message.from_user.id}</code>\n'
        f'{PE_TIME} Reason : <code>{_html_escape(str(reason))}</code>\n'
        f'{PE_STATUS} Request : <code>{request_id}</code>\n\n'
        f'{PE_TIME} The file is quarantined and will <b>NOT</b> run unless an admin approves it.'
    )
    text, _ = premium_card('EVIL HOST SECURITY', body)
    sent = 0
    for admin_id in list(admin_ids):
        try:
            try:
                bot.forward_message(admin_id, message.chat.id, message.message_id)
            except Exception as forward_error:
                logger.warning(f'Original forward failed for {admin_id}: {forward_error}')
                try:
                    with open(bin_path, 'rb') as fh:
                        bot.send_document(admin_id, fh, caption=f'Uploaded file: {file_name}')
                except Exception as send_error:
                    logger.error(f'File delivery failed for {admin_id}: {send_error}', exc_info=True)
                    continue
            bot.send_message(admin_id, text, reply_markup=markup, parse_mode='HTML')
            sent += 1
        except Exception as e:
            logger.error(f'Approval notification failed for {admin_id}: {e}', exc_info=True)
    return sent > 0

def _load_pending(request_id):
    bin_path, meta_path = _pending_paths(request_id)
    if not os.path.exists(bin_path) or not os.path.exists(meta_path):
        return None, None, None
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        if meta.get('status') != 'pending':
            return None, None, None
        with open(bin_path, 'rb') as f:
            content = f.read()
        return meta, content, (bin_path, meta_path)
    except Exception as e:
        logger.error(f'Pending request read failed: {e}', exc_info=True)
        return None, None, None

def _finish_pending(request_id, status):
    bin_path, meta_path = _pending_paths(request_id)
    try:
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            meta['status'] = status
            meta['resolved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)
        if os.path.exists(bin_path):
            os.remove(bin_path)
        if os.path.exists(meta_path):
            os.remove(meta_path)
    except Exception as e:
        logger.error(f'Pending cleanup failed: {e}', exc_info=True)

def _approval_message(user_id, chat_id):
    return SimpleNamespace(
        chat=SimpleNamespace(id=chat_id),
        from_user=SimpleNamespace(id=user_id)
    )

def approve_pending_callback(call):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, 'Admin only.', show_alert=True); return
    request_id = call.data[len('approve_pending_'):]
    meta, content, paths = _load_pending(request_id)
    if not meta:
        bot.answer_callback_query(call.id, 'Request already resolved or expired.', show_alert=True); return
    user_id = int(meta['user_id'])
    fname = meta['file_name']
    folder = get_user_folder(user_id)
    dest = os.path.join(folder, fname)
    try:
        if not deduct_credit(user_id):
            bot.answer_callback_query(call.id, 'User has no credits.', show_alert=True)
            return
        with open(dest, 'wb') as f:
            f.write(content)
        _finish_pending(request_id, 'approved')
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id,
            f'{PE_OK} <b>APPROVED & HOSTED</b>\n\n{PE_VIEW} File : <code>{_html_escape(fname)}</code>\n{PE_OWNER} Approved by : <code>{call.from_user.id}</code>',
            parse_mode='HTML')
        try:
            bot.send_message(user_id,
                f'{PE_OK} <b>SECURITY REVIEW APPROVED</b>\n\n{PE_VIEW} Your file <code>{_html_escape(fname)}</code> was approved by the admin and is now being hosted.',
                parse_mode='HTML')
        except Exception: pass
        msg = _approval_message(user_id, int(meta['chat_id']))
        if fname.lower().endswith('.py'):
            handle_py_file(dest, user_id, folder, fname, msg)
        elif fname.lower().endswith('.js'):
            handle_js_file(dest, user_id, folder, fname, msg)
        elif fname.lower().endswith('.zip'):
            handle_zip_file(content, fname, msg)
        elif fname.lower() == 'requirements.txt':
            install_requirements(folder, msg)
    except Exception as e:
        if os.path.exists(dest):
            try: os.remove(dest)
            except Exception: pass
        try: add_credits(user_id, 1, action='approval_refund')
        except Exception: pass
        bot.send_message(call.message.chat.id, f'{PE_TIME} <b>Approval hosting failed:</b> <code>{_html_escape(str(e))}</code>', parse_mode='HTML')

def reject_pending_callback(call):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, 'Admin only.', show_alert=True); return
    request_id = call.data[len('reject_pending_'):]
    meta, content, paths = _load_pending(request_id)
    if not meta:
        bot.answer_callback_query(call.id, 'Request already resolved or expired.', show_alert=True); return
    fname = meta['file_name']; user_id = int(meta['user_id'])
    _finish_pending(request_id, 'rejected')
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception: pass
    bot.answer_callback_query(call.id, 'Rejected.')
    bot.send_message(call.message.chat.id,
        f'{PE_TIME} <b>FILE REJECTED</b>\n\n{PE_VIEW} File : <code>{_html_escape(fname)}</code>\n{PE_OWNER} Rejected by : <code>{call.from_user.id}</code>',
        parse_mode='HTML')
    try:
        bot.send_message(user_id,
            f'{PE_TIME} <b>SECURITY REVIEW REJECTED</b>\n\n{PE_VIEW} Your file <code>{_html_escape(fname)}</code> was rejected by the admin and was not hosted.',
            parse_mode='HTML')
    except Exception: pass

# ══════════════════════════════════════════════════════
#  FILE UPLOAD HANDLER
# ══════════════════════════════════════════════════════
@bot.message_handler(content_types=['document'])
def handle_document(message):
    _set_reply_context(message)
    user_id = message.from_user.id
    threading.Thread(target=auto_react, args=(message,), daemon=True).start()
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "Bot locked."); return
    credits = get_credits(user_id)
    if credits != float('inf') and credits <= 0:
        markup = types.InlineKeyboardMarkup()
        markup.add(premium_inline_button('Get Credits', callback_data='refer'))
        markup.add(premium_inline_button('Contact Owner', url=f'https://t.me/{YOUR_USERNAME.lstrip("@")}'))
        bot.reply_to(message, "No credits! Refer friends or contact the owner.", reply_markup=markup); return
    doc = message.document
    if not doc: return
    fname = doc.file_name or 'uploaded_file'
    lower = fname.lower()
    if not (lower.endswith(('.py', '.js', '.zip')) or lower == 'requirements.txt'):
        bot.reply_to(message, f"Only .py, .js, .zip or requirements.txt allowed. Got: {fname}"); return
    if doc.file_size > 50 * 1024 * 1024:
        bot.reply_to(message, "File too large (>50 MB)."); return
    try:
        info = bot.get_file(doc.file_id)
        content = bot.download_file(info.file_path)
    except Exception as e:
        bot.reply_to(message, f"Download failed: {e}"); return
    deploy_loading = premium_loading(message.chat.id, "SECURITY REVIEW")
    ok, reason = scan_file(content, fname, user_id)
    review_reason = "Automatic security scan passed; awaiting mandatory admin approval." if ok else reason
    queued = queue_security_review(message, content, fname, review_reason)
    premium_loading_done(message.chat.id, deploy_loading, "ADMIN REVIEW PENDING",
        f"{PE_LOADING2} <b>Upload received and quarantined.</b>\n\n"
        f"{PE_VIEW} File : <code>{_html_escape(fname)}</code>\n"
        f"{PE_ADMIN} Status : <b>WAITING FOR ADMIN APPROVAL</b>\n"
        f"{PE_SIGNAL} The file will not be hosted or executed before approval.")
    if not queued:
        bot.send_message(message.chat.id, f"{PE_TIME} Could not create the admin review request. Please contact the owner.", parse_mode='HTML')

# ══════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ══════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data
    if bot_locked and user_id not in admin_ids and data not in ['speed', 'stats', 'my_credits', 'refer', 'back_to_main']:
        bot.answer_callback_query(call.id, "Bot locked.", show_alert=True); return
    try:
        bot.answer_callback_query(call.id)
        if data.startswith('approve_pending_'): approve_pending_callback(call)
        elif data.startswith('reject_pending_'): reject_pending_callback(call)
        elif data == 'upload': upload_callback(call)
        elif data == 'check_files': check_files_callback(call)
        elif data.startswith('file_'): file_control_callback(call)
        elif data.startswith('start_'): start_bot_callback(call)
        elif data.startswith('stop_'): stop_bot_callback(call)
        elif data.startswith('restart_'): restart_bot_callback(call)
        elif data.startswith('delete_'): delete_bot_callback(call)
        elif data.startswith('logs_'): logs_bot_callback(call)
        elif data == 'speed': speed_callback(call)
        elif data == 'stats': stats_callback(call)
        elif data == 'my_credits': my_credits_callback(call)
        elif data == 'refer': refer_callback(call)
        elif data == 'back_to_main': back_to_main_callback(call)
        elif data == 'send_command': send_command_callback(call)
        elif data == 'send_to_process': send_to_process_callback(call)
        elif data.startswith('sendcmd_select_'): sendcmd_select_callback(call)
        elif data == 'view_all_logs': view_all_logs_callback(call)
        elif data.startswith('viewlog_'): viewlog_callback(call)
        elif data == 'credits_panel': _admin_cb(call, credits_panel_callback)
        elif data == 'add_credits_init': _admin_cb(call, add_credits_init_callback)
        elif data == 'remove_credits_init': _admin_cb(call, remove_credits_init_callback)
        elif data == 'check_credits_init': _admin_cb(call, check_credits_init_callback)
        elif data == 'credit_history': _admin_cb(call, credit_history_callback)
        elif data == 'broadcast': _admin_cb(call, broadcast_init_callback)
        elif data == 'lock_bot': _admin_cb(call, lock_bot_callback)
        elif data == 'unlock_bot': _admin_cb(call, unlock_bot_callback)
        elif data == 'run_all_scripts': _admin_cb(call, run_all_scripts_callback)
        elif data == 'admin_panel': _admin_cb(call, admin_panel_callback)
        elif data == 'gen_redeem': _admin_cb(call, gen_redeem_callback)
        elif data == 'user_see': _admin_cb(call, user_see_callback)
        elif data == 'add_admin': _owner_cb(call, add_admin_init_callback)
        elif data == 'remove_admin': _owner_cb(call, remove_admin_init_callback)
        elif data == 'list_admins': _admin_cb(call, list_admins_callback)
        elif data.startswith('confirm_broadcast_'): handle_confirm_broadcast(call)
        elif data == 'cancel_broadcast': handle_cancel_broadcast(call)
        else:
            bot.answer_callback_query(call.id, "Unknown action.")
    except Exception as e:
        logger.error(f"Callback '{data}' for {user_id}: {e}", exc_info=True)
        try: bot.answer_callback_query(call.id, "Error.", show_alert=True)
        except: pass

def _admin_cb(call, fn):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "Admin only.", show_alert=True); return
    fn(call)

def _owner_cb(call, fn):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "Owner only.", show_alert=True); return
    fn(call)

# ══════════════════════════════════════════════════════
#  CALLBACK IMPLEMENTATIONS
# ══════════════════════════════════════════════════════
def upload_callback(call):
    user_id = call.from_user.id
    credits = get_credits(user_id)
    if credits != float('inf') and credits <= 0:
        bot.answer_callback_query(call.id, "No credits left! Refer friends or contact owner.", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    credits_str = "∞" if credits == float('inf') else str(credits)
    bot.send_message(
        call.message.chat.id,
        f"Send your `.py`, `.js`, `.zip`, or `requirements.txt` file.\n Credits: `{credits_str}`",
        parse_mode='Markdown'
    )

def check_files_callback(call):
    user_id = call.from_user.id
    files = sync_user_files(user_id)
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    if not files:
        body = f"{PE_VIEW} <b>No hosted files found.</b>\n\n{PE_OK} Upload a <code>.py</code>, <code>.js</code> or <code>.zip</code> file to begin."
    else:
        for fn, ft in files:
            running = is_bot_running(user_id, fn)
            label = f"{fn}  •  {ft.upper()}  •  {'RUNNING' if running else 'STOPPED'}"
            markup.add(premium_inline_button(label, callback_data=f'file_{user_id}_{fn}'))
        body = f"{PE_VIEW} <b>{len(files)} hosted file(s)</b>\n{PE_OK} Select a file to manage its process.\n{PE_TIME} Live status is checked when selected."
    text, _ = premium_card("MY FILES", body, copy_value="EVIL HOST BOT")
    try:
        markup.keyboard.insert(0, [types.InlineKeyboardButton("COPY CODE", icon_custom_emoji_id=PREMIUM_BUTTON_IDS["ok"], style="success", copy_text=types.CopyTextButton(text="EVIL HOST BOT"))])
    except Exception:
        pass
    markup.add(premium_inline_button("BACK TO PANEL", callback_data='back_to_main'))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
        if "not modified" not in str(e): logger.error(f"check_files CB: {e}")

def file_control_callback(call):
    try:
        _, oid_str, fname = call.data.split('_', 2)
        oid = int(oid_str); uid = call.from_user.id
        if not (uid == oid or uid in admin_ids):
            bot.answer_callback_query(call.id, "Permission denied.", show_alert=True); return
        files = sync_user_files(oid)
        fi = next((f for f in files if f[0] == fname), None)
        if not fi:
            bot.answer_callback_query(call.id, "File not found.", show_alert=True); return
        bot.answer_callback_query(call.id)
        running = is_bot_running(oid, fname)
        ft = fi[1]
        status = f"{PE_OK} <b>RUNNING</b>" if running else f"{PE_TIME} <b>STOPPED</b>"
        body = (
            f"{PE_VIEW} <b>File</b> : <code>{_html_escape(fname)}</code>\n"
            f"{PE_DEV} <b>Type</b> : <code>{_html_escape(ft.upper())}</code>\n"
            f"{PE_OWNER} <b>Owner</b> : <code>{oid}</code>\n"
            f"{PE_VIEW} <b>Status</b> : {status}"
        )
        text, _ = premium_card("FILE CONTROL", body, copy_value=fname, copy_label="COPY FILE NAME")
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(oid, fname, running), parse_mode='HTML')
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
            bot.answer_callback_query(call.id, "Permission denied.", show_alert=True); return
        files = user_files.get(oid, [])
        fi = next((f for f in files if f[0] == fname), None)
        if not fi:
            bot.answer_callback_query(call.id, "File not found.", show_alert=True); return
        ft = fi[1]; folder = get_user_folder(oid); fpath = os.path.join(folder, fname)
        if not os.path.exists(fpath):
            bot.answer_callback_query(call.id, "File missing. Re-upload.", show_alert=True)
            remove_user_file_db(oid, fname); return
        if is_bot_running(oid, fname):
            bot.answer_callback_query(call.id, "Already running.", show_alert=True); return
        bot.answer_callback_query(call.id, f"▶ Starting {fname}...")
        set_hosted_process_state(oid, fname, ft, True)
        fn = run_script if ft == 'py' else run_js_script
        threading.Thread(target=fn, args=(fpath, oid, folder, fname, call.message)).start()
        time.sleep(3.5)
        running = is_bot_running(oid, fname)
        status = "Running" if running else "Starting..."
        try:
            bot.edit_message_text(
                f" *{fname}* `[{ft}]`\nStatus: {status}",
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
            bot.answer_callback_query(call.id, "Permission denied.", show_alert=True); return
        files = user_files.get(oid, [])
        fi = next((f for f in files if f[0] == fname), None)
        if not fi:
            bot.answer_callback_query(call.id, "File not found.", show_alert=True); return
        ft = fi[1]; key = f"{oid}_{fname}"
        if not is_bot_running(oid, fname):
            bot.answer_callback_query(call.id, "Not running.", show_alert=True); return
        bot.answer_callback_query(call.id, f"Stopping {fname}...")
        set_hosted_process_state(oid, fname, ft, False)
        info = bot_scripts.get(key)
        if info: kill_process_tree(info)
        bot_scripts.pop(key, None)
        try:
            bot.edit_message_text(
                f" *{fname}* `[{ft}]`\nStatus:  Stopped",
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
            bot.answer_callback_query(call.id, "Permission denied.", show_alert=True); return
        files = user_files.get(oid, [])
        fi = next((f for f in files if f[0] == fname), None)
        if not fi:
            bot.answer_callback_query(call.id, "File not found.", show_alert=True); return
        ft = fi[1]; folder = get_user_folder(oid); fpath = os.path.join(folder, fname)
        if not os.path.exists(fpath):
            bot.answer_callback_query(call.id, "File missing. Re-upload.", show_alert=True)
            remove_user_file_db(oid, fname); return
        bot.answer_callback_query(call.id, f"Restarting {fname}...")
        set_hosted_process_state(oid, fname, ft, True)
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
        status = "Running" if running else "Starting..."
        try:
            bot.edit_message_text(
                f" *{fname}* `[{ft}]`\nStatus: {status}",
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
            bot.answer_callback_query(call.id, "Permission denied.", show_alert=True); return
        remove_hosted_process_state(oid, fname)
        if not any(f[0] == fname for f in user_files.get(oid, [])):
            bot.answer_callback_query(call.id, "File not found.", show_alert=True); return
        bot.answer_callback_query(call.id, f"Deleting {fname}...")
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
                f" `{fname}` deleted.",
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
            bot.answer_callback_query(call.id, "Permission denied.", show_alert=True); return
        if not any(f[0] == fname for f in user_files.get(oid, [])):
            bot.answer_callback_query(call.id, "File not found.", show_alert=True); return
        log_path = os.path.join(get_user_folder(oid), f"{os.path.splitext(fname)[0]}.log")
        if not os.path.exists(log_path):
            bot.answer_callback_query(call.id, "No logs yet.", show_alert=True); return
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
            f" *Logs — `{fname}`*:\n```\n{content}\n```",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"logs CB: {e}")
        bot.answer_callback_query(call.id, "Error fetching logs.", show_alert=True)

def speed_callback(call):
    uid = call.from_user.id; cid = call.message.chat.id
    t0 = time.time()
    try:
        ms = round((time.time() - t0) * 1000, 2)
        lvl = get_user_status_str(uid)
        body = (
            f"{PE_OK} <b>Ping</b> : <code>{ms} ms</code>\n"
            f"{PE_VIEW} <b>Bot</b> : <code>{'LOCKED' if bot_locked else 'ONLINE'}</code>\n"
            f"{PE_OWNER} <b>You</b> : {lvl}"
        )
        text, _ = premium_card("SPEED REPORT", body, copy_value=f"Ping: {ms} ms", copy_label="COPY REPORT")
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, cid, call.message.message_id, reply_markup=create_main_menu_inline(uid), parse_mode='HTML')
    except Exception as e:
        bot.answer_callback_query(call.id, "Speed test error.", show_alert=True)

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
    files = get_user_file_count(uid)
    body = (
        f"{PE_OK} <b>Welcome back, {_html_escape(call.from_user.first_name or 'User').upper()}.</b>\n\n"
        f"{PE_VIEW} Status : {status}\n"
        f"{PE_DEV} Credits : <code>{credits_str}</code>\n"
        f"{PE_TIME} Hosted : <code>{files}</code>\n\n"
        f"{PE_OWNER} Select an action from your EVIL HOST control deck."
    )
    text, _ = premium_card("EVIL HOST CONTROL DECK", body)
    try:
        bot.answer_callback_query(call.id)
        if getattr(call.message, 'content_type', '') == 'video':
            bot.send_message(call.message.chat.id, text, reply_markup=create_main_menu_inline(uid), parse_mode='HTML')
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                  reply_markup=create_main_menu_inline(uid), parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
        if 'there is no text in the message to edit' in str(e).lower():
            bot.send_message(call.message.chat.id, text, reply_markup=create_main_menu_inline(uid), parse_mode='HTML')
        elif 'not modified' not in str(e).lower():
            logger.error(f'back_to_main: {e}')

def send_command_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(" *Send Command*", call.message.chat.id, call.message.message_id,
                              reply_markup=create_send_command_menu(), parse_mode='Markdown')
    except Exception as e: logger.error(f"send_command CB: {e}")

def send_to_process_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "Type your command:")
    bot.register_next_step_handler(msg, send_to_process_init)

def sendcmd_select_callback(call):
    key = call.data.replace('sendcmd_select_', '')
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"Command for `{key}`:", parse_mode='Markdown')
    bot.register_next_step_handler(msg, lambda m: process_send_command(m, key))

def view_all_logs_callback(call):
    bot.answer_callback_query(call.id)
    view_all_logs(call.message)

def viewlog_callback(call):
    try:
        _, uid_str, lf = call.data.split('_', 2)
        uid = int(uid_str); req = call.from_user.id
        if not (req == uid or req in admin_ids):
            bot.answer_callback_query(call.id, "Permission denied.", show_alert=True); return
        lpath = os.path.join(get_user_folder(uid), lf)
        if not os.path.exists(lpath):
            bot.answer_callback_query(call.id, "Log not found.", show_alert=True); return
        bot.answer_callback_query(call.id, "Sending...")
        send_log_file(call.message, lpath, lf)
    except Exception as e:
        logger.error(f"viewlog CB: {e}")
        bot.answer_callback_query(call.id, "Error.", show_alert=True)

def credits_panel_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(" *Credits Manager*",
            call.message.chat.id, call.message.message_id,
            reply_markup=create_credits_panel(), parse_mode='Markdown')
    except Exception as e: logger.error(f"credits panel CB: {e}")

def add_credits_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        "Enter: `USER_ID AMOUNT`\n/cancel to abort.", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_add_credits)

def process_add_credits(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "Admin only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        parts = message.text.split()
        if len(parts) != 2: raise ValueError("Format: USER_ID AMOUNT")
        uid = int(parts[0]); amount = int(parts[1])
        if amount <= 0: raise ValueError("Amount must be positive")
        add_credits(uid, amount, admin_id=message.from_user.id, action='admin_add')
        new_bal = get_credits(uid)
        bot.reply_to(message, f"Added `{amount}` credits to `{uid}`.\nBalance: `{new_bal}`", parse_mode='Markdown')
        try:
            bot.send_message(uid,
                f" *Credits Added!*\n+`{amount}` credits by admin.\n Balance: `{new_bal}`",
                parse_mode='Markdown')
        except: pass
    except ValueError as e:
        msg = bot.reply_to(message, f" {e}. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_add_credits)

def remove_credits_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        "Enter: `USER_ID AMOUNT`\n/cancel to abort.", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_remove_credits)

def process_remove_credits(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "Admin only."); return
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
        bot.reply_to(message, f"Removed `{amount}` from `{uid}`. New balance: `{new_bal}`", parse_mode='Markdown')
    except ValueError as e:
        msg = bot.reply_to(message, f" {e}. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_remove_credits)

def check_credits_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        "Enter User ID to check. /cancel to abort.")
    bot.register_next_step_handler(msg, process_check_credits)

def process_check_credits(message):
    if message.from_user.id not in admin_ids: bot.reply_to(message, "Admin only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        uid = int(message.text.strip())
        credits = get_credits(uid)
        credits_str = "∞ (Admin/Owner)" if credits == float('inf') else str(credits)
        status = get_user_status_str(uid)
        bot.reply_to(message,
            f"Credits for `{uid}`:\n"
            f"Balance: `{credits_str}`\n"
            f"Status: {status}",
            parse_mode='Markdown')
    except ValueError:
        msg = bot.reply_to(message, "Invalid ID. /cancel to abort.")
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
            text = " *Credit History*\n\nNo transactions yet."
        else:
            lines = [" *Credit History*", ""]
            for uid, aid, action, amount, balance, created in rows:
                bal = "∞" if balance is None else str(balance)
                who = "System" if aid is None else str(aid)
                lines.append(f"• `{uid}` — *{action}* `{amount}` | Bal: `{bal}` | By: `{who}`")
                lines.append(f"   {created}")
            text = "\n".join(lines)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=create_credits_panel(), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"credit history CB: {e}")
        try: bot.answer_callback_query(call.id, "Could not load history.", show_alert=True)
        except: pass

def lock_bot_callback(call):
    global bot_locked; bot_locked = True
    bot.answer_callback_query(call.id, "Bot locked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                       reply_markup=create_main_menu_inline(call.from_user.id))
    except: pass

def unlock_bot_callback(call):
    global bot_locked; bot_locked = False
    bot.answer_callback_query(call.id, "Bot unlocked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                       reply_markup=create_main_menu_inline(call.from_user.id))
    except: pass

def run_all_scripts_callback(call): _logic_run_all_scripts(call)

def broadcast_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "Send broadcast message. /cancel to abort.")
    bot.register_next_step_handler(msg, process_broadcast_message)

def admin_panel_callback(call):
    bot.answer_callback_query(call.id)
    body = f"{PE_OWNER} <b>Administrator control center</b>\n\n{PE_OK} Manage admins, credits and bot operations."
    text, _ = premium_card("ADMIN CONTROL PANEL", body)
    try:
        if getattr(call.message, 'content_type', '') == 'video':
            bot.send_message(call.message.chat.id, text, reply_markup=create_admin_panel(), parse_mode='HTML')
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                  reply_markup=create_admin_panel(), parse_mode='HTML')
    except Exception as e:
        if 'there is no text in the message to edit' in str(e).lower():
            bot.send_message(call.message.chat.id, text, reply_markup=create_admin_panel(), parse_mode='HTML')
        else:
            logger.error(f"admin panel CB: {e}")

def add_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        "Enter Telegram User ID to promote.\n/cancel to abort.")
    bot.register_next_step_handler(msg, process_add_admin_id)

def process_add_admin_id(message):
    if message.from_user.id != OWNER_ID: bot.reply_to(message, "Owner only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        nid = int(message.text.strip())
        if nid == OWNER_ID: bot.reply_to(message, "Already owner."); return
        if nid in admin_ids: bot.reply_to(message, f" `{nid}` already admin.", parse_mode='Markdown'); return
        add_admin_db(nid)
        bot.reply_to(message, f" `{nid}` promoted to Admin.", parse_mode='Markdown')
        try: bot.send_message(nid, "You are now an Admin of EvilHostsBot!")
        except: pass
    except ValueError:
        msg = bot.reply_to(message, "Invalid ID. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_add_admin_id)

def remove_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "Enter Admin ID to demote. /cancel to abort.")
    bot.register_next_step_handler(msg, process_remove_admin_id)

def process_remove_admin_id(message):
    if message.from_user.id != OWNER_ID: bot.reply_to(message, "Owner only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Cancelled."); return
    try:
        rid = int(message.text.strip())
        if rid == OWNER_ID: bot.reply_to(message, "Cannot demote owner."); return
        if rid not in admin_ids: bot.reply_to(message, f" `{rid}` not admin.", parse_mode='Markdown'); return
        if remove_admin_db(rid):
            bot.reply_to(message, f"Admin `{rid}` removed.", parse_mode='Markdown')
            try: bot.send_message(rid, "ℹ Admin access revoked.")
            except: pass
        else:
            bot.reply_to(message, f"Failed to remove `{rid}`.", parse_mode='Markdown')
    except ValueError:
        msg = bot.reply_to(message, "Invalid ID. /cancel to abort.")
        bot.register_next_step_handler(msg, process_remove_admin_id)

def list_admins_callback(call):
    bot.answer_callback_query(call.id)
    lines = "\n".join(f"• `{a}` {'Owner' if a == OWNER_ID else 'Admin'}" for a in sorted(admin_ids))
    try:
        bot.edit_message_text(
            f" *Admin List:*\n\n{lines or '(none)'}",
            call.message.chat.id, call.message.message_id,
            reply_markup=create_admin_panel(), parse_mode='Markdown'
        )
    except Exception as e: logger.error(f"list_admins CB: {e}")

def gen_redeem_callback(call):
    if call.from_user.id not in admin_ids: return
    code = "EV-" + uuid.uuid4().hex[:10].upper()
    amount = 1
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS redeem_codes (code TEXT PRIMARY KEY, amount INTEGER NOT NULL, used_by INTEGER, created_at TEXT NOT NULL)")
        conn.execute("INSERT INTO redeem_codes(code,amount,used_by,created_at) VALUES (?,?,NULL,?)", (code, amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    finally: conn.close()
    bot.send_message(call.message.chat.id, f"{PE_REDEEM} <b>REDEEM GENERATED</b>\n\n<code>{code}</code>\n{PE_CREDITS} Credits: <b>{amount}</b>", parse_mode='HTML')

def user_see_callback(call):
    if call.from_user.id not in admin_ids: return
    rows = sorted(active_users)
    preview = rows[-50:]
    body = f"{PE_USER_SEE} <b>Total Users:</b> <code>{len(rows)}</code>\n\n" + "\n".join(f"• <code>{uid}</code>" for uid in preview)
    bot.send_message(call.message.chat.id, f"{PE_ADMIN} <b>USER LIST</b>\n\n{body}", parse_mode='HTML')

@bot.message_handler(func=lambda message: bool(message.text) and message.text in {
    " HOST FILE", " MY FILES", " SPEED TEST", " STATISTICS",
    " MY CREDITS", " REFER FRIENDS", " SEND COMMAND", " CONTACT OWNER",
    " CREDITS PANEL", " BROADCAST", " LOCK BOT", " UNLOCK BOT",
    "▶️ RUN ALL", "🛡️ ADMIN PANEL",
})
def reply_keyboard_router(message):
    action = message.text
    actions = {
        " HOST FILE": _logic_upload_file,
        " MY FILES": _logic_check_files,
        " SPEED TEST": _logic_bot_speed,
        " STATISTICS": _logic_statistics,
        " MY CREDITS": _logic_my_credits,
        " REFER FRIENDS": _logic_refer,
        " SEND COMMAND": _logic_send_command,
        " CONTACT OWNER": _logic_contact_owner,
        " CREDITS PANEL": _logic_credits_panel,
        " BROADCAST": _logic_broadcast_init,
        " LOCK BOT": _logic_toggle_lock_bot,
        " UNLOCK BOT": _logic_toggle_lock_bot,
        "▶️ RUN ALL": _logic_run_all_scripts,
        "🛡️ ADMIN PANEL": _logic_admin_panel,
    }
    fn = actions.get(action)
    if not fn:
        return
    if action in {" CREDITS PANEL", " BROADCAST", " LOCK BOT", " UNLOCK BOT", "▶️ RUN ALL", "🛡️ ADMIN PANEL"} and message.from_user.id not in admin_ids:
        bot.reply_to(message, "Admin only.")
        return
    try:
        fn(message)
    except Exception as e:
        logger.error(f"Reply keyboard action failed ({action}): {e}", exc_info=True)
        bot.reply_to(message, "Something went wrong. Please try again.")

@bot.message_handler(commands=['deploy'])
def menu_deploy(message): _logic_upload_file(message)

@bot.message_handler(commands=['mybots'])
def menu_mybots(message): _logic_check_files(message)

@bot.message_handler(commands=['logs'])
def menu_logs(message): view_all_logs(message)

@bot.message_handler(commands=['restart'])
def menu_restart(message):
    bot.reply_to(message, "Open /mybots and select the bot to restart.")

@bot.message_handler(commands=['stop'])
def menu_stop(message):
    bot.reply_to(message, "Open /mybots and select the bot to stop.")

@bot.message_handler(commands=['credits'])
def menu_credits(message): _logic_my_credits(message)

@bot.message_handler(commands=['broadcast'])
def menu_broadcast(message): _logic_broadcast_init(message)

# ══════════════════════════════════════════════════════
#  OFFICIAL TELEGRAM MENU COMMANDS
# ══════════════════════════════════════════════════════
def configure_bot_menu():
    try:
        bot.delete_my_commands(scope=types.BotCommandScopeDefault())
        bot.delete_my_commands(scope=types.BotCommandScopeChat(chat_id=OWNER_ID))
        for aid in list(admin_ids):
            if aid != OWNER_ID:
                bot.delete_my_commands(scope=types.BotCommandScopeChat(chat_id=aid))
        logger.info("Official Telegram command menu cleared; reply keyboard is the main UI.")
    except Exception as e:
        logger.error(f"Menu command cleanup failed: {e}", exc_info=True)

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
        f"   {BOT_NAME}\n"
        f"  Dev    : {CREDIT}\n"
        f"  Bot    : {BOT_USERNAME}\n"
        f"  Owner  : {OWNER_ID}\n"
        f"  Python : {sys.version.split()[0]}\n"
        f"{'═'*50}"
    )
    keep_alive()
    configure_bot_menu()
    start_persistent_supervisor()
    logger.info("Polling started...")
    while True:
        try:
            bot.infinity_polling(logger_level=logging.INFO, timeout=60, long_polling_timeout=30)
        except requests.exceptions.ReadTimeout:
            logger.warning("ReadTimeout — retry in 5s..."); time.sleep(5)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"ConnectionError: {e} — retry in 15s..."); time.sleep(15)
        except Exception as e:
            logger.critical(f"Polling crash: {e}", exc_info=True)
            time.sleep(30)
        finally:
            time.sleep(1)
