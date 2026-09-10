# Global AI Assistant - Ultra Best World Edition 2026
import os
import json
import logging
import threading
import asyncio
import random
import re
import time
import traceback
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    x.strip()
    for x in os.environ.get("ADMIN_IDS", "").split(",")
    if x.strip()
}
FREE_LIMIT = 5
PREMIUM_PRICE = 49
PREMIUM_PLUS = 99
PREMIUM_ELITE = 199
RATE_LIMIT_SECONDS = 1.5
DATA_FILE = "users.json"
BANS_FILE = "bans.json"

PREMIUM_TIERS = {
    49: {"days": 30, "name": "Premium", "perks": "Unlimited tools for 30 days"},
    99: {"days": 90, "name": "Premium Plus", "perks": "90 days + priority queue"},
    199: {"days": 180, "name": "Premium Elite", "perks": "180 days + resume review notes"},
}

INVITE_MILESTONES = {
    3: {"uses": 5, "xp": 20, "premium_days": 0, "label": "3 friends = +5 uses"},
    10: {"uses": 0, "xp": 80, "premium_days": 30, "label": "10 friends = 1 month Premium"},
    25: {"uses": 10, "xp": 150, "premium_days": 60, "label": "25 friends = 60 days Premium"},
    50: {"uses": 20, "xp": 300, "premium_days": 90, "label": "50 friends = 90 days + cash claim flag"},
    100: {"uses": 50, "xp": 800, "premium_days": 3650, "label": "100 friends = lifetime-style Premium"},
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

web_app = Flask(__name__)
_file_lock = threading.Lock()
_rate_memory: Dict[str, float] = {}
users: Dict[str, Any] = {}
banned_ids: Dict[str, Any] = {}


def now_iso() -> str:
    return datetime.now().isoformat()


def today_str() -> str:
    return date.today().isoformat()


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "")).date()
    except ValueError:
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def load_json_file(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if data is not None else default
    except Exception as e:
        logger.error("Failed to load %s: %s", path, e)
        return default


def save_json_file(path: str, data) -> None:
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        logger.error("Failed to save %s: %s", path, e)


def load_users_safe() -> Dict[str, Any]:
    data = load_json_file(DATA_FILE, {})
    return data if isinstance(data, dict) else {}


def save_users(d: Dict[str, Any]) -> None:
    with _file_lock:
        save_json_file(DATA_FILE, d)


def load_bans() -> Dict[str, Any]:
    data = load_json_file(BANS_FILE, {})
    return data if isinstance(data, dict) else {}


def save_bans() -> None:
    save_json_file(BANS_FILE, banned_ids)


def default_user_record() -> Dict[str, Any]:
    return {
        "uses": 0,
        "premium": False,
        "premium_till": None,
        "invited": 0,
        "invited_by": None,
        "milestones": [],
        "joined": now_iso(),
        "xp": 0,
        "streak": 0,
        "last_streak_date": None,
        "streak_rewards": [],
        "last_bonus_date": None,
        "last_quiz_date": None,
        "quiz_score": 0,
        "quiz_pending": None,
        "banned": False,
        "ban_reason": None,
        "last_tool": None,
        "last_job": None,
    }


def migrate_user(record: Dict[str, Any]) -> Dict[str, Any]:
    base = default_user_record()
    base.update(record if isinstance(record, dict) else {})
    if not isinstance(base.get("milestones"), list):
        base["milestones"] = []
    if not isinstance(base.get("streak_rewards"), list):
        base["streak_rewards"] = []
    if not isinstance(base.get("xp"), int):
        try:
            base["xp"] = int(base.get("xp") or 0)
        except (TypeError, ValueError):
            base["xp"] = 0
    if not isinstance(base.get("uses"), int):
        try:
            base["uses"] = int(base.get("uses") or 0)
        except (TypeError, ValueError):
            base["uses"] = 0
    return base


def expire_premium_if_needed(user: Dict[str, Any]) -> None:
    till = user.get("premium_till")
    if not till:
        return
    try:
        end = datetime.fromisoformat(str(till))
        if datetime.now() > end:
            user["premium"] = False
            user["premium_till"] = None
    except ValueError:
        user["premium"] = False
        user["premium_till"] = None


def grant_premium_days(user: Dict[str, Any], days: int) -> None:
    if days <= 0:
        return
    start = datetime.now()
    current = user.get("premium_till")
    if current:
        try:
            existing = datetime.fromisoformat(str(current))
            if existing > start:
                start = existing
        except ValueError:
            pass
    user["premium"] = True
    user["premium_till"] = (start + timedelta(days=days)).isoformat()


def add_xp(user: Dict[str, Any], amount: int) -> int:
    if amount <= 0:
        return get_level(user)
    user["xp"] = max(0, int(user.get("xp") or 0) + amount)
    return get_level(user)


def get_level(user: Dict[str, Any]) -> int:
    xp = max(0, int(user.get("xp") or 0))
    level = xp // 50 + 1
    return min(100, max(1, level))


def get_rank(level: int) -> str:
    if level <= 5:
        return "🌱 Starter"
    if level <= 12:
        return "📘 Learner"
    if level <= 20:
        return "🧭 Explorer"
    if level <= 30:
        return "🛠️ Builder"
    if level <= 40:
        return "📈 Hustler"
    if level <= 50:
        return "💼 Professional"
    if level <= 60:
        return "🏅 Specialist"
    if level <= 70:
        return "🔥 Expert"
    if level <= 80:
        return "🎯 Mentor"
    if level <= 90:
        return "🏆 Elite"
    if level <= 99:
        return "👑 Master"
    return "💎 Legend 100"


def xp_to_next(user: Dict[str, Any]) -> int:
    xp = max(0, int(user.get("xp") or 0))
    if get_level(user) >= 100:
        return 0
    return 50 - (xp % 50)


def apply_streak(user: Dict[str, Any]) -> Dict[str, Any]:
    today = date.today()
    last = parse_iso_date(user.get("last_streak_date"))
    result = {
        "increased": False,
        "reset": False,
        "streak": int(user.get("streak") or 0),
        "xp_gain": 0,
        "uses_gain": 0,
        "premium_days": 0,
        "reward_note": "",
    }
    if last == today:
        result["streak"] = max(1, int(user.get("streak") or 0))
        return result
    if last == today - timedelta(days=1):
        user["streak"] = int(user.get("streak") or 0) + 1
        add_xp(user, 15)
        result["increased"] = True
        result["xp_gain"] = 15
    else:
        user["streak"] = 1
        result["reset"] = last is not None
        add_xp(user, 5)
        result["xp_gain"] = 5
        user["streak_rewards"] = []
    user["last_streak_date"] = today.isoformat()
    streak = int(user["streak"])
    result["streak"] = streak
    rewards = set(user.get("streak_rewards") or [])
    if streak >= 3 and "d3" not in rewards:
        user["uses"] = max(0, int(user.get("uses") or 0) - 1)
        rewards.add("d3")
        result["uses_gain"] += 1
        result["reward_note"] = "3-day streak: +1 free use"
    if streak >= 7 and "d7" not in rewards:
        user["uses"] = max(0, int(user.get("uses") or 0) - 2)
        add_xp(user, 50)
        rewards.add("d7")
        result["uses_gain"] += 2
        result["xp_gain"] += 50
        result["reward_note"] = "7-day streak: +2 uses and +50 XP"
    if streak >= 30 and "d30" not in rewards:
        grant_premium_days(user, 7)
        rewards.add("d30")
        result["premium_days"] = 7
        result["reward_note"] = "30-day streak: 1 week Premium FREE"
    user["streak_rewards"] = list(rewards)
    return result


def is_banned(uid) -> Tuple[bool, str]:
    uid = str(uid)
    if uid in banned_ids:
        rec = banned_ids.get(uid) or {}
        return True, str(rec.get("reason") or "Account restricted")
    rec = users.get(uid) or {}
    if rec.get("banned"):
        return True, str(rec.get("ban_reason") or "Account restricted")
    return False, ""


def is_rate_limited(uid) -> bool:
    uid = str(uid)
    now = time.time()
    last = _rate_memory.get(uid, 0.0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    _rate_memory[uid] = now
    if len(_rate_memory) > 5000:
        cutoff = now - 60
        stale = [k for k, v in _rate_memory.items() if v < cutoff]
        for k in stale[:2000]:
            _rate_memory.pop(k, None)
    return False


def strip_markdown(text: str) -> str:
    cleaned = text.replace("**", "").replace("__", "").replace("`", "")
    cleaned = cleaned.replace("*", "")
    return cleaned


async def send_long(message, text: str, reply_markup=None, parse_mode: str = "Markdown") -> None:
    chunks = []
    remaining = text
    limit = 3900
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        cut = remaining.rfind("\n", 0, limit)
        if cut < 500:
            cut = limit
        chunks.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")
    for i, chunk in enumerate(chunks):
        markup = reply_markup if i == len(chunks) - 1 else None
        try:
            await message.reply_text(chunk, parse_mode=parse_mode, reply_markup=markup)
        except Exception:
            try:
                await message.reply_text(strip_markdown(chunk), reply_markup=markup)
            except Exception as e:
                logger.error("send_long failed: %s", e)


def get_user(uid) -> Dict[str, Any]:
    uid = str(uid)
    if uid not in users:
        users[uid] = default_user_record()
    else:
        users[uid] = migrate_user(users[uid])
    expire_premium_if_needed(users[uid])
    return users[uid]


def uses_left(user: Dict[str, Any]) -> str:
    if user.get("premium"):
        return "Unlimited"
    return str(max(0, FREE_LIMIT - int(user.get("uses") or 0)))


def consume_use(user: Dict[str, Any]) -> None:
    if user.get("premium"):
        add_xp(user, 2)
        return
    user["uses"] = int(user.get("uses") or 0) + 1
    add_xp(user, 8)


def clean_prompt(text: str, prefixes: List[str]) -> str:
    t = (text or "").strip()
    low = t.lower()
    for p in sorted(prefixes, key=len, reverse=True):
        if low.startswith(p):
            t = t[len(p) :].strip(" :-")
            low = t.lower()
    t = re.sub(r"^/+", "", t).strip()
    return t


def detect_track(text: str) -> str:
    t = (text or "").lower()
    if any(x in t for x in ["data", "excel", "analyst", "mis", "sql", "power bi"]):
        return "data"
    if any(x in t for x in ["market", "digital", "seo", "ads", "content creator"]):
        return "marketing"
    if any(x in t for x in ["bpo", "call", "customer", "support", "tele"]):
        return "customer"
    if any(x in t for x in ["account", "tally", "gst", "ca ", "bookkeep"]):
        return "accounts"
    if any(x in t for x in ["teacher", "tutor", "school"]):
        return "teaching"
    if any(x in t for x in ["design", "canva", "graphic", "video edit"]):
        return "design"
    if any(x in t for x in ["delivery", "driver", "rider", "warehouse"]):
        return "ops"
    if any(x in t for x in ["it", "developer", "python", "java", "computer"]):
        return "it"
    if any(x in t for x in ["sale", "retail", "shop", "executive", "field"]):
        return "sales"
    return "sales"


JOB_PROFILES: Dict[str, Dict[str, Any]] = {
    "sales": {
        "title_default": "Sales Executive",
        "keywords": [
            "Sales Target",
            "Customer Handling",
            "Lead Generation",
            "Closing",
            "CRM",
            "Follow-up",
            "Upselling",
            "Negotiation",
            "Field Sales",
            "Retail Sales",
            "WhatsApp Business",
            "MS Excel",
            "Hindi",
            "Marathi",
            "English",
        ],
        "summary": "Results-driven sales professional who converts walk-ins and follow-ups into repeat buyers.",
        "bullets": [
            "Handled 50+ customer queries daily and improved repeat purchase rate by 30%.",
            "Maintained daily sales tracker in Excel with 100% billing accuracy.",
            "Achieved daily target 10/10 days during festival week in local market.",
            "Collected 20+ qualified leads per week from WhatsApp and shop visits.",
        ],
        "skills": ["MS Excel", "WhatsApp Business", "CRM Basics", "Negotiation", "Product Demo"],
        "salary_akola": "₹12,000–₹18,000 + incentives",
    },
    "data": {
        "title_default": "Data / MIS Executive",
        "keywords": [
            "MS Excel",
            "VLOOKUP",
            "Pivot Tables",
            "MIS Report",
            "Data Cleaning",
            "Dashboard",
            "Google Sheets",
            "Accuracy",
            "Deadline",
            "SQL Basics",
            "Power BI",
            "Reporting",
        ],
        "summary": "Accurate MIS professional who turns daily numbers into simple reports managers can act on.",
        "bullets": [
            "Built a daily sales tracker that saved 5 hours/week of manual counting.",
            "Cleaned 1,000+ rows of customer data and reduced duplicate records.",
            "Prepared MIS summary for owner every evening before 7 PM.",
            "Used VLOOKUP and pivot tables for product-wise profit view.",
        ],
        "skills": ["Excel Advanced", "Google Sheets", "Data Validation", "Charts", "Attention to Detail"],
        "salary_akola": "₹14,000–₹22,000",
    },
    "marketing": {
        "title_default": "Digital Marketing Executive",
        "keywords": [
            "Instagram Reels",
            "Hashtags",
            "Canva",
            "Copywriting",
            "Meta Ads Basics",
            "Content Calendar",
            "Engagement",
            "WhatsApp Catalog",
            "Local SEO",
            "Google Business Profile",
        ],
        "summary": "Local-market marketer who creates daily content and converts comments into WhatsApp orders.",
        "bullets": [
            "Posted daily Reels and grew local reach with 30 researched hashtags.",
            "Set up WhatsApp catalog of 20 products and generated 15 orders.",
            "Replied to first 10 comments within 30 minutes to boost distribution.",
            "Ran simple festival offer creatives in Canva for shop promotions.",
        ],
        "skills": ["Canva", "Instagram", "Copywriting", "Canva Stories", "Google Business"],
        "salary_akola": "₹12,000–₹20,000 + performance",
    },
    "customer": {
        "title_default": "Customer Support Associate",
        "keywords": [
            "Customer Handling",
            "Call Etiquette",
            "Ticket Resolution",
            "CRM",
            "Listening",
            "Hindi",
            "Marathi",
            "English",
            "SLA",
            "Empathy",
        ],
        "summary": "Calm support associate who solves issues fast and keeps customers coming back.",
        "bullets": [
            "Handled 50+ customers daily across walk-in and phone queries.",
            "Resolved billing doubts with 100% polite close and follow-up.",
            "Logged complaints in a simple Excel sheet for the owner.",
            "Trained family members on greeting script and closing lines.",
        ],
        "skills": ["Communication", "CRM Basics", "Excel", "Patience", "Multilingual"],
        "salary_akola": "₹11,000–₹16,000",
    },
    "accounts": {
        "title_default": "Accounts Executive",
        "keywords": [
            "Tally",
            "GST",
            "Invoicing",
            "Bank Reconciliation",
            "MS Excel",
            "Voucher Entry",
            "TDS Basics",
            "Cash Book",
        ],
        "summary": "Accounts executive who keeps books clean, GST-ready, and cash matching every day.",
        "bullets": [
            "Managed billing of ₹15,000/day with zero mismatch vs cash drawer.",
            "Prepared simple purchase and sales register in Excel.",
            "Followed up pending payments with polite reminder messages.",
            "Filed supporting bills in date-wise folders for CA visits.",
        ],
        "skills": ["Excel", "Tally Basics", "GST Invoice", "Accuracy", "Documentation"],
        "salary_akola": "₹13,000–₹20,000",
    },
    "teaching": {
        "title_default": "Tutor / Teaching Assistant",
        "keywords": [
            "Lesson Plan",
            "Classroom Management",
            "Hindi",
            "Marathi",
            "English",
            "Doubt Solving",
            "Parents Communication",
        ],
        "summary": "Patient tutor who explains basics clearly and tracks student homework completion.",
        "bullets": [
            "Took small-group tuition and improved homework completion.",
            "Created simple notes and weekly test papers.",
            "Spoke with parents in Marathi/Hindi about progress.",
            "Used WhatsApp to share daily practice worksheets.",
        ],
        "skills": ["Explanation", "Patience", "MS Word", "Canva Notes", "Punctuality"],
        "salary_akola": "₹8,000–₹15,000 part-time",
    },
    "design": {
        "title_default": "Graphic / Video Creator",
        "keywords": [
            "Canva",
            "Reels",
            "Thumbnail",
            "Color Theory",
            "Typography",
            "CapCut",
            "Brand Kit",
        ],
        "summary": "Creator who designs scroll-stopping posters and short videos for local brands.",
        "bullets": [
            "Designed festival posters and product catalogs for local shops.",
            "Edited 15-second Reels with captions and trending audio.",
            "Built a simple brand kit: colors, fonts, logo placement.",
            "Delivered same-day creatives for WhatsApp status marketing.",
        ],
        "skills": ["Canva", "CapCut", "Thumbnails", "Copy + Design", "Deadlines"],
        "salary_akola": "₹10,000–₹18,000 + per post",
    },
    "ops": {
        "title_default": "Operations / Delivery Coordinator",
        "keywords": [
            "Route Planning",
            "COD",
            "Customer Call",
            "Inventory",
            "Time Management",
            "Google Maps",
        ],
        "summary": "On-ground coordinator who delivers on time and updates customers before delay happens.",
        "bullets": [
            "Planned 10 local deliveries per day with same-day promise in Akola.",
            "Collected COD and submitted cash with 100% count match.",
            "Called customers 20 minutes before arrival.",
            "Kept a simple pending-order sheet to avoid missed drops.",
        ],
        "skills": ["Navigation", "Customer Calls", "Cash Handling", "Excel List"],
        "salary_akola": "₹10,000–₹16,000 + fuel",
    },
    "it": {
        "title_default": "Computer / IT Support",
        "keywords": [
            "MS Office",
            "Hardware Basics",
            "Troubleshooting",
            "Internet Setup",
            "Data Backup",
            "Typing",
        ],
        "summary": "IT support fresher who fixes daily computer issues and trains staff on MS Office.",
        "bullets": [
            "Set up billing Excel and backup copies every night.",
            "Solved printer and WhatsApp Business catalog issues for shop staff.",
            "Typed documents with high accuracy for owner correspondence.",
            "Learned basic HTML/Python tutorials and documented steps.",
        ],
        "skills": ["MS Office", "Google Workspace", "Troubleshooting", "Fast Typing"],
        "salary_akola": "₹12,000–₹20,000",
    },
}


def extract_job_title(prompt: str) -> str:
    cleaned = clean_prompt(
        prompt,
        [
            "resume for",
            "resume",
            "/resume",
            "cv for",
            "cv",
            "biodata for",
            "biodata",
            "cover letter for",
            "cover for",
            "cover",
            "interview for",
            "interview",
            "email for",
            "email",
            "roadmap for",
            "roadmap",
            "salary for",
            "negotiate",
            "linkedin for",
            "linkedin",
        ],
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        track = detect_track(prompt)
        return JOB_PROFILES[track]["title_default"]
    return cleaned.title()[:80]


def profile_for(prompt: str) -> Dict[str, Any]:
    track = detect_track(prompt)
    return JOB_PROFILES[track]


QUIZ_BANK = [
    {
        "id": "q1",
        "q": "ATS resume me heading kaunsa safest hai?",
        "options": ["Work Experience", "My Amazing Journey", "Stuff I Did", "Chapter 2"],
        "answer": 0,
        "why": "ATS parsers look for standard headings like Work Experience, Education, Skills.",
    },
    {
        "id": "q2",
        "q": "HR email bhejne ka best time (India) usually kab hota hai?",
        "options": ["2 AM", "9:30–11:00 AM", "Sunday midnight", "Anytime equally"],
        "answer": 1,
        "why": "Most HRs open mail in the first office window 9:30–11 AM.",
    },
    {
        "id": "q3",
        "q": "Salary negotiation me pehla smart step kya hai?",
        "options": [
            "Pehle hi lowest number bolo",
            "Range do + research bolo",
            "Offer reject without reason",
            "Silent rehna",
        ],
        "answer": 1,
        "why": "A researched range keeps you flexible and signals you know the market.",
    },
    {
        "id": "q4",
        "q": "Instagram Reels ke liye India me strong posting window kaunsi hai?",
        "options": ["4–5 AM only", "7–9 PM IST", "11 AM exam time", "Never evenings"],
        "answer": 1,
        "why": "7–9 PM IST is when many local audiences scroll after work/college.",
    },
    {
        "id": "q5",
        "q": "Resume PDF name best practice?",
        "options": ["finalfinal2.pdf", "Resume_Sales_Akola.pdf", "doc.pdf", "new folder.pdf"],
        "answer": 1,
        "why": "File name with role + city helps HR search and looks professional.",
    },
    {
        "id": "q6",
        "q": "Cover letter subject line me kya hona chahiye?",
        "options": ["Hi", "Role + city + joiner", "Only emoji", "No subject"],
        "answer": 1,
        "why": "Role, location and joining availability get the mail opened.",
    },
    {
        "id": "q7",
        "q": "Interview me weakness ka better frame?",
        "options": [
            "I am lazy",
            "I overwork then I time-box tasks",
            "I hate people",
            "No weakness",
        ],
        "answer": 1,
        "why": "Show self-awareness plus a fix, not a fatal flaw.",
    },
    {
        "id": "q8",
        "q": "Thumbnail CTR boost karne ka MrBeast-style rule?",
        "options": [
            "Tiny text + busy background",
            "One big face/object + 3–5 words",
            "Paragraph on thumbnail",
            "No contrast",
        ],
        "answer": 1,
        "why": "Readable 3–5 words and one clear focal point lift CTR toward 10%+.",
    },
]


def daily_quiz_for_user(uid: str) -> Dict[str, Any]:
    seed = today_str() + str(uid)
    idx = abs(hash(seed)) % len(QUIZ_BANK)
    return QUIZ_BANK[idx]


def apply_invite_progress(ref_user: Dict[str, Any]) -> List[str]:
    notes = []
    ref_user["invited"] = int(ref_user.get("invited") or 0) + 1
    ref_user["uses"] = max(0, int(ref_user.get("uses") or 0) - 1)
    add_xp(ref_user, 10)
    notes.append("+1 use and +10 XP for 1 friend")
    count = int(ref_user["invited"])
    claimed = set(ref_user.get("milestones") or [])
    for n, reward in INVITE_MILESTONES.items():
        key = f"inv{n}"
        if count >= n and key not in claimed:
            if reward["uses"]:
                ref_user["uses"] = max(0, int(ref_user.get("uses") or 0) - int(reward["uses"]))
            if reward["xp"]:
                add_xp(ref_user, int(reward["xp"]))
            if reward["premium_days"]:
                grant_premium_days(user=ref_user, days=int(reward["premium_days"]))
            if n >= 50:
                ref_user["cash_claim"] = True
                ref_user["cash_note"] = "₹500 UPI claim unlocked (manual payout by admin)"
            if n >= 100:
                ref_user["cash_note"] = "₹1500 + lifetime-style Premium flag"
            claimed.add(key)
            notes.append(reward["label"])
    ref_user["milestones"] = list(claimed)
    return notes


def leaderboard_rows(limit: int = 10) -> List[Tuple[str, Dict[str, Any], int]]:
    rows = []
    for uid, rec in users.items():
        if not isinstance(rec, dict):
            continue
        rec = migrate_user(rec)
        score = int(rec.get("xp") or 0) + int(rec.get("invited") or 0) * 25
        rows.append((uid, rec, score))
    rows.sort(key=lambda x: x[2], reverse=True)
    return rows[:limit]


def badge_for_rank(position: int) -> str:
    if position == 1:
        return "👑"
    if position == 2:
        return "🥇"
    if position == 3:
        return "🥈"
    if position == 4:
        return "🥉"
    return "⭐"


def tool_resume(prompt: str) -> str:
    job = extract_job_title(prompt)
    track = detect_track(prompt)
    prof = JOB_PROFILES[track]
    keywords = ", ".join(prof["keywords"])
    bullets = "\n".join([f"• {b}" for b in prof["bullets"]])
    skills = ", ".join(prof["skills"])
    extra_kw = []
    low = (prompt or "").lower()
    if "12th" in low or "hsc" in low:
        extra_kw.append("12th Pass Immediate Joiner")
    if "fresher" in low or "0 year" in low:
        extra_kw.append("Fresher Training Ready")
    if "akola" in low:
        extra_kw.append("Akola Local Market")
    if "pune" in low:
        extra_kw.append("Willing to Relocate Pune")
    if extra_kw:
        keywords = keywords + ", " + ", ".join(extra_kw)
    education = "12th / Graduation - Maharashtra Board - 2024"
    if "graduate" in low or "bcom" in low or "bba" in low:
        education = "Graduation (BCom/BBA or equivalent) - 2024-2026"
    if "diploma" in low:
        education = "Diploma - MSBTE / equivalent"
    cert = f"{job} Fundamentals + MS Office + Computer Basics"
    if track == "data":
        cert = "Excel + Pivot + MIS Reporting practice sheet"
    elif track == "marketing":
        cert = "Canva + Instagram Organic + WhatsApp Catalog"
    elif track == "accounts":
        cert = "Tally basics + GST invoice practice"
    elif track == "it":
        cert = "MS Office + Typing + Basic troubleshooting"
    projects = [
        "Created sales/attendance tracker sheet — saved 5 hrs/week",
        "Made WhatsApp Business catalog of 20 products — got 15 orders",
        "Wrote SOP for greeting + closing so family staff could follow",
    ]
    if track == "data":
        projects = [
            "MIS dashboard: daily, weekly, monthly sheets linked with SUMIF",
            "Cleaned customer list and tagged repeat vs new buyers",
            "Built a late-payment follow-up list for the owner",
        ]
    elif track == "marketing":
        projects = [
            "30-day content calendar for a local shop",
            "Festival offer creatives + 30 hashtag sets",
            "Google Business profile photos + weekly post plan",
        ]
    project_txt = "\n".join([f"• {p}" for p in projects])
    return f"""✅ **ULTRA ATS RESUME - {job} - Track: {track.upper()}**
**Target ATS score path: 90–98 when you replace placeholders with real numbers**

**[YOUR FULL NAME]**
📍 Akola, Maharashtra | 📞 +91 9XXXX XXXXX
✉️ yourname@gmail.com | 🔗 linkedin.com/in/yourname | 🌐 Portfolio / Google Drive

**PROFESSIONAL SUMMARY (HR 6-second rule)**
{prof["summary"]} Targeting **{job}** in Akola/Nagpur/Pune. 1 year customer/ops exposure (50+ daily interactions), MS Excel, bilingual Hindi/Marathi + professional English. Immediate joiner.

**ATS KEYWORDS (paste naturally into bullets, do not stuff)**
{keywords}

**EDUCATION**
• {education} — add your exact %, board, and year
• Certification: {cert}

**EXPERIENCE (fresher: use family business / internship / project)**
**{prof["title_default"]} | Family Business / Internship | Akola | 2023–Present**
{bullets}

**PROJECTS**
{project_txt}

**SKILLS**
Technical: {skills}
Soft: Punctual, Quick learner, Target ownership, Team coordination

**LANGUAGES**
Hindi (Native), Marathi (Native), English (Professional)

**DECLARATION**
I hereby declare that the information is true to the best of my knowledge.

---
**7-DAY JOB SPRINT**
1. Paste in Word → export PDF: `Resume_{job.replace(" ", "_")}.pdf`
2. Naukri/Indeed/LinkedIn: 20 applies 9:30–11 AM
3. Subject: `{job} - Akola - Immediate Joiner - Keyword Match`
4. WhatsApp HR: "Hi, I applied for {job}. 1 yr exposure, can join tomorrow. 10-min call?"
5. Track applies in a sheet: Date | Company | Portal | Follow-up day+2

Salary research (Akola 2026 band for this track): **{prof["salary_akola"]}**
Next: `cover letter for {job}` or `interview for {job}` or `salary for {job}`
"""


def tool_cover(prompt: str) -> str:
    job = extract_job_title(prompt)
    prof = profile_for(prompt)
    bullets = "\n".join([f"• {b}" for b in prof["bullets"][:3]])
    today = datetime.now().strftime("%d %B %Y")
    return f"""📄 **COVER LETTER - {job} - US-style 3-paragraph (India-ready)**
[Your Name] | Akola, Maharashtra | +91 9XXXX XXXXX | {today}

Hiring Manager
[Company Name]
[City: Akola / Nagpur / Pune]

Subject: Application for {job} — Immediate Joiner — Keyword Match

Dear Hiring Manager,

I am applying for the **{job}** opening at [Company Name]. I can contribute from day 1 with customer handling, {", ".join(prof["skills"][:3])}, and local-market communication in Hindi, Marathi, and English.

In my recent work:
{bullets}

I am based in Akola, understand local buying behavior, and can join within 24 hours. I am available for a 10-minute call tomorrow 11:00 AM or an in-person interview the same day.

Thank you for your time.

Sincerely,
[Your Name]
Akola | [email] | [phone]

---
**Send checklist**
• Attach Resume PDF named with role
• Keep letter under 250 words
• Same keywords as resume (ATS + human)
• Follow-up on working day +2 before 11 AM

**3 subject-line tests**
1. {job} — Akola — Immediate Joiner
2. {job} Application — Ready to join tomorrow
3. {job} — 1 yr exposure — Excel + {prof["skills"][0]}

Market salary to mention only if asked: {prof["salary_akola"]}
Need interview answers? Type: `interview for {job}`
"""


def tool_interview(prompt: str) -> str:
    job = extract_job_title(prompt)
    track = detect_track(prompt)
    prof = JOB_PROFILES[track]
    q_why = {
        "sales": "I like converting conversations into orders and hitting a visible target.",
        "data": "I like making messy numbers simple so the owner can decide faster.",
        "marketing": "I like testing content daily and watching which post creates WhatsApp chats.",
        "customer": "I like solving problems calmly so the customer returns.",
        "accounts": "I like clean books and zero cash mismatch.",
        "teaching": "I like explaining until the student can do it alone.",
        "design": "I like making a shop look premium with simple posters and Reels.",
        "ops": "I like routes, timing, and keeping promises on delivery.",
        "it": "I like fixing daily computer issues and documenting the fix.",
    }[track]
    return f"""🎯 **INTERVIEW Q&A - {job}**

**Q1: Tell me about yourself? (60–75 sec)**
"I am from Akola. I completed 12th/graduation in 2024. For 1 year I handled customers and daily records in a family business/internship: 50+ people a day, Excel billing, Hindi-Marathi-English. I am punctual and can join immediately. I want {job} because {q_why}"

**Q2: Why should we hire you?**
"Three reasons: I can join in 24 hours, I already use {", ".join(prof["skills"][:3])}, and I know Akola customer language and market timing."

**Q3: Expected salary?**
"For {job} in Akola I researched {prof["salary_akola"]}. I am flexible for a fair offer if learning and incentives are clear. Growth matters as much as the starting number."

**Q4: Strength?**
Pick 2 from: {", ".join(prof["skills"][:4])}. Give one number (customers/day, accuracy, posts/week).

**Q5: Weakness?**
"I used to say yes to every extra task and finish late. Now I write a 3-item list every morning and close it before new work."

**Q6: Where do you see yourself in 5 years?**
"Team lead / senior {job} in this company, training new joiners on the same SOP I will follow from week 1."

**Q7: Why this company?**
"I checked your products/location. Local customers already know you. I can help with {prof["bullets"][0]}"

**Q8: Gap / fresher?**
"I used the gap to practice Excel, WhatsApp Business, and mock interviews. I can show the tracker sheet."

**STAR story (use this)**
Situation: festival rush / messy register
Task: keep billing accurate and customers moving
Action: {prof["bullets"][1]}
Result: owner trusted me with cash/closing

**Ask them 3 questions**
1. Typical day for {job} in first 30 days?
2. Biggest bottleneck the team faces this month?
3. How is a good first-month performance measured?

**Dress & kit**
Formal / clean ironed shirt, 2 resume copies, notepad, phone on silent, 5 minutes early.

**Red-flag answers to avoid**
• "I need money only"
• Fake experience dates
• Insult previous shop/family business

Next: `salary for {job}` or `cover letter for {job}`
"""


def tool_email(prompt: str) -> str:
    job = extract_job_title(prompt)
    prof = profile_for(prompt)
    return f"""📧 **HR EMAIL PACK - {job}**

**SUBJECT A (highest open intent):** Application for {job} — Immediate Joiner — Akola
**SUBJECT B:** {job} — ready for 10-min call tomorrow 11 AM
**SUBJECT C:** {job} application — Excel + {prof["skills"][0]} — Akola

**BODY (short)**
Dear Hiring Manager,

I am applying for the {job} role I saw on Naukri/Indeed/your WhatsApp status.

Why I fit:
• {prof["bullets"][0]}
• {prof["bullets"][1]}
• Languages: Hindi, Marathi, English
• Tools: {", ".join(prof["skills"][:4])}
• Join timeline: 24 hours

Resume is attached (PDF). I can do a 10-minute call tomorrow 11:00 AM or visit the office the same day.

Thank you.
[Your Name]
Akola, Maharashtra
+91 9XXXX XXXXX

**P.S.** I can share a 1-page Excel sample / content calendar if useful.

**Follow-up (day +2, 10:15 AM)**
Subject: Following up — {job} application — [Your Name]
Body: Sharing my resume again. Happy to visit this week. Thank you.

**WhatsApp version (even shorter)**
"Namaste, I applied for {job}. 1 yr customer/Excel exposure, Akola, join tomorrow. May I send resume here?"

**Do not**
• 5 MB images
• "Please reply madam sir urgent"
• Wrong company name from copy-paste

Send window: **9:30–11:00 AM IST** on a working day.
Need resume? `resume for {job}`
"""


def tool_caption(prompt: str) -> str:
    topic = clean_prompt(
        prompt,
        ["caption for", "caption", "hashtag for", "hashtags", "reel for", "insta for"],
    ) or "my small business"
    hooks = [
        f"POV: You finally started {topic} from Akola ✨",
        f"Day 1 of building {topic} — no fancy office, only consistency 🌍",
        f"Nobody talks about this side of {topic} 🤫",
        f"{topic} is not talent. It is 30 days of showing up 👇",
        f"I gave {topic} 7 days. The 8th day paid the tea bill 🔥",
    ]
    hook = random.choice(hooks)
    tag = re.sub(r"[^a-z0-9]+", "", topic.lower())[:24] or "akolabusiness"
    return f"""📸 **VIRAL CAPTION SYSTEM - {topic}**

**CAPTION (copy)**
{hook}

I thought {topic} needed money first.
It needed a daily proof post.

3 rules I follow:
1. Start with tools I already have
2. Post even if the lighting is average
3. Help 1 person in comments every day

Building {topic}? Drop ❤️
Comment START and I will share the 7-day checklist.

.
.
.

**30 HASHTAGS**
#viral #trending #reels #explore #{tag} #akola #maharashtra #nagpur #pune #smallbusiness #indianentrepreneur #startupindia #sidehustle #digitalmarketing #reelsinstagram #growthmindset #success #entrepreneur #2026 #contentcreator #branding #marketingtips #earnmoneyonline #workfromhome #localbusiness #madeinindia #maharashtrian #instagood #motivation #businessideas

**POST TIME:** 7–9 PM IST, extra test 11:30 AM Sunday
**First 30 minutes:** reply 10 comments with a question (algorithm boost)
**CTA tests:** START / PRICE / CITY

**7-day reel map**
Day1: origin story (hook above)
Day2: behind the process
Day3: customer reaction
Day4: price myth
Day5: before/after
Day6: FAQ stitch
Day7: offer + WhatsApp link in bio

Need a logo prompt? `image prompt for {topic} logo`
Need a YouTube version? `youtube script for {topic}`
"""


def tool_image(prompt: str) -> str:
    topic = clean_prompt(
        prompt,
        ["image prompt for", "image for", "image", "logo for", "prompt for", "thumbnail for"],
    ) or "modern shop in Akola"
    return f"""🎨 **IMAGE PROMPT PACK - {topic}**

**PROMPT 1 — Photo real (Instagram 4:5)**
Ultra realistic 8K DSLR photo of {topic}, Akola Maharashtra street context, late-afternoon cinematic light, highly detailed textures, sharp focus, Sony A7R IV, 85mm f/1.4, commercial photography, clean background separation, no watermark --ar 4:5 --style raw

**PROMPT 2 — Logo (Ideogram / vector feel)**
Minimalist modern logo for {topic}, geometric, golden ratio, flat vector, 2 colors maximum, white background, professional branding, no tiny unreadable text, --no photoreal, 3D clay, extra words

**PROMPT 3 — Poster 9:16**
{topic} promo poster, Indian festival color blocking, bold Hindi + English headline space, Akola market energy, high contrast, 8K, --ar 9:16

**PROMPT 4 — Product packshot**
Studio packshot of {topic} product, softbox lighting, seamless backdrop, price-tag safe negative space on right, 8K

**PROMPT 5 — Founder portrait (optional)**
Candid portrait of a young Indian entrepreneur at {topic} stall, natural smile, bokeh of market lights, respectful, photoreal, --ar 4:5

**NEGATIVE**
blurry, extra fingers, watermark, misspelled letters, extra limbs, low-res, crowded collage, ugly oversharpen

**Tools**
Leonardo or Bing Image Creator for photos, Ideogram for logos with text, Canva to add final Marathi/English copy.

**Export**
Logo: PNG transparent 2000px
Reel cover: 1080x1920
Carousel: 1080x1350

Next: `thumbnail for {topic}` or `caption for {topic}`
"""


def tool_business(prompt: str) -> str:
    biz = clean_prompt(
        prompt,
        ["business idea for", "idea for", "business for", "business", "startup for", "startup"],
    ) or "t-shirt printing"
    handle = re.sub(r"[^a-z0-9]", "", biz.lower())[:18] or "akolashop"
    return f"""💡 **₹1 LAKH / MONTH PLAN - {biz.title()} - Akola validated path**

**Model:** {biz.title()} service + WhatsApp catalog + local delivery
**Start capital:** ₹8,000–₹15,000 (home / shared table)
**Unit economics (edit with your real numbers)**
• Ticket: ₹150–₹400
• Daily 5 orders = ₹750–₹2,000
• Month 1 organic: ₹22k–₹60k
• Scale path: ₹1L+ needs ads + helper + repeat customers

**Unit cost sheet (fill this)**
Material ____ + packaging ____ + delivery ____ = cost
Price - cost = gross. Keep gross above 40% or raise price/bundle.

**7 DAYS TO FIRST ORDER**
**Day 1–2**
1. Instagram @{handle}akola — bio: DM to order | Akola + courier
2. WhatsApp Business catalog: 10 designs/services
3. Google Business Profile: photos + WhatsApp button
**Day 3–4**
1. One Reel/day: process of {biz}
2. 3 Facebook/WhatsApp groups: honest offer, no spam walls
3. 10 shop visits with 1 sample and a rate card
**Day 5–7**
Offer: first 10 customers 20% off + free delivery inside Akola
3 WhatsApp statuses/day
Referral: 1 friend = ₹100 credit

**MONTH 2–4 SCALE**
M2: delivery helper ₹8k if COD volume > 8/day
M3: simple website or Shopify Lite only after 30 repeat buyers
M4: ads ₹100–₹300/day only after 10 organic conversions tracked

**Risks**
COD fake orders → confirm on call
Copycats → weekly new design
Festival cash crunch → 50% advance on bulk

**Bot growth:** /invite (3/10/25/50/100 reward tiers)
Next: `caption for {biz}` • `roadmap for {biz} staff` • `youtube script for {biz}`
"""


def tool_linkedin(prompt: str) -> str:
    job = extract_job_title(prompt)
    prof = profile_for(prompt)
    return f"""🔗 **LINKEDIN KIT - {job}**

**Headline (220 chars mindset)**
{job} | Akola | Excel + {prof["skills"][0]} | Immediate Joiner | Hindi-Marathi-English

**About (first 3 lines must work before See more)**
I help shops and teams with {job.lower()} outcomes: {prof["summary"]}
Open to {job} roles in Akola / Nagpur / Pune.
Skills: {", ".join(prof["skills"])}

**Featured**
1. Resume PDF
2. Excel sample / Canva poster
3. 60-sec intro video

**Experience bullets (same as resume, numbers first)**
{chr(10).join(["• " + b for b in prof["bullets"]])}

**Open to work**
Title: {job}
Locations: Akola, Nagpur, Pune
Start: Immediately

**10 connection note**
"Hi [Name], I am applying for {job} in your city. I would value 1 tip on what you look for in the first 30 days."

**Weekly LinkedIn cadence**
Mon: 1 career carousel
Wed: 1 lesson from shop floor
Fri: 1 apply-sprint screenshot (no private data)

Do not copy fake MNCs. Local proof beats fake brands.
"""


def tool_roadmap(prompt: str) -> str:
    job = extract_job_title(prompt)
    if "sales" not in (prompt or "").lower() and detect_track(prompt) != "sales":
        job_display = job
    else:
        job_display = job if job else "Sales Executive"
    return f"""🗺️ **0 → ₹50,000 ROADMAP (12 months) - {job_display}**
Designed for Akola start, optional Pune/Nagpur move in month 8–12.

**MONTH 1 — Foundation (₹0–₹12k)**
Week 1: Resume + cover + 40 applies. Daily mock Q1-Q3.
Week 2: Join any ethical sales/counter/field role even at ₹10–12k.
Week 3: Learn product 20 cards. Shadow top closer if any.
Week 4: Personal tracker: talks / demos / closes. Target: 1 close/day equivalent.

**MONTH 2 — Skill (₹12–₹15k + small incentive)**
• CRM or notebook: name, need, next follow-up date
• Script: greeting, 2 questions, offer, close, WhatsApp catalog
• Night: 30 min Excel (VLOOKUP, SUMIF)

**MONTH 3 — Consistency (₹15–₹18k)**
• Conversion diary: why deals died
• Ask manager for inbound + one field beat
• Referral ask after every happy bill

**MONTH 4–5 — Income mix (₹18–₹25k)**
• Negotiate after 90 days using `salary for {job_display}`
• Weekend micro-skill: Canva posters for shop = proof for next job
• Emergency fund: ₹2000 kept aside

**MONTH 6 — Proof pack (₹22–₹30k)**
Build a 1-page case study: "Festival week: X bills, Y repeat, Z WhatsApp reorders"
Apply to better shops/brands with this PDF.

**MONTH 7–8 — Territory (₹25–₹35k)**
If city cap is real, interview Nagpur/Pune with relocation line.
Keep 2 months rent saved before moving.

**MONTH 9–10 — Team skill (₹30–₹40k)**
Train 1 junior. Document SOP. This is how you become supervisor.

**MONTH 11–12 — ₹50k path**
₹50k in Akola is usually **salary + incentive + side skill** (training, weekend selling, or digital catalog for 2 shops).
Math example: ₹22k salary + ₹12k incentive + ₹16k weekend catalogs = ₹50k.
Pure salary ₹50k more common in bigger city or team-lead seat — target that interview in month 12.

**Weekly habit forever**
Mon-Fri: 9:30 AM apply or follow-up if job hunting
Daily: 10 follow-ups before 11 AM if in sales seat
Sunday: 60 min skill (Excel or product)

Next: `interview for {job_display}` • `salary for {job_display}`
"""


def tool_salary(prompt: str) -> str:
    job = extract_job_title(prompt)
    track = detect_track(prompt)
    bands = {
        "sales": {
            "akola": "₹12k–₹18k + 1–3% incentive / festival extra",
            "nagpur": "₹15k–₹22k + incentive",
            "pune": "₹18k–₹28k + incentive (travel cost higher)",
        },
        "data": {
            "akola": "₹14k–₹22k",
            "nagpur": "₹18k–₹28k",
            "pune": "₹22k–₹35k",
        },
        "marketing": {
            "akola": "₹12k–₹20k + freelance posts",
            "nagpur": "₹16k–₹26k",
            "pune": "₹20k–₹32k",
        },
        "customer": {
            "akola": "₹11k–₹16k",
            "nagpur": "₹14k–₹20k",
            "pune": "₹16k–₹24k",
        },
        "accounts": {
            "akola": "₹13k–₹20k",
            "nagpur": "₹16k–₹25k",
            "pune": "₹18k–₹30k",
        },
        "teaching": {
            "akola": "₹8k–₹15k part-time; ₹15k–₹22k full-time school",
            "nagpur": "₹12k–₹22k",
            "pune": "₹18k–₹28k",
        },
        "design": {
            "akola": "₹10k–₹18k + per-post",
            "nagpur": "₹14k–₹24k",
            "pune": "₹18k–₹30k",
        },
        "ops": {
            "akola": "₹10k–₹16k + fuel",
            "nagpur": "₹13k–₹20k",
            "pune": "₹16k–₹24k",
        },
        "it": {
            "akola": "₹12k–₹20k",
            "nagpur": "₹16k–₹28k",
            "pune": "₹20k–₹35k fresher support",
        },
    }
    b = bands.get(track, bands["sales"])
    return f"""💸 **SALARY NEGOTIATION - {job} (2026 local research)**
Figures are **practical bands**, not a government gazette. Always confirm with 3 local offers.

**Akola 2026 band:** {b["akola"]}
**Nagpur:** {b["nagpur"]}
**Pune:** {b["pune"]}

**When to negotiate**
After they say they like you, not in the first 10 seconds.
If they ask early: give a range, not a single desperate number.

**SCRIPT 1 — First ask (polite)**
"Based on {job} work in Akola, I was expecting {b["akola"]}. I am flexible if incentives and learning are clear. What range did you plan for this seat?"

**SCRIPT 2 — Counter after low offer**
"Thank you. I can start at [offer] for 90 days if we review at ₹____ after I hit [target: bills / tickets / posts]. I have already been handling [number] customers and Excel closing."

**SCRIPT 3 — You have another option**
"I have another local option near ₹____. I prefer your shop because of [product/location]. If you can meet ₹____ or add travel/PF/weekly off, I will join tomorrow."

**Never**
• Lie about another offer
• Ghost after offer
• Accept verbal only — ask WhatsApp confirmation of salary + timing

**Incentive math**
If basic is ₹12,000 and incentive is ₹50 per closed bundle, you need 160 extra closes/month to add ₹8,000. Write this before you say yes.

**Benefits that beat ₹1,000 cash**
Weekly off, PF, travel, meal, festival advance, training certificate.

Next: `roadmap for {job}` to see how to ₹50k in 12 months.
"""


def tool_youtube(prompt: str) -> str:
    topic = clean_prompt(
        prompt, ["youtube script for", "youtube for", "script for", "youtube", "yt for"]
    ) or "sales job from Akola"
    return f"""🎬 **8-MINUTE YOUTUBE SCRIPT - {topic}**
Format: hook 8s → promise → 3 blocks → CTA. Spoken Hindi-English mix.

**TITLE OPTIONS**
1. I tried {topic} for 7 days in Akola — day 7 shocked me
2. {topic}: the 0 to 1 mistake nobody explains
3. Stop scrolling if you want {topic} without a big city

**HOOK (0:00–0:08)**
"If you are in Akola and think {topic} needs Mumbai money — watch this 8-minute proof."

**COLD OPEN VISUAL**
You holding a notebook + phone. One sentence on screen: 7 DAYS. {topic.upper()}.

**INTRO (0:08–0:40)**
Who you are, city, what you will prove today, who this is NOT for (people who will not post daily).

**BLOCK 1 (0:40–2:30) — Mistake**
"I wasted week 1 on logo instead of 10 conversations."
Show the wrong way vs the 10-conversation sheet.

**BLOCK 2 (2:30–5:00) — Method**
Minute-by-minute: wake, 9:30 applies or outreach, 7 PM reel, 10 follow-ups.
For {topic}: name 3 actions the viewer can copy tonight.

**BLOCK 3 (5:00–7:10) — Proof**
Show screenshot with private data cropped. One number. One lesson.

**CLOSE (7:10–8:00)**
"Comment START. I reply with the checklist. Subscribe if you want day-2."
End screen: video 2 = resume/ATS or caption system.

**ON-SCREEN TEXT**
Max 6 words per flash. Big font. High contrast.

**DESCRIPTION**
Line 1: promise. Line 2: timestamps.
0:00 Hook
0:08 Intro
0:40 Mistake
2:30 Method
5:00 Proof
7:10 CTA
Hashtags: #akola #career #smallbusiness #{topic.replace(" ", "")[:20]}

**PINS**
Top comment: checklist link / Telegram bot link (your /invite)

Need CTR packaging? `thumbnail for {topic}`
"""


def tool_thumbnail(prompt: str) -> str:
    topic = clean_prompt(prompt, ["thumbnail for", "thumbnail", "ctr for"]) or "Akola career video"
    return f"""🖼️ **THUMBNAIL SYSTEM — 10% CTR path (MrBeast-style constraints)**
Topic: {topic}

**The 10% CTR formula (constraints, not magic)**
1. One focal object/face occupying ~40% of frame
2. 3–5 words MAX, thickness that reads at phone size
3. Emotion: shock / curiosity / before-after — only one
4. Contrast: dark vs neon or black vs yellow
5. Crop tight. Empty sky wastes CTR
6. No more than 2 colors for text
7. Arrow/circle only if it hides a detail the click reveals
8. Face looking at the text or at the mystery object
9. Mobile test: lock screen from 1 meter — still readable
10. A/B two versions, keep winner 48 hours

**TEXT OPTIONS (pick one)**
• 7 DAYS LEFT
• ₹0 TO FIRST
• HR SAID NO
• AKOLA SECRET
• DAY 7 SHOCK

**COLOR PAIRS**
Yellow on black, white on red, black on neon green. Avoid pastel on pastel.

**PROMPT (image model)**
Close-up of a young Indian creator, surprised expression, holding a phone showing a graph, high contrast studio light, {topic} vibe, empty left third for giant text, 8K, --ar 16:9 --no watermark tiny text extra fingers

**Canva overlay**
Font: extra bold. Outline 8px. Shadow. Place text on the empty third.

**CTR tracking sheet**
Date | Title | Thumb A/B | Impressions | CTR | Keep?
If CTR < 4% after 1,000 impressions, change thumb before changing topic.

**Illegal/unsafe**
No fake celebrity, no misleading medical/income guarantee screenshots.

Pair with: `youtube script for {topic}`
"""


def ai_router(text: str) -> Optional[str]:
    t = (text or "").lower().strip()
    greetings = {
        "hi",
        "hello",
        "hii",
        "hey",
        "hiiii",
        "ho",
        "start",
        "/start",
        "namaste",
        "yo",
        "ok",
        "menu",
    }
    if t in greetings or t.startswith("/start"):
        return None
    if any(x in t for x in ["roadmap", "0 to 50", "50k", "50 k"]):
        return tool_roadmap(text)
    if any(x in t for x in ["salary", "negotiate", "ctc", "package", "expectation"]):
        return tool_salary(text)
    if any(x in t for x in ["youtube", "yt script", "video script"]):
        return tool_youtube(text)
    if any(x in t for x in ["thumbnail", "ctr", "mrbeast"]):
        return tool_thumbnail(text)
    if any(x in t for x in ["linkedin", "headline", "about section"]):
        return tool_linkedin(text)
    if any(x in t for x in ["resume", "cv", "biodata"]):
        return tool_resume(text)
    if "cover" in t:
        return tool_cover(text)
    if "interview" in t:
        return tool_interview(text)
    if "email" in t or "mail" in t:
        return tool_email(text)
    if any(x in t for x in ["caption", "hashtag", "insta", "reel"]):
        return tool_caption(text)
    if any(x in t for x in ["image", "photo", "logo", "prompt", "leonardo", "midjourney", "bing"]):
        return tool_image(text)
    if any(x in t for x in ["business", "idea", "startup", "earn", "paise kamana"]):
        return tool_business(text)
    if len(t.split()) < 4:
        return tool_business(text)
    return tool_resume(text)


def paywall_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"⭐ Premium {PREMIUM_PRICE}⭐", callback_data="premium")],
            [InlineKeyboardButton("🔗 Invite 3 friends = +5 uses", callback_data="invite")],
            [InlineKeyboardButton("📄 Sample resume", callback_data="resume_sample")],
        ]
    )


def main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📄 ATS Resume", callback_data="resume"),
                InlineKeyboardButton("🎯 Interview", callback_data="interview"),
            ],
            [
                InlineKeyboardButton("📧 HR Email", callback_data="email"),
                InlineKeyboardButton("💌 Cover Letter", callback_data="cover"),
            ],
            [
                InlineKeyboardButton("📸 Caption", callback_data="caption"),
                InlineKeyboardButton("🎨 Image Prompt", callback_data="image"),
            ],
            [
                InlineKeyboardButton("💡 Business", callback_data="business"),
                InlineKeyboardButton("🗺️ Roadmap 50k", callback_data="roadmap"),
            ],
            [
                InlineKeyboardButton("💸 Salary Talk", callback_data="salary"),
                InlineKeyboardButton("🎬 YouTube 8m", callback_data="youtube"),
            ],
            [
                InlineKeyboardButton("🖼️ Thumbnail CTR", callback_data="thumbnail"),
                InlineKeyboardButton("🔗 LinkedIn", callback_data="linkedin"),
            ],
            [
                InlineKeyboardButton(f"⭐ {PREMIUM_PRICE}/{PREMIUM_PLUS}/{PREMIUM_ELITE}", callback_data="premium"),
                InlineKeyboardButton("🔗 Invite", callback_data="invite"),
            ],
            [
                InlineKeyboardButton("🎁 /bonus", callback_data="bonus"),
                InlineKeyboardButton("🧠 /quiz", callback_data="quiz"),
            ],
            [
                InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
                InlineKeyboardButton("📊 Stats", callback_data="stats"),
            ],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    banned, reason = is_banned(uid)
    if banned:
        await update.message.reply_text(f"Access paused: {reason}")
        return
    user = get_user(uid)
    if context.args:
        ref = str(context.args[0])
        if ref != str(uid) and ref in users and not user.get("invited_by"):
            user["invited_by"] = ref
            notes = apply_invite_progress(get_user(ref))
            save_users(users)
            try:
                await context.bot.send_message(
                    chat_id=int(ref),
                    text="🎉 Invite progress!\n" + "\n".join(notes),
                )
            except Exception:
                pass
    apply_streak(user)
    save_users(users)
    left = uses_left(user)
    lvl = get_level(user)
    welcome = f"""🌍 **GLOBAL AI - ULTRA BEST | {len(users)}+ users**

Namaste **{update.effective_user.first_name}**!
Career + business + Instagram toolkit.

**Balance:** {left} | **Level {lvl}** {get_rank(lvl)} | Streak: {user.get("streak", 0)} days
**Premium:** {PREMIUM_PRICE} / {PREMIUM_PLUS} / {PREMIUM_ELITE} Stars

**Type like:**
`resume for 12th pass sales job in Akola`
`interview for sales job`
`salary for sales executive`
`roadmap for sales job`
`caption for my t-shirt shop`
`youtube script for tiffin service`
`thumbnail for career shorts`

Commands: /bonus /quiz /leaderboard /invite /premium /stats
"""
    await send_long(update.message, welcome, reply_markup=main_keyboard())


async def handle_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    uid = update.effective_user.id
    banned, reason = is_banned(uid)
    if banned:
        await update.message.reply_text(f"Access paused: {reason}")
        return
    if is_rate_limited(uid):
        await update.message.reply_text("⏳ Slow down 1.5 sec — bot is working.")
        return
    user = get_user(uid)
    text = update.message.text.strip()
    low = text.lower()
    if low in {"/stats", "stats"}:
        await stats(update, context)
        return
    if low in {"/help", "help"}:
        await help_cmd(update, context)
        return
    if not user.get("premium") and int(user.get("uses") or 0) >= FREE_LIMIT:
        await send_long(
            update.message,
            f"❌ **Free limit over ({FREE_LIMIT})**\nInvite tiers 3/10/25/50/100 or Premium Stars.",
            reply_markup=paywall_keyboard(),
        )
        return
    await update.message.reply_chat_action("typing")
    result = ai_router(text)
    if result is None:
        await start(update, context)
        return
    consume_use(user)
    user["last_tool"] = text[:80]
    user["last_job"] = extract_job_title(text)
    apply_streak(user)
    save_users(users)
    rem = uses_left(user)
    footer = (
        f"\n\n---\n💳 Balance: {rem} | XP {user.get('xp', 0)} | Lvl {get_level(user)} "
        f"{get_rank(get_level(user))}\n⭐ /premium | 🔗 /invite | 🎁 /bonus | 🧠 /quiz"
    )
    await send_long(
        update.message,
        result + footer,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🔄 Another", callback_data="more"),
                    InlineKeyboardButton("⭐ Premium", callback_data="premium"),
                ],
                [
                    InlineKeyboardButton("📤 Share", callback_data="share"),
                    InlineKeyboardButton("🏠 Menu", callback_data="main"),
                ],
            ]
        ),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    banned, reason = is_banned(uid)
    if banned:
        await q.message.reply_text(f"Access paused: {reason}")
        return
    if is_rate_limited(uid) and q.data not in {"premium", "invite", "stats", "help"}:
        await q.message.reply_text("⏳ Wait 1.5 sec")
        return
    d = q.data
    if d == "premium":
        await premium(update, context)
    elif d == "invite":
        await invite(update, context)
    elif d == "stats":
        await stats(update, context)
    elif d == "help":
        await help_cmd(update, context)
    elif d == "bonus":
        await bonus_cmd(update, context)
    elif d == "quiz":
        await quiz_cmd(update, context)
    elif d == "leaderboard":
        await leaderboard_cmd(update, context)
    elif d in {"main", "start"}:
        await q.message.reply_text("🏠 Type /start")
    elif d == "more":
        await q.message.reply_text(
            "🔄 Send a topic, e.g. `resume for 12th pass sales job in Akola`",
            parse_mode="Markdown",
        )
    elif d == "share":
        bot = (await context.bot.get_me()).username
        await q.message.reply_text(f"📤 https://t.me/{bot} — ATS resume + career tools")
    elif d == "resume_sample":
        await send_long(q.message, tool_resume("sales job")[:4000])
    elif d.startswith("quizans_"):
        await quiz_answer(update, context, d)
    else:
        mp = {
            "resume": "📄 `resume for 12th pass sales job in Akola`",
            "email": "📧 `email for sales job`",
            "caption": "📸 `caption for my shop`",
            "image": "🎨 `image prompt for shop logo`",
            "business": "💡 `business idea for tiffin service`",
            "interview": "🎯 `interview for sales job`",
            "cover": "💌 `cover letter for sales job`",
            "linkedin": "🔗 `linkedin for sales job`",
            "roadmap": "🗺️ `roadmap for sales job`",
            "salary": "💸 `salary for sales executive`",
            "youtube": "🎬 `youtube script for tiffin service`",
            "thumbnail": "🖼️ `thumbnail for career shorts`",
        }
        await q.message.reply_text(mp.get(d, f"Send a topic for {d}"), parse_mode="Markdown")


async def cmd_resume(u, c):
    await u.message.reply_text("📄 `resume for 12th pass sales job in Akola`", parse_mode="Markdown")


async def cmd_email(u, c):
    await u.message.reply_text("📧 `email for job application`", parse_mode="Markdown")


async def cmd_caption(u, c):
    await u.message.reply_text("📸 `caption for my shop`", parse_mode="Markdown")


async def cmd_image(u, c):
    await u.message.reply_text("🎨 `image prompt for logo`", parse_mode="Markdown")


async def cmd_idea(u, c):
    await u.message.reply_text("💡 `business idea for t-shirt`", parse_mode="Markdown")


async def cmd_interview(u, c):
    await u.message.reply_text("🎯 `interview for sales job`", parse_mode="Markdown")


async def cmd_cover(u, c):
    await u.message.reply_text("💌 `cover letter for sales job`", parse_mode="Markdown")


async def cmd_roadmap(u, c):
    await u.message.reply_text("🗺️ `roadmap for sales job`", parse_mode="Markdown")


async def cmd_salary(u, c):
    await u.message.reply_text("💸 `salary for sales executive`", parse_mode="Markdown")


async def cmd_youtube(u, c):
    await u.message.reply_text("🎬 `youtube script for my shop`", parse_mode="Markdown")


async def cmd_thumb(u, c):
    await u.message.reply_text("🖼️ `thumbnail for career video`", parse_mode="Markdown")


async def premium(update, context):
    txt = f"""⭐ **PREMIUM TIERS (Telegram Stars)**

**FREE:** {FREE_LIMIT} uses + daily /bonus + /quiz XP

**{PREMIUM_PRICE} Stars — {PREMIUM_TIERS[49]["name"]}**
{PREMIUM_TIERS[49]["perks"]}

**{PREMIUM_PLUS} Stars — {PREMIUM_TIERS[99]["name"]}**
{PREMIUM_TIERS[99]["perks"]}

**{PREMIUM_ELITE} Stars — {PREMIUM_TIERS[199]["name"]}**
{PREMIUM_TIERS[199]["perks"]}

Invite still works: 3 / 10 / 25 / 50 / 100
"""
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"⭐ {PREMIUM_PRICE} — 30 days", callback_data="buy_49")],
            [InlineKeyboardButton(f"⭐ {PREMIUM_PLUS} — 90 days", callback_data="buy_99")],
            [InlineKeyboardButton(f"⭐ {PREMIUM_ELITE} — 180 days", callback_data="buy_199")],
            [InlineKeyboardButton("🔗 Invite = free uses", callback_data="invite")],
        ]
    )
    target = update.callback_query.message if update.callback_query else update.message
    await send_long(target, txt, reply_markup=kb)


async def buy_premium(update, context, stars: int):
    chat_id = update.effective_chat.id if update.effective_chat else update.callback_query.message.chat.id
    tier = PREMIUM_TIERS.get(stars, PREMIUM_TIERS[49])
    try:
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=f"{tier['name']} {stars} Stars",
            description=tier["perks"],
            payload=f"premium_{stars}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(f"{tier['name']} {stars}", stars)],
        )
    except Exception as e:
        logger.error("invoice: %s", e)
        await context.bot.send_message(
            chat_id=chat_id,
            text="Invoice failed. Use /invite for free uses or retry /premium.",
        )


async def precheckout(u, c):
    await u.pre_checkout_query.answer(ok=True)


async def successful_payment(u, c):
    payload = "premium_49"
    if u.message and u.message.successful_payment:
        payload = u.message.successful_payment.invoice_payload
    stars = 49
    if "199" in str(payload):
        stars = 199
    elif "99" in str(payload):
        stars = 99
    days = PREMIUM_TIERS[stars]["days"]
    user = get_user(str(u.effective_user.id))
    grant_premium_days(user, days)
    user["uses"] = 0
    add_xp(user, 40)
    save_users(users)
    await u.message.reply_text(
        f"🎉 **{PREMIUM_TIERS[stars]['name']} on for {days} days**\nTry: `resume for dream job`",
        parse_mode="Markdown",
    )


async def invite(update, context):
    uid = update.effective_user.id
    user = get_user(uid)
    bot = (await context.bot.get_me()).username
    link = f"https://t.me/{bot}?start={uid}"
    txt = f"""🔗 **INVITE TIERS**

Link: `{link}`

Invites: {user.get("invited", 0)}
Balance: {uses_left(user)}
Premium: {"Yes" if user.get("premium") else "No"}

**Rewards**
• 1 friend = +1 use +10 XP
• 3 = +5 uses
• 10 = 1 month Premium
• 25 = 60 days Premium +10 uses
• 50 = 90 days + cash claim flag
• 100 = long Premium + higher cash flag

Cash is **manual** (you still need a real payout process). The bot only unlocks a claim flag.
"""
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("WhatsApp", url=f"https://wa.me/?text=ATS%20Resume%20bot%20{link}")],
            [InlineKeyboardButton("Telegram", url=f"https://t.me/share/url?url={link}&text=Free%20ATS%20resume%20bot")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        ]
    )
    target = update.callback_query.message if update.callback_query else update.message
    await send_long(target, txt, reply_markup=kb)


async def stats(update, context):
    uid = update.effective_user.id
    user = get_user(uid)
    apply_streak(user)
    save_users(users)
    lvl = get_level(user)
    txt = f"""📊 **Stats**
ID: {uid}
Joined: {str(user.get("joined", "")).split("T")[0]}
Balance: {uses_left(user)}
Premium till: {user.get("premium_till") or "—"}
XP: {user.get("xp", 0)} | Level: {lvl}/100 | Rank: {get_rank(lvl)}
Next level in: {xp_to_next(user)} XP
Streak: {user.get("streak", 0)} | Last streak: {user.get("last_streak_date") or "—"}
Bonus claimed: {user.get("last_bonus_date") or "never"}
Quiz score: {user.get("quiz_score", 0)} | Last quiz: {user.get("last_quiz_date") or "—"}
Invited: {user.get("invited", 0)}
Users on this instance: {len(users)}
"""
    target = update.callback_query.message if update.callback_query else update.message
    await send_long(target, txt)


async def help_cmd(update, context):
    txt = """🆘 **HELP**
`resume for 12th pass sales job in Akola`
`email for job application`
`caption for my shop`
`business idea for tiffin service`
`image prompt for logo`
`interview for sales job`
`roadmap for sales job`
`salary for sales executive`
`youtube script for my shop`
`thumbnail for career video`
/bonus /quiz /leaderboard /invite /premium /stats
Limit? Invite 3/10/25/50/100 or Stars 49/99/199.
"""
    target = update.callback_query.message if update.callback_query else update.message
    await send_long(target, txt)


async def bonus_cmd(update, context):
    uid = update.effective_user.id
    banned, reason = is_banned(uid)
    target = update.message or (update.callback_query.message if update.callback_query else None)
    if banned:
        await target.reply_text(f"Access paused: {reason}")
        return
    user = get_user(uid)
    today = today_str()
    if user.get("last_bonus_date") == today:
        await send_long(target, f"🎁 Daily bonus already claimed for {today}. Come back tomorrow.")
        return
    user["last_bonus_date"] = today
    user["uses"] = max(0, int(user.get("uses") or 0) - 1)
    add_xp(user, 10)
    streak_info = apply_streak(user)
    save_users(users)
    extra = streak_info.get("reward_note") or "Streak updated"
    await send_long(
        target,
        f"🎁 **Daily bonus claimed**\n+1 use, +10 XP\nStreak {user.get('streak')} | {extra}\nBalance: {uses_left(user)}",
    )


async def quiz_cmd(update, context):
    uid = str(update.effective_user.id)
    target = update.message or update.callback_query.message
    banned, reason = is_banned(uid)
    if banned:
        await target.reply_text(f"Access paused: {reason}")
        return
    user = get_user(uid)
    if user.get("last_quiz_date") == today_str() and user.get("quiz_pending") is None:
        await send_long(target, "🧠 Today's quiz already completed. +XP tomorrow.")
        return
    q = daily_quiz_for_user(uid)
    user["quiz_pending"] = q["id"]
    save_users(users)
    buttons = [
        [InlineKeyboardButton(opt, callback_data=f"quizans_{q['id']}_{i}")]
        for i, opt in enumerate(q["options"])
    ]
    await send_long(
        target,
        f"🧠 **Daily quiz**\n{q['q']}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def quiz_answer(update, context, data: str):
    uid = str(update.effective_user.id)
    user = get_user(uid)
    parts = data.split("_")
    qid = parts[1]
    try:
        choice = int(parts[2])
    except (IndexError, ValueError):
        return
    q = next((x for x in QUIZ_BANK if x["id"] == qid), None)
    if not q:
        return
    if user.get("quiz_pending") != qid:
        await update.callback_query.message.reply_text("This quiz expired. /quiz")
        return
    user["quiz_pending"] = None
    user["last_quiz_date"] = today_str()
    correct = choice == q["answer"]
    if correct:
        user["quiz_score"] = int(user.get("quiz_score") or 0) + 1
        add_xp(user, 20)
        user["uses"] = max(0, int(user.get("uses") or 0) - 1)
        msg = f"✅ Correct! +20 XP and +1 use.\n{q['why']}"
    else:
        add_xp(user, 5)
        right = q["options"][q["answer"]]
        msg = f"❌ Answer: **{right}**\n{q['why']}\n+5 XP for trying."
    save_users(users)
    await send_long(update.callback_query.message, msg)


async def leaderboard_cmd(update, context):
    target = update.message or update.callback_query.message
    rows = leaderboard_rows(10)
    if not rows:
        await target.reply_text("No users yet.")
        return
    lines = ["🏆 **TOP 10 — XP + invites**\nScore = XP + (invites × 25)\n"]
    for i, (uid, rec, score) in enumerate(rows, start=1):
        lvl = get_level(rec)
        lines.append(
            f"{badge_for_rank(i)} {i}. `{uid[-4:]}` | {score} pts | L{lvl} {get_rank(lvl)} | {rec.get('invited', 0)} invites"
        )
    await send_long(target, "\n".join(lines))


async def admin_ban(update, context):
    uid = str(update.effective_user.id)
    if ADMIN_IDS and uid not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /ban <telegram_id> [reason]")
        return
    target_id = context.args[0]
    reason = " ".join(context.args[1:]) or "policy"
    banned_ids[target_id] = {"reason": reason, "at": now_iso()}
    if target_id in users:
        users[target_id]["banned"] = True
        users[target_id]["ban_reason"] = reason
        save_users(users)
    save_bans()
    await update.message.reply_text(f"Banned {target_id}: {reason}")


async def admin_unban(update, context):
    uid = str(update.effective_user.id)
    if ADMIN_IDS and uid not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /unban <telegram_id>")
        return
    target_id = context.args[0]
    banned_ids.pop(target_id, None)
    if target_id in users:
        users[target_id]["banned"] = False
        users[target_id]["ban_reason"] = None
        save_users(users)
    save_bans()
    await update.message.reply_text(f"Unbanned {target_id}")


@web_app.route("/")
def home():
    return jsonify(
        {
            "bot": "Global AI Assistant - Ultra Best",
            "status": "Live 24/7",
            "version": "2026.6 ULTRA BEST",
            "users": len(load_users_safe()),
            "features": [
                "Resume ATS",
                "Cover Letter",
                "Interview",
                "Email",
                "Caption",
                "Image Prompt",
                "Business",
                "LinkedIn",
                "Roadmap",
                "Salary",
                "YouTube",
                "Thumbnail",
                "Streak",
                "Quiz",
                "Leaderboard",
            ],
        }
    ), 200


@web_app.route("/health")
def health():
    return "OK - Ultra Best Live", 200


@web_app.route("/ping")
def ping():
    return "pong", 200


def run_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing in environment")
        return
    print(f"TOKEN OK len={len(BOT_TOKEN)} starting bot")

    async def polling():
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("resume", cmd_resume))
        app.add_handler(CommandHandler("email", cmd_email))
        app.add_handler(CommandHandler("caption", cmd_caption))
        app.add_handler(CommandHandler("image", cmd_image))
        app.add_handler(CommandHandler("idea", cmd_idea))
        app.add_handler(CommandHandler("interview", cmd_interview))
        app.add_handler(CommandHandler("cover", cmd_cover))
        app.add_handler(CommandHandler("roadmap", cmd_roadmap))
        app.add_handler(CommandHandler("salary", cmd_salary))
        app.add_handler(CommandHandler("youtube", cmd_youtube))
        app.add_handler(CommandHandler("thumbnail", cmd_thumb))
        app.add_handler(CommandHandler("premium", premium))
        app.add_handler(CommandHandler("invite", invite))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(CommandHandler("bonus", bonus_cmd))
        app.add_handler(CommandHandler("quiz", quiz_cmd))
        app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
        app.add_handler(CommandHandler("ban", admin_ban))
        app.add_handler(CommandHandler("unban", admin_unban))
        app.add_handler(PreCheckoutQueryHandler(precheckout))
        app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

        async def b49(u, c):
            await buy_premium(u, c, 49)

        async def b99(u, c):
            await buy_premium(u, c, 99)

        async def b199(u, c):
            await buy_premium(u, c, 199)

        app.add_handler(CallbackQueryHandler(b49, pattern="^buy_49$"))
        app.add_handler(CallbackQueryHandler(b99, pattern="^buy_99$"))
        app.add_handler(CallbackQueryHandler(b199, pattern="^buy_199$"))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tool))
        await app.initialize()
        await app.bot.delete_webhook(drop_pending_updates=True)
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
        print("Bot polling live")
        while True:
            await asyncio.sleep(3600)

    try:
        asyncio.run(polling())
    except Exception as e:
        print(f"Crash: {e}")
        traceback.print_exc()
        time.sleep(5)
        run_bot()


if __name__ == "__main__":
    users.update(load_users_safe())
    banned_ids.update(load_bans())
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    print(f"Flask 0.0.0.0:{port} TOKEN={bool(BOT_TOKEN)}")
    web_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

