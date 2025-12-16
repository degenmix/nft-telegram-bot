import os
import io
import logging
import requests
from telegram import LabeledPrice, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, 
    PreCheckoutQueryHandler, filters, ContextTypes
)

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GPU_API = os.environ.get('GPU_API', 'http://106.54.57.182:8000')
FREE_CREDITS = 50
ADMIN_ID = 7226303447

# In-memory storage
user_credits = {}

# NFT style presets
STYLES = {
    'pfp': 'pfp style, profile picture, avatar, clean background',
    'anime': 'anime style, vibrant colors, detailed',
    'cyberpunk': 'cyberpunk style, neon, futuristic',
    'pixel': 'pixel art style, 8bit, retro',
    'ape': 'bored ape style, NFT collection',
    'abstract': 'abstract art, colorful, unique',
    '3d': '3d rendered, high quality, detailed',
    'fantasy': 'fantasy art, magical, ethereal'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    user_id = update.message.from_user.id
    
    if user_id not in user_credits:
        user_credits[user_id] = FREE_CREDITS
        logger.info(f"New user {user_id} - gave {FREE_CREDITS} credits")
    
    credits = user_credits.get(user_id, 0)
    
    try:
        r = requests.get(f"{GPU_API}/health", timeout=3)
        status_emoji = "🟢" if r.status_code == 200 else "🟡"
    except:
        status_emoji = "🔴"
    
    keyboard = [
        [InlineKeyboardButton("🎨 Generate Image", callback_data='gen')],
        [InlineKeyboardButton("🎯 NFT Styles", callback_data='styles')],
        [InlineKeyboardButton("💎 My Credits", callback_data='cred')],
        [InlineKeyboardButton("💰 Buy Credits", callback_data='buy')]
    ]
    
    await update.message.reply_text(
        f"🎨 *AI Image Generator*\n\n"
        f"{status_emoji} GPU Status\n"
        f"⚡ L40 GPU Powered\n"
        f"💎 *Your Credits:* {credits}\n\n"
        f"*Quick Start:*\n"
        f"Just type: `a cool robot`\n\n"
        f"Or use styles:\n"
        f"`/anime magical girl`\n"
        f"`/cyberpunk city`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show credit packages"""
    keyboard = [
        [InlineKeyboardButton("💎 100 Credits - 50 Stars (~₹99)", callback_data="buy_100")],
        [InlineKeyboardButton("🔥 500 Credits - 200 Stars (~₹399) ⭐BEST", callback_data="buy_500")],
        [InlineKeyboardButton("⚡ 1000 Credits - 350 Stars (~₹699)", callback_data="buy_1000")]
    ]
    await update.message.reply_text(
        "💰 *Buy Credits with Telegram Stars*\n\n"
        "💎 100 credits = 50 Stars (~₹99)\n"
        "🔥 500 credits = 200 Stars (~₹399) ⭐BEST VALUE\n"
        "⚡ 1000 credits = 350 Stars (~₹699)\n\n"
        "Choose a package below:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    credits = user_credits.get(user_id, 0)
    
    if query.data == 'gen':
        await query.message.reply_text(
            "🎨 *Generate Image*\n\n"
            "Send your prompt:\n"
            "`a futuristic robot`",
            parse_mode='Markdown'
        )
    
    elif query.data == 'styles':
        styles_text = "*🎨 Available Styles:*\n\n"
        for name in STYLES.keys():
            styles_text += f"/{name}\n"
        styles_text += "\n*Usage:* `/anime your prompt`"
        await query.message.reply_text(styles_text, parse_mode='Markdown')
    
    elif query.data == 'cred':
        await query.message.reply_text(
            f"💎 *Your Credits: {credits}*\n\n"
            f"Need more? Use /buy",
            parse_mode='Markdown'
        )
    
    elif query.data == 'buy':
        await buy_handler(query, context)
    
    # Handle payment buttons
    elif query.data.startswith('buy_'):
        packages = {
            "buy_100": (100, 50, "100 Credits Pack"),
            "buy_500": (500, 200, "500 Credits ⭐BEST VALUE"),
            "buy_1000": (1000, 350, "1000 Credits Pack")
        }
        
        if query.data in packages:
            credits_amount, stars, title = packages[query.data]
            
            await context.bot.send_invoice(
                chat_id=query.from_user.id,
                title=title,
                description=f"Get {credits_amount} credits to generate AI images!",
                payload=f"credits_{credits_amount}",
                currency="XTR",
                prices=[LabeledPrice(label=f"{credits_amount} Credits", amount=stars)]
            )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve payment"""
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add credits after successful payment"""
    user_id = update.message.from_user.id
    payload = update.message.successful_payment.invoice_payload
    
    # Extract credits from payload
    credits_amount = int(payload.split('_')[1])
    
    # Add credits
    if user_id not in user_credits:
        user_credits[user_id] = 0
    user_credits[user_id] += credits_amount
    
    await update.message.reply_text(
        f"✅ *Payment Successful!*\n\n"
        f"💎 Added {credits_amount} credits!\n"
        f"💰 New balance: {user_credits[user_id]}\n\n"
        f"Start generating with any prompt! 🎨",
        parse_mode='Markdown'
    )
    
    logger.info(f"User {user_id} bought {credits_amount} credits")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user ID"""
    user_id = update.message.from_user.id
    credits = user_credits.get(user_id, 0)
    
    await update.message.reply_text(
        f"👤 *Your Details*\n\n"
        f"User ID: `{user_id}`\n"
        f"💎 Credits: {credits}",
        parse_mode='Markdown'
    )

async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image generation"""
    user_id = update.message.from_user.id
    text = update.message.text
    
    # Check for style command
    style = 'default'
    prompt = text
    
    for style_name in STYLES.keys():
        if text.startswith(f'/{style_name} '):
            style = style_name
            prompt = text.replace(f'/{style_name} ', '')
            break
    
    # Check credits
    if user_credits.get(user_id, 0) < 1:
        keyboard = [[InlineKeyboardButton("💰 Buy Credits", callback_data='buy')]]
        await update.message.reply_text(
            "❌ *No credits left!*\n\n"
            "Buy more to continue:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    status = await update.message.reply_text("🎨 Generating...")
    
    try:
        # Add style to prompt
        if style in STYLES:
            full_prompt = f"{prompt}, {STYLES[style]}"
        else:
            full_prompt = prompt
        
        logger.info(f"User {user_id} generating: {full_prompt}")
        
        # Call GPU API
        r = requests.post(
            f"{GPU_API}/generate",
            json={"prompt": full_prompt},
            timeout=60
        )
        
        if r.status_code == 200:
            # Deduct credit
            user_credits[user_id] -= 1
            remaining = user_credits[user_id]
            
            # Send image
            photo = io.BytesIO(r.content)
            photo.name = 'image.png'
            
            await update.message.reply_photo(
                photo=photo,
                caption=f"✨ {prompt}\n💎 Credits left: {remaining}"
            )
            
            await status.delete()
            logger.info(f"Success! User {user_id} has {remaining} credits")
        else:
            await status.edit_text("❌ Failed. Try again!")
    
    except requests.exceptions.Timeout:
        await status.edit_text("⏱️ Timeout! Try again.")
    except Exception as e:
        await status.edit_text("❌ Error occurred!")
        logger.error(f"Error: {e}")

def main():
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add ALL handlers here
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy_handler))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_handler))
    
    logger.info("✅ @Jenerator_bot starting...")
    logger.info(f"🔗 GPU API: {GPU_API}")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
