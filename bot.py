import os
import io
import logging
import requests
from telegram import LabeledPrice, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, 
    PreCheckoutQueryHandler, filters, ContextTypes
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GPU_API = os.environ.get('GPU_API', 'http://106.54.57.182:8000')
FREE_CREDITS = 15
REFERRAL_BONUS = 20
ADMIN_ID = 7226303447

# In-memory storage
user_credits = {}
user_referrals = {}

# Styles
STYLES = {
    'pfp': 'pfp style, profile picture, avatar, clean background',
    'anime': 'anime style, vibrant colors, detailed',
    'cyberpunk': 'cyberpunk style, neon, futuristic',
    'pixel': 'pixel art style, 8bit, retro',
    'abstract': 'abstract art, colorful, unique',
    '3d': '3d rendered, high quality, detailed',
    'fantasy': 'fantasy art, magical, ethereal'
}

# Quality tiers
QUALITY_TIERS = {
    'standard': {'size': '512x512', 'credits': 1, 'name': 'Standard'},
    'hd': {'size': '1024x1024', 'credits': 3, 'name': 'HD'},
    '4k': {'size': '2048x2048', 'credits': 10, 'name': '4K'}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Check for referral
    if context.args and len(context.args) > 0:
        referrer_id = int(context.args[0])
        if referrer_id != user_id and user_id not in user_credits:
            # New user from referral
            user_credits[user_id] = FREE_CREDITS + REFERRAL_BONUS
            user_credits[referrer_id] = user_credits.get(referrer_id, 0) + REFERRAL_BONUS
            
            await update.message.reply_text(
                f"🎉 Welcome! You got {FREE_CREDITS + REFERRAL_BONUS} credits!\n"
                f"(+{REFERRAL_BONUS} bonus from referral!)"
            )
            
            try:
                await context.bot.send_message(
                    referrer_id,
                    f"🎁 Friend joined! You got +{REFERRAL_BONUS} credits!"
                )
            except:
                pass
    
    if user_id not in user_credits:
        user_credits[user_id] = FREE_CREDITS
    
    credits = user_credits.get(user_id, 0)
    
    try:
        r = requests.get(f"{GPU_API}/health", timeout=3)
        status_emoji = "🟢" if r.status_code == 200 else "🟡"
    except:
        status_emoji = "🔴"
    
    keyboard = [
        [InlineKeyboardButton("🎨 Generate Image", callback_data='gen')],
        [InlineKeyboardButton("💎 My Credits", callback_data='cred')],
        [InlineKeyboardButton("💰 Buy Credits", callback_data='buy')],
        [InlineKeyboardButton("🎁 Invite Friends", callback_data='invite')]
    ]
    
    await update.message.reply_text(
        f"🎨 *AI Image Generator*\n\n"
        f"{status_emoji} GPU Status: L40 Powered\n"
        f"💎 *Your Credits:* {credits}\n\n"
        f"*Quality Tiers:*\n"
        f"📱 Standard (512x512) - 1 credit\n"
        f"💎 HD (1024x1024) - 3 credits\n"
        f"🔥 4K (2048x2048) - 10 credits\n\n"
        f"*Quick Start:*\n"
        f"Type any prompt: `a cool robot`\n"
        f"Or use styles: `/anime girl`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    credits = user_credits.get(user_id, 0)
    
    if query.data == 'gen':
        keyboard = [
            [InlineKeyboardButton("📱 Standard (1 credit)", callback_data='quality_standard')],
            [InlineKeyboardButton("💎 HD (3 credits)", callback_data='quality_hd')],
            [InlineKeyboardButton("🔥 4K (10 credits)", callback_data='quality_4k')]
        ]
        await query.message.reply_text(
            f"*Choose Quality:*\n\n"
            f"Your credits: {credits}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data.startswith('quality_'):
        quality = query.data.split('_')[1]
        context.user_data['quality'] = quality
        await query.message.reply_text(
            f"*{QUALITY_TIERS[quality]['name']} Quality Selected*\n\n"
            f"Send your prompt now:\n"
            f"`a futuristic robot warrior`",
            parse_mode='Markdown'
        )
    
    elif query.data == 'cred':
        await query.message.reply_text(
            f"💎 *Your Credits: {credits}*\n\n"
            f"Need more? /buy",
            parse_mode='Markdown'
        )
    
    elif query.data == 'buy':
        keyboard = [
            [InlineKeyboardButton("💎 100 Credits - 50 Stars (~₹99)", callback_data="buy_100")],
            [InlineKeyboardButton("🔥 500 Credits - 200 Stars (~₹399) ⭐BEST", callback_data="buy_500")],
            [InlineKeyboardButton("⚡ 1000 Credits - 350 Stars (~₹699)", callback_data="buy_1000")]
        ]
        await query.message.reply_text(
            f"💰 *Buy Credits*\n\n"
            f"Standard: 1 credit per image\n"
            f"HD: 3 credits per image\n"
            f"4K: 10 credits per image\n\n"
            f"Choose package:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'invite':
        bot_username = (await context.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start={user_id}"
        referral_count = user_referrals.get(user_id, 0)
        
        await query.message.reply_text(
            f"🎁 *Invite & Earn!*\n\n"
            f"Share your link:\n"
            f"`{invite_link}`\n\n"
            f"Both you and your friend get *{REFERRAL_BONUS} bonus credits!*\n\n"
            f"Your referrals: {referral_count}",
            parse_mode='Markdown'
        )
    
    elif query.data.startswith('buy_'):
        packages = {
            "buy_100": (100, 50, "100 Credits"),
            "buy_500": (500, 200, "500 Credits ⭐BEST"),
            "buy_1000": (1000, 350, "1000 Credits")
        }
        
        if query.data in packages:
            credits_amount, stars, title = packages[query.data]
            
            await context.bot.send_invoice(
                chat_id=query.from_user.id,
                title=title,
                description=f"Get {credits_amount} credits!",
                payload=f"credits_{credits_amount}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label=f"{credits_amount} Credits", amount=stars)]
            )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    payload = update.message.successful_payment.invoice_payload
    credits_amount = int(payload.split('_')[1])
    
    if user_id not in user_credits:
        user_credits[user_id] = 0
    user_credits[user_id] += credits_amount
    
    await update.message.reply_text(
        f"✅ *Payment Successful!*\n\n"
        f"💎 +{credits_amount} credits!\n"
        f"💰 Balance: {user_credits[user_id]}\n\n"
        f"Start generating! 🎨",
        parse_mode='Markdown'
    )
    
    logger.info(f"User {user_id} bought {credits_amount} credits")

async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    # Get quality from user_data or default to standard
    quality = context.user_data.get('quality', 'standard')
    required_credits = QUALITY_TIERS[quality]['credits']
    
    # Check style
    style = 'default'
    prompt = text
    for style_name in STYLES.keys():
        if text.startswith(f'/{style_name} '):
            style = style_name
            prompt = text.replace(f'/{style_name} ', '')
            break
    
    if user_credits.get(user_id, 0) < required_credits:
        keyboard = [[InlineKeyboardButton("💰 Buy Credits", callback_data='buy')]]
        await update.message.reply_text(
            f"❌ Need {required_credits} credits for {QUALITY_TIERS[quality]['name']}!\n"
            f"You have: {user_credits.get(user_id, 0)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    status = await update.message.reply_text(f"🎨 Generating {QUALITY_TIERS[quality]['name']}...")
    
    try:
        if style in STYLES:
            full_prompt = f"{prompt}, {STYLES[style]}"
        else:
            full_prompt = prompt
        
        logger.info(f"User {user_id} generating {quality}: {full_prompt}")
        
        r = requests.post(
            f"{GPU_API}/generate",
            json={"prompt": full_prompt, "size": QUALITY_TIERS[quality]['size']},
            timeout=60
        )
        
        if r.status_code == 200:
            user_credits[user_id] -= required_credits
            remaining = user_credits[user_id]
            
            photo = io.BytesIO(r.content)
            photo.name = 'image.png'
            
            await update.message.reply_photo(
                photo=photo,
                caption=f"✨ {prompt}\n💎 Credits: {remaining} | Quality: {QUALITY_TIERS[quality]['name']}"
            )
            
            await status.delete()
            logger.info(f"Success! User {user_id} has {remaining} credits")
        else:
            await status.edit_text("❌ Failed. Try again!")
    
    except requests.exceptions.Timeout:
        await status.edit_text("⏱️ Timeout! Try again.")
    except Exception as e:
        await status.edit_text("❌ Error!")
        logger.error(f"Error: {e}")

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_handler))
    
    logger.info("✅ @Jenerator_bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
