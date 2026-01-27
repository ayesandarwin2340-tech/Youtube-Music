import os
import yt_dlp
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# ====== TELEGRAM CREDENTIALS (ဒီနေရာကို မင်းရဲ့အသစ်တွေနဲ့ အစားထိုးပါ!) ======
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
# =======================================================================

app = Client("music_bot_king", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Pydroid3 အတွက် path
WORKING_DIR = "/tmp"

# သိမ်းထားမယ့် ဖိုင်နာမည်များ
downloaded_files = []

@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Start command with cool styling"""
    welcome_text = """
✨ **MUSIC BOT v2.0** ✨

🎵 **ကြိုဆိုပါတယ်!** 🎵
ဒီ Bot ကနေ YouTube ကသီချင်းတွေကို MP3 အနေနဲ့ ဒေါင်းလုပ်ချနိုင်ပါတယ်!

📌 **အသုံးပြုနည်း:**
`/play သီချင်းနာမည်`
ဥပမာ: `/play blackpink pink venom`

🔥 **Features:**
• အရည်အသွေးမြင့် MP3
• မြန်ဆန်သော Download
• ရိုးရှင်းလွယ်ကူသော အသုံးပြုနည်း

👑 **Created with ❤️ by Music Lover**
    """
    await message.reply(welcome_text)

@app.on_message(filters.command("play"))
async def download_song(client, message):
    global downloaded_files
    
    # Variable များကို ကြိုတင်သတ်မှတ်ခြင်း
    original_filename = None
    mp3_filename = None
    target_file = None
    
    if len(message.command) < 2:
        await message.reply("🔥 **ဟေ့ကောင်!** 🔥\n\n"
                          "❌ **သီချင်းနာမည်မထည့်ရင် ဘာဒေါင်းချမှာလဲ?**\n\n"
                          "✅ **ဒီလိုရေးပါ:**\n"
                          "`/play သီချင်းနာမည်`\n"
                          "ဥပမာ: `/play dua lipa levitating`")
        return

    query = message.text.split(None, 1)[1]
    
    # အလန်းစား status message
    status_msg = await message.reply("""
🔮 **MAGIC STARTING...** 🔮

🎯 **တိတ်တိတ်လေး စောင့်ပါ...**
📡 YouTube ကနေ ရှာဖွေနေပါတယ်!
    """)

    # FFmpeg မလိုတဲ့ option - Android/Pydroid3 အတွက် သင့်တော်တယ်
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "default_search": "ytsearch1",
        "outtmpl": os.path.join(WORKING_DIR, "%(title).100s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        # Postprocessor ကို ဖယ်ထားတယ် - FFmpeg မလိုဘူး
        "postprocessors": [],
        "extractaudio": True,
        "audioformat": "m4a",  # m4a ကို MP3 လိုပဲ Telegram ကလက်ခံတယ်
    }

    try:
        # အဆင့် 1: ရှာဖွေခြင်း
        await status_msg.edit("""
🎵 **TRACK LOCATED!** 🎵

⬇️ **DOWNLOAD INITIATED...**
⚡ မြန်မြန်ဆန်ဆန် ယူနေပါတယ်!
⏳ 10-30 စက္ကန့်လောက် စောင့်ပါ...
        """)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            
            if not info or "entries" not in info or not info["entries"]:
                await status_msg.edit("""
❌ **ဟား! မတွေ့ပါဘူးကွာ** ❌

😔 ဒီသီချင်းကို YouTube မှာမရှိဘူးနဲ့တူတယ်
🔍 နာမည်ပြန်စစ်ကြည့်ပါ:
• စာလုံးပေါင်း မှန်ရဲ့လား?
• အင်္ဂလိပ်လိုရေးထားရဲ့လား?

🎧 **ဥပမာ:** `/play coldplay yellow`
                """)
                return
                
            video_info = info["entries"][0]
            title = video_info.get("title", "Unknown Track")
            uploader = video_info.get("uploader", "Unknown Artist")
            duration = video_info.get("duration", 0)
            thumbnail = video_info.get("thumbnail")  # YouTube က thumbnail
            
            # Download လုပ်ထားတဲ့ ဖိုင်ကိုရှာဖွေခြင်း
            import glob
            search_pattern = os.path.join(WORKING_DIR, f"*{title[:50]}*")
            found_files = glob.glob(search_pattern)
            
            if not found_files:
                # Alternative search
                all_files = [f for f in os.listdir(WORKING_DIR) if f.endswith('.m4a') or f.endswith('.webm')]
                if all_files:
                    found_files = [os.path.join(WORKING_DIR, all_files[-1])]
            
            if not found_files:
                await status_msg.edit("""
⚠️ **FILE NOT FOUND** ⚠️

😟 Download ချထားပေမယ့် ဖိုင်ကိုမတွေ့ဘူး
🔄 Bot ကို restart လုပ်ကြည့်ပါ
📛 ဒါမှမဟုတ် နောက်တစ်ခါပြန်ကြိုးစားပါ
                    """)
                return
            
            target_file = found_files[0]
            downloaded_files.append(target_file)
            
            # File size check
            file_size = os.path.getsize(target_file) / (1024 * 1024)  # MB
            
            # အဆင့် 2: Upload လုပ်ခြင်း
            await status_msg.edit(f"""
🚀 **READY FOR LIFTOFF!** 🚀

📦 **File Details:**
🎶 Track: {title[:50]}
👤 Artist: {uploader[:30]}
📊 Size: {file_size:.1f} MB
⏱️ Duration: {duration//60}:{duration%60:02d}

📤 **TELEGRAM ဆီ ပျံသန်းနေပါပြီ...**
            """)
            
            # Telegram သို့ upload (thumbnail ကိုဖယ်ထားတယ်)
            await message.reply_audio(
                audio=target_file,
                title=title[:64],
                performer=uploader[:64],
                duration=duration
                # thumb parameter ကို ဖယ်ထားတယ်
            )
            
            # အောင်မြင်မှု message
            await status_msg.edit(f"""
🎉 **MISSION ACCOMPLISHED!** 🎉

✅ **သီချင်းအောင်မြင်စွာရပြီ!** ✅

🎵 **{title[:50]}**
👑 **{uploader[:30]}**

📥 Download Successful!
📁 File Size: {file_size:.1f} MB

🔥 **ကျေးဇူးတင်ပါတယ်!**
🎧 နောက်ထပ်သီချင်းရှာချင်ရင် `/play` ကိုပြန်သုံးပါ
            """)
            
            # 5 စက္ကန့်ကြာပြီးမှ delete
            await asyncio.sleep(5)
            await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)[:150]
        await status_msg.edit(f"""
❌ **DOWNLOAD FAILED** ❌

😢 **ဒေါင်းလုပ်မရဘူးကွာ:**
`{error_msg}`

💡 **ဖြေရှင်းနည်းများ:**
1. အင်တာနက်ကောင်းကောင်းသုံးပါ
2. သီချင်းနာမည်ပြန်စစ်ပါ
3. ခဏလောက်စောင့်ပြီးပြန်ကြိုးစားပါ
        """)
    except FloodWait as e:
        wait_time = e.value
        await status_msg.edit(f"""
⏳ **SLOW DOWN TIGER!** ⏳

🚦 **Telegram က {wait_time} စက္ကန့်စောင့်ခိုင်းတယ်**
🍵 လက်ဖက်ရည်တစ်ခွက်သောက်ပြီးမှပြန်လာပါ

⏰ {wait_time} seconds remaining...
        """)
        await asyncio.sleep(wait_time)
        # Retry automatically
        await download_song(client, message)
    except Exception as e:
        error_msg = str(e)[:150]
        await status_msg.edit(f"""
⚡ **UNEXPECTED ERROR** ⚡

🤯 **အား... မမျှော်လင့်တဲ့အမှား:**
`{error_msg}`

🔧 **ဘာလုပ်ရမလဲ:**
1. Bot ကို restart လုပ်ကြည့်ပါ
2. နောက်တစ်ခါပြန်ကြိုးစားပါ
3. မရဘူးဆိုရင် Developer ကိုပြောပါ
        """)
    finally:
        # Cleanup files
        await cleanup_files()

async def cleanup_files():
    """ဖိုင်များကို သန့်ရှင်းရန်"""
    for file_path in downloaded_files:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
    downloaded_files.clear()

@app.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = """
🆘 **HELP MENU** 🆘

📌 **Commands Available:**
• `/start` - Bot ကိုစတင်ရန်
• `/play <song name>` - သီချင်းဒေါင်းလုပ်ရန်
• `/help` - ဒီအကူအညီမီနူးကိုကြည့်ရန်

🎯 **Examples:**
`/play taylor swift`
`/play shape of you`
`/play bts dynamite`

⚠️ **Notes:**
• သီချင်းနာမည်ကို အင်္ဂလိပ်လိုရေးပါ
• တစ်ခါတစ်ရံ 1-2 မိနစ်ကြာနိုင်ပါတယ်
• အင်တာနက်ကောင်းကောင်းလိုပါတယ်

📞 **Support:** @username (မင်း Telegram username ထည့်ပါ)
    """
    await message.reply(help_text)

# Cool startup message
print("""
██████╗░░█████╗░████████╗  ░██████╗████████╗░█████╗░██████╗░████████╗
██╔══██╗██╔══██╗╚══██╔══╝  ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝
██████╦╝██║░░██║░░░██║░░░  ╚█████╗░░░░██║░░░██║░░██║██████╔╝░░░██║░░░
██╔══██╗██║░░██║░░░██║░░░  ░╚═══██╗░░░██║░░░██║░░██║██╔══██╗░░░██║░░░
██████╦╝╚█████╔╝░░░██║░░░  ██████╔╝░░░██║░░░╚█████╔╝██║░░██║░░░██║░░░
╚═════╝░░╚════╝░░░░╚═╝░░░  ╚═════╝░░░░╚═╝░░░░╚════╝░╚═╝░░╚═╝░░░╚═╝░░░

✅ **MUSIC BOT v2.0 STARTED SUCCESSFULLY!**
🔥 **Ready to rock your world with music!**
🎵 **Use /play command to start downloading**
👑 **Bot created with passion by Music Lover**
""")

app.run()
