import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

TOKEN = "8719037892:AAHo65_rkPuLfRNTBAv6aTb37_-XT0Ig07k"
GROUP_ID = -1002312326448
ADMINS = [7966376623]

SUPORTE = "https://t.me/teus_67"

PLANOS = {
    "1m": (30, "1 Month — $25"),
    "3m": (90, "3 Months — $55"),
    "6m": (180, "6 Months — $85"),
    "12m": (365, "1 Year — $120")
}

PAYPAL = "susanesantos4@gmail.com"
CASHAPP = "$BassBaddict"

conn = sqlite3.connect("db.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    expire_date TEXT
)
""")
conn.commit()


def get_user(user_id):
    cursor.execute("SELECT expire_date FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()


# START + FOLLOW-UP
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔓 Unlock Access", callback_data="planos")],
        [InlineKeyboardButton("📅 My Subscription", callback_data="acesso")],
        [InlineKeyboardButton("💬 Support", url=SUPORTE)]
    ]

    await update.message.reply_text(
        """Hi 👋

Welcome to Farts Wardrobe.

You’re about to access a private collection that most people will never see.

🔥 Inside:
• 40,000+ exclusive videos  
• 100+ premium models  
• Daily updates  
• Organized content  
• Custom requests available 👀  

⚠️ Access is limited.

🔒 No leaks. Permanent ban.

Tap below 👇""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    context.job_queue.run_once(followup_1, 60, chat_id=update.effective_chat.id)
    context.job_queue.run_once(followup_2, 180, chat_id=update.effective_chat.id)


async def followup_1(context):
    await context.bot.send_message(context.job.chat_id,
        "Still thinking? 👀\n\nMost users join quickly once they see what’s inside.")


async def followup_2(context):
    await context.bot.send_message(context.job.chat_id,
        "Last chance ⚠️\n\nAccess can close anytime.")


# BOTÕES
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "planos":
        keyboard = [[InlineKeyboardButton(v[1], callback_data=k)] for k, v in PLANOS.items()]
        await query.message.reply_text("Choose your plan:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in PLANOS:
        dias, texto = PLANOS[query.data]
        context.user_data["plano"] = dias

        await query.message.reply_text(f"""
{texto}

PayPal:
{PAYPAL}

CashApp:
{CASHAPP}

Send proof after payment.
""")

    elif query.data == "acesso":
        user = get_user(query.from_user.id)
        if user:
            await query.message.reply_text(f"Valid until:\n{user[0]}")
        else:
            await query.message.reply_text("No active subscription.")


# COMPROVANTE
async def comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    plano = context.user_data.get("plano")

    if not plano:
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar|{user.id}|{plano}")],
        [InlineKeyboardButton("❌ Negar", callback_data=f"negar|{user.id}")]
    ])

    for admin in ADMINS:
        await context.bot.forward_message(admin, update.message.chat_id, update.message.message_id)

        await context.bot.send_message(
            admin,
            f"💰 PAGAMENTO\nID: {user.id}\nPlano: {plano} dias",
            reply_markup=keyboard
        )

    await update.message.reply_text("Waiting approval...")


# APROVAR
async def aprovar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, user_id, dias = query.data.split("|")
    user_id = int(user_id)
    dias = int(dias)

    user = get_user(user_id)

    if user:
        base = max(datetime.strptime(user[0], "%Y-%m-%d %H:%M:%S"), datetime.now())
        msg = "Subscription renewed ✅"
    else:
        base = datetime.now()
        msg = "Subscription activated ✅"

    expire = base + timedelta(days=dias)

    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?)",
                   (user_id, expire.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

    try:
        member = await context.bot.get_chat_member(GROUP_ID, user_id)

        if member.status in ["member", "administrator", "creator"]:
            await context.bot.send_message(user_id, f"{msg}\n\nValid until:\n{expire}")
        else:
            raise Exception
    except:
        invite = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1
        )

        await context.bot.send_message(
            user_id,
            f"{msg}\n\nJoin:\n{invite.invite_link}\n\nValid until:\n{expire}"
        )

    await query.edit_message_text("✅ Approved")


# NEGAR
async def negar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, user_id = query.data.split("|")
    user_id = int(user_id)

    await context.bot.send_message(user_id, "Payment rejected. Contact support.")
    await query.edit_message_text("❌ Rejected")


# EXPIRAÇÃO
async def check_expired(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()

    cursor.execute("SELECT user_id, expire_date FROM users")
    for user_id, expire_date in cursor.fetchall():
        expire = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S")

        if now > expire:
            try:
                await context.bot.ban_chat_member(GROUP_ID, user_id)
                await context.bot.unban_chat_member(GROUP_ID, user_id)
            except:
                pass

            cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
            conn.commit()


# APP
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(aprovar, pattern="^aprovar"))
app.add_handler(CallbackQueryHandler(negar, pattern="^negar"))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, comprovante))

app.job_queue.run_repeating(check_expired, interval=60)

print("🔥 BOT COMPLETO RODANDO 🔥")
app.run_polling()
