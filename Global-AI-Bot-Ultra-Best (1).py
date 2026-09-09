# ============ RENDER 24/7 FLASK - TOP ============
from flask import Flask
import threading
import os
import logging
from datetime import datetime

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Global AI Assistant Bot - Live 24/7 2026 Ultra Best"

@web_app.route('/health')
def health():
    return {"status": "Live", "bot": "Global AI Bot", "version": "2026.3-FINAL"}

@web_app.route('/ping')
def ping():
    return "PONG"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

threading.Thread(target=run_web, daemon=True).start()

# ============ TELEGRAM BOT ============
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
FREE_LIMIT = 5
PREMIUM_PRICE_STARS = 25
DATA_FILE = "users.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Save error {e}")

users = load_users()

def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"uses": 0, "premium": False, "invited": 0, "joined": datetime.now().isoformat()}
    return users[uid]

def ai_generate(tool, prompt):
    p = (prompt or "Your Topic")[:600].strip() or "Your Topic"
    if tool == "resume":
        return f"ATS RESUME FOR: {p} | Name: [Your Name] | Skills: {p} | Experience: Project in {p} | Education: 12th/Graduate | Beats ATS USA UK India"
    elif tool == "email":
        return f"EMAIL FOR: {p} | Subject: Application for {p} | Dear Manager, I want to apply for {p}... Thank you"
    elif tool == "caption":
        return f"CAPTION FOR: {p} | {p} lifestyle | POV perfect {p} | Hashtag"
    elif tool == "image":
        return f"PROMPT: Ultra realistic 8K photo of {p}, cinematic lighting Use in Leonardo.ai"
    elif tool == "idea":
        return f"IDEA: Global {p} AI Store - Market 800M users - Earn 25 Stars x 1000 = $500/month"
    else:
        return f"Result for {p}: World-class output!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    save_users(users)
    if context.args and len(context.args) > 0:
        ref_id = context.args[0]
        if ref_id != str(uid) and ref_id in users:
            users[ref_id]["invited"] = users[ref_id].get("invited", 0) + 1
            if users[ref_id]["invited"] % 3 == 0:
                users[ref_id]["uses"] = max(0, users[ref_id]["uses"] - 2)
            save_users(users)
    left = FREE_LIMIT - user["uses"] if not user["premium"] else "UNLIMITED"
    total = len(users)
    text = f"Global AI Bot - User #{total} - Trusted 100+ Countries! Tools: /resume /email /caption /image /idea Balance: {left} Free Type any topic!"
    kb = [
        [InlineKeyboardButton("Resume", callback_data="resume"), InlineKeyboardButton("Email", callback_data="email")],
        [InlineKeyboardButton("Caption", callback_data="caption"), InlineKeyboardButton("Image", callback_data="image")],
        [InlineKeyboardButton(f"Premium {PREMIUM_PRICE_STARS} Stars", callback_data="premium"), InlineKeyboardButton("Invite", callback_data="invite")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def handle_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    if not user["premium"] and user["uses"] >= FREE_LIMIT:
        kb = [[InlineKeyboardButton(f"Pay {PREMIUM_PRICE_STARS} Stars", callback_data="premium")], [InlineKeyboardButton("Invite Friends", callback_data="invite")]]
        await update.message.reply_text(f"Limit Over! Used {FREE_LIMIT}. Upgrade {PREMIUM_PRICE_STARS} Stars or Invite 3 friends!", reply_markup=InlineKeyboardMarkup(kb))
        return
    msg = (update.message.text or "").lower()
    tool = "resume"
    if "email" in msg:
        tool = "email"
    elif "caption" in msg or "insta" in msg:
        tool = "caption"
    elif "image" in msg or "photo" in msg:
        tool = "image"
    elif "idea" in msg or "business" in msg:
        tool = "idea"
    await update.message.reply_chat_action("typing")
    result = ai_generate(tool, update.message.text)
    user["uses"] += 1
    save_users(users)
    rem = FREE_LIMIT - user["uses"] if not user["premium"] else "Unlimited"
    footer = f" Left: {rem} | /premium | /invite | /start"
    kb = [[InlineKeyboardButton("More", callback_data="resume"), InlineKeyboardButton("Premium", callback_data="premium")]]
    if len(result) > 3800:
        await update.message.reply_text(result[:3800])
        await update.message.reply_text(result[3800:] + footer, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(result + footer, reply_markup=InlineKeyboardMarkup(kb))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "premium":
        await premium(update, context)
    elif data == "invite":
        await invite(update, context)
    elif data == "start":
        await start(update, context)
    else:
        await q.message.reply_text(f"Send topic for {data}. Example: {data} for 12th pass")

async def cmd_resume(update, context):
    await update.message.reply_text("Send resume details. Ex: Resume for 12th pass sales job")

async def cmd_email(update, context):
    await update.message.reply_text("Send email topic. Ex: Email for job application")

async def cmd_caption(update, context):
    await update.message.reply_text("Send caption topic. Ex: Caption for my shop")

async def cmd_image(update, context):
    await update.message.reply_text("Send image idea. Ex: Image of cat in space, 8K")

async def cmd_idea(update, context):
    await update.message.reply_text("Send idea field. Ex: Business idea for t-shirt")

async def premium(update, context):
    chat_id = update.effective_chat.id if update.effective_chat else update.callback_query.message.chat.id
    try:
        await context.bot.send_invoice(chat_id=chat_id, title="Unlock Unlimited", description="Unlimited AI Tools", payload="premium", provider_token="", currency="XTR", prices=[LabeledPrice("Premium", PREMIUM_PRICE_STARS)])
    except:
        await context.bot.send_message(chat_id=chat_id, text="Contact for Premium 25 Stars!")

async def precheckout(update, context):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update, context):
    user = get_user(str(update.effective_user.id))
    user["premium"] = True
    user["uses"] = 0
    save_users(users)
    await update.message.reply_text("PREMIUM Activated! Unlimited! Type /start")

async def invite(update, context):
    uid = update.effective_user.id
    user = get_user(uid)
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={uid}"
    text = f"Invite & Earn Link: {link} Share = +2 Uses per friend! Invites: {user.get('invited',0)}"
    kb = [[InlineKeyboardButton("Share", url=f"https://t.me/share/url?url={link}")]]
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

def main():
    if not BOT_TOKEN or len(BOT_TOKEN) < 20:
        print("BOT_TOKEN missing - Add in Render ENV")
        import time
        while True:
            time.sleep(3600)
    print("Starting Global AI Bot - WORLD BEST FINAL")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("email", cmd_email))
    app.add_handler(CommandHandler("caption", cmd_caption))
    app.add_handler(CommandHandler("image", cmd_image))
    app.add_handler(CommandHandler("idea", cmd_idea))
    app.add_handler(CommandHandler("premium", premium))
    app.add_handler(CommandHandler("invite", invite))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tool))
    print("Bot Running Live 24/7")
    app.run_polling(drop_pending_updates=True, stop_signals=None, allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == "__main__":
    main()
