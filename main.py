import sqlite3
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")

GROUP_ID = -1002312326448
ADMINS = [7966376623]

SUPORTE = "https://t.me/teus_67"

PAYPAL = "susanesantos40@gmail.com"
CASHAPP = "$BassBaddict"

PLANOS = {
    "1m": (30, "1 Month — $25"),
    "3m": (90, "3 Months — $55"),
    "6m": (180, "6 Months — $85"),
    "12m": (365, "🔥 BEST VALUE — 1 Year $120")
}

# ===== DATABASE =====
conn = sqlite3.connect("db.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expire_date TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS all_users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS avisos (user_id INTEGER, tipo TEXT)")
conn.commit()

def salvar_usuario(user_id):
    cursor.execute("INSERT OR IGNORE INTO all_users VALUES (?)", (user_id,))
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT expire_date FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()

async def safe_answer(query):
    try:
        await query.answer()
    except:
        pass

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salvar_usuario(update.message.from_user.id)

    user = get_user(update.message.from_user.id)

    if user:
        text = "✅ You already have an active subscription.\n\nUse the options below."
        keyboard = [
            [InlineKeyboardButton("🔄 Renew Subscription", callback_data="unlock")],
            [InlineKeyboardButton("📅 My Subscription", callback_data="sub")],
            [InlineKeyboardButton("💬 Support", url=SUPORTE)]
        ]
    else:
        text = """Hi 😊

Welcome! The VIP Farts Wardrobe group is a paid group with full access to exclusive content. We currently have over 40,000 videos and more than 100 models, all well organized and constantly updated.

You’ll get full access to everything, and you can also make requests if you’re looking for something specific 👀

We focus on keeping the group active, organized, and always bringing new content.

Let me know if you’d like to join and I’ll guide you through everything 👍"""

        keyboard = [
            [InlineKeyboardButton("🔓 Become a Member", callback_data="unlock")],
            [InlineKeyboardButton("💬 Support", url=SUPORTE)]
        ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== PLANOS =====
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    salvar_usuario(query.from_user.id)

    keyboard = []
    for key, value in PLANOS.items():
        keyboard.append([InlineKeyboardButton(value[1], callback_data=f"plan_{key}")])

    await query.message.reply_text("Choose your plan 👇", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== ESCOLHA =====
async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    plano = query.data.split("_")[1]
    context.user_data["plano"] = plano

    texto = f"""
💳 Payment Methods

PayPal:
{PAYPAL}

CashApp:
{CASHAPP}

Selected:
{PLANOS[plano][1]}

Send proof after payment.
"""

    await query.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Send Proof", callback_data="proof")]])
    )

# ===== PROVA =====
async def proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)
    await query.message.reply_text("Send your payment proof now.")

# ===== RECEBER =====
async def receber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salvar_usuario(update.message.from_user.id)

    user = update.message.from_user
    plano = context.user_data.get("plano", "1m")
    plano_nome = PLANOS[plano][1]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar|{user.id}|{plano}")],
        [InlineKeyboardButton("❌ Negar", callback_data=f"negar|{user.id}")]
    ])

    for admin in ADMINS:
        try:
            await context.bot.forward_message(admin, update.message.chat_id, update.message.message_id)
            await context.bot.send_message(
                admin,
                f"💰 Pagamento recebido\n\nUsuário: {user.id}\nPlano: {plano_nome}",
                reply_markup=keyboard
            )
        except:
            pass

# ===== APROVAR =====
async def aprovar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    try:
        data = query.data.split("|")
        user_id = int(data[1])
        plano = data[2]
    except:
        return

    dias, nome_plano = PLANOS.get(plano, PLANOS["1m"])

    user = get_user(user_id)

    base = datetime.now()
    if user:
        base = max(datetime.strptime(user[0], "%Y-%m-%d %H:%M:%S"), base)
        msg = "Subscription renewed ✅"
    else:
        msg = "Subscription activated ✅"

    expire = base + timedelta(days=dias)

    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, expire.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

    try:
        invite = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1
        )

        await context.bot.send_message(
            user_id,
            f"{msg}\n\nPlan: {nome_plano}\n\nJoin here 👇\n{invite.invite_link}\n\nValid until:\n{expire}"
        )
    except:
        await context.bot.send_message(user_id, "Error generating link. Contact support.")

    await query.edit_message_text("✅ Aprovado")

# ===== NEGAR =====
async def negar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    try:
        user_id = int(query.data.split("|")[1])
        await context.bot.send_message(user_id, "Payment rejected.")
    except:
        pass

    await query.edit_message_text("❌ Negado")

# ===== SUB =====
async def sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    user = get_user(query.from_user.id)

    if user:
        await query.message.reply_text(f"Válido até:\n{user[0]}")
    else:
        await query.message.reply_text("Você não possui assinatura ativa.")

# ===== ADMIN =====
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return

    keyboard = [
        [InlineKeyboardButton("📊 Total de Usuários", callback_data="adm_total")],
        [InlineKeyboardButton("👥 Usuários Ativos", callback_data="adm_ativos")],
        [InlineKeyboardButton("⏳ Expirando", callback_data="adm_expirando")],
        [InlineKeyboardButton("🆔 Ver IDs", callback_data="adm_ids")],
        [InlineKeyboardButton("❌ Remover Usuário", callback_data="adm_remove")]
    ]

    await update.message.reply_text("⚙️ Painel Administrativo", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== FUNÇÕES QUE FALTAVAM =====
async def adm_total(update, context):
    query = update.callback_query
    await safe_answer(query)

    cursor.execute("SELECT COUNT(*) FROM all_users")
    total = cursor.fetchone()[0]

    await query.message.reply_text(f"Total: {total}")

async def adm_ativos(update, context):
    query = update.callback_query
    await safe_answer(query)

    cursor.execute("SELECT user_id, expire_date FROM users")
    data = cursor.fetchall()

    texto = "\n".join([f"{u} → {d}" for u, d in data])

    await query.message.reply_text(texto or "Nenhum ativo.")

async def adm_ids(update, context):
    query = update.callback_query
    await safe_answer(query)

    cursor.execute("SELECT user_id FROM all_users")
    users = cursor.fetchall()

    await query.message.reply_text("\n".join([str(u[0]) for u in users])[:4000])

async def adm_remove_start(update, context):
    query = update.callback_query
    await safe_answer(query)

    context.user_data["remover"] = True
    await query.message.reply_text("Digite o ID:")

async def adm_remove_exec(update, context):
    if update.message.from_user.id not in ADMINS:
        return
    if not context.user_data.get("remover"):
        return

    try:
        user_id = int(update.message.text)

        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        conn.commit()

        await context.bot.ban_chat_member(GROUP_ID, user_id)
        await context.bot.unban_chat_member(GROUP_ID, user_id)

        await update.message.reply_text("Removido ✅")
    except:
        await update.message.reply_text("Erro ❌")

    context.user_data["remover"] = False

async def adm_expirando(update, context):
    query = update.callback_query
    await safe_answer(query)

    now = datetime.now()
    texto = ""

    cursor.execute("SELECT user_id, expire_date FROM users")
    for user_id, expire_date in cursor.fetchall():
        expire = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S")
        dias = (expire - now).days

        if dias <= 3:
            texto += f"{user_id} → {dias} dias\n"

    await query.message.reply_text(texto or "Ninguém próximo de expirar.")

# ===== AVISOS =====
async def check_warnings(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()

    cursor.execute("SELECT user_id, expire_date FROM users")
    for user_id, expire_date in cursor.fetchall():
        expire = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S")
        dias = (expire - now).days

        def enviado(tipo):
            cursor.execute("SELECT 1 FROM avisos WHERE user_id=? AND tipo=?", (user_id, tipo))
            return cursor.fetchone()

        try:
            if dias == 3 and not enviado("3d"):
                await context.bot.send_message(user_id, "⚠️ Sua assinatura expira em 3 dias.")
                cursor.execute("INSERT INTO avisos VALUES (?,?)", (user_id, "3d"))

            elif dias == 1 and not enviado("1d"):
                await context.bot.send_message(user_id, "⚠️ Expira amanhã.")
                cursor.execute("INSERT INTO avisos VALUES (?,?)", (user_id, "1d"))

            elif dias == 0 and not enviado("0d"):
                await context.bot.send_message(user_id, "⏳ Último dia da sua assinatura.")
                cursor.execute("INSERT INTO avisos VALUES (?,?)", (user_id, "0d"))

            conn.commit()
        except:
            pass

# ===== EXPIRAR =====
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
            cursor.execute("DELETE FROM avisos WHERE user_id=?", (user_id,))
            conn.commit()

# ===== APP =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(unlock, pattern="unlock"))
app.add_handler(CallbackQueryHandler(select_plan, pattern="^plan_"))
app.add_handler(CallbackQueryHandler(proof, pattern="proof"))
app.add_handler(CallbackQueryHandler(sub, pattern="sub"))
app.add_handler(CallbackQueryHandler(aprovar, pattern="^aprovar"))
app.add_handler(CallbackQueryHandler(negar, pattern="^negar"))

app.add_handler(CallbackQueryHandler(adm_expirando, pattern="adm_expirando"))
app.add_handler(CallbackQueryHandler(adm_total, pattern="adm_total"))
app.add_handler(CallbackQueryHandler(adm_ativos, pattern="adm_ativos"))
app.add_handler(CallbackQueryHandler(adm_ids, pattern="adm_ids"))
app.add_handler(CallbackQueryHandler(adm_remove_start, pattern="adm_remove"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, adm_remove_exec))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receber))

app.job_queue.run_repeating(check_warnings, interval=3600)
app.job_queue.run_repeating(check_expired, interval=60)

print("🔥 BOT ONLINE 24H 🔥")
app.run_polling()
