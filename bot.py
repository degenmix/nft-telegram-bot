import os
import io
import logging
import requests
from telegram import LabeledPrice
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GPU_API = os.environ.get('GPU_API', 'http://106.54.57.182:8000')
FREE_CREDITS = 50  # Set to 50 as you wanted
ADMIN_ID = 7226303447  # Replace with your Telegram user ID
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
    
    # Give free credits to new users
    if user_id not in user_credits:
        user_credits[user_id] = FREE_CREDITS
        logger.info(f"New user {user_id} - gave {FREE_CREDITS} credits")
    
    credits = user_credits.get(user_id, 0)
    
    # Check API status
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
        f"🎨 *AI NFT Image Generator*\n\n"
        f"{status_emoji} GPU Status\n"
        f"⚡ L40 GPU Powered\n"
        f"💎 *Your Credits:* {credits}\n\n"
        f"*Quick Start:*\n"
        f"Just type any prompt:\n"
        f"`a cool robot warrior`\n\n"
        f"Or use style commands:\n"
        f"`/pfp cute character`\n"
        f"`/anime magical girl`\n"
        f"`/cyberpunk city`",
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
            "`a futuristic robot`\n\n"
            "Or use style:\n"
            "`/pfp cute cat`\n"
            "`/anime hero`",
            parse_mode='Markdown'
        )
    
    elif query.data == 'styles':
        styles_text = "*🎨 Available NFT Styles:*\n\n"
        for name, desc in STYLES.items():
            styles_text += f"/{name} - {desc.split(',')[0]}\n"
        styles_text += "\n*Usage:* `/pfp your prompt here`"
        
        await query.message.reply_text(styles_text, parse_mode='Markdown')
    
    elif query.data == 'cred':
        await query.message.reply_text(
            f"💎 *Your Credits*\n\n"
            f"Balance: {credits}\n\n"
            f"Need more? /buy",
            parse_mode='Markdown'
        )
    
    elif query.data == 'buy':
        await query.message.reply_text(
            "💰 *Buy More Credits*\n\n"
            "📦 *Packages:*\n"
            "💎 10 images = ₹100 (0.5 TON)\n"
            "⚡ 50 images = ₹400 (2 TON)\n"
            "🚀 100 images = ₹700 (3.5 TON)\n\n"
            "🇮🇳 *UPI:* `rahulkhunte@ybl`\n"
            "🌐 *TON:* `UQAUDbGlEj0mgQe-yu8r7Iree8OEAn4CB7l8t2447N6tteRI`\n\n"
            "📝 *After payment:*\n"
            "1. Send payment screenshot\n"
            "2. Use /myid to get your ID\n"
            "3. Credits added in 5 mins!\n\n"
            "Questions? Message @rahul_username",
            parse_mode='Markdown'
        )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user their ID"""
    user_id = update.message.from_user.id
    credits = user_credits.get(user_id, 0)
    
    await update.message.reply_text(
        f"👤 *Your Details*\n\n"
        f"User ID: `{user_id}`\n"
        f"💎 Credits: {credits}\n\n"
        f"Send this ID after payment!",
        parse_mode='Markdown'
    )

async def add_credits_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to add credits"""
    if update.message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])
        
        if user_id not in user_credits:
            user_credits[user_id] = 0
        
        user_credits[user_id] += amount
        
        await update.message.reply_text(
            f"✅ Added {amount} credits to user {user_id}\n"
            f"New balance: {user_credits[user_id]}"
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"💎 *Payment Received!*\n\n"
                     f"{amount} credits added\n"
                     f"Balance: {user_credits[user_id]}\n\n"
                     f"Thanks for your purchase! 🎉",
                parse_mode='Markdown'
            )
        except:
            pass
        
        logger.info(f"Admin added {amount} credits to user {user_id}")
        
    except Exception as e:
        await update.message.reply_text(f"Error: {e}\n\nUsage: /addcredits user_id amount")

async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image generation"""
    user_id = update.message.from_user.id
    text = update.message.text
    
    # Check if it's a style command
    style = 'default'
    prompt = text
    
    for style_name in STYLES.keys():
        if text.startswith(f'/{style_name} '):
            style = style_name
            prompt = text.replace(f'/{style_name} ', '')
            break
    
    # Check credits
    if user_credits.get(user_id, 0) < 1:
        await update.message.reply_text(
            "❌ *No credits left!*\n\n"
            "Buy more: /buy",
            parse_mode='Markdown'
        )
        return
    
    # Generate image
    status = await update.message.reply_text("🎨 Generating...")
    
    try:
        # Prepare prompt with style
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
            photo.name = 'nft.png'
            
            await update.message.reply_photo(
                photo=photo,
                caption=f"✨ {prompt}\n💎 Credits left: {remaining}"
            )
            
            await status.delete()
            logger.info(f"Success! User {user_id} has {remaining} credits left")
        else:
            await status.edit_text("❌ Generation failed. Try again!")
            logger.error(f"API error: {r.status_code}")
    
    except requests.exceptions.Timeout:
        await status.edit_text("⏱️ Timeout! GPU is busy. Try again in 1 min.")
        logger.error("Request timeout")
    
    except Exception as e:
        await status.edit_text("❌ Error occurred. Try again!")
        logger.error(f"Error: {e}")

def main():
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("addcredits", add_credits_admin))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_handler))
    
    logger.info("✅ @Jenerator_bot starting...")
    logger.info(f"🔗 GPU API: {GPU_API}")
    
    # Clear pending updates and start
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show credit packages"""
    keyboard = [
        [InlineKeyboardButton("💎 100 Credits - 50 Stars", callback_data="buy_100")],
        [InlineKeyboardButton("🔥 500 Credits - 200 Stars (BEST VALUE)", callback_data="buy_500")],
        [InlineKeyboardButton("⭐ 1000 Credits - 350 Stars", callback_data="buy_1000")]
    ]
    await update.message.reply_text(
        "💰 Buy More Credits:\n\n"
        "100 credits = 50 Stars (~₹99)\n"
        "500 credits = 200 Stars (~₹399) ⭐BEST VALUE\n"
        "1000 credits = 350 Stars (~₹699)\n\n"
        "Choose a package:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment button clicks"""
    query = update.callback_query
    await query.answer()
    
    packages = {
        "buy_100": (100, 50, "100 Credits Pack"),
        "buy_500": (500, 200, "500 Credits Pack ⭐BEST VALUE"),
        "buy_1000": (1000, 350, "1000 Credits Pack")
    }
    
    if query.data in packages:
        credits, stars, title = packages[query.data]
        
        # Send invoice
        await context.bot.send_invoice(
            chat_id=query.from_user.id,
            title=title,
            description=f"Get {credits} credits to generate amazing AI images!",
            payload=f"credits_{credits}",
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=f"{credits} Credits", amount=stars)]
        )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve payment"""
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add credits after successful payment"""
    user_id = update.message.from_user.id
    payload = update.message.successful_payment.invoice_payload
    
    # Extract credits from payload (e.g., "credits_100" -> 100)
    credits = int(payload.split('_')[1])
    
    # Add credits to user (you'll need to implement credit tracking)
    # For now, just confirm:
    await update.message.reply_text(
        f"✅ Payment successful!\n\n"
        f"💎 Added {credits} credits to your account!\n"
        f"Use /generate to create images!"
    )

# Add these to your application
application.add_handler(CommandHandler("buy", buy_handler))
application.add_handler(CallbackQueryHandler(payment_callback, pattern="^buy_"))
application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

if __name__ == '__main__':
    main()




