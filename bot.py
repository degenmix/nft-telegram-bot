import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests
import io
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8290885550:AAHGgUtc4J_dycHzkRqhPCH81Qeq_fDEIT8')
GPU_API = os.environ.get('GPU_API', 'http://106.54.57.182:8000')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_credits = {}
FREE_CREDITS = 50

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in user_credits:
        user_credits[user_id] = FREE_CREDITS
        logger.info(f"New user: {user_id}")
    
    credits = user_credits[user_id]
    
    keyboard = [
        [InlineKeyboardButton("🎨 Generate Image", callback_data='gen')],
        [InlineKeyboardButton("🎯 NFT Styles", callback_data='styles')],
        [InlineKeyboardButton("💎 My Credits", callback_data='cred')]
    ]
    
    await update.message.reply_text(
        f"🎨 *AI NFT Image Generator*\n\n"
        f"⚡ L40 GPU Powered\n"
        f"🚀 Generation: 3-5 seconds\n"
        f"🎁 FREE credits for everyone!\n\n"
        f"💰 *Your Credits:* {credits}\n\n"
        f"*How to use:*\n"
        f"Just send your prompt:\n"
        f"`a cool robot warrior`\n\n"
        f"Or use NFT styles:\n"
        f"`/pfp cute character`\n"
        f"`/anime magical girl`\n"
        f"`/cyberpunk city`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'gen':
        await query.message.reply_text(
            "🎨 Send your prompt:\n`a futuristic robot`\n\nOr:\n`/pfp cool character`",
            parse_mode='Markdown'
        )
    elif query.data == 'styles':
        try:
            r = requests.get(f"{GPU_API}/styles", timeout=5)
            if r.ok:
                styles = r.json().get('styles', [])
                text = "🎯 *NFT Styles:*\n\n" + "\n".join([f"/{s}" for s in styles])
                await query.message.reply_text(text, parse_mode='Markdown')
            else:
                await query.message.reply_text("❌ GPU offline")
        except Exception as e:
            logger.error(f"Styles error: {e}")
            await query.message.reply_text("❌ GPU unavailable")
    elif query.data == 'cred':
        credits = user_credits.get(query.from_user.id, 0)
        await query.message.reply_text(
            f"💎 Credits: {credits}\n\n🎁 Share bot for more!\nContact @rk for bulk"
        )

async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    style = ""
    if text.startswith('/'):
        parts = text.split(' ', 1)
        if len(parts) == 2:
            style = parts[0][1:]
            prompt = parts[1]
        else:
            await update.message.reply_text("Usage: `/pfp your prompt`", parse_mode='Markdown')
            return
    else:
        prompt = text
    
    if user_credits.get(user_id, 0) < 1:
        await update.message.reply_text("❌ No credits! Use /start")
        return
    
    prompts = [p.strip() for p in prompt.split('\n') if p.strip()]
    if user_credits.get(user_id, 0) < len(prompts):
        await update.message.reply_text(f"Need {len(prompts)} credits, have {user_credits[user_id]}")
        return
    
    status = await update.message.reply_text(f"🎨 Generating {len(prompts)} image(s)...")
    
    success = 0
    for i, p in enumerate(prompts):
        try:
            logger.info(f"Requesting: {p[:50]}")
            
            r = requests.post(
                f"{GPU_API}/generate",
                json={"prompt": p, "style": style},
                timeout=60
            
            )
            
            logger.info(f"Response status: {r.status_code}, size: {len(r.content)} bytes")
            
            if r.status_code == 200 and len(r.content) > 1000:
                photo = io.BytesIO(r.content)
                photo.name = 'image.png'
                photo.seek(0)
                
                logger.info(f"Sending photo to user {user_id}")
                
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"✨ {p[:80]}"
                )
                
                success += 1
                logger.info(f"✅ Sent image {i+1}")
            else:
                logger.error(f"GPU API returned {r.status_code}, content: {r.text[:200]}")
                await update.message.reply_text(f"❌ Generation {i+1} failed")
                
        except requests.exceptions.Timeout:
            logger.error("Timeout connecting to GPU")
            await update.message.reply_text(f"⏱️ Timeout - GPU taking too long")
        except Exception as e:
            logger.error(f"Error on image {i+1}: {type(e).__name__}: {e}")
            await update.message.reply_text(f"❌ Error: {type(e).__name__}")
    
    user_credits[user_id] -= success
    remaining = user_credits[user_id]
    
    await update.message.reply_text(f"✅ Done! 💎 Left: {remaining}")
    
    try:
        await status.delete()
    except:
        pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_handler))
    logger.info("✅ @Jenerator_bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()


