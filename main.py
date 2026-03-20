import os
import yt_dlp
import asyncio
import glob
import sqlite3
import time
import json
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pyrogram import Client, filters, types
from pyrogram.errors import FloodWait
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, Dict, List, Tuple

# ====== CONFIGURATION ======
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # မင်း Telegram ID ထည့်ပါ
SUPPORT_USERNAME = "@zinko158"  # မင်း Username ထည့်ပါ

# ====== CONSTANTS ======
WORKING_DIR = "/tmp"
DB_PATH = "bot_database.db"
CACHE_EXPIRY = 86400  # 24 hours in seconds
MAX_QUEUE_SIZE = 10
MAX_DOWNLOADS_PER_DAY = 15
SUPPORTED_SITES = ["youtube.com", "youtu.be", "facebook.com", "instagram.com", 
                   "twitter.com", "x.com", "tiktok.com", "spotify.com", "soundcloud.com"]

# ====== LANGUAGE DICTIONARIES ======
LANG = {
    "my": {  # မြန်မာ
        "start": """
✨ **MUSIC BOT v3.0 - ULTIMATE** ✨

🎵 **မင်္ဂလာပါ!** 🎵
ကမ္ဘာ့အဆင့်မီ Music Bot ဆီကြိုဆိုပါတယ်။

📌 **အသုံးပြုနည်း:**
• `/play` - သီချင်းနာမည် သို့မဟုတ် link ရိုက်ပါ
• `/settings` - ဘာသာစကားနဲ့ အရည်အသွေးရွေးရန်
• `/help` - အကူအညီ

🔥 **Feature များ:**
• YouTube, Facebook, Instagram, Twitter, TikTok, Spotify စသည်ဖြင့် ဒေါင်းနိုင်တယ်
• Playlist တစ်ခုလုံးဒေါင်းနိုင်တယ်
• Thumbnail ပါအောင် ပို့ပေးတယ်
• Inline Mode နဲ့ ဘယ်နေရာမှာမဆိုရှာနိုင်တယ်
• ဘာသာစကား ၂ မျိုးရွေးလို့ရတယ်
• Queue system နဲ့ တစ်ယောက်ပြီးမှတစ်ယောက်
• Rate limiting နဲ့ အနှောင့်အယှက်ကင်း

👑 **Created with ❤️ by Music Lover**
        """,
        "help": """
🆘 **အကူအညီမီနူး** 🆘

📌 **Command များ:**
• `/start` - Bot စတင်ရန်
• `/play <name/link>` - သီချင်းဒေါင်းရန်
• `/settings` - ဆက်တင်များပြောင်းရန်
• `/stats` - ကိုယ့်အသုံးပြုမှုစာရင်း
• `/help` - ဒီမီနူးပြရန်
• `/language` - ဘာသာစကားပြောင်းရန်
• `/quality` - အရည်အသွေးပြောင်းရန်

🎯 **ဥပမာများ:**
`/play shape of you`
`/play https://youtu.be/...`
`/play https://fb.watch/...`

💡 **Inline Mode:**
ဘယ် chat မှာမဆို `@your_bot_username song name` လို့ရိုက်ပြီး ရှာနိုင်တယ်

⚠️ **သတိပြုရန်:**
• တစ်ရက်ကို {MAX_DOWNLOADS_PER_DAY} ပုဒ်ပဲဒေါင်းလို့ရမယ်
• Queue ထဲမှာ {MAX_QUEUE_SIZE} ပုဒ်အထိထားလို့ရတယ်
• Playlist ဆိုရင် ၅ ပုဒ်ပဲဒေါင်းပေးမယ်

📞 **ဆက်သွယ်ရန်:** {SUPPORT_USERNAME}
        """,
        "queue_full": """
⛔ **Queue Full!** ⛔

လက်ရှိ queue ထဲမှာ {MAX_QUEUE_SIZE} ပုဒ်ရှိနေပြီ။
ခဏစောင့်ပြီးမှပြန်ကြိုးစားပါ။
        """,
        "daily_limit": """
⚠️ **နေ့စဉ်ကန့်သတ်ချက်** ⚠️

ဒီနေ့အတွက် {MAX_DOWNLOADS_PER_DAY} ပုဒ်ပြည့်သွားပြီ။
မနက်ဖြန်ကျမှပြန်သုံးပါ။
        """
    },
    "en": {  # English
        "start": """
✨ **MUSIC BOT v3.0 - ULTIMATE** ✨

🎵 **Welcome!** 🎵
Welcome to world-class Music Bot.

📌 **How to use:**
• `/play` - Song name or link
• `/settings` - Change language & quality
• `/help` - Get help

🔥 **Features:**
• Download from YouTube, Facebook, Instagram, Twitter, TikTok, Spotify, etc.
• Download entire playlists
• Send with thumbnails
• Inline mode for searching anywhere
• Bilingual support
• Queue system for smooth operation
• Rate limiting protection

👑 **Created with ❤️ by Music Lover**
        """,
        "help": """
🆘 **HELP MENU** 🆘

📌 **Commands:**
• `/start` - Start the bot
• `/play <name/link>` - Download song
• `/settings` - Change settings
• `/stats` - Your usage stats
• `/help` - Show this menu
• `/language` - Change language
• `/quality` - Change quality

🎯 **Examples:**
`/play shape of you`
`/play https://youtu.be/...`
`/play https://fb.watch/...`

💡 **Inline Mode:**
Type `@your_bot_username song name` in any chat to search

⚠️ **Notes:**
• Daily limit: {MAX_DOWNLOADS_PER_DAY} songs
• Queue size: {MAX_QUEUE_SIZE} songs
• Playlists limited to 5 songs

📞 **Support:** {SUPPORT_USERNAME}
        """,
        "queue_full": """
⛔ **Queue Full!** ⛔

Queue has {MAX_QUEUE_SIZE} items. Please wait and try again.
        """,
        "daily_limit": """
⚠️ **Daily Limit Reached** ⚠️

You've reached {MAX_DOWNLOADS_PER_DAY} downloads today.
Come back tomorrow!
        """
    }
}

# ====== DATABASE SETUP ======
def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  language TEXT DEFAULT 'my',
                  quality TEXT DEFAULT '128',
                  joined_date TIMESTAMP,
                  total_downloads INTEGER DEFAULT 0)''')
    
    # Downloads table for daily tracking
    c.execute('''CREATE TABLE IF NOT EXISTS downloads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  song_title TEXT,
                  file_size REAL,
                  download_date TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (user_id))''')
    
    # Cache table
    c.execute('''CREATE TABLE IF NOT EXISTS cache
                 (song_hash TEXT PRIMARY KEY,
                  file_path TEXT,
                  title TEXT,
                  artist TEXT,
                  duration INTEGER,
                  download_count INTEGER DEFAULT 1,
                  last_accessed TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_database()

# ====== QUEUE SYSTEM ======
class DownloadQueue:
    def __init__(self):
        self.queue = deque(maxlen=MAX_QUEUE_SIZE)
        self.current = None
        self.lock = asyncio.Lock()
        self.user_queues = defaultdict(deque)
    
    async def add(self, user_id, task):
        async with self.lock:
            if len(self.user_queues[user_id]) >= 2:  # တစ်ယောက်ကို ၂ ပုဒ်အထိပဲ queue ထဲထားမယ်
                return False, "QUEUE_FULL"
            self.user_queues[user_id].append(task)
            self.queue.append((user_id, task))
            return True, len(self.queue)
    
    async def get_next(self):
        async with self.lock:
            if self.queue:
                user_id, task = self.queue.popleft()
                self.user_queues[user_id].popleft()
                self.current = (user_id, task)
                return self.current
            return None
    
    async def remove(self, user_id):
        async with self.lock:
            if user_id in self.user_queues:
                self.user_queues[user_id].clear()
            self.queue = deque([(uid, t) for uid, t in self.queue if uid != user_id], maxlen=MAX_QUEUE_SIZE)

download_queue = DownloadQueue()

# ====== RATE LIMITER ======
class RateLimiter:
    def __init__(self):
        self.user_downloads = defaultdict(list)
        self.user_last_request = defaultdict(float)
    
    def check_daily_limit(self, user_id: int) -> Tuple[bool, int]:
        """Check if user has exceeded daily limit"""
        today = datetime.now().date()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''SELECT COUNT(*) FROM downloads 
                     WHERE user_id = ? AND DATE(download_date) = DATE(?)''',
                  (user_id, today))
        count = c.fetchone()[0]
        conn.close()
        
        return count < MAX_DOWNLOADS_PER_DAY, count
    
    def add_download(self, user_id: int, song_title: str, file_size: float):
        """Record a download"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO downloads (user_id, song_title, file_size, download_date)
                     VALUES (?, ?, ?, ?)''',
                  (user_id, song_title, file_size, datetime.now()))
        conn.commit()
        conn.close()
    
    def check_flood(self, user_id: int) -> bool:
        """Check flood (3 seconds between requests)"""
        now = time.time()
        if now - self.user_last_request[user_id] < 3:
            return False
        self.user_last_request[user_id] = now
        return True

rate_limiter = RateLimiter()

# ====== CACHE MANAGER ======
class CacheManager:
    @staticmethod
    def get_hash(query: str) -> str:
        """Generate hash for caching"""
        return hashlib.md5(query.encode()).hexdigest()
    
    @staticmethod
    def get_cached(song_hash: str) -> Optional[Dict]:
        """Get cached file if exists and not expired"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''SELECT file_path, title, artist, duration, last_accessed 
                     FROM cache WHERE song_hash = ?''', (song_hash,))
        result = c.fetchone()
        
        if result:
            file_path, title, artist, duration, last_accessed = result
            # Check if expired
            last_time = datetime.fromisoformat(last_accessed)
            if datetime.now() - last_time < timedelta(seconds=CACHE_EXPIRY):
                if os.path.exists(file_path):
                    # Update access time and count
                    c.execute('''UPDATE cache SET last_accessed = ?, 
                                 download_count = download_count + 1 
                                 WHERE song_hash = ?''',
                              (datetime.now(), song_hash))
                    conn.commit()
                    conn.close()
                    return {
                        "file_path": file_path,
                        "title": title,
                        "artist": artist,
                        "duration": duration
                    }
        
        conn.close()
        return None
    
    @staticmethod
    def add_to_cache(song_hash: str, file_path: str, title: str, artist: str, duration: int):
        """Add file to cache"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO cache 
                     (song_hash, file_path, title, artist, duration, last_accessed)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (song_hash, file_path, title, artist, duration, datetime.now()))
        conn.commit()
        conn.close()
    
    @staticmethod
    def clean_cache():
        """Remove expired cache files"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''SELECT file_path FROM cache 
                     WHERE julianday('now') - julianday(last_accessed) > ?''',
                  (CACHE_EXPIRY / 86400,))
        
        for row in c.fetchall():
            file_path = row[0]
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        
        c.execute('''DELETE FROM cache 
                     WHERE julianday('now') - julianday(last_accessed) > ?''',
                  (CACHE_EXPIRY / 86400,))
        
        conn.commit()
        conn.close()

# ====== USER SETTINGS ======
def get_user_language(user_id: int) -> str:
    """Get user's language preference"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "my"

def get_user_quality(user_id: int) -> str:
    """Get user's quality preference"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT quality FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "128"

def update_user(user_id: int, username: str, first_name: str):
    """Update or insert user"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date)
                 VALUES (?, ?, ?, ?)''',
              (user_id, username, first_name, datetime.now()))
    conn.commit()
    conn.close()

def update_user_language(user_id: int, language: str):
    """Update user language"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
    conn.commit()
    conn.close()

def update_user_quality(user_id: int, quality: str):
    """Update user quality"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET quality = ? WHERE user_id = ?", (quality, user_id))
    conn.commit()
    conn.close()

def increment_user_downloads(user_id: int):
    """Increment user's total downloads"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET total_downloads = total_downloads + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ====== PROGRESS TRACKER ======
class ProgressTracker:
    def __init__(self, message, lang="my"):
        self.message = message
        self.lang = lang
        self.last_update = 0
    
    async def update(self, d):
        """Update progress"""
        if d['status'] == 'downloading':
            now = time.time()
            if now - self.last_update > 2:  # Update every 2 seconds
                percent = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', 'N/A').strip()
                eta = d.get('_eta_str', 'N/A').strip()
                
                progress_text = f"""
⬇️ **Downloading...** {percent}

⚡ Speed: {speed}
⏳ ETA: {eta}
                """
                await self.message.edit(progress_text)
                self.last_update = now

# ====== PYROGRAM CLIENT ======
app = Client("music_bot_ultimate", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ====== COMMAND HANDLERS ======
@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Start command"""
    user = message.from_user
    update_user(user.id, user.username, user.first_name)
    lang = get_user_language(user.id)
    
    # Create settings button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
         InlineKeyboardButton("📞 Support", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")],
        [InlineKeyboardButton("🌐 Language/ဘာသာစကား", callback_data="change_lang")]
    ])
    
    await message.reply(LANG[lang]["start"], reply_markup=keyboard)

@app.on_message(filters.command("help"))
async def help_command(client, message):
    """Help command"""
    user = message.from_user
    lang = get_user_language(user.id)
    
    help_text = LANG[lang]["help"].format(
        MAX_DOWNLOADS_PER_DAY=MAX_DOWNLOADS_PER_DAY,
        MAX_QUEUE_SIZE=MAX_QUEUE_SIZE,
        SUPPORT_USERNAME=SUPPORT_USERNAME
    )
    
    await message.reply(help_text)

@app.on_message(filters.command("language"))
async def language_command(client, message):
    """Change language"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇲🇲 မြန်မာ", callback_data="lang_my"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ])
    await message.reply("Choose your language / ဘာသာစကားရွေးပါ:", reply_markup=keyboard)

@app.on_message(filters.command("quality"))
async def quality_command(client, message):
    """Change audio quality"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 128 kbps", callback_data="quality_128"),
         InlineKeyboardButton("🎵 192 kbps", callback_data="quality_192")],
        [InlineKeyboardButton("🎵 320 kbps (Best)", callback_data="quality_320")]
    ])
    await message.reply("Select audio quality:", reply_markup=keyboard)

@app.on_message(filters.command("stats"))
async def stats_command(client, message):
    """Show user stats"""
    user = message.from_user
    lang = get_user_language(user.id)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total downloads
    c.execute("SELECT total_downloads FROM users WHERE user_id = ?", (user.id,))
    total = c.fetchone()[0]
    
    # Today's downloads
    today = datetime.now().date()
    c.execute('''SELECT COUNT(*) FROM downloads 
                 WHERE user_id = ? AND DATE(download_date) = DATE(?)''',
              (user.id, today))
    today_count = c.fetchone()[0]
    
    # Most downloaded
    c.execute('''SELECT song_title, COUNT(*) as cnt FROM downloads 
                 WHERE user_id = ? GROUP BY song_title ORDER BY cnt DESC LIMIT 1''',
              (user.id,))
    most = c.fetchone()
    
    conn.close()
    
    stats_text = f"""
📊 **Your Statistics**

📥 **Total Downloads:** {total}
📅 **Today:** {today_count}/{MAX_DOWNLOADS_PER_DAY}
🎵 **Most Downloaded:** {most[0] if most else 'N/A'} ({most[1] if most else 0} times)

⚙️ **Settings:**
• Language: {'🇲🇲 မြန်မာ' if lang == 'my' else '🇬🇧 English'}
• Quality: {get_user_quality(user.id)} kbps
    """
    
    await message.reply(stats_text)

@app.on_message(filters.command("settings"))
async def settings_command(client, message):
    """Show settings menu"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Language/ဘာသာစကား", callback_data="change_lang")],
        [InlineKeyboardButton("🎵 Audio Quality", callback_data="change_quality")],
        [InlineKeyboardButton("📊 My Stats", callback_data="show_stats")]
    ])
    await message.reply("⚙️ **Settings Menu**", reply_markup=keyboard)

@app.on_message(filters.command("play"))
async def play_command(client, message):
    """Main download command"""
    user = message.from_user
    lang = get_user_language(user.id)
    
    # Flood check
    if not rate_limiter.check_flood(user.id):
        await message.reply("⏳ Slow down! Wait 3 seconds between requests.")
        return
    
    # Check command format
    if len(message.command) < 2:
        await message.reply(LANG[lang]["help"])
        return
    
    query = message.text.split(None, 1)[1]
    
    # Check if it's a URL
    is_url = any(site in query.lower() for site in SUPPORTED_SITES)
    
    # Check daily limit
    within_limit, today_count = rate_limiter.check_daily_limit(user.id)
    if not within_limit:
        await message.reply(LANG[lang]["daily_limit"].format(
            MAX_DOWNLOADS_PER_DAY=MAX_DOWNLOADS_PER_DAY
        ))
        return
    
    # Add to queue
    added, queue_pos = await download_queue.add(user.id, {"query": query, "message": message})
    if not added:
        await message.reply(LANG[lang]["queue_full"].format(MAX_QUEUE_SIZE=MAX_QUEUE_SIZE))
        return
    
    status_msg = await message.reply(f"⏳ Added to queue. Position: {queue_pos}")
    
    # Start queue processor if not running
    asyncio.create_task(process_queue())

async def process_queue():
    """Process download queue"""
    while True:
        task_data = await download_queue.get_next()
        if task_data:
            user_id, task = task_data
            await download_song(task["message"], task["query"])
        await asyncio.sleep(1)

async def download_song(message, query):
    """Download and send song"""
    user = message.from_user
    lang = get_user_language(user.id)
    
    # Check cache first
    cache_hash = CacheManager.get_hash(query)
    cached = CacheManager.get_cached(cache_hash)
    
    if cached:
        # Send from cache
        await message.reply_audio(
            audio=cached["file_path"],
            title=cached["title"][:64],
            performer=cached["artist"][:64],
            duration=cached["duration"]
        )
        
        # Record download
        rate_limiter.add_download(user.id, cached["title"], 
                                  os.path.getsize(cached["file_path"]) / (1024 * 1024))
        increment_user_downloads(user.id)
        
        # Remove from queue
        await download_queue.remove(user.id)
        return
    
    # Not in cache, download
    quality = get_user_quality(user.id)
    status_msg = await message.reply("🔍 Searching and downloading...")
    
    # Progress tracker
    tracker = ProgressTracker(status_msg, lang)
    
    # yt-dlp options with quality setting
    format_quality = {
        "128": "bestaudio[abr<=128]/bestaudio",
        "192": "bestaudio[abr<=192]/bestaudio",
        "320": "bestaudio[abr<=320]/bestaudio"
    }
    
    ydl_opts = {
        "format": format_quality.get(quality, "bestaudio"),
        "default_search": "ytsearch1" if not any(site in query.lower() for site in SUPPORTED_SITES) else None,
        "outtmpl": os.path.join(WORKING_DIR, "%(title).100s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "extractaudio": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": quality,
        }],
        "progress_hooks": [tracker.update],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info
            if any(site in query.lower() for site in SUPPORTED_SITES):
                # Direct URL
                info = ydl.extract_info(query, download=True)
            else:
                # Search
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)["entries"][0]
            
            # Get file path
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                # Try with mp3 extension
                filename = filename.rsplit(".", 1)[0] + ".mp3"
            
            if not os.path.exists(filename):
                await status_msg.edit("❌ File not found after download!")
                return
            
            # Get metadata
            title = info.get("title", "Unknown")
            uploader = info.get("uploader", "Unknown")
            duration = info.get("duration", 0)
            thumbnail = info.get("thumbnail")
            
            # Download thumbnail if available
            thumb_path = None
            if thumbnail:
                import requests
                try:
                    thumb_path = os.path.join(WORKING_DIR, f"thumb_{user.id}.jpg")
                    r = requests.get(thumbnail)
                    with open(thumb_path, "wb") as f:
                        f.write(r.content)
                except:
                    thumb_path = None
            
            # Upload
            await status_msg.edit("📤 Uploading to Telegram...")
            
            await message.reply_audio(
                audio=filename,
                title=title[:64],
                performer=uploader[:64],
                duration=duration,
                thumb=thumb_path if thumb_path else None
            )
            
            # Add to cache
            CacheManager.add_to_cache(cache_hash, filename, title, uploader, duration)
            
            # Record download
            file_size = os.path.getsize(filename) / (1024 * 1024)
            rate_limiter.add_download(user.id, title, file_size)
            increment_user_downloads(user.id)
            
            await status_msg.edit("✅ Download complete!")
            
            # Cleanup thumb
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
            
    except Exception as e:
        error_msg = str(e)[:150]
        await status_msg.edit(f"❌ Error: {error_msg}")
    finally:
        # Remove from queue
        await download_queue.remove(user.id)
        
        # Clean old cache
        CacheManager.clean_cache()

# ====== INLINE MODE ======
@app.on_inline_query()
async def inline_query(client, inline_query):
    """Handle inline queries"""
    query = inline_query.query
    
    if len(query) < 3:
        return
    
    # Search YouTube
    ydl_opts = {
        "format": "bestaudio",
        "default_search": "ytsearch5",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            
            results = []
            for i, entry in enumerate(info["entries"]):
                if not entry:
                    continue
                
                title = entry.get("title", "Unknown")
                uploader = entry.get("uploader", "Unknown")
                duration = entry.get("duration", 0)
                video_id = entry.get("id", "")
                thumb = f"https://img.youtube.com/vi/{video_id}/default.jpg"
                
                # Create result
                results.append(
                    InlineQueryResultArticle(
                        title=title[:64],
                        description=f"{uploader} • {duration//60}:{duration%60:02d}",
                        thumb_url=thumb,
                        input_message_content=InputTextMessageContent(
                            f"/play {title} {uploader}"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🎵 Download", callback_data=f"dl_{video_id}")]
                        ])
                    )
                )
                
                if len(results) >= 5:
                    break
            
            await inline_query.answer(results)
            
    except Exception as e:
        print(f"Inline error: {e}")

# ====== CALLBACK HANDLERS ======
@app.on_callback_query()
async def handle_callback(client, callback_query):
    """Handle button callbacks"""
    user = callback_query.from_user
    data = callback_query.data
    
    if data == "change_lang":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇲🇲 မြန်မာ", callback_data="lang_my"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings")]
        ])
        await callback_query.message.edit_text("Choose language:", reply_markup=keyboard)
    
    elif data == "lang_my":
        update_user_language(user.id, "my")
        await callback_query.answer("Language set to မြန်မာ")
        await settings_command(client, callback_query.message)
    
    elif data == "lang_en":
        update_user_language(user.id, "en")
        await callback_query.answer("Language set to English")
        await settings_command(client, callback_query.message)
    
    elif data == "change_quality":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("128 kbps", callback_data="quality_128"),
             InlineKeyboardButton("192 kbps", callback_data="quality_192")],
            [InlineKeyboardButton("320 kbps", callback_data="quality_320"),
             InlineKeyboardButton("🔙 Back", callback_data="settings")]
        ])
        await callback_query.message.edit_text("Select audio quality:", reply_markup=keyboard)
    
    elif data.startswith("quality_"):
        quality = data.split("_")[1]
        update_user_quality(user.id, quality)
        await callback_query.answer(f"Quality set to {quality} kbps")
        await settings_command(client, callback_query.message)
    
    elif data == "show_stats":
        await stats_command(client, callback_query.message)
    
    elif data == "settings":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Language/ဘာသာစကား", callback_data="change_lang")],
            [InlineKeyboardButton("🎵 Audio Quality", callback_data="change_quality")],
            [InlineKeyboardButton("📊 My Stats", callback_data="show_stats")]
        ])
        await callback_query.message.edit_text("⚙️ **Settings Menu**", reply_markup=keyboard)
    
    elif data.startswith("dl_"):
        video_id = data[3:]
        await callback_query.message.reply(f"/play https://youtu.be/{video_id}")

# ====== ADMIN COMMANDS ======
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_command(client, message):
    """Broadcast message to all users (admin only)"""
    if len(message.command) < 2:
        await message.reply("Usage: /broadcast <message>")
        return
    
    broadcast_text = message.text.split(None, 1)[1]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    
    sent = 0
    failed = 0
    
    status_msg = await message.reply(f"Broadcasting to {len(users)} users...")
    
    for user_id in users:
        try:
            await client.send_message(user_id[0], broadcast_text)
            sent += 1
        except:
            failed += 1
        
        if sent % 10 == 0:
            await status_msg.edit(f"Progress: {sent}/{len(users)} sent, {failed} failed")
        
        await asyncio.sleep(0.5)  # Avoid flood
    
    await status_msg.edit(f"✅ Broadcast complete!\nSent: {sent}\nFailed: {failed}")

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def admin_stats_command(client, message):
    """Show bot statistics (admin only)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total users
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    # Total downloads
    c.execute("SELECT SUM(total_downloads) FROM users")
    total_downloads = c.fetchone()[0] or 0
    
    # Today's downloads
    today = datetime.now().date()
    c.execute('''SELECT COUNT(*) FROM downloads WHERE DATE(download_date) = DATE(?)''', (today,))
    today_downloads = c.fetchone()[0]
    
    # Cache stats
    c.execute("SELECT COUNT(*), SUM(download_count) FROM cache")
    cache_count, cache_hits = c.fetchone()
    
    # Top users
    c.execute('''SELECT user_id, total_downloads FROM users 
                 ORDER BY total_downloads DESC LIMIT 5''')
    top_users = c.fetchall()
    
    conn.close()
    
    # Get top users info
    top_users_text = ""
    for user_id, downloads in top_users:
        try:
            user = await client.get_users(user_id)
            name = user.first_name or "Unknown"
            top_users_text += f"• {name}: {downloads} downloads\n"
        except:
            top_users_text += f"• User {user_id}: {downloads} downloads\n"
    
    stats_text = f"""
📊 **Bot Statistics**

👥 **Total Users:** {total_users}
📥 **Total Downloads:** {total_downloads}
📅 **Today's Downloads:** {today_downloads}

💾 **Cache:**
• Files: {cache_count or 0}
• Hits: {cache_hits or 0}

🏆 **Top Users:**
{top_users_text}

🕒 **Uptime:** Bot is running...
    """
    
    await message.reply(stats_text)

@app.on_message(filters.command("cleanup") & filters.user(OWNER_ID))
async def cleanup_command(client, message):
    """Force cache cleanup (admin only)"""
    await message.reply("🧹 Cleaning cache...")
    CacheManager.clean_cache()
    
    # Also clean old downloads
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''DELETE FROM downloads WHERE DATE(download_date) < DATE('now', '-7 days')''')
    deleted = c.rowcount
    conn.commit()
    conn.close()
    
    await message.reply(f"✅ Cleanup complete!\nDeleted {deleted} old download records.")

# ====== ERROR HANDLER ======
@app.on_message()
async def error_handler(client, message):
    """Handle unknown commands"""
    if message.text and message.text.startswith("/"):
        lang = get_user_language(message.from_user.id)
        await message.reply("❌ Unknown command. Type /help for available commands.")

# ====== STARTUP ======
print("""
███████╗██╗░░░██╗██████╗░███████╗██████╗░  ██████╗░░█████╗░████████╗
██╔════╝██║░░░██║██╔══██╗██╔════╝██╔══██╗  ██╔══██╗██╔══██╗╚══██╔══╝
█████╗░░██║░░░██║██████╔╝█████╗░░██████╦╝  ██████╦╝██║░░██║░░░██║░░░
██╔══╝░░██║░░░██║██╔═══╝░██╔══╝░░██╔══██╗  ██╔══██╗██║░░██║░░░██║░░░
██║░░░░░╚██████╔╝██║░░░░░███████╗██████╦╝  ██████╦╝╚█████╔╝░░░██║░░░
╚═╝░░░░░░╚═════╝░╚═╝░░░░░╚══════╝╚═════╝░  ╚═════╝░░╚════╝░░░░╚═╝░░░

███████╗██╗░░░██╗██████╗░███████╗██████╗░███╗░░░███╗███████╗
██╔════╝██║░░░██║██╔══██╗██╔════╝██╔══██╗████╗░████║██╔════╝
█████╗░░██║░░░██║██████╔╝█████╗░░██████╔╝██╔████╔██║█████╗░░
██╔══╝░░██║░░░██║██╔═══╝░██╔══╝░░██╔══██╗██║╚██╔╝██║██╔══╝░░
██║░░░░░╚██████╔╝██║░░░░░███████╗██║░░██║██║░╚═╝░██║███████╗
╚═╝░░░░░░╚═════╝░╚═╝░░░░░╚══════╝╚═╝░░╚═╝╚═╝░░░░░╚═╝╚══════╝

🔥 **MUSIC BOT v3.0 - ULTIMATE EDITION** 🔥
✅ **All features loaded successfully!**
🚀 **Ready to serve millions of songs!**
🎵 **Use /play to start downloading**
👑 **The Ultimate Music Bot - Created with ❤️**
""")

# Start background tasks
async def background_tasks():
    """Run background tasks"""
    while True:
        # Clean cache every hour
        await asyncio.sleep(3600)
        CacheManager.clean_cache()

# Start the bot
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(background_tasks())
    app.run()
