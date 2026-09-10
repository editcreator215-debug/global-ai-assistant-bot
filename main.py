# ============ GLOBAL AI ASSISTANT - ULTRA BEST WORLD EDITION 2026 ============
# USA ATS Resume Engine | India Market Tools | GenZ Viral Content | Gamified Growth
# Core: 12 Career/Business Tools | Streaks | Levels | Quiz | Leaderboard | Premium + Invite Economy
 
import os
import json
import logging
import threading
import asyncio
import random
import re
import time
from datetime import datetime, timedelta, date
from flask import Flask, jsonify
 
web_app = Flask(__name__)
 
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = os.environ.get("ADMIN_ID", "").strip()
FREE_LIMIT = 5
PREMIUM_TIER1 = 49
PREMIUM_TIER2 = 99
PREMIUM_TIER3 = 199
PREMIUM_TIER1_DAYS = 30
PREMIUM_TIER2_DAYS = 90
PREMIUM_TIER3_DAYS = 365
DATA_FILE = "users.json"
RATE_LIMIT_SECONDS = 1.5
INVITE_TIERS = [3, 10, 25, 50, 100]
MAX_LEVEL = 100
 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
 
_last_action_time = {}
 
 
@web_app.route('/')
def home():
    return jsonify({
        "bot": "Global AI Assistant - Ultra Best",
        "status": "Live 24/7 World Wide",
        "version": "2026.7 ULTRA BEST GAMIFIED",
        "users": len(load_users_safe()),
        "features": [
            "Resume 98 ATS", "Cover Letter", "Interview Q&A", "Email",
            "Caption Viral", "Image Prompt 8K", "Business 1Lakh", "LinkedIn",
            "Sales Roadmap", "Salary Negotiation", "YouTube Script", "Thumbnail CTR",
            "Streaks", "Levels", "Daily Quiz", "Leaderboard"
        ],
        "earning": "Premium Stars 49/99/199 + Invite Rewards 3/10/25/50/100"
    }), 200
 
 
@web_app.route('/health')
def health():
    return "OK - Ultra Best Live", 200
 
 
@web_app.route('/ping')
def ping():
    return "pong", 200
 
 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, filters, ContextTypes
)
 
 
# ==================== DATA PERSISTENCE ====================
 
def load_users_safe():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Load error: {e}")
            return {}
    return {}
 
 
def save_users(d):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Save error: {e}")
 
 
users = load_users_safe()
 
 
def get_user(uid, name=None):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "uses": 0,
            "premium": False,
            "premium_till": None,
            "invited": 0,
            "joined": datetime.now().isoformat(),
            "xp": 0,
            "level": 1,
            "streak": 0,
            "last_streak_date": None,
            "last_bonus_date": None,
            "last_quiz_date": None,
            "last_quiz_id": None,
            "quiz_score": 0,
            "quiz_correct": 0,
            "quiz_attempted": 0,
            "banned": False,
            "invite_tiers_claimed": [],
            "name": name or "Player"
        }
    u = users[uid]
    u.setdefault("xp", 0)
    u.setdefault("level", 1)
    u.setdefault("streak", 0)
    u.setdefault("last_streak_date", None)
    u.setdefault("last_bonus_date", None)
    u.setdefault("last_quiz_date", None)
    u.setdefault("last_quiz_id", None)
    u.setdefault("quiz_score", 0)
    u.setdefault("quiz_correct", 0)
    u.setdefault("quiz_attempted", 0)
    u.setdefault("banned", False)
    u.setdefault("invite_tiers_claimed", [])
    u.setdefault("name", name or "Player")
    if name:
        u["name"] = name
    if u.get("premium_till"):
        try:
            if datetime.now() > datetime.fromisoformat(u["premium_till"]):
                u["premium"] = False
                u["premium_till"] = None
        except Exception:
            pass
    return u
 
 
def is_banned(uid):
    uid = str(uid)
    return users.get(uid, {}).get("banned", False)
 
 
def ban_user(uid):
    u = get_user(uid)
    u["banned"] = True
    save_users(users)
 
 
def unban_user(uid):
    u = get_user(uid)
    u["banned"] = False
    save_users(users)
 
 
def is_rate_limited(uid):
    uid = str(uid)
    now = time.time()
    last = _last_action_time.get(uid, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    _last_action_time[uid] = now
    return False
 
 
async def safe_reply(target, text, reply_markup=None):
    """Send a message with Markdown, silently falling back to plain text
    if Telegram rejects the markdown entities (unbalanced * _ ` etc.)."""
    try:
        await target.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Markdown send failed, falling back to plain text: {e}")
        plain = re.sub(r'[*_`\[\]]', '', text)
        try:
            await target.reply_text(plain, reply_markup=reply_markup)
        except Exception as e2:
            logger.error(f"Plain text send also failed: {e2}")
 
 
# ==================== LEVEL / XP / RANK SYSTEM ====================
 
def get_level(xp):
    lvl = (xp // 50) + 1
    return min(lvl, MAX_LEVEL)
 
 
def get_rank(level):
    if level >= 100:
        return "👑 LEGEND"
    if level >= 75:
        return "💎 MASTER"
    if level >= 50:
        return "🔥 EXPERT"
    if level >= 25:
        return "🥇 PRO"
    if level >= 10:
        return "🥈 HUSTLER"
    return "🥉 ROOKIE"
 
 
def add_xp(user, amount):
    """Adds XP, recomputes level, returns True if the user leveled up."""
    old_level = get_level(user.get("xp", 0))
    user["xp"] = user.get("xp", 0) + amount
    new_level = get_level(user["xp"])
    user["level"] = new_level
    return new_level > old_level
 
 
# ==================== STREAK SYSTEM ====================
 
def update_streak_and_get_message(user):
    """Call once per user interaction. Only actually updates the streak once
    per calendar day (tracked via last_streak_date) so repeated tool use in
    the same day does not farm XP or streak length."""
    today = date.today()
    last_raw = user.get("last_streak_date")
    messages = []
 
    if last_raw:
        try:
            last_date = date.fromisoformat(last_raw)
        except Exception:
            last_date = None
    else:
        last_date = None
 
    if last_date == today:
        return None  # already processed today
 
    if last_date == today - timedelta(days=1):
        user["streak"] = user.get("streak", 0) + 1
        add_xp(user, 15)
        messages.append(f"🔥 Streak Day {user['streak']}! +15 XP")
    else:
        user["streak"] = 1
        add_xp(user, 15)
        if last_date is not None:
            messages.append("😅 Streak reset - Day 1 restarted. +15 XP")
        else:
            messages.append("🔥 Streak started! Day 1. +15 XP")
 
    user["last_streak_date"] = today.isoformat()
    streak = user["streak"]
 
    if streak == 3:
        user["uses"] = max(0, user.get("uses", 0) - 1)
        messages.append("🎉 3-Day Streak Reward: +1 Free Use!")
    if streak == 7:
        user["uses"] = max(0, user.get("uses", 0) - 2)
        add_xp(user, 50)
        messages.append("🎉 7-Day Streak Reward: +2 Free Uses & +50 XP!")
    if streak == 30:
        user["premium"] = True
        current_till = user.get("premium_till")
        base = datetime.now()
        if current_till:
            try:
                existing = datetime.fromisoformat(current_till)
                if existing > base:
                    base = existing
            except Exception:
                pass
        user["premium_till"] = (base + timedelta(days=7)).isoformat()
        messages.append("🏆 30-Day Streak Reward: 1 Week FREE Premium unlocked!")
 
    return " | ".join(messages) if messages else None
 
 
# ==================== DAILY BONUS ====================
 
def claim_daily_bonus(user):
    today = date.today().isoformat()
    if user.get("last_bonus_date") == today:
        return None, False
    bonus_uses = random.choice([1, 1, 2, 2, 3])
    bonus_xp = random.choice([10, 15, 20])
    user["uses"] = max(0, user.get("uses", 0) - bonus_uses)
    add_xp(user, bonus_xp)
    user["last_bonus_date"] = today
    msg = f"🎁 Daily Bonus Claimed!\n+{bonus_uses} Free Uses\n+{bonus_xp} XP"
    return msg, True
 
 
# ==================== DAILY QUIZ SYSTEM ====================
 
QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "🎯 ATS Resume: Kaunsa format ATS score sabse zyada badhata hai?",
        "options": ["Fancy graphics + tables", "Simple text with keywords", "Photo + colorful design", "PDF with columns only"],
        "answer": 1,
        "explain": "ATS bots tables/graphics/columns ko misread karte hain. Simple single-column text + exact job keywords = highest ATS score (95+)."
    },
    {
        "id": 2,
        "question": "🎯 ATS Resume: Resume me keywords kahan se copy karne chahiye?",
        "options": ["Google se random", "Job description se exact match", "Friend ke resume se", "Sirf apne skills se"],
        "answer": 1,
        "explain": "Job description me jo exact words hain (jaise 'CRM', 'Lead Generation') wahi resume me use karo — ATS exact match search karta hai."
    },
    {
        "id": 3,
        "question": "📧 Email: Job application email bhejne ka best time kaunsa hai?",
        "options": ["Raat 11 PM", "Subah 9:30-11 AM", "Sunday din bhar", "Dopahar 3-4 PM"],
        "answer": 1,
        "explain": "HR log office khulte hi (9:30-11 AM) inbox check karte hain — is time bheja email top pe dikhta hai aur jaldi khulta hai."
    },
    {
        "id": 4,
        "question": "📧 Email: Follow-up email kitne din baad bhejna chahiye?",
        "options": ["Usi din 5 baar", "2-3 din baad ek baar", "1 mahine baad", "Kabhi nahi"],
        "answer": 1,
        "explain": "2-3 din ka gap professional hai — HR ko time milta hai reply karne ka, aur aap unke radar pe bhi rehte ho."
    },
    {
        "id": 5,
        "question": "💰 Salary Negotiation: Salary discussion me pehle number kaun bataye?",
        "options": ["Aap khud pehle bol do", "Company se pehle range poochho", "Kabhi mat batao", "Bahut kam bata do"],
        "answer": 1,
        "explain": "Jo pehle number bolta hai wo usually kam pe settle hota hai. Pehle company ka budget/range poochho, phir apna range 10-15% upar rakho."
    },
    {
        "id": 6,
        "question": "💰 Salary Negotiation: Counter-offer karte time sabse important cheez?",
        "options": ["Emotional ho jao", "Market data + apni value batao", "Threat do naukri chhodne ka", "Chup rehna"],
        "answer": 1,
        "explain": "Data-backed negotiation (market salary research + apne achievements) HR ko convince karta hai, emotion ya threat nahi."
    },
    {
        "id": 7,
        "question": "📱 Instagram: Reel post karne ka best time kaunsa hai (India audience)?",
        "options": ["Subah 5 AM", "Raat 7-9 PM", "Dopahar 1-2 PM office time", "Koi bhi time same hai"],
        "answer": 1,
        "explain": "7-9 PM me log office/college se free hokar phone scroll karte hain — is window me reach aur engagement sabse zyada milta hai."
    },
    {
        "id": 8,
        "question": "📱 Instagram: Reel ka pehla 3 second sabse important kyun hai?",
        "options": ["Bas aise hi", "Hook wahi decide karta hai scroll rukega ya nahi", "Instagram rule hai", "Views count nahi hota"],
        "answer": 1,
        "explain": "Algorithm dekhta hai log 3 second ke andar scroll karte hain ya rukte hain. Strong hook (question/shock/curiosity) = zyada watch time = zyada reach."
    },
]
 
 
def get_quiz_question(user):
    today = date.today().isoformat()
    if user.get("last_quiz_date") == today:
        return None
    q = random.choice(QUIZ_QUESTIONS)
    user["last_quiz_id"] = q["id"]
    return q
 
 
def check_quiz_answer(user, qid, option_idx):
    today = date.today().isoformat()
    if user.get("last_quiz_date") == today:
        return None
    question = next((q for q in QUIZ_QUESTIONS if q["id"] == qid), None)
    if not question:
        return None
    user["last_quiz_date"] = today
    user["quiz_attempted"] = user.get("quiz_attempted", 0) + 1
    correct = (option_idx == question["answer"])
    if correct:
        user["quiz_correct"] = user.get("quiz_correct", 0) + 1
        user["quiz_score"] = user.get("quiz_score", 0) + 10
        add_xp(user, 10)
    return {
        "correct": correct,
        "explain": question["explain"],
        "correct_option": question["options"][question["answer"]]
    }
 
 
# ==================== LEADERBOARD ====================
 
LEADERBOARD_BADGES = ["👑", "🥇", "🥈", "🥉"]
 
 
def build_leaderboard_text():
    scored = []
    for uid, u in users.items():
        score = u.get("xp", 0) + (u.get("invited", 0) * 20)
        scored.append((uid, u.get("name", "Player"), score, u.get("xp", 0), u.get("invited", 0), u.get("level", 1)))
    scored.sort(key=lambda x: x[2], reverse=True)
    top10 = scored[:10]
    if not top10:
        return "📊 **LEADERBOARD**\n\nAbhi koi ranked user nahi hai. Pehle bano! Kuch tool use karo aur XP kamao."
    lines = ["🏆 **TOP 10 LEADERBOARD - XP + Invites**\n"]
    for i, (uid, name, score, xp, invited, level) in enumerate(top10):
        badge = LEADERBOARD_BADGES[i] if i < len(LEADERBOARD_BADGES) else f"#{i+1}"
        rank_name = get_rank(level)
        lines.append(f"{badge} **{name}** - Score {score} (XP:{xp} + Invites:{invited}) | Lvl {level} {rank_name}")
    lines.append("\n💡 XP kamane ke liye tools use karo, streak maintain karo, quiz kheelo, friends invite karo!")
    return "\n".join(lines)
 
 
# ==================== JOB CATEGORY DETECTION (for dynamic resume content) ====================
 
JOB_KEYWORDS = {
    "sales": {
        "keywords": "Sales Target, Lead Generation, Cold Calling, CRM (Zoho/Salesforce), Client Relationship, Negotiation, B2B/B2C Sales, Revenue Growth, Upselling, Pipeline Management, Field Sales, Channel Sales",
        "summary_line": "target-driven sales professional with proven record of lead generation, client relationship management and quota achievement",
        "experience_bullets": [
            "Consistently achieved 100-120% of monthly sales target for 6 consecutive months",
            "Generated 40+ qualified leads/month via cold calling, field visits and referrals",
            "Built and maintained relationships with 60+ active clients, improving retention by 25%",
            "Negotiated deals worth ₹2L+ monthly, closing at healthy margins"
        ],
        "skills": "CRM Software (Zoho/Salesforce basics), Lead Generation, Cold Calling, Negotiation, Client Onboarding, MS Excel for Sales MIS, Territory Planning",
        "certifications": "Certificate in Sales & Negotiation Skills, CRM Basics Certification"
    },
    "data": {
        "keywords": "Data Entry, MS Excel (VLOOKUP/Pivot), SQL Basics, Data Cleaning, Data Analysis, Power BI, Google Sheets, Reporting, Data Visualization, Attention to Detail, Database Management",
        "summary_line": "detail-oriented data professional skilled in Excel, data cleaning and reporting with high accuracy under deadlines",
        "experience_bullets": [
            "Processed 500+ data entries daily with 99.8% accuracy using Excel and Google Sheets",
            "Built automated Pivot Table dashboards, reducing manual reporting time by 5 hrs/week",
            "Cleaned and validated 10,000+ row datasets, removing duplicates and errors before analysis",
            "Created weekly MIS reports for management using VLOOKUP, charts and conditional formatting"
        ],
        "skills": "MS Excel (Advanced), SQL Basics, Power BI Basics, Google Sheets, Data Cleaning, Data Validation, Typing Speed 45+ WPM",
        "certifications": "Certificate in Advanced Excel & Data Analytics, SQL for Beginners Certification"
    },
    "marketing": {
        "keywords": "Social Media Marketing, Content Calendar, SEO Basics, Instagram/Facebook Ads, Campaign Analytics, Brand Awareness, Copywriting, Canva Design, Influencer Outreach, Email Marketing, Google Analytics",
        "summary_line": "creative digital marketing professional experienced in content planning, social media growth and campaign execution",
        "experience_bullets": [
            "Grew Instagram page from 500 to 8,000 followers in 4 months via consistent Reels strategy",
            "Planned and executed monthly content calendar across Instagram, Facebook and WhatsApp",
            "Ran ₹5k/month Instagram ad campaigns achieving 3.5x ROAS",
            "Designed 100+ creatives using Canva, improving post engagement rate by 40%"
        ],
        "skills": "Canva, Instagram/Facebook Ads Manager, Content Calendar Planning, Basic SEO, Copywriting, Google Analytics Basics, Email Marketing (Mailchimp)",
        "certifications": "Google Digital Marketing Certification, Meta Social Media Marketing Certificate"
    },
    "default": {
        "keywords": "Customer Handling, MS Office, Excel, Team Work, Communication, CRM, Problem Solving, Time Management, Hindi, Marathi, English",
        "summary_line": "motivated and results-driven professional with strong communication and customer handling skills",
        "experience_bullets": [
            "Handled 50+ customers daily, increasing satisfaction score by 30%",
            "Managed billing worth ₹15k/day in Excel with 100% accuracy",
            "Achieved daily targets 10 out of 10 working days",
            "Learned new job-specific tools and processes within 7 days of joining"
        ],
        "skills": "MS Word, Excel, Google Sheets, WhatsApp Business, CRM Basics, Leadership, Punctuality, Quick Learning",
        "certifications": "Certificate in Computer Fundamentals & MS Office"
    }
}
 
 
JOB_KEYWORDS["support"] = {
    "keywords": "Customer Support, Query Resolution, Zendesk/Freshdesk, Ticket Handling, SLA Adherence, Voice/Chat Process, Complaint Handling, Product Knowledge, Escalation Management, Customer Satisfaction (CSAT)",
    "summary_line": "patient and solution-focused customer support professional experienced in ticket resolution and maintaining high CSAT scores",
    "experience_bullets": [
        "Resolved 60+ customer tickets/calls daily while maintaining 90%+ CSAT score",
        "Handled escalations calmly, reducing repeat complaints by 20%",
        "Maintained SLA compliance of 95%+ across voice and chat support channels",
        "Documented common issues into a knowledge base, cutting average resolution time by 15%"
    ],
    "skills": "Zendesk/Freshdesk Basics, Ticket Management, Active Listening, Complaint Handling, MS Excel, Typing Speed 40+ WPM",
    "certifications": "Certificate in Customer Service Excellence, Communication Skills Certification"
}
JOB_KEYWORDS["teaching"] = {
    "keywords": "Lesson Planning, Classroom Management, Student Engagement, Curriculum Delivery, Assessment Design, Subject Expertise, Parent Communication, Online Teaching Tools (Zoom/Google Classroom)",
    "summary_line": "dedicated and patient teaching professional skilled in lesson planning, classroom management and student engagement",
    "experience_bullets": [
        "Planned and delivered lessons for 30+ students, improving average test scores by 15%",
        "Managed classroom of 25-35 students maintaining discipline and engagement",
        "Conducted parent-teacher meetings, improving parent satisfaction and student attendance",
        "Used Google Classroom/Zoom for hybrid teaching during online sessions"
    ],
    "skills": "Lesson Planning, Classroom Management, MS Office/Google Classroom, Assessment Design, Subject Matter Expertise, Communication",
    "certifications": "B.Ed / Teaching Certification (if applicable), Subject-specific Certification"
}
 
 
def detect_job_category(text):
    t = text.lower()
    if any(x in t for x in ["sales", "bd executive", "business development", "field sales", "telecaller"]):
        return "sales"
    if any(x in t for x in ["data entry", "data analyst", "data ", "excel operator", "mis executive"]):
        return "data"
    if any(x in t for x in ["marketing", "social media", "digital marketing", "content creator", "seo"]):
        return "marketing"
    if any(x in t for x in ["support", "customer care", "helpdesk", "bpo", "call center", "call centre"]):
        return "support"
    if any(x in t for x in ["teacher", "teaching", "tutor", "faculty", "professor"]):
        return "teaching"
    return "default"
 
 
# ==================== TOOL: ULTRA ATS RESUME (Dynamic by Job Category) ====================
 
def tool_resume(p):
    job = p.replace("resume for", "").replace("resume", "").replace("/resume", "").strip().title() or "Sales Executive in Akola"
    category = detect_job_category(p)
    data = JOB_KEYWORDS[category]
 
    exp_bullets_text = "\n".join([f"• {b}" for b in data["experience_bullets"]])
 
    return f"""✅ **ULTRA ATS RESUME - {job} - Score 98/100 (USA + India Format)**
🎯 Category Detected: {category.upper()} — content customized for this field
 
**[YOUR FULL NAME]**
📍 Akola, Maharashtra | 📞 +91 9XXXX XXXXX
✉️ yourname@gmail.com | 🔗 linkedin.com/in/yourname | 🌐 Portfolio (optional)
 
**PROFESSIONAL SUMMARY (2 Lines = HR 6-Second Rule)**
Motivated and {data['summary_line']} looking to join as {job}. 1 year hands-on experience, fluent in Hindi/Marathi/English, immediate joiner in Akola/Nagpur/Pune region.
 
**ATS KEYWORDS (Copy Exactly — Required for 98 Score)**
{data['keywords']}
 
**EDUCATION**
• 12th / Graduation - Maharashtra State Board - 2024 - 75%
• Certification: {data['certifications']}
 
**EXPERIENCE (Fresher? Frame Internship/Family Business Like a Pro)**
**{job} Associate | Family Business / Internship | Akola | 2023 - Present**
{exp_bullets_text}
 
**PROJECTS (Fills Gap if No Formal Job Yet)**
• Built a {category if category != 'default' else 'work'} tracker sheet in Excel — saved 5+ hrs/week of manual effort
• Created WhatsApp Business catalog of 20 products — generated 15 direct orders in 2 weeks
• Ran a small local awareness drive — reached 200+ people offline and online combined
 
**SKILLS**
Technical: {data['skills']}
Soft Skills: Leadership, Punctuality, Hardworking, Quick Learner, Time Management, Adaptability
 
**LANGUAGES**
Hindi (Native), Marathi (Native), English (Professional Working Proficiency)
 
**ACHIEVEMENTS**
• Consistent top performer in attendance and task completion (95%+)
• Recognized by supervisor/family business for reliability and initiative
 
**DECLARATION**
I hereby declare that the above information is true to the best of my knowledge.
 
---
🔥 **7-DIN ME NAUKRI TRICK ({category.upper()} SPECIAL):**
1. Word me paste karke PDF banao: `Resume_{job.replace(' ', '_')}.pdf` (never send .docx to HR)
2. Naukri/Indeed/LinkedIn pe roz 15-20 applications daalo, subah 9:30-11 AM ke beech
3. Application subject line: "{job} - Akola - Immediate Joiner - 95% Match"
4. Apply karne ke 1 ghante baad HR ko WhatsApp/LinkedIn pe seedha message karo:
   "Hi, maine {job} role apply kiya hai, 1 saal experience hai, kal se join kar sakta/sakti hoon."
5. Resume ke top pe hamesha job description ke exact keywords rakho — ATS filter sabse pehle unhi ko match karta hai.
 
📊 **Category-Specific Tip:** {"Sales resumes should always show a NUMBER (target %, leads, revenue) in every bullet — HR skips resumes without measurable results." if category == "sales" else "Data resumes should highlight ACCURACY % and tools (Excel/SQL) — recruiters scan for exact tool names." if category == "data" else "Marketing resumes should show GROWTH metrics (followers, reach, ROAS) — vague 'managed social media' lines get rejected." if category == "marketing" else "Generic resumes should still add at least 2-3 numbers (customers handled, accuracy %, targets hit) to stand out."}
 
Type next: `cover letter for {job}` or `interview for {job}` for the next step!
"""
 
 
# ==================== TOOL: COVER LETTER ====================
 
def tool_cover(p):
    job = p.replace("cover letter for", "").replace("cover for", "").replace("cover", "").strip().title() or "Sales Executive"
    category = detect_job_category(p)
    data = JOB_KEYWORDS[category]
    return f"""📄 **COVER LETTER - {job} - USA Format (3x More Interview Calls)**
 
[Your Name] | Akola | +91 9XXXX | {datetime.now().strftime('%d %B %Y')}
 
Hiring Manager, [Company Name], [City]
 
Subject: Application for {job} - 98% ATS Match - Immediate Joiner
 
Dear Hiring Manager,
 
I am excited to apply for the {job} role at [Company Name]. As a {data['summary_line']}, I believe I can contribute from Day 1.
 
In my last role I:
• {data['experience_bullets'][0]}
• {data['experience_bullets'][1]}
• {data['experience_bullets'][2]}
 
I am based in Akola, familiar with the local market, and can join within 24 hours of an offer. I am available for an interview tomorrow at 11 AM, in person or on call.
 
Thank you for considering my application.
 
Sincerely,
[Your Name]
 
---
📌 **Usage Tip:** Copy this into Word, convert to PDF, and attach it along with your resume in the same email — applications with a cover letter get roughly 3x more interview calls than resume-only applications.
"""
 
 
# ==================== TOOL: INTERVIEW Q&A ====================
 
def tool_interview(p):
    job = p.replace("interview for", "").replace("interview", "").strip().title() or "Sales Job"
    category = detect_job_category(p)
    return f"""🎯 **INTERVIEW Q&A - {job} - Selection Prep**
 
**Q1: Tell me about yourself?**
"I am from Akola, completed 12th in 2024. I have 1 year of experience in {category if category != 'default' else 'customer handling'}, worked closely with day-to-day operations, and I am fluent in Hindi, Marathi and English. I am hardworking, punctual, and an immediate joiner. I'm interested in {job} because it matches my skills and growth goals."
 
**Q2: Why should we hire you?**
"Three reasons: 1) I can join within 24 hours, 2) I know Hindi/Marathi/English plus the tools required for {job}, 3) I understand the local Akola market. I am confident I can hit my targets within the first month."
 
**Q3: What is your expected salary?**
"As per the company standard for {job} in Akola, I'd expect somewhere in the typical local range, but I'm flexible — growth and learning matter more to me than the starting number."
 
**Q4: What is your biggest strength?**
"Hardworking, quick learner, and strong at {('closing deals and building client trust' if category=='sales' else 'accuracy under deadlines' if category=='data' else 'creating content that gets engagement' if category=='marketing' else 'customer handling')}."
 
**Q5: What is your biggest weakness?**
"Sometimes I push myself too hard to complete a target — I'm actively working on better time management to balance that."
 
**Q6: Where do you see yourself in 5 years?**
"Growing into a senior/team lead role within {job}, ideally within your company, having built strong results along the way."
 
**3 SMART QUESTIONS TO ASK THE INTERVIEWER (Impress Them Back):**
1. What does a typical day look like for someone in this {job} role?
2. What's the biggest challenge the team is currently facing?
3. What growth or promotion path exists for someone who performs well here?
 
**Before You Go:** Formal dress, 2 printed resume copies, arrive 10 minutes early, confident smile, firm handshake.
 
Next: `cover letter for {job}` or `salary negotiation for {job}`
"""
 
 
# ==================== TOOL: PROFESSIONAL EMAIL ====================
 
def tool_email(p):
    role = p.replace("email for", "").replace("email", "").strip().title() or "Sales Job"
    category = detect_job_category(p)
    return f"""📧 **PRO EMAIL - {role} - 90% Open Rate**
 
**SUBJECT 1:** Application for {role} - Immediate Joiner - Akola - 95% Match
**SUBJECT 2:** {role} Application - Ready to Join Tomorrow
 
---
**BODY (Copy Paste):**
 
Dear Hiring Manager,
 
I hope you're doing well. I'm writing to apply for the {role} role that I saw posted on Naukri/LinkedIn.
 
**Why I'm a good fit:**
• 12th pass + working knowledge of MS Office and Excel
• 1 year of relevant {category if category != 'default' else 'customer handling'} experience
• Fluent in Hindi, Marathi and English
• Hardworking, punctual, can join within 24 hours
• Track record of hitting targets and maintaining 95%+ attendance
 
My resume is attached. Would a 10-minute call tomorrow around 11 AM work for you? I'm also available to come in for an interview at short notice.
 
Thank you for your time.
 
Best regards,
[Your Name], Akola, +91 9XXXX XXXXX
 
**P.S.** I'm already familiar with tools relevant to {role} and can pick up any CRM/software within 2 days.
 
**Best Send Time:** 9:30-11 AM (highest HR open rate). Send one polite follow-up if no reply after 2 days.
 
Need next: `resume for {role}` or `interview for {role}`
"""
 
 
# ==================== TOOL: VIRAL INSTAGRAM CAPTION ====================
 
def tool_caption(p):
    topic = p.replace("caption for", "").replace("caption", "").strip() or "my small business"
    hooks = [
        f"POV: You finally started your {topic} journey ✨",
        f"Day 1 of building {topic} from Akola to the World 🌍",
        f"No one talks about this side of {topic} 🤫",
        f"{topic} is not hard, you just need this... 👇"
    ]
    hook = random.choice(hooks)
    tag_topic = re.sub(r'[^a-zA-Z0-9]', '', topic).lower() or "business"
    return f"""📸 **VIRAL CAPTION + 30 HASHTAGS - High Reach Formula**
 
**COPY CAPTION:**
 
{hook}
 
I thought {topic} would be hard... but consistency beats talent every time! 🔥
 
3 lessons I learned:
1. Start with whatever you already have
2. Post daily even when it feels imperfect
3. Help one person a day — trust follows
 
Building something around {topic}? Drop a ❤️ and let's grow together! 👇
Comment "START" and I'll send you my free checklist!
 
.
.
.
**30 HASHTAGS (Copy):**
#viral #trending #reels #explore #{tag_topic} #akola #maharashtra #smallbusiness #indianentrepreneur #motivation #businessideas #sidehustle #startupindia #digitalmarketing #instagood #reelsinstagram #growthmindset #success #entrepreneur #2026 #contentcreator #branding #marketingtips #earnmoneyonline #workfromhome #maharashtrian #nagpur #pune #hustle #india
 
**Best Post Time:** 7-9 PM IST (highest active audience — use `/quiz` if you want to test your Instagram timing knowledge!)
**Engagement Trick:** Reply to your first 10 comments within 30 minutes — this signals the algorithm to push the post further.
 
Need a logo too? Try: `image prompt for {topic} logo`
"""
 
 
# ==================== TOOL: AI IMAGE PROMPTS ====================
 
def tool_image(p):
    topic = p.replace("image prompt for", "").replace("image for", "").replace("image", "").strip() or "modern shop in Akola"
    return f"""🎨 **AI IMAGE PROMPTS - 8K ULTRA (Leonardo / Bing / Ideogram)**
 
**PROMPT 1 - Photo Real (Business):**
```
Ultra realistic 8K DSLR photo of {topic}, Akola Maharashtra, cinematic lighting, highly detailed, sharp focus, Sony A7R IV, 85mm f/1.4, vibrant colors, professional commercial photography, trending on Instagram --ar 4:5 --style raw
```
 
**PROMPT 2 - Logo:**
```
Minimalist modern luxury logo for {topic}, vector, flat design, golden ratio, professional branding, clean white background, 4K --no text, words
```
 
**PROMPT 3 - Poster 9:16 (Story/Reel Cover):**
```
{topic} promotional poster, Indian festival aesthetic, bold Hindi + English text, colorful, highly attractive, Akola local market vibe, 8K --ar 9:16
```
 
**NEGATIVE PROMPT (paste in negative field):** blurry, low quality, distorted, extra fingers, watermark, ugly, low resolution
 
**Where to Use:** Leonardo.ai (free tier is strong) → paste prompt → generate. For clean vector logos, Ideogram.ai tends to render text/shapes more accurately.
 
**Next Step:** `business idea for {topic}` or `thumbnail for {topic} youtube video`
"""
 
 
# ==================== TOOL: BUSINESS IDEA (₹1 LAKH/MONTH PLAN) ====================
 
def tool_business(p):
    biz = p.replace("business idea for", "").replace("idea for", "").replace("business", "").strip() or "t-shirt printing"
    tag = re.sub(r'[^a-zA-Z0-9]', '', biz).lower() or "business"
    return f"""💡 **₹1 LAKH/MONTH PLAN - {biz.title()} - Akola Validated**
 
**BUSINESS:** {biz.title()} Service, run from Akola, deliverable pan-India
 
**INVESTMENT:** ₹8,000-15,000 (can start from home)
**PROFIT MATH:** 1 order ₹150-400 profit → 5 orders/day = ₹750-2,000/day → Monthly ₹22,000-60,000 → Scale target ₹1L+
 
**7 DAYS TO YOUR FIRST ORDER:**
 
**Day 1-2 — Setup:**
1. Instagram page: @{tag}akola — Bio: "DM to Order | Pan India Delivery"
2. WhatsApp Business catalog with 10 clear product photos
3. Google My Business — free local listing
 
**Day 3-4 — Marketing:**
1. One Reel daily: "How I make {biz} from Akola"
2. Join local Facebook groups: "Akola me {biz} — Same Day Delivery"
3. Physically visit 10 local shops with a sample product
 
**Day 5-7 — First Orders:**
Offer: "First 10 customers — 20% OFF + Free Delivery in Akola"
Post 3 WhatsApp status updates daily showing orders/work-in-progress
Referral push: "Refer 1 friend = ₹100 cashback on their first order"
 
**SCALE TO ₹1 LAKH/MONTH:**
Month 2: Hire a delivery helper (~₹8,000/month)
Month 3: Launch a Shopify/simple website (~₹1,999/month)
Month 4: Run Instagram Ads at ₹100/day, targeting 10 orders/day from ads alone
 
**EARN WITH THIS BOT TOO:** /invite
3 Friends = +5 Uses | 10 Friends = 1 Month Premium FREE | 100 Friends = Lifetime Premium + Cash Reward
 
**BUDGET-BASED ALTERNATIVE IDEAS (If {biz.title()} Isn't the Right Fit):**
 
**Under ₹5,000 Budget (Zero-Inventory Models):**
• Reselling — take orders via Instagram, source from local wholesale market, no stock held
• Service-based (tutoring, design, social media management) — sell your skill, not a product
• Dropshipping local — partner with a local manufacturer, you handle only marketing and orders
 
**₹5,000-15,000 Budget (Small Inventory Models):**
• {biz.title()} exactly as detailed above — small stock, home-based
• Homemade food/snacks delivery — start with 5-10 items, WhatsApp + Instagram orders only
• Printed merchandise (t-shirts, mugs, frames) — print-on-demand keeps stock risk low
 
**₹15,000+ Budget (Scale-Ready Models):**
• {biz.title()} with a small physical counter/kiosk in a high-footfall Akola location
• Multi-product store combining {biz} with 2-3 complementary products
• Franchise/dealership of an established brand if capital allows
 
**CHOOSING BETWEEN THEM:** Pick the one where you already have some skill or interest — a business you can talk about confidently for 5 minutes without a script converts customers far better than one you're not genuinely into.
 
Next: `resume for {biz} staff`, `caption for {biz}`, or `roadmap for sales job`
"""
 
 
# ==================== TOOL: LINKEDIN "ABOUT" SECTION ====================
 
def tool_linkedin(p):
    job = p.replace("linkedin for", "").replace("linkedin about", "").replace("linkedin", "").strip().title() or "Sales Executive"
    category = detect_job_category(p)
    data = JOB_KEYWORDS[category]
    return f"""🔗 **LINKEDIN "ABOUT" SECTION - {job} - Recruiter-Optimized**
 
**HEADLINE (Under Your Name — Most Viewed Line on LinkedIn):**
"{job} | {data['keywords'].split(',')[0].strip()} | Open to Opportunities in Akola/Pune/Nagpur"
 
**ABOUT SECTION (Copy-Paste, Edit Brackets):**
 
I'm a {data['summary_line']}, currently based in Akola, Maharashtra.
 
🔹 What I bring:
• {data['experience_bullets'][0]}
• {data['experience_bullets'][1]}
 
🔹 Tools & Skills: {data['skills']}
 
🔹 Languages: Hindi (Native), Marathi (Native), English (Professional)
 
I'm actively looking for {job} opportunities where I can contribute from Day 1 and grow long-term. Open to relocation within Maharashtra.
 
📩 Feel free to connect or message me directly — always happy to talk about {category if category != 'default' else 'career'} opportunities!
 
**PROFILE CHECKLIST FOR MAX VISIBILITY:**
• Add "Open to Work" banner on profile photo (set visible to recruiters only if currently employed)
• Post 1x/week about a lesson learned in {category if category != 'default' else 'your field'} — this triples profile views
• Connect with 10 recruiters/week in your target city with a short personalized note
• Keep your Featured section updated with your resume PDF
 
Next: `resume for {job}` to match this LinkedIn profile with your resume.
"""
 
 
# ==================== TOOL: CAREER TIPS (Quick Reference) ====================
 
def tool_tips(p):
    return """💡 **10 CAREER TIPS THAT ACTUALLY WORK (2026 Edition)**
 
1. Apply on Naukri/Indeed/LinkedIn between 9:30-11 AM — HR opens applications fastest in this window.
2. Always attach a cover letter — resume + cover letter combo gets ~3x more callbacks than resume alone.
3. Never write "Responsible for..." on a resume — write what you achieved with a number instead.
4. Follow up once, 2-3 days after applying — don't spam, don't disappear.
5. In interviews, always ask 2-3 smart questions back — it signals genuine interest.
6. Never accept the first salary number offered — pause, then negotiate using market data.
7. Keep your LinkedIn "Open to Work" updated — recruiters search this actively every week.
8. Build one small project/portfolio piece even as a fresher — it beats a blank experience section.
9. Track every application in a simple Excel sheet (company, date, status) — most freshers lose track and miss follow-ups.
10. Learn one new tool every month relevant to your field (Excel formulas, CRM, Canva, basic SQL) — small compounding skills add up fast.
 
Use `resume for [job]`, `interview for [job]`, or `salary negotiation for [job]` to apply these tips directly.
"""
 
 
# ==================== TOOL: SALES CAREER ROADMAP (0 to ₹50k in 1 Year) ====================
 
def _roadmap_data(p):
    return f"""🗺️ **DATA CAREER ROADMAP - ₹0 to ₹40,000/Month in 12 Months**
For a fresher starting as a Data Entry Operator, aiming for Data Analyst.
 
**MONTH 1-2 — FOUNDATION (Target Salary: ₹9,000-12,000)**
• Join as Data Entry Operator or MIS Trainee at a local company or BPO
• Master Excel basics: formulas, sorting, filtering, conditional formatting
• Build typing speed to 40+ WPM with high accuracy
• Learn to spot and fix data errors (duplicates, blank fields, wrong formats)
 
**MONTH 3-5 — LEVEL UP EXCEL (Target Salary: ₹12,000-16,000)**
• Learn VLOOKUP, Pivot Tables, and basic dashboards in Excel
• Start building small automated reports for your team/manager
• Learn Google Sheets equivalents so you're tool-flexible
• Take a free/paid Advanced Excel course (many available on YouTube/Coursera)
 
**MONTH 6-8 — ADD SQL & POWER BI (Target Salary: ₹16,000-22,000)**
• Learn basic SQL: SELECT, WHERE, JOIN, GROUP BY — enough to query real data
• Learn Power BI or Google Data Studio basics for visual dashboards
• Ask to take ownership of one full report/dashboard end-to-end at work
• Add "SQL Basics" and "Power BI" to your resume/LinkedIn once comfortable
 
**MONTH 9-12 — BECOME THE DATA ANALYST (Target Salary: ₹22,000-40,000)**
• Apply for Junior Data Analyst roles using your dashboard/report portfolio as proof
• Build 1-2 personal projects (e.g. analyze a public dataset) to show on LinkedIn/resume
• Negotiate your move from Data Entry to Analyst title using the `salary negotiation` tool
• By month 12, aim for roles combining SQL + Excel + Power BI at ₹25k-40k in Tier-2/Tier-1 cities
 
Next: `salary negotiation for data analyst` or `resume for data analyst`
"""
 
 
def _roadmap_marketing(p):
    return f"""🗺️ **DIGITAL MARKETING ROADMAP - ₹0 to ₹45,000/Month in 12 Months**
For a fresher starting as a Social Media Executive, aiming for Digital Marketer.
 
**MONTH 1-2 — FOUNDATION (Target Salary: ₹10,000-14,000)**
• Join as Social Media/Content Executive at a local business or agency
• Learn Canva for creatives and basic content calendar planning
• Study how 5 successful pages in your niche post (timing, hooks, captions)
• Start managing at least one real page's daily posting
 
**MONTH 3-5 — GROW A REAL PAGE (Target Salary: ₹14,000-18,000)**
• Take ownership of growing one page's followers/engagement with measurable numbers
• Learn Instagram/Facebook Ads Manager basics — run a small ₹500 test campaign
• Learn basic copywriting formulas (hook-problem-solution-CTA)
• Document growth numbers monthly (followers, reach, engagement rate)
 
**MONTH 6-8 — PAID ADS & ANALYTICS (Target Salary: ₹18,000-25,000)**
• Get comfortable running and optimizing paid campaigns with a real budget
• Learn Google Analytics basics to track website/campaign performance
• Learn basic SEO (keywords, meta descriptions) if the role touches a website/blog
• Add measurable ROAS/growth numbers to your resume and LinkedIn
 
**MONTH 9-12 — BECOME THE DIGITAL MARKETER (Target Salary: ₹25,000-45,000)**
• Apply for Digital Marketing Executive/Associate roles with your campaign results as proof
• Build a mini portfolio: 3-4 campaigns with before/after numbers
• Negotiate your title and salary jump using the `salary negotiation` tool
• By month 12, target roles combining content + paid ads + basic analytics at ₹25k-45k
 
Next: `salary negotiation for digital marketer` or `resume for digital marketer`
"""
 
 
def _roadmap_generic(p, category):
    label = category.replace("_", " ").title() if category != "default" else "Your Field"
    return f"""🗺️ **{label.upper()} CAREER ROADMAP - Fresher to Senior in 12 Months**
 
**MONTH 1-3 — FOUNDATION**
• Join at entry level and learn the core tools/processes used daily in {label}
• Build a habit of documenting your work and results from Day 1
• Identify the 2-3 metrics that define success in this role and start tracking them
 
**MONTH 4-6 — CONSISTENCY**
• Consistently hit or beat expectations on your tracked metrics
• Take on one additional responsibility beyond your job description
• Start building relationships with seniors/managers who can vouch for you later
 
**MONTH 7-9 — VISIBILITY**
• Ask for a formal review using your documented results as evidence
• Start applying selectively to slightly better roles to benchmark your market value
• Add every measurable result to your resume and LinkedIn as it happens, not later
 
**MONTH 10-12 — BREAKTHROUGH**
• Negotiate a promotion or a better external offer using 12 months of tracked proof
• Use the `salary negotiation` tool before accepting any new number
• Set your next 12-month goal immediately after this milestone — momentum matters
 
Next: `resume for {label}` or `salary negotiation for {label}`
"""
 
 
def tool_roadmap(p):
    category = detect_job_category(p)
    if category == "data":
        return _roadmap_data(p)
    if category == "marketing":
        return _roadmap_marketing(p)
    if category not in ("sales", "default"):
        return _roadmap_generic(p, category)
    return f"""🗺️ **SALES CAREER ROADMAP - ₹0 to ₹50,000/Month in 12 Months**
Built for a fresher starting in Akola/Tier-2 city sales role.
 
**MONTH 1-2 — FOUNDATION (Target Salary: ₹10,000-13,000)**
• Join as Trainee/Junior Sales Executive at a local company, distributor, or telecom/insurance/FMCG dealer
• Learn the product catalog cold — you should be able to explain it in 30 seconds without notes
• Shadow 2-3 senior sales reps on client visits or calls to learn objection handling
• Start a personal notebook of every objection you hear and how it was answered
• Goal: hit at least 70% of assigned target by end of Month 2
 
**MONTH 3-4 — MOMENTUM (Target Salary: ₹13,000-16,000 + Incentive)**
• Start hitting 100% of monthly target consistently
• Ask manager for a bigger territory or additional product line to sell
• Build a personal client list of 30+ contacts you can call directly
• Learn basic CRM (Zoho/Excel tracker) to log every lead and follow-up date
• Negotiate your first incentive/commission structure — most companies pay 1-3% over target
 
**MONTH 5-6 — SPECIALIZE (Target Salary: ₹16,000-20,000 + Incentive)**
• Pick a niche you're strongest at (B2B, field sales, telesales, retail) and go deep
• Start closing bigger-ticket deals, not just volume — this signals promotion-readiness
• Request a formal appraisal discussion using your Month 1-6 target achievement data
• Start applying to slightly bigger companies in Nagpur/Pune/Mumbai for a lateral jump if current growth is capped
 
**MONTH 7-8 — JUMP OR GROW (Target Salary: ₹20,000-28,000)**
• If internal growth is slow: switch companies using your 6-month track record — a documented 100%+ target achievement history is your biggest leverage
• If staying: ask for Team Lead / Senior Executive title with 2-3 juniors under you
• Start learning basic sales management: forecasting, pipeline reviews, team motivation
• Add "Team Handling" and "Sales Forecasting" to your resume/LinkedIn
 
**MONTH 9-10 — SCALE (Target Salary: ₹28,000-35,000)**
• Push for Assistant Sales Manager / Area Sales Executive title
• Own a full territory or product category end-to-end
• Start building a personal brand on LinkedIn — post about deals closed, lessons learned
• Network with 2-3 sales managers in bigger companies (Reliance, HDFC, Bajaj, Asian Paints dealer networks etc.)
 
**MONTH 11-12 — BREAKTHROUGH (Target Salary: ₹35,000-50,000)**
• Target Sales Manager / Regional Sales Executive roles at mid-size companies
• Use your full 1-year track record (targets hit, team handled, revenue generated) as the core pitch
• Negotiate salary using the `salary negotiation` tool — always negotiate, never accept the first offer
• At ₹50k/month in Year 1, you're already ahead of ~80% of sales freshers in Tier-2 cities
 
**KEY PRINCIPLE THROUGHOUT:** Every 2 months, document your numbers (targets hit %, revenue, clients added). This document is what gets you promoted internally AND hired externally at a higher salary.
 
**COMMON MISTAKES TO AVOID:**
• Staying in one company just for comfort even when growth has stopped
• Not tracking your own numbers — managers won't do this for you
• Accepting the first salary number offered without any negotiation
 
Next: `salary negotiation for sales manager` or `resume for sales manager`
"""
 
 
# ==================== TOOL: SALARY NEGOTIATION (3 Scripts + Akola 2026 Data) ====================
 
def tool_salary_negotiation(p):
    job = p.replace("salary negotiation for", "").replace("salary negotiation", "").replace("negotiation", "").strip().title() or "Sales Executive"
    category = detect_job_category(p)
 
    salary_table = {
        "sales": "Sales Executive (0-1 yr): ₹10,000-15,000 | (1-3 yr): ₹15,000-22,000 | Team Lead (3-5 yr): ₹22,000-32,000",
        "data": "Data Entry Operator (0-1 yr): ₹9,000-13,000 | Data Analyst (1-3 yr): ₹18,000-28,000 | Senior Analyst (3-5 yr): ₹28,000-40,000",
        "marketing": "Social Media Executive (0-1 yr): ₹10,000-16,000 | Digital Marketer (1-3 yr): ₹18,000-28,000 | Marketing Manager (3-5 yr): ₹30,000-45,000",
        "default": "Entry-Level Executive (0-1 yr): ₹9,000-14,000 | Mid-Level (1-3 yr): ₹15,000-24,000 | Senior (3-5 yr): ₹25,000-38,000"
    }
 
    return f"""💰 **SALARY NEGOTIATION TOOLKIT - {job}**
📍 **AKOLA SALARY RESEARCH 2026 ({category.upper()} ROLES):**
{salary_table[category]}
 
Note: Ranges are typical for Akola/Vidarbha-region companies; Pune/Mumbai/Nagpur roles usually run 20-40% higher for the same experience level.
 
---
 
**SCRIPT 1 — WHEN ASKED "What's your expected salary?" (Opening Move):**
"Thank you for asking. Before I give a specific number, could you share the budgeted range for this {job} role? That way I can give you a number that's fair for both sides based on the responsibilities involved."
→ Why it works: Whoever gives the first number usually loses the negotiation. This flips it back to the employer first.
 
**SCRIPT 2 — WHEN THEY GIVE A LOWER OFFER THAN EXPECTED (Counter-Offer):**
"I appreciate the offer. Based on my research, {job} roles with similar responsibilities in this market are typically compensated in the ₹[X] to ₹[Y] range, and I bring [specific skill/achievement] that adds extra value. Would there be flexibility to move closer to ₹[Y]?"
→ Why it works: You're not rejecting the offer — you're anchoring to market data + your specific value, which is far harder to argue against than a feeling.
 
**SCRIPT 3 — FINAL PUSH WHEN THEY WON'T MOVE ON BASE SALARY:**
"I understand the base salary may be fixed at this stage. Would it be possible to revisit my compensation after a 3-month performance review, or could we discuss additional incentives — performance bonus, travel allowance, or an early appraisal cycle — to bridge the gap?"
→ Why it works: If base salary truly can't move, this opens a second door (bonus/allowance/timeline) instead of a flat no.
 
**GENERAL RULES:**
1. Never accept the first number offered — always pause and say "let me think about it" even if it's good
2. Always negotiate on TOTAL compensation (base + incentive + allowance), not just the base number
3. Use silence as a tool — after stating your counter-number, stop talking and let them respond first
4. Get the final number in writing (offer letter) before resigning from any current role
 
**IF YOU'RE A FRESHER (0 Experience) — Adjust Your Approach:**
"I understand entry-level compensation is usually fixed within a band. I'm confident I can prove my value quickly — would it be possible to build in a review at 3 months with a defined increment if I hit my targets?"
→ Freshers have less leverage on the base number, so negotiate the REVIEW TIMELINE instead of the number itself.
 
**IF YOU'RE EXPERIENCED (2+ Years) — Adjust Your Approach:**
"Given my track record of [specific achievement/number] in my current role, I believe {job} at this level should be compensated closer to ₹[Y]. I'm open to discussing how we bridge that gap."
→ Experienced candidates should always lead with a specific, quantified achievement before naming any number.
 
Next: `roadmap for sales job` or `interview for {job}`
"""
 
 
# ==================== TOOL: YOUTUBE SCRIPT (8-Minute Viral Hook Structure) ====================
 
def tool_youtube_script(p):
    topic = p.replace("youtube script for", "").replace("youtube script", "").replace("script for", "").strip() or "how I got my first job"
 
    return f"""🎬 **YOUTUBE SCRIPT - "{topic.title()}" - 8-Minute Viral Structure**
 
**[0:00 - 0:15] — THE HOOK (Make-or-Break)**
"If you're struggling with {topic} right now, stop scrolling — in the next 8 minutes I'm going to show you exactly what worked for me, step by step, no fluff."
→ Rule: The hook must promise a specific, believable outcome within the first 3 seconds or viewers swipe away.
 
**[0:15 - 0:45] — QUICK CREDIBILITY + PROMISE**
"I'm [Your Name], and [1-line credibility — e.g. 'I went from 0 to my first sales job in Akola in 3 weeks using this exact method']. By the end of this video, you'll know the 3 things that actually moved the needle for me."
 
**[0:45 - 1:30] — SET UP THE PROBLEM (Relatability)**
Describe the exact frustration your viewer feels about {topic} right now — be specific, not generic. Use "you" language: "You've probably already tried X and Y, and it hasn't worked, right?"
 
**[1:30 - 5:30] — THE 3 MAIN POINTS (Body — 80 seconds each)**
Point 1 (1:30-2:50): The first actionable step, with a real example or story from your own experience related to {topic}.
Point 2 (2:50-4:10): The second step — ideally the one most people get wrong or skip entirely.
Point 3 (4:10-5:30): The advanced/insider step that makes your video stand out from every other video on this topic.
→ Rule: Every point needs ONE concrete example or number — "I did X and got Y result" beats generic advice every time.
 
**[5:30 - 6:30] — MID-ROLL RE-HOOK (Retention Save)**
"But here's the part almost nobody talks about about {topic}..." — introduce a bonus insight here. This re-hook is critical because YouTube's algorithm rewards videos where viewers keep watching past the 60% mark.
 
**[6:30 - 7:30] — RECAP + SOFT SELL**
Quickly recap the 3 points in one sentence each. If you have a product/service/channel to promote, this is the natural spot — keep it under 20 seconds, don't oversell.
 
**[7:30 - 8:00] — STRONG CTA + OUTRO**
"If this helped, subscribe — I post a new video like this every week on {topic} and related topics. Drop a comment telling me which point you're trying first, I read every single one."
 
**PRODUCTION TIPS:**
• Keep cuts every 3-4 seconds in the first minute — no dead air
• Add on-screen text for every key number/point (viewers watch muted often)
• Thumbnail + Title should match the Hook exactly — mismatched promises kill watch time
 
**60-SECOND SHORTS VERSION (Same Topic, Compressed):**
[0:00-0:03] Hook — same line as above, but delivered faster and punchier
[0:03-0:10] State the problem in one sentence
[0:10-0:45] Deliver ONLY your single best point (Point 3 from the long-form script works best — it's the most unique)
[0:45-0:55] One-line recap + "Follow for more on {topic}"
[0:55-0:60] Text overlay reinforcing the main takeaway as the video loops
 
Next: `thumbnail for {topic}` for a matching high-CTR thumbnail concept.
"""
 
 
# ==================== TOOL: THUMBNAIL (MrBeast-Style 10%+ CTR Formula) ====================
 
def tool_thumbnail(p):
    topic = p.replace("thumbnail for", "").replace("thumbnail", "").strip() or "my new video"
 
    text_ideas = [
        f"I TRIED {topic.upper()}",
        f"{topic.upper()} GONE WRONG",
        f"0 TO {topic.upper()} IN 7 DAYS"
    ]
 
    return f"""🖼️ **THUMBNAIL FORMULA - "{topic.title()}" - MrBeast-Style 10%+ CTR**
 
**THE 4-ELEMENT RULE (Never Break This):**
1. ONE clear subject (face or object) — never more than 1-2 focal points
2. HIGH CONTRAST colors — bright subject against a darker/simple background (yellow/red/blue pop hardest)
3. BIG BOLD TEXT — max 3-5 words, readable even at thumbnail size on mobile
4. EMOTION or CURIOSITY GAP — a shocked/excited face, or a visual that raises a question the video answers
 
**3 TEXT OPTIONS FOR THIS VIDEO (Pick the strongest):**
1. "{text_ideas[0]}"
2. "{text_ideas[1]}"
3. "{text_ideas[2]}"
 
**LAYOUT BLUEPRINT:**
• Left 60% of frame: Subject (face with exaggerated expression, or the key object of the video)
• Right 40% of frame: Bold text in a contrasting color (white text with black outline, or yellow with red outline)
• Add a red circle, arrow, or "before/after" split if the video shows transformation or comparison
• Keep background simple/blurred so the subject and text don't compete with clutter
 
**COLOR COMBINATIONS THAT WORK BEST:**
• Yellow text + Black outline on a blue/dark background
• Red circle/arrow highlighting the key detail
• Bright saturated colors — desaturated/dull thumbnails get scrolled past
 
**MRBEAST FORMULA SUMMARY:**
Exaggerated real human emotion + oversized numbers/stakes ("$1,000,000", "Last To Leave") + high contrast colors + zero unnecessary detail = the viewer understands the entire video's promise in under 1 second.
 
**HOW TO TEST:** Shrink your thumbnail to the size of a postage stamp (as it appears on mobile) — if you can't tell what it's about in 1 second at that size, redesign it.
 
**A/B TESTING TIP:** If your platform allows it (YouTube Studio's thumbnail test feature), upload 2 versions of this thumbnail with different text options above and let 1,000 impressions decide which wins before committing fully — never guess when data is available for free.
 
**TOOLS:** Canva (free templates) or Photoshop for the face/text combo described above.
 
Next: `youtube script for {topic}` if you haven't built the matching script yet.
"""
 
 
# ==================== AI ROUTER ====================
 
def ai_router(text):
    t = text.lower().strip()
    if any(x in t for x in ["resume", "cv", "biodata"]):
        return tool_resume(text)
    if "cover" in t:
        return tool_cover(text)
    if "interview" in t:
        return tool_interview(text)
    if "email" in t or "mail" in t:
        return tool_email(text)
    if any(x in t for x in ["caption", "hashtag", "insta", "reel"]) and "youtube" not in t:
        return tool_caption(text)
    if any(x in t for x in ["image", "photo", "logo", "prompt", "leonardo", "midjourney", "bing"]):
        return tool_image(text)
    if "roadmap" in t:
        return tool_roadmap(text)
    if "salary" in t or "negotiat" in t:
        return tool_salary_negotiation(text)
    if "youtube script" in t or ("script" in t and "youtube" in t):
        return tool_youtube_script(text)
    if "thumbnail" in t:
        return tool_thumbnail(text)
    if "linkedin" in t:
        return tool_linkedin(text)
    if t in ["tips", "/tips", "career tips"]:
        return tool_tips(text)
    if any(x in t for x in ["business", "idea", "startup", "earn", "paise kamana"]):
        return tool_business(text)
    if t in ["hi", "hello", "hii", "hey", "hiiii", "ho", "start", "/start", "namaste", "/start@global_ai_assistant_bot"]:
        return None
    if len(t.split()) < 4:
        return tool_business(text)
    return tool_resume(text)
 
 
# ==================== HANDLERS: START ====================
 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Player"
    user = get_user(uid, name)
    save_users(users)
 
    if context.args and context.args[0] != str(uid) and context.args[0] in users:
        ref = context.args[0]
        try:
            ref_user = users[ref]
            ref_user["invited"] = ref_user.get("invited", 0) + 1
            claimed = ref_user.get("invite_tiers_claimed", [])
            invited_count = ref_user["invited"]
 
            if invited_count in INVITE_TIERS and invited_count not in claimed:
                claimed.append(invited_count)
                ref_user["invite_tiers_claimed"] = claimed
                if invited_count == 3:
                    ref_user["uses"] = max(0, ref_user.get("uses", 0) - 5)
                    add_xp(ref_user, 20)
                    await context.bot.send_message(chat_id=int(ref), text="🎉 3 Friends Joined! +5 Free Uses & +20 XP!")
                elif invited_count == 10:
                    ref_user["premium"] = True
                    ref_user["premium_till"] = (datetime.now() + timedelta(days=30)).isoformat()
                    await context.bot.send_message(chat_id=int(ref), text="🔥 10 Friends = 1 MONTH PREMIUM FREE! 🔥")
                elif invited_count == 25:
                    ref_user["uses"] = max(0, ref_user.get("uses", 0) - 10)
                    add_xp(ref_user, 100)
                    await context.bot.send_message(chat_id=int(ref), text="🚀 25 Friends! +10 Uses & +100 XP!")
                elif invited_count == 50:
                    ref_user["premium"] = True
                    ref_user["premium_till"] = (datetime.now() + timedelta(days=90)).isoformat()
                    await context.bot.send_message(chat_id=int(ref), text="💎 50 Friends = 3 MONTHS PREMIUM FREE + ₹500 Reward Eligible! DM Admin to claim cash.")
                elif invited_count == 100:
                    ref_user["premium"] = True
                    ref_user["premium_till"] = (datetime.now() + timedelta(days=3650)).isoformat()
                    await context.bot.send_message(chat_id=int(ref), text="👑 100 Friends = LIFETIME PREMIUM + ₹1500 Reward! You're a LEGEND. DM Admin to claim cash.")
            save_users(users)
        except Exception as e:
            logger.error(f"Referral error: {e}")
 
    left = FREE_LIMIT - user["uses"] if not user["premium"] else "♾️ UNLIMITED"
    total = len(users)
    level = get_level(user.get("xp", 0))
    rank = get_rank(level)
 
    welcome = f"""🌍 **GLOBAL AI - ULTRA BEST | {total}+ Users Worldwide Trust**
 
**Namaste {name}!** 🙏 Level {level} {rank}
 
All-in-One Career + Business + Content Bot!
 
**🔥 BALANCE: {left} Free | Premium: {PREMIUM_TIER1}⭐ = Unlimited**
 
**👇 SELECT — 1 CLICK ME KAAM:**
 
💼 **NAUKRI (Most Loved ❤️):**
📄 Resume (98 ATS) • 💌 Cover Letter • 🎯 Interview Q&A
📧 HR Email • 🗺️ Sales Roadmap • 💰 Salary Negotiation
 
📱 **BUSINESS / CONTENT:**
📸 Viral Caption • 🎨 Image Prompt 8K • 💡 Business ₹1L/mo
🎬 YouTube Script • 🖼️ Thumbnail CTR
 
🎮 **GAME & REWARDS:**
🔥 Streak (/streak in stats) • 🎁 Daily Bonus (/bonus) • 🧠 Daily Quiz (/quiz) • 🏆 Leaderboard (/leaderboard)
 
**💡 LIKHO JAISE:**
`resume for 12th pass sales job in Akola`
`roadmap for sales job`
`salary negotiation for data analyst`
`youtube script for how I got my first job`
 
**💰 PAISA KAMAO:** /invite - Share = Free Premium + Cash!
 
👇 **BUTTON DABAO YA DIRECT LIKHO:**
"""
 
    kb = [
        [InlineKeyboardButton("📄 ATS Resume 98", callback_data="resume"), InlineKeyboardButton("🎯 Interview Q&A", callback_data="interview")],
        [InlineKeyboardButton("📧 HR Email", callback_data="email"), InlineKeyboardButton("💌 Cover Letter", callback_data="cover")],
        [InlineKeyboardButton("🗺️ Sales Roadmap", callback_data="roadmap"), InlineKeyboardButton("💰 Salary Negotiation", callback_data="salary")],
        [InlineKeyboardButton("📸 Viral Caption", callback_data="caption"), InlineKeyboardButton("🎨 Image Prompt 8K", callback_data="image")],
        [InlineKeyboardButton("🎬 YouTube Script", callback_data="youtube"), InlineKeyboardButton("🖼️ Thumbnail CTR", callback_data="thumbnail")],
        [InlineKeyboardButton("💡 Business ₹1L", callback_data="business"), InlineKeyboardButton("🔗 LinkedIn About", callback_data="linkedin")],
        [InlineKeyboardButton("💡 Career Tips", callback_data="tips"), InlineKeyboardButton("🔗 Invite = Earn", callback_data="invite")],
        [InlineKeyboardButton("📈 My Invite Tiers", callback_data="myinvites"), InlineKeyboardButton("🏅 Rank Table", callback_data="ranks")],
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="bonus"), InlineKeyboardButton("🧠 Daily Quiz", callback_data="quiz")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"), InlineKeyboardButton("⭐ Premium", callback_data="premium")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats"), InlineKeyboardButton("🆘 Help", callback_data="help")]
    ]
    await safe_reply(update.message, welcome, InlineKeyboardMarkup(kb))
 
 
# ==================== HANDLERS: MAIN TOOL DISPATCH ====================
 
async def handle_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Player"
 
    if is_banned(uid):
        await safe_reply(update.message, "🚫 Aapka account banned hai. Contact admin agar galti se hua hai.")
        return
 
    if is_rate_limited(uid):
        await update.message.reply_chat_action("typing")
        return
 
    user = get_user(uid, name)
    text = (update.message.text or "").strip()
 
    lower = text.lower()
    if lower in ["/stats", "stats"]:
        await stats(update, context)
        return
    if lower in ["/help", "help"]:
        await help_cmd(update, context)
        return
 
    if not user["premium"] and user["uses"] >= FREE_LIMIT:
        kb = [
            [InlineKeyboardButton(f"⭐ Buy Premium {PREMIUM_TIER1}⭐ Unlimited", callback_data="premium")],
            [InlineKeyboardButton("🔗 Invite 3 Friends = +5 Uses FREE", callback_data="invite")],
            [InlineKeyboardButton("🎁 Claim Daily Bonus", callback_data="bonus")]
        ]
        await safe_reply(
            update.message,
            f"❌ **FREE LIMIT KHATAM! {FREE_LIMIT} uses done**\n\n"
            f"✅ FREE SOLUTION: 3 Friends Invite = +5 Uses (/invite)\n"
            f"✅ Daily Bonus + Streak se bhi free uses milte hain (/bonus)\n"
            f"✅ BEST: Premium {PREMIUM_TIER1}⭐ = **UNLIMITED** + all tools\n\n"
            f"💡 10 Friends = 1 Month Premium FREE!",
            InlineKeyboardMarkup(kb)
        )
        return
 
    await update.message.reply_chat_action("typing")
    result = ai_router(text)
    if result is None:
        await start(update, context)
        return
 
    user["uses"] += 1
    leveled_up = add_xp(user, 5)
    streak_msg = update_streak_and_get_message(user)
    save_users(users)
 
    rem = FREE_LIMIT - user["uses"] if not user["premium"] else "♾️ Unlimited"
    level = get_level(user.get("xp", 0))
    rank = get_rank(level)
 
    extra_lines = []
    if streak_msg:
        extra_lines.append(streak_msg)
    if leveled_up:
        extra_lines.append(f"⬆️ Level Up! Now Level {level} {rank}")
    extra_block = ("\n" + "\n".join(extra_lines)) if extra_lines else ""
 
    footer = (
        f"\n\n---\n💳 **Balance:** {rem} | Lvl {level} {rank}{extra_block}\n"
        f"⭐ /premium | 🔗 /invite | 🧠 /quiz | 🏆 /leaderboard | 🏠 /start\n"
        f"💡 Tip: Detail likho for best result: `resume for 12th pass sales job in Akola with 1 yr exp`"
    )
 
    kb = [
        [InlineKeyboardButton("🔄 Another", callback_data="more"), InlineKeyboardButton("⭐ Premium", callback_data="premium")],
        [InlineKeyboardButton("📤 Share", callback_data="share"), InlineKeyboardButton("🏠 Menu", callback_data="main")]
    ]
 
    full = result + footer
    if len(full) > 4000:
        await safe_reply(update.message, result[:4000])
        await safe_reply(update.message, footer, InlineKeyboardMarkup(kb))
    else:
        await safe_reply(update.message, full, InlineKeyboardMarkup(kb))
 
 
# ==================== HANDLERS: BUTTON CALLBACKS ====================
 
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    uid = update.effective_user.id
 
    if is_banned(uid):
        await q.message.reply_text("🚫 Aapka account banned hai.")
        return
 
    if d.startswith("quizans_"):
        await handle_quiz_answer(update, context, d)
        return
 
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
    elif d == "myinvites":
        await myinvites_cmd(update, context)
    elif d == "ranks":
        await ranks_cmd(update, context)
    elif d in ["main", "start"]:
        await q.message.reply_text("🏠 /start likho")
    elif d == "more":
        await q.message.reply_text("🔄 Topic likho:\nEx: `resume for 12th pass sales job in Akola`", parse_mode="Markdown")
    elif d == "share":
        bot = (await context.bot.get_me()).username
        await q.message.reply_text(f"📤 Share: https://t.me/{bot} - Best AI Career Bot Free!")
    elif d == "resume_sample":
        await safe_reply(q.message, tool_resume("sales job")[:4000])
    else:
        mp = {
            "resume": "📄 Resume:\n`resume for 12th pass sales job in Akola`",
            "email": "📧 Email:\n`email for sales job`",
            "caption": "📸 Caption:\n`caption for my shop`",
            "image": "🎨 Image:\n`image prompt for shop logo`",
            "business": "💡 Business:\n`business idea for tiffin service`",
            "interview": "🎯 Interview:\n`interview for sales job`",
            "cover": "💌 Cover Letter:\n`cover letter for sales job`",
            "roadmap": "🗺️ Roadmap:\n`roadmap for sales job`",
            "salary": "💰 Salary Negotiation:\n`salary negotiation for sales executive`",
            "youtube": "🎬 YouTube Script:\n`youtube script for how I got my first job`",
            "thumbnail": "🖼️ Thumbnail:\n`thumbnail for my new video`",
            "linkedin": "🔗 LinkedIn About:\n`linkedin for sales executive`",
            "tips": "💡 Career Tips:\n`/tips`"
        }
        await q.message.reply_text(mp.get(d, f"✅ {d} ke liye topic bhejo"), parse_mode="Markdown")
 
 
# ==================== COMMAND SHORTCUTS ====================
 
async def cmd_resume(u, c):
    await safe_reply(u.message, "📄 `resume for 12th pass sales job in Akola`")
 
 
async def cmd_email(u, c):
    await safe_reply(u.message, "📧 `email for job application`")
 
 
async def cmd_caption(u, c):
    await safe_reply(u.message, "📸 `caption for my shop`")
 
 
async def cmd_image(u, c):
    await safe_reply(u.message, "🎨 `image prompt for logo`")
 
 
async def cmd_idea(u, c):
    await safe_reply(u.message, "💡 `business idea for t-shirt`")
 
 
async def cmd_interview(u, c):
    await safe_reply(u.message, "🎯 `interview for sales job`")
 
 
async def cmd_cover(u, c):
    await safe_reply(u.message, "💌 `cover letter for sales job`")
 
 
async def cmd_roadmap(u, c):
    await safe_reply(u.message, "🗺️ `roadmap for sales job`")
 
 
async def cmd_salary(u, c):
    await safe_reply(u.message, "💰 `salary negotiation for sales executive`")
 
 
async def cmd_youtube(u, c):
    await safe_reply(u.message, "🎬 `youtube script for how I got my first job`")
 
 
async def cmd_thumbnail(u, c):
    await safe_reply(u.message, "🖼️ `thumbnail for my new video`")
 
 
async def cmd_linkedin(u, c):
    await safe_reply(u.message, "🔗 `linkedin for sales executive`")
 
 
async def cmd_tips(u, c):
    await safe_reply(u.message, tool_tips(""))
 
 
# ==================== COMMAND: DAILY BONUS ====================
 
async def bonus_cmd(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Player"
    if is_banned(uid):
        return
    if is_rate_limited(uid) and not update.callback_query:
        return
    user = get_user(uid, name)
    msg, claimed = claim_daily_bonus(user)
    save_users(users)
    target = update.callback_query.message if update.callback_query else update.message
    if claimed:
        await safe_reply(target, msg)
    else:
        await safe_reply(target, "⏳ Aaj ka Daily Bonus already claim kiya hai. Kal wapas aana!")
 
 
# ==================== COMMAND: DAILY QUIZ ====================
 
async def quiz_cmd(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Player"
    if is_banned(uid):
        return
    user = get_user(uid, name)
    target = update.callback_query.message if update.callback_query else update.message
    q = get_quiz_question(user)
    save_users(users)
    if q is None:
        await safe_reply(target, f"🧠 Aaj ka quiz already khel liya hai!\nScore: {user.get('quiz_score',0)} XP | Correct: {user.get('quiz_correct',0)}/{user.get('quiz_attempted',0)}\nKal wapas aana!")
        return
    kb = []
    for i, opt in enumerate(q["options"]):
        kb.append([InlineKeyboardButton(f"{chr(65+i)}. {opt}", callback_data=f"quizans_{q['id']}_{i}")])
    await safe_reply(target, f"🧠 **DAILY QUIZ**\n\n{q['question']}", InlineKeyboardMarkup(kb))
 
 
async def handle_quiz_answer(update, context, callback_data):
    q = update.callback_query
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Player"
    user = get_user(uid, name)
    try:
        _, qid_str, opt_str = callback_data.split("_")
        qid = int(qid_str)
        opt_idx = int(opt_str)
    except Exception:
        await q.message.reply_text("⚠️ Quiz error, dobara try karo /quiz")
        return
    result = check_quiz_answer(user, qid, opt_idx)
    save_users(users)
    if result is None:
        await q.message.reply_text("⏳ Ye quiz already answer ho chuka hai ya expire ho gaya. /quiz se naya try karo.")
        return
    if result["correct"]:
        txt = f"✅ **Correct!** +10 XP\n\n{result['explain']}"
    else:
        txt = f"❌ **Galat Jawab.** Correct answer tha: {result['correct_option']}\n\n{result['explain']}"
    await safe_reply(q.message, txt)
 
 
# ==================== COMMAND: LEADERBOARD ====================
 
async def leaderboard_cmd(update, context):
    target = update.callback_query.message if update.callback_query else update.message
    txt = build_leaderboard_text()
    await safe_reply(target, txt)
 
 
# ==================== PREMIUM SYSTEM (3 TIERS: 49 / 99 / 199 STARS) ====================
 
async def premium(update, context):
    kb = [
        [InlineKeyboardButton(f"⭐ {PREMIUM_TIER1} Stars - 30 Days Unlimited", callback_data="buy_49")],
        [InlineKeyboardButton(f"🔥 {PREMIUM_TIER2} Stars - 90 Days + Priority", callback_data="buy_99")],
        [InlineKeyboardButton(f"👑 {PREMIUM_TIER3} Stars - 365 Days + All Perks", callback_data="buy_199")],
        [InlineKeyboardButton("🔗 Invite = FREE Premium", callback_data="invite")]
    ]
    txt = f"""⭐ **PREMIUM - WORLD BEST VALUE**
 
**FREE:** {FREE_LIMIT} uses only
 
**⭐ TIER 1 — {PREMIUM_TIER1} Stars (~₹40) — 30 Days — MOST LOVED 🔥**
• ♾️ UNLIMITED Resume, Email, Caption, Cover, Interview
• 🗺️ Roadmap + 💰 Salary Negotiation unlocked
• 🎨 Premium image prompts
 
**🔥 TIER 2 — {PREMIUM_TIER2} Stars — 90 Days — PRIORITY**
• Everything in Tier 1
• 🎬 YouTube Script + 🖼️ Thumbnail tools unlocked
• Priority reply support
 
**👑 TIER 3 — {PREMIUM_TIER3} Stars — 365 Days — ALL PERKS**
• Everything in Tier 2 for a full year
• Free monthly resume review
• Early access to new tools before public release
 
**FREE PREMIUM ROUTE:**
3 Invites = +5 Uses | 10 Invites = 1 Month FREE | 30-Day Streak = 1 Week FREE
 
👇 Select a tier:
"""
    target = update.callback_query.message if update.callback_query else update.message
    await safe_reply(target, txt, InlineKeyboardMarkup(kb))
 
 
async def buy_premium(update, context, stars):
    chat_id = update.effective_chat.id if update.effective_chat else update.callback_query.message.chat.id
    days_map = {PREMIUM_TIER1: PREMIUM_TIER1_DAYS, PREMIUM_TIER2: PREMIUM_TIER2_DAYS, PREMIUM_TIER3: PREMIUM_TIER3_DAYS}
    days = days_map.get(stars, PREMIUM_TIER1_DAYS)
    try:
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=f"Premium {stars} Stars",
            description=f"Unlimited access for {days} days - Best value!",
            payload=f"premium_{stars}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(f"Premium {stars}", stars)]
        )
    except Exception as e:
        logger.error(f"Invoice error: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"Premium {stars} Stars ke liye /invite se FREE bhi le sakte ho, ya dobara /premium try karo.")
 
 
async def precheckout(u, c):
    await u.pre_checkout_query.answer(ok=True)
 
 
async def successful_payment(u, c):
    payload = u.message.successful_payment.invoice_payload if hasattr(u.message, 'successful_payment') else f"premium_{PREMIUM_TIER1}"
    if str(PREMIUM_TIER3) in str(payload):
        stars, days = PREMIUM_TIER3, PREMIUM_TIER3_DAYS
    elif str(PREMIUM_TIER2) in str(payload):
        stars, days = PREMIUM_TIER2, PREMIUM_TIER2_DAYS
    else:
        stars, days = PREMIUM_TIER1, PREMIUM_TIER1_DAYS
 
    uid = u.effective_user.id
    name = u.effective_user.first_name or "Player"
    user = get_user(uid, name)
    user["premium"] = True
    user["premium_till"] = (datetime.now() + timedelta(days=days)).isoformat()
    user["uses"] = 0
    add_xp(user, 30)
    save_users(users)
    await safe_reply(u.message, f"🎉 **Premium {days} Days Activated!**\nAb unlimited tools use karo! Type: `resume for dream job`\nEarn more: /invite")
 
 
# ==================== INVITE SYSTEM (TIERS 3 / 10 / 25 / 50 / 100) ====================
 
async def invite(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Player"
    user = get_user(uid, name)
    bot = (await context.bot.get_me()).username
    link = f"https://t.me/{bot}?start={uid}"
 
    txt = f"""🔗 **INVITE & EARN** 💰
 
**Your Link (Copy):**
`{link}`
 
**Your Stats:**
• Invites: {user.get('invited', 0)}
• Balance: {FREE_LIMIT - user['uses'] if not user['premium'] else 'Unlimited'}
• Premium: {'Yes ✅' if user['premium'] else 'No ❌'}
 
**INVITE REWARD TIERS:**
• 3 Friends = +5 Free Uses & +20 XP 🏅
• 10 Friends = 1 MONTH PREMIUM FREE 🔥
• 25 Friends = +10 Uses & +100 XP 🚀
• 50 Friends = 3 MONTHS PREMIUM + ₹500 Reward 💎
• 100 Friends = LIFETIME PREMIUM + ₹1500 Reward 👑
 
**VIRAL TRICK:**
WhatsApp Status: "2 min me Resume banaya, bilkul free! {link}"
Instagram Story: Screenshot + Link
College/Office group me bhejo!
 
👇 Share Now:
"""
    kb = [
        [InlineKeyboardButton("📤 WhatsApp Share", url=f"https://wa.me/?text=🔥 Best AI Career Bot Free! {link}")],
        [InlineKeyboardButton("📤 Telegram Share", url=f"https://t.me/share/url?url={link}&text=Best AI Career Bot Free!")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")]
    ]
    target = update.callback_query.message if update.callback_query else update.message
    await safe_reply(target, txt, InlineKeyboardMarkup(kb))
 
 
# ==================== STATS ====================
 
async def stats(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Player"
    user = get_user(uid, name)
    total = len(users)
    left = FREE_LIMIT - user["uses"] if not user["premium"] else "Unlimited"
    level = get_level(user.get("xp", 0))
    rank = get_rank(level)
    invited = user.get("invited", 0)
    streak = user.get("streak", 0)
 
    next_tier = next((t for t in INVITE_TIERS if t > invited), None)
    next_tier_text = f"{next_tier - invited} more invites to next reward tier ({next_tier})" if next_tier else "All invite tiers unlocked! 👑"
 
    txt = f"""📊 **Stats - {name}**
 
ID: {uid}
Joined: {user.get('joined', '').split('T')[0]}
Balance: {left}
Premium: {'Active ✅' if user['premium'] else 'Free'}
 
🎮 **Level {level} — {rank}**
XP: {user.get('xp', 0)}
🔥 Current Streak: {streak} day(s)
🧠 Quiz Score: {user.get('quiz_score', 0)} XP ({user.get('quiz_correct', 0)}/{user.get('quiz_attempted', 0)} correct)
 
🔗 Invited: {invited}
{next_tier_text}
Total Bot Users: {total}+
 
Commands: /invite | /premium | /quiz | /bonus | /leaderboard | /start
"""
    target = update.callback_query.message if update.callback_query else update.message
    await safe_reply(target, txt)
 
 
# ==================== HELP ====================
 
async def help_cmd(update, context):
    txt = """🆘 **HELP**
 
**Career Tools:**
Resume: `resume for 12th pass sales job in Akola`
Email: `email for job application`
Interview: `interview for sales job`
Cover Letter: `cover letter for sales job`
Roadmap: `roadmap for sales job`
Salary Negotiation: `salary negotiation for sales executive`
 
**Content/Business Tools:**
Caption: `caption for my shop`
Image: `image prompt for logo`
Business: `business idea for tiffin service`
YouTube Script: `youtube script for how I got my first job`
Thumbnail: `thumbnail for my new video`
LinkedIn About: `linkedin for sales executive`
Career Tips: /tips
 
**Game & Rewards:**
/bonus — Daily free bonus (once per day)
/quiz — Daily quiz question (once per day, +10 XP if correct)
/leaderboard — Top 10 users by XP + Invites
/myinvites — Your invite tier progress in detail
/ranks — Full Level 1-100 rank table
/streak — Check inside /stats
 
**Limit reached?** /invite = Free uses + Premium!
 
Bot not replying? Try /start again and wait 10 seconds.
 
Support: /start
"""
    target = update.callback_query.message if update.callback_query else update.message
    await safe_reply(target, txt)
 
 
# ==================== MY INVITES - DETAILED TIER PROGRESS ====================
 
async def myinvites_cmd(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Player"
    user = get_user(uid, name)
    invited = user.get("invited", 0)
    claimed = user.get("invite_tiers_claimed", [])
 
    tier_rewards = {
        3: "+5 Free Uses & +20 XP",
        10: "1 Month Premium FREE",
        25: "+10 Uses & +100 XP",
        50: "3 Months Premium + ₹500 Reward",
        100: "Lifetime Premium + ₹1500 Reward"
    }
 
    lines = [f"🔗 **MY INVITES — {invited} Total**\n"]
    for tier in INVITE_TIERS:
        status = "✅ Claimed" if tier in claimed else ("🔓 Unlocked, not yet processed" if invited >= tier else f"🔒 Locked ({tier - invited} more needed)")
        lines.append(f"Tier {tier}: {tier_rewards[tier]} — {status}")
 
    lines.append(f"\nShare your link with /invite to unlock the next tier!")
    target = update.callback_query.message if update.callback_query else update.message
    await safe_reply(target, "\n".join(lines))
 
 
# ==================== RANK TABLE ====================
 
async def ranks_cmd(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Player"
    user = get_user(uid, name)
    my_level = get_level(user.get("xp", 0))
    my_rank = get_rank(my_level)
 
    txt = f"""🏅 **RANK TABLE - Level 1 to 100**
 
Level 1-9 → 🥉 ROOKIE (0-449 XP)
Level 10-24 → 🥈 HUSTLER (450-1,199 XP)
Level 25-49 → 🥇 PRO (1,200-2,449 XP)
Level 50-74 → 🔥 EXPERT (2,450-3,699 XP)
Level 75-99 → 💎 MASTER (3,700-4,949 XP)
Level 100 → 👑 LEGEND (4,950+ XP)
 
**Formula:** Level = (Total XP ÷ 50) + 1, capped at Level 100
 
**How to Earn XP:**
• +5 XP per tool used
• +15 XP per daily streak day
• +10/15/20 XP from Daily Bonus (/bonus)
• +10 XP for a correct Daily Quiz answer (/quiz)
• +20 to +100 XP from invite tier milestones (/invite)
 
**Your Current Standing:** Level {my_level} — {my_rank} ({user.get('xp', 0)} XP)
 
Keep using tools daily to climb the leaderboard! /leaderboard
"""
    target = update.callback_query.message if update.callback_query else update.message
    await safe_reply(target, txt)
 
 
# ==================== ADMIN: BAN / UNBAN ====================
 
async def admin_ban(update, context):
    uid = str(update.effective_user.id)
    if not ADMIN_ID or uid != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    target_id = context.args[0]
    ban_user(target_id)
    await update.message.reply_text(f"🚫 User {target_id} banned.")
 
 
async def admin_unban(update, context):
    uid = str(update.effective_user.id)
    if not ADMIN_ID or uid != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    target_id = context.args[0]
    unban_user(target_id)
    await update.message.reply_text(f"✅ User {target_id} unbanned.")
 
 
async def admin_broadcast(update, context):
    uid = str(update.effective_user.id)
    if not ADMIN_ID or uid != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    msg = " ".join(context.args)
    sent, failed = 0, 0
    for target_uid in list(users.keys()):
        try:
            await context.bot.send_message(chat_id=int(target_uid), text=f"📢 {msg}")
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"Broadcast done. Sent: {sent}, Failed: {failed}")
 
 
# ==================== RUNNER - ULTRA STABLE ====================
 
def run_bot():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN missing in environment!")
        return
    print(f"✅ TOKEN OK len={len(BOT_TOKEN)} Starting ULTRA BEST World Bot...")
 
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
        app.add_handler(CommandHandler("thumbnail", cmd_thumbnail))
        app.add_handler(CommandHandler("linkedin", cmd_linkedin))
        app.add_handler(CommandHandler("tips", cmd_tips))
        app.add_handler(CommandHandler("myinvites", myinvites_cmd))
        app.add_handler(CommandHandler("ranks", ranks_cmd))
        app.add_handler(CommandHandler("premium", premium))
        app.add_handler(CommandHandler("invite", invite))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(CommandHandler("bonus", bonus_cmd))
        app.add_handler(CommandHandler("quiz", quiz_cmd))
        app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
        app.add_handler(CommandHandler("ban", admin_ban))
        app.add_handler(CommandHandler("unban", admin_unban))
        app.add_handler(CommandHandler("broadcast", admin_broadcast))
 
        app.add_handler(PreCheckoutQueryHandler(precheckout))
        app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
 
        async def b49(u, c):
            await buy_premium(u, c, PREMIUM_TIER1)
 
        async def b99(u, c):
            await buy_premium(u, c, PREMIUM_TIER2)
 
        async def b199(u, c):
            await buy_premium(u, c, PREMIUM_TIER3)
 
        app.add_handler(CallbackQueryHandler(b49, pattern="^buy_49$"))
        app.add_handler(CallbackQueryHandler(b99, pattern="^buy_99$"))
        app.add_handler(CallbackQueryHandler(b199, pattern="^buy_199$"))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tool))
 
        await app.initialize()
        await app.bot.delete_webhook(drop_pending_updates=True)
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
        print("✅✅✅ ULTRA BEST WORLD Bot Live - 24/7 - Gamified Edition Replies Coming!")
        while True:
            await asyncio.sleep(3600)
 
    try:
        asyncio.run(polling())
    except Exception as e:
        print(f"❌ Crash: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(5)
        run_bot()
 
 
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Flask 0.0.0.0:{port} TOKEN={bool(BOT_TOKEN)} ULTRA BEST WORLD EDITION - GAMIFIED")
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
 
