import sqlite3
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ===== CONFIG =====
TOKEN = "8719037892:AAFEhus2FQISF-gMtSrh_kcTB0lHtUfhxM8"  # Coloque seu token aqui

GROUP_ID = -1002312326448
ADMINS = [7966376623]

SUPORTE = "https://t.me/teus_67"

PAYPAL = "susanesantos4@gmail.com"
CASHAPP = "$BassBaddict"
REVOLUT = "@matheus67"
CRYPTO_ADDRESS = "TMPx4r6jEFEbYX1Vs2BoN6pXEdETFE39wJ"

# Dicionário para facilitar a exibição de cada método
METODOS_PAGAMENTO = {
    "pay": ("PayPal", f"PayPal: {PAYPAL}", "https://media.discordapp.net/attachments/1493784274325737672/1504622536623783946/photo_2026-05-05_15-39-26.jpg?ex=6a07a86f&is=6a0656ef&hm=ec4e1119cd4e77e4158de16ffacdb152d2da9eee850de91a9ec2b86c8ac618d9&"),
    "cash": ("CashApp", f"CashApp: {CASHAPP}", "https://media.discordapp.net/attachments/1493784274325737672/1504622575454785626/IMG_20260505_154000_475_2.jpg?ex=6a07a878&is=6a0656f8&hm=2f6e3715e896d12e10526dc47e8fe8081bb9e98b71c8a1b41e8f586ec7f1c1c9&"), # Link temporário
    "rev": ("Revolut", f"Revolut: {REVOLUT}", "https://media.discordapp.net/attachments/1493784274325737672/1504622615111667722/photo_2026-05-14_18-48-52.jpg?ex=6a07a881&is=6a065701&hm=d1b46f1e6ccf5c2586ccb475a3bb09b4855780ea9ebf336a291c95dbf784bcff&"),
    "cryp": ("Crypto (USDT)", f"USDT-TRX(TRC20):\n`{CRYPTO_ADDRESS}`", "https://media.discordapp.net/attachments/1493784274325737672/1504622650243416154/photo_2026-05-14_19-33-25.jpg?ex=6a07a88a&is=6a06570a&hm=8a9e1fbadce06524a3941563383c5901d23db926a0c44adf9f4d5d6a335691fe&")
}

PLANOS = {
    "1m": (30, "1 Month — $20"),
    "3m": (90, "3 Months — $55"),
    "6m": (180, "6 Months — $85"),
    "12m": (365, "1 Year $120 (Best Deal)")
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
        text = "# Welcome!\n\nThe VIP Farts Wardrobe is a paid group with full access to exclusive content.\n\nWe currently have over 40,000 videos and more than 200 models, all organized and constantly updated!\n\nYou can make requests if you’re looking for something specific!\n\nClick below to subscribe ⬇️"

        keyboard = [
            [InlineKeyboardButton("🔓 Become a Member", callback_data="unlock")],
            [InlineKeyboardButton("💬 Support", url=SUPORTE)]
        ]

    video_source = "https://www.dropbox.com/scl/fi/szkfy3ptz7kmrk0g2jx6e/1_4.mp4?raw=1"

try:
        # Tenta enviar o vídeo com a legenda e botões
        await update.message.reply_video(
            video=video_source,
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        # Se o link do vídeo der erro (ex: link quebrado), ele envia só o texto
        print(f"Erro ao carregar vídeo: {e}")
        await update.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ===== UNLOCK (FUNÇÃO QUE FALTAVA) =====
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)
    
    keyboard = []
    for key, value in PLANOS.items():
        keyboard.append([InlineKeyboardButton(value[1], callback_data=f"plan_{key}")])
    
    await query.message.reply_text("Select the plan that suits you best 👇", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== ESCOLHA DO PLANO =====
async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    plano = query.data.split("_")[1]
    context.user_data["plano"] = plano

    keyboard = [
        [InlineKeyboardButton("🅿️ PayPal", callback_data="pay_pay")],
        [InlineKeyboardButton("💵 CashApp", callback_data="pay_cash")],
        [InlineKeyboardButton("🌀 Revolut", callback_data="pay_rev")],
        [InlineKeyboardButton("₿ Crypto (USDT)", callback_data="pay_cryp")]
    ]

    await query.message.reply_text(
        f"You selected: {PLANOS[plano][1]}\n\nNow, choose your payment method 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== DETALHES DO PAGAMENTO =====
async def detalhes_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)

    metodo_key = query.data.split("_")[1]
    nome, info, qr_code = METODOS_PAGAMENTO[metodo_key]
    
    plano = context.user_data.get("plano", "1m")
    valor_plano = PLANOS[plano][1]

    texto = f"✅ *Selected Method:* {nome}\n💎 *Plan:* {valor_plano}\n\n{info}\n\nPlease send the exact amount and then click the button below to send your proof."

    keyboard = [[InlineKeyboardButton("📤 Send Proof", callback_data="proof")]]

    try:
        await query.message.reply_photo(
            photo=qr_code,
            caption=texto,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.reply_text(texto, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== PROVA =====
async def proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)
    await query.message.reply_text("Please send your payment proof (photo or screenshot) now.")

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
    await update.message.reply_text("Proof received! Please wait while an admin reviews it.")

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
        invite = await context.bot.create_chat_invite_link(chat_id=GROUP_ID, member_limit=1)
        await context.bot.send_message(
            user_id,
            f"{msg}\n\nPlan: {nome_plano}\n\nJoin here 👇\n{invite.invite_link}\n\nValid until: {expire.strftime('%Y-%m-%d')}"
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
        await context.bot.send_message(user_id, "Payment rejected. If you think this is a mistake, contact support.")
    except:
        pass
    await query.edit_message_text("❌ Negado")

# ===== SUB =====
async def sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)
    user = get_user(query.from_user.id)
    if user:
        await query.message.reply_text(f"Your subscription is valid until:\n{user[0]}")
    else:
        await query.message.reply_text("You do not have an active subscription.")

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

# ===== FUNÇÕES ADMIN =====
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
    await query.message.reply_text("Digite o ID do usuário para remover:")

async def adm_remove_exec(update, context):
    if update.message.from_user.id not in ADMINS or not context.user_data.get("remover"):
        return
    try:
        user_id = int(update.message.text)
        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        conn.commit()
        await context.bot.ban_chat_member(GROUP_ID, user_id)
        await context.bot.unban_chat_member(GROUP_ID, user_id)
        await update.message.reply_text("Removido com sucesso ✅")
    except:
        await update.message.reply_text("Erro ao remover usuário ❌")
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

# ===== TAREFAS DE FUNDO =====
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
                await context.bot.send_message(user_id, "⚠️ Sua assinatura expira amanhã.")
                cursor.execute("INSERT INTO avisos VALUES (?,?)", (user_id, "1d"))
            elif dias == 0 and not enviado("0d"):
                await context.bot.send_message(user_id, "⏳ Último dia da sua assinatura!")
                cursor.execute("INSERT INTO avisos VALUES (?,?)", (user_id, "0d"))
            conn.commit()
        except: pass

async def check_expired(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    cursor.execute("SELECT user_id, expire_date FROM users")
    for user_id, expire_date in cursor.fetchall():
        expire = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S")
        if now > expire:
            try:
                await context.bot.ban_chat_member(GROUP_ID, user_id)
                await context.bot.unban_chat_member(GROUP_ID, user_id)
            except: pass
            cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
            cursor.execute("DELETE FROM avisos WHERE user_id=?", (user_id,))
            conn.commit()

# ===== APP =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(unlock, pattern="unlock"))
app.add_handler(CallbackQueryHandler(select_plan, pattern="^plan_"))
app.add_handler(CallbackQueryHandler(detalhes_pagamento, pattern="^pay_"))
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

if app.job_queue:
    app.job_queue.run_repeating(check_warnings, interval=3600)
    app.job_queue.run_repeating(check_expired, interval=60)

print("🔥 BOT ONLINE 24H 🔥")
app.run_polling()
