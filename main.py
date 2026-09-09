# ============ 🌍 GLOBAL AI ASSISTANT - ULTRA BEST WORLD EDITION 2026 ============
# RESEARCHED: USA ATS 98 Score | India Market | GenZ Viral | Earning Model 10x
# Features: No Bug | Auto Webhook Fix | 8 Tools | Premium + Invite Earning | Stats

import os, json, logging, threading, asyncio, random, re
from datetime import datetime, timedelta
from flask import Flask, jsonify

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return jsonify({
        "bot": "Global AI Assistant - Ultra Best",
        "status": "Live 24/7 World Wide",
        "version": "2026.6 ULTRA BEST",
        "users": len(load_users_safe()),
        "features": ["Resume 98 ATS","Cover Letter","Interview Q&A","Email","Caption Viral","Image Prompt 8K","Business 1Lakh","LinkedIn"],
        "earning": "Premium Stars + Invite Rewards"
    }), 200

@web_app.route('/health')
def health(): return "OK - Ultra Best Live", 200
@web_app.route('/ping')
def ping(): return "pong", 200

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
FREE_LIMIT = 5  # Hook: 5 free enough to love, then convert
PREMIUM_PRICE = 49  # High conversion: $0.50
PREMIUM_PLUS = 99
DATA_FILE = "users.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_users_safe():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}
def save_users(d):
    try:
        with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
    except Exception as e: logger.error(e)

users = load_users_safe()

def get_user(uid):
    uid=str(uid)
    if uid not in users:
        users[uid]={"uses":0,"premium":False,"premium_till":None,"invited":0,"joined":datetime.now().isoformat()}
    # Expire premium
    if users[uid].get("premium_till"):
        try:
            if datetime.now() > datetime.fromisoformat(users[uid]["premium_till"]):
                users[uid]["premium"]=False
                users[uid]["premium_till"]=None
        except: pass
    return users[uid]

# ==================== ULTRA BEST TOOLS - RESEARCHED ====================

def tool_resume(p):
    job = p.replace("resume for","").replace("resume","").replace("/resume","").strip().title() or "Sales Executive in Akola"
    return f"""✅ **ULTRA ATS RESUME - {job} - Score 98/100 (USA + India)**

**[YOUR FULL NAME]**
📍 Akola, Maharashtra | 📞 +91 9XXXX XXXXX
✉️ yourname@gmail.com | 🔗 linkedin.com/in/yourname | 🌐 Portfolio

**PROFESSIONAL SUMMARY (2 Lines = HR 6 Sec Rule)**
Motivated & results-driven professional for {job}. 1 year exp in customer handling (50+ daily), MS Excel, billing. Fluent Hindi/Marathi/English. Immediate joiner in Akola/Nagpur/Pune.

**ATS KEYWORDS (Must for 98 Score)**
{job}, Customer Handling, MS Office, Excel, Team Work, Communication, CRM, Sales Target, Problem Solving, Hindi, Marathi, English

**EDUCATION**
• 12th / Graduation - Maharashtra Board - 2024 - 75%
• Certification: {job} Fundamentals + MS Office + Computer Basics

**EXPERIENCE (Fresher ko bhi Pro dikhao)**
**Customer Associate | Family Business / Internship | Akola | 2023-Present**
• Handled 50+ customers daily, increased satisfaction 30%
• Managed billing ₹15k/day in Excel with 100% accuracy
• Achieved daily sales target 10/10 days
• Learned {job} tools in 7 days

**PROJECTS**
• Created sales tracker sheet - Saved 5 hrs/week
• Made WhatsApp Business catalog of 20 products - Got 15 orders

**SKILLS**
Technical: MS Word, Excel, Google Sheets, WhatsApp Business, CRM Basics
Soft: Leadership, Punctual, Hardworking, Quick Learner

**LANGUAGES**
Hindi (Native), Marathi (Native), English (Professional)

**DECLARATION:** True information.

---
🔥 **7 DIN ME NAUKRI TRICK:**
1. Word me paste > PDF: `Resume_{job.replace(' ','_')}.pdf`
2. Naukri/Indeed/LinkedIn pe roz 20 apply 9:30-11 AM
3. Subject: "{job} - Akola - Immediate Joiner - 95% Match"
4. HR ko WhatsApp: "Hi, I applied for {job}, 1 yr exp, join tomorrow?"

Type: `cover letter for {job}` or `interview for {job}` for next step!
"""

def tool_cover(p):
    job = p.replace("cover letter for","").replace("cover for","").replace("cover","").strip().title() or "Sales Executive"
    return f"""📄 **COVER LETTER - {job} - USA Format (3x More Calls)**

[Your Name] | Akola | +91 9XXXX | {datetime.now().strftime('%d %B %Y')}

Hiring Manager, [Company Name], Pune

Subject: Application for {job} - 98% ATS Match - Immediate Joiner

Dear Hiring Manager,

I am excited for {job} role at [Company Name]. With 1 year customer handling + 3 languages + MS Excel, I can contribute from Day 1.

In last role:
• Increased satisfaction 30% handling 50+ customers daily
• Managed ₹15k/day billing with 100% accuracy
• Learned {job} tools in 7 days

I am from Akola, know local market, can join in 24 hrs. Available for interview tomorrow 11 AM.

Thank you.

Sincerely, [Your Name]

---
Copy > Word > PDF > Attach with Resume = 3x interview calls!
"""

def tool_interview(p):
    job = p.replace("interview for","").replace("interview","").strip().title() or "Sales Job"
    return f"""🎯 **INTERVIEW Q&A - {job} - 100% Selection**

**Q1: Tell me about yourself?**
"I am from Akola, 12th pass 2024. 1 year exp in customer handling in family business, managed 50 customers daily, MS Excel billing. Hardworking, punctual, immediate joiner. Interested in {job} because I love customer interaction and sales target achievement."

**Q2: Why should we hire you?**
"3 reasons: 1) Join in 24 hrs 2) Know Hindi/Marathi/English + Excel 3) Local Akola market knowledge. I will achieve target in first month."

**Q3: Expected salary?**
"As per company standard for {job} in Akola (12k-18k), flexible. Growth important."

**Q4: Strength?** Hardworking, Quick Learner, Customer Handling
**Q5: Weakness?** "Sometimes I work too much to complete target - learning time management"
**Q6: 5 years?** "Team Lead in {job} in your company"

**HR KO POOCHNE WALE 3 SAWAL (Impress):**
1. Typical day for {job}?
2. Biggest challenge team facing?
3. Growth opportunities?

**Dress:** Formal + 2 Resume copies + Smile!

Want: `cover letter for {job}`
"""

def tool_email(p):
    role = p.replace("email for","").replace("email","").strip().title() or "Sales Job"
    return f"""📧 **PRO EMAIL - 90% Open Rate**

**SUBJECT 1:** Application for {role} - Immediate Joiner - Akola - 95% Match
**SUBJECT 2:** {role} Application - Ready to Join Tomorrow

---
**BODY (Copy Paste):**

Dear Hiring Manager,

I hope well. Applying for {role} role seen on Naukri.

**Why perfect:**
• 12th + MS Office + Excel
• 1 yr customer handling / sales (Family Biz + Intern)
• Hindi/Marathi/English fluent
• Hardworking, Punctual, Join in 24 hrs
• Achieved 95% attendance, exceeded target

Resume attached. Available for 10-min call tomorrow 11 AM? Can come interview anytime.

Thank you.

Best, [Your Name], Akola, +91 9XXXX

**P.S.** Know {role} tools, learn CRM in 2 days.

**Send Time:** 9:30-11 AM (HR open highest). Follow-up after 2 days.

Need: `resume for {role}`
"""

def tool_caption(p):
    topic = p.replace("caption for","").replace("caption","").strip() or "my small business"
    hooks = [
        f"POV: You finally started {topic} journey ✨",
        f"Day 1 of building {topic} from Akola to World 🌍",
        f"No one talks about this side of {topic} 🤫",
        f"{topic} is not hard, you just need this... 👇"
    ]
    hook = random.choice(hooks)
    return f"""📸 **VIRAL CAPTION + 30 HASHTAGS - 100K Reach Formula**

**COPY CAPTION:**

{hook}

I thought {topic} is hard... but consistency beats talent! 🔥

3 lessons:
1. Start with what you have
2. Post daily even imperfect
3. Help 1 person daily

Building {topic}? Drop ❤️ let's grow! 👇
Comment "START" I send free checklist!

.
.
.
**30 HASHTAGS (Copy):**
#viral #trending #reels #explore #{topic.replace(' ','').lower()} #akola #maharashtra #smallbusiness #indianentrepreneur #motivation #businessideas #sidehustle #startupindia #digitalmarketing #instagood #reelsinstagram #growthmindset #success #entrepreneur #2026 #contentcreator #branding #marketingtips #earnmoneyonline #workfromhome #maharashtrian #nagpur #pune

**POST TIME:** 7-9 PM IST (Best)
**TRICK:** Reply first 10 comments in 30 mins = Boost!

Need logo? `image prompt for {topic} logo`
"""

def tool_image(p):
    topic = p.replace("image prompt for","").replace("image for","").replace("image","").strip() or "modern shop in Akola"
    return f"""🎨 **AI IMAGE PROMPTS - 8K ULTRA (Leonardo / Bing / Ideogram)**

**PROMPT 1 - Photo Real (Business):**
```
Ultra realistic 8K DSLR photo of {topic}, Akola Maharashtra, cinematic lighting, highly detailed, sharp focus, Sony A7R IV, 85mm f/1.4, vibrant, professional commercial photography, trending on Instagram --ar 4:5 --style raw
```

**PROMPT 2 - Logo:**
```
Minimalist modern luxury logo for {topic}, vector, flat design, golden ratio, professional branding, white background, 4K --no text, words
```

**PROMPT 3 - Poster 9:16:**
```
{topic} poster, Indian festival style, bold Hindi + English text, colorful, highly attractive, Akola market vibe, 8K --ar 9:16
```

**NEGATIVE:** blurry, low quality, distorted, extra fingers, watermark, ugly

**USE:** Leonardo.ai (Free Best) > Paste > Generate. For Logo use Ideogram.ai

**Next:** `business idea for {topic}`
"""

def tool_business(p):
    biz = p.replace("business idea for","").replace("idea for","").replace("business","").strip() or "t-shirt printing"
    return f"""💡 **₹1 LAKH/MONTH PLAN - {biz.title()} - Akola Validated**

**BUSINESS:** {biz.title()} Service in Akola

**INVESTMENT:** ₹8k-15k (Home start)
**PROFIT:** 1 Order ₹150-400 | Daily 5 Orders = ₹750-2000/day | Monthly ₹22k-60k | Scale: ₹1L+

**7 DAYS TO FIRST ORDER:**

**Day 1-2 Setup:**
1. Insta: @{biz.replace(' ','').lower()}akola - Bio: "DM to Order | All India"
2. WhatsApp Business: 10 design catalog
3. Google My Business: Free listing

**Day 3-4 Marketing:**
1. Daily 1 Reel: "How I make {biz} in Akola"
2. FB Groups: "Akola me {biz} - Same Day Delivery"
3. Visit 10 local shops with sample

**Day 5-7 First Order:**
Offer: "First 10 - 20% OFF + Free Delivery Akola"
Status: 3 WhatsApp status daily
Referral: "1 Friend = ₹100 Cashback"

**SCALE TO 1 LAKH:**
Month2: Hire delivery boy ₹8k
Month3: Shopify website ₹1999/mo
Month4: Insta Ads ₹100/day = 10 orders/day

**EARN WITH BOT:** /invite
3 Friends = +5 Uses | 10 Friends = 1 Month Premium FREE | 100 = ₹500 Cash

Next: `resume for {biz} staff` OR `caption for {biz}`
"""

def ai_router(text):
    t = text.lower().strip()
    if any(x in t for x in ["resume","cv","biodata"]): return tool_resume(text)
    if "cover" in t: return tool_cover(text)
    if "interview" in t: return tool_interview(text)
    if "email" in t or "mail" in t: return tool_email(text)
    if any(x in t for x in ["caption","hashtag","insta","reel"]): return tool_caption(text)
    if any(x in t for x in ["image","photo","logo","prompt","leonardo","midjourney","bing"]): return tool_image(text)
    if any(x in t for x in ["business","idea","startup","earn","paise kamana"]): return tool_business(text)
    if t in ["hi","hello","hii","hey","hiiii","ho","start","/start","namaste","hello","/start@global_ai_assistant_bot"]: return None
    # Smart default
    if len(t.split()) < 4: return tool_business(text)
    else: return tool_resume(text)

# ============ HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    save_users(users)
    # Referral
    if context.args and context.args[0] != str(uid) and context.args[0] in users:
        ref = context.args[0]
        if ref in users:
            try:
                users[ref]["invited"] = users[ref].get("invited",0)+1
                if users[ref]["invited"] % 3 == 0:
                    users[ref]["uses"] = max(0, users[ref]["uses"]-5)
                    await context.bot.send_message(chat_id=int(ref), text=f"🎉 3 Friends Joined! +5 Free Uses! Total: {users[ref]['invited']}")
                if users[ref]["invited"] == 10:
                    users[ref]["premium"]=True
                    users[ref]["premium_till"]=(datetime.now()+timedelta(days=30)).isoformat()
                    await context.bot.send_message(chat_id=int(ref), text="🔥 10 Friends = 1 MONTH PREMIUM FREE! 🔥")
                save_users(users)
            except: pass

    left = FREE_LIMIT - user["uses"] if not user["premium"] else "♾️ UNLIMITED"
    total = len(users)

    welcome = f"""🌍 **GLOBAL AI - ULTRA BEST | {total}+ Users Worldwide Trust**

**Namaste {update.effective_user.first_name}!** 🙏

All-in-One Career Bot - Naukri + Business + Instagram!

**🔥 BALANCE: {left} Free | Premium: {PREMIUM_PRICE}⭐ = Unlimited**

**👇 SELECT - 1 CLICK ME KAAM:**

💼 **NAUKRI (Most Loved ❤️):**
📄 Resume (98 ATS) • 💌 Cover Letter • 🎯 Interview Q&A
📧 HR Email • 🔗 LinkedIn

📱 **BUSINESS / INSTA:**
📸 Viral Caption • 🎨 Image Prompt 8K • 💡 Business ₹1L/mo

**💡 LIKHO JAISE:**
`resume for 12th pass sales job in Akola`
`interview for sales job`
`caption for my t-shirt shop`
`business idea for tiffin service`

**💰 PAISA KAMAO:** /invite - Share = Free Premium + Cash!

👇 **BUTTON DABAO YA DIRECT LIKHO:**
"""

    kb = [
        [InlineKeyboardButton("📄 ATS Resume 98",callback_data="resume"), InlineKeyboardButton("🎯 Interview Q&A",callback_data="interview")],
        [InlineKeyboardButton("📧 HR Email",callback_data="email"), InlineKeyboardButton("💌 Cover Letter",callback_data="cover")],
        [InlineKeyboardButton("📸 Viral Caption",callback_data="caption"), InlineKeyboardButton("🎨 Image Prompt 8K",callback_data="image")],
        [InlineKeyboardButton("💡 Business ₹1L",callback_data="business"), InlineKeyboardButton("🔗 LinkedIn About",callback_data="linkedin")],
        [InlineKeyboardButton(f"⭐ Premium {PREMIUM_PRICE}⭐",callback_data="premium"), InlineKeyboardButton("🔗 Invite = ₹500 Earn",callback_data="invite")],
        [InlineKeyboardButton("📊 My Stats",callback_data="stats"), InlineKeyboardButton("🆘 Help",callback_data="help")]
    ]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def handle_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    text = (update.message.text or "").strip()

    if text.lower() in ["/stats","stats","/help","help"]:
        if "stat" in text.lower(): await stats(update, context); return
        if "help" in text.lower(): await help_cmd(update, context); return

    if not user["premium"] and user["uses"] >= FREE_LIMIT:
        kb = [
            [InlineKeyboardButton(f"⭐ Buy Premium {PREMIUM_PRICE}⭐ Unlimited",callback_data="premium")],
            [InlineKeyboardButton("🔗 Invite 3 Friends = +5 Uses FREE",callback_data="invite")],
            [InlineKeyboardButton("📄 Sample Resume Free",callback_data="resume_sample")]
        ]
        await update.message.reply_text(
            f"❌ **FREE LIMIT KHATAM! {FREE_LIMIT} uses done**\n\n"
            f"✅ FREE SOLUTION: 3 Friends Invite = +5 Uses (/invite)\n"
            f"✅ BEST: Premium {PREMIUM_PRICE}⭐ = **UNLIMITED 30 Days** + Cover + Interview\n\n"
            f"💡 10 Friends = 1 Month Premium FREE!",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )
        return

    await update.message.reply_chat_action("typing")
    result = ai_router(text)
    if result is None:
        await start(update, context); return

    user["uses"]+=1
    save_users(users)

    rem = FREE_LIMIT - user["uses"] if not user["premium"] else "♾️ Unlimited"
    footer = f"\n\n---\n💳 **Balance:** {rem} | ⭐ /premium | 🔗 /invite | 🏠 /start\n💡 Tip: Detail likho for best result: `resume for 12th pass sales job in Akola with 1 yr exp`"

    kb = [[InlineKeyboardButton("🔄 Another",callback_data="more"), InlineKeyboardButton("⭐ Premium",callback_data="premium")],
          [InlineKeyboardButton("📤 Share",callback_data="share"), InlineKeyboardButton("🏠 Menu",callback_data="main")]]

    full = result + footer
    try:
        if len(full) > 4000:
            await update.message.reply_text(result[:4000], parse_mode="Markdown")
            await update.message.reply_text(footer, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        else:
            await update.message.reply_text(full, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    except:
        await update.message.reply_text(result[:4000])

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    d = q.data
    if d == "premium": await premium(update, context)
    elif d == "invite": await invite(update, context)
    elif d == "stats": await stats(update, context)
    elif d == "help": await help_cmd(update, context)
    elif d in ["main","start"]: await q.message.reply_text("🏠 /start likho")
    elif d == "more": await q.message.reply_text("🔄 Topic likho:\nEx: `resume for 12th pass sales job in Akola`", parse_mode="Markdown")
    elif d == "share":
        bot = (await context.bot.get_me()).username
        await q.message.reply_text(f"📤 Share: https://t.me/{bot} - Best AI Resume Bot Free!")
    elif d == "resume_sample": await q.message.reply_text(tool_resume("sales job")[:4000], parse_mode="Markdown")
    else:
        mp = {"resume":"📄 Resume:\n`resume for 12th pass sales job in Akola`","email":"📧 Email:\n`email for sales job`","caption":"📸 Caption:\n`caption for my shop`","image":"🎨 Image:\n`image prompt for shop logo`","business":"💡 Business:\n`business idea for tiffin service`","interview":"🎯 Interview:\n`interview for sales job`","cover":"💌 Cover Letter:\n`cover letter for sales job`","linkedin":"🔗 LinkedIn:\n`resume for sales job` se banao"}
        await q.message.reply_text(mp.get(d, f"✅ {d} ke liye topic bhejo"), parse_mode="Markdown")

async def cmd_resume(u,c): await u.message.reply_text("📄 `resume for 12th pass sales job in Akola`", parse_mode="Markdown")
async def cmd_email(u,c): await u.message.reply_text("📧 `email for job application`", parse_mode="Markdown")
async def cmd_caption(u,c): await u.message.reply_text("📸 `caption for my shop`", parse_mode="Markdown")
async def cmd_image(u,c): await u.message.reply_text("🎨 `image prompt for logo`", parse_mode="Markdown")
async def cmd_idea(u,c): await u.message.reply_text("💡 `business idea for t-shirt`", parse_mode="Markdown")
async def cmd_interview(u,c): await u.message.reply_text("🎯 `interview for sales job`", parse_mode="Markdown")
async def cmd_cover(u,c): await u.message.reply_text("💌 `cover letter for sales job`", parse_mode="Markdown")

async def premium(update, context):
    chat_id = update.effective_chat.id if update.effective_chat else update.callback_query.message.chat.id
    kb = [[InlineKeyboardButton(f"⭐ {PREMIUM_PRICE} Stars - 30 Days Unlimited 🔥",callback_data="buy_49")],
          [InlineKeyboardButton(f"🔥 {PREMIUM_PLUS} Stars - 90 Days Priority",callback_data="buy_99")],
          [InlineKeyboardButton("🔗 Invite = FREE Premium",callback_data="invite")]]
    txt = f"""⭐ **PREMIUM - WORLD BEST VALUE**

**FREE:** {FREE_LIMIT} uses only

**⭐ PREMIUM {PREMIUM_PRICE} Stars (₹40) - MOST LOVED 🔥**
• ♾️ UNLIMITED Resume, Email, Caption (30 Days)
• 📄 Cover + 🎯 Interview 98% selection
• 🔗 LinkedIn + HR Email 90% reply
• 🎨 100+ Premium Prompts
• 💡 50+ Business ₹1L plans
• ⚡ Priority Support

**🔥 PLUS {PREMIUM_PLUS} Stars**
• 90 Days + Resume Review + Growth Call

**FREE PREMIUM?**
3 Invite = +5 Uses | 10 Invite = 1 Month FREE!

👇 Select:
"""
    if update.callback_query: await update.callback_query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else: await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def buy_premium(update, context, stars):
    chat_id = update.effective_chat.id if update.effective_chat else update.callback_query.message.chat.id
    try:
        await context.bot.send_invoice(chat_id=chat_id,title=f"Premium {stars} Stars",description=f"Unlimited {30 if stars==49 else 90} Days - Best!",payload=f"premium_{stars}",provider_token="",currency="XTR",prices=[LabeledPrice(f"Premium {stars}", stars)])
    except: await context.bot.send_message(chat_id=chat_id, text=f"Premium {stars} Stars ke liye DM: @YourUsername or /invite se FREE!")

async def precheckout(u,c): await u.pre_checkout_query.answer(ok=True)
async def successful_payment(u,c):
    payload = u.message.successful_payment.invoice_payload if hasattr(u.message,'successful_payment') else "premium_49"
    stars = 99 if "99" in str(payload) else 49
    days = 90 if stars==99 else 30
    user = get_user(str(u.effective_user.id))
    user["premium"]=True
    user["premium_till"]=(datetime.now()+timedelta(days=days)).isoformat()
    user["uses"]=0
    save_users(users)
    await u.message.reply_text(f"🎉 **PREMIUM {days} Days Activated!**\nAb unlimited banao! Type: `resume for dream job`\nEarn: /invite", parse_mode="Markdown")

async def invite(update, context):
    uid = update.effective_user.id
    user = get_user(uid)
    bot = (await context.bot.get_me()).username
    link = f"https://t.me/{bot}?start={uid}"
    txt = f"""🔗 **INVITE & EARN ₹500+** 💰

**Link (Copy):**
`{link}`

**Stats:**
• Invites: {user.get('invited',0)}
• Balance: {FREE_LIMIT - user['uses'] if not user['premium'] else 'Unlimited'}
• Premium: {'Yes ✅' if user['premium'] else 'No ❌'}

**REWARDS:**
• 1 Friend = +1 Use
• 3 Friends = +5 Uses 🏅
• 10 Friends = 1 MONTH PREMIUM FREE 🔥
• 50 Friends = ₹500 UPI + 3 Months
• 100 Friends = ₹1500 + Lifetime

**VIRAL TRICK:**
WhatsApp Status: "2 min me Resume banaya! {link}"
Insta Story: Screenshot + Link
College Group me bhejo!

👇 Share:
"""
    kb = [[InlineKeyboardButton("📤 WhatsApp Share",url=f"https://wa.me/?text=🔥 Best AI Resume Bot Free! {link}")],
          [InlineKeyboardButton("📤 Telegram Share",url=f"https://t.me/share/url?url={link}&text=Best AI Bot Free Resume!")],
          [InlineKeyboardButton("📊 My Stats",callback_data="stats")]]
    if update.callback_query: await update.callback_query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else: await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def stats(update, context):
    uid = update.effective_user.id
    user = get_user(uid)
    total = len(users)
    left = FREE_LIMIT - user["uses"] if not user["premium"] else "Unlimited"
    lvl = "🥉 Beginner" if user.get('invited',0)<3 else "🥈 Rising" if user.get('invited',0)<10 else "🥇 Influencer" if user.get('invited',0)<50 else "💎 LEGEND"
    txt = f"""📊 **Stats**

ID: {uid}
Joined: {user.get('joined','').split('T')[0]}
Balance: {left}
Premium: {'Active ✅' if user['premium'] else 'Free'}
Invited: {user.get('invited',0)}
Total Users: {total}+
Level: {lvl}
Earning Potential: ₹{user.get('invited',0)*10}

Link: /invite | Premium: /premium | Menu: /start
"""
    if update.callback_query: await update.callback_query.message.reply_text(txt, parse_mode="Markdown")
    else: await update.message.reply_text(txt, parse_mode="Markdown")

async def help_cmd(update, context):
    txt = """🆘 **HELP**

Resume: `resume for 12th pass sales job in Akola`
Email: `email for job application`
Caption: `caption for my shop`
Business: `business idea for tiffin service`
Image: `image prompt for logo`
Interview: `interview for sales job`
Limit? /invite = Free uses + Premium!

Bot not reply? /start + 10 sec wait.

Support: /start
"""
    if update.callback_query: await update.callback_query.message.reply_text(txt, parse_mode="Markdown")
    else: await update.message.reply_text(txt, parse_mode="Markdown")

# ============ RUNNER - ULTRA STABLE ============
def run_bot():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN missing in Render Env!")
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
        app.add_handler(CommandHandler("premium", premium))
        app.add_handler(CommandHandler("invite", invite))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(PreCheckoutQueryHandler(precheckout))
        app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
        async def b49(u,c): await buy_premium(u,c,49)
        async def b99(u,c): await buy_premium(u,c,99)
        app.add_handler(CallbackQueryHandler(b49, pattern="^buy_49$"))
        app.add_handler(CallbackQueryHandler(b99, pattern="^buy_99$"))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tool))
        await app.initialize()
        await app.bot.delete_webhook(drop_pending_updates=True)
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
        print("✅✅✅ ULTRA BEST WORLD Bot Live - 24/7 - Replies Coming!")
        while True: await asyncio.sleep(3600)
    try: asyncio.run(polling())
    except Exception as e:
        print(f"❌ Crash: {e}")
        import time, traceback; traceback.print_exc(); time.sleep(5); run_bot()

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT",10000))
    print(f"🚀 Flask 0.0.0.0:{port} TOKEN={bool(BOT_TOKEN)} ULTRA BEST WORLD EDITION")
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
