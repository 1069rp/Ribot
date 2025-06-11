import os, json, random, glob
from datetime import datetime
from instagrapi import Client
from apscheduler.schedulers.blocking import BlockingScheduler
import yt_dlp

# ——— CONFIG ———
USERNAME = os.environ["IG_USERNAME"]
PASSWORD = os.environ["IG_PASSWORD"]
SESSION_FILE = "session.json"
SOURCE_ACCOUNTS = [
    "terabox_links.hub",
    "divya_links",
    "duniyaa_links_ki",
    "mx_links"
]
DOWNLOAD_DIR = "reels"
POST_TIMES = [8, 14, 20]  # 8 AM, 2 PM, 8 PM
DM_TARGET = "linuxlifestyle"
COMMENT_TEXT = "All the latest videos Link In Bio"
# ————————

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def login_with_session():
    cl = Client()
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE) as f:
                s = json.load(f)
            cl.set_settings(s["settings"])
            cl.set_uuids(s["uuids"])
            cl.login(USERNAME, PASSWORD)
            return cl
        except Exception:
            pass
    cl.login(USERNAME, PASSWORD)
    with open(SESSION_FILE, "w") as f:
        json.dump({
            "settings": cl.get_settings(),
            "uuids": cl.get_uuids()
        }, f)
    return cl

cl = login_with_session()
scheduler = BlockingScheduler()

def download_reels():
    for user in SOURCE_ACCOUNTS:
        url = f"https://www.instagram.com/{user}/reels/"
        opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/{user}_%(id)s.%(ext)s',
            'format': 'mp4', 'quiet': True
        }
        try:
            yt_dlp.YoutubeDL(opts).download([url])
        except Exception as e:
            send_dm(f"🚨 Download error for {user}: {e}")
            
def upload_and_comment():
    try:
        fn = random.choice(glob.glob(f"{DOWNLOAD_DIR}/*.mp4"))
    except IndexError:
        download_reels()
        all_files = glob.glob(f"{DOWNLOAD_DIR}/*.mp4")
        if not all_files:
            return send_dm("❌ No reels found to upload.")
        fn = random.choice(all_files)

    try:
        cl.clip_upload(fn, caption=f"🔥 Repost 📅 {datetime.now().strftime('%Y-%m-%d')}")
        os.remove(fn)
    except Exception as e:
        return send_dm(f"❌ Upload failed: {e}")

    for user in SOURCE_ACCOUNTS:
        try:
            media = cl.user_medias(cl.user_id_from_username(user), 1)[0]
            cl.media_comment(media.id, COMMENT_TEXT)
        except Exception as e:
            send_dm(f"👁️ Comment error for {user}: {e}")
    send_dm("✅ Successfully posted and commented ✅")

def send_dm(msg):
    try:
        cl.direct_send(msg, [cl.user_id_from_username(DM_TARGET)])
    except:
        pass

# Set schedules
for h in POST_TIMES:
    scheduler.add_job(upload_and_comment, 'cron', hour=h)

# Initial run
download_reels()
upload_and_comment()
print("✅ Bot scheduled for 8 AM, 2 PM, 8 PM daily")
scheduler.start()
