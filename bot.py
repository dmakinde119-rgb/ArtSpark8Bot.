import os
import logging
import io
import json
import requests
from PIL import Image
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from Railway environment variables
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# Get API keys from environment variables (optional)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')  # For AI features

# Dictionary to store user session data
user_sessions = {}

# ============ URL SHORTENER ============

async def shorten_url(update: Update, url: str) -> None:
    """Shorten a URL using multiple free services with fallback."""
    try:
        # Try is.gd first (most reliable)
        response = requests.get(
            'https://is.gd/create.php',
            params={'format': 'json', 'url': url},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if 'shorturl' in data:
                short_url = data['shorturl']
                await update.message.reply_text(
                    f"✅ **URL Shortened Successfully!**\n\n"
                    f"🔗 Original: {url}\n"
                    f"📎 Short: {short_url}\n\n"
                    f"✨ Use /shorten to shorten another URL."
                )
                return

        # Fallback to TinyURL
        response = requests.get(
            f'https://tinyurl.com/api-create.php',
            params={'url': url},
            timeout=10
        )

        if response.status_code == 200 and response.text:
            short_url = response.text.strip()
            await update.message.reply_text(
                f"✅ **URL Shortened Successfully!**\n\n"
                f"🔗 Original: {url}\n"
                f"📎 Short: {short_url}\n\n"
                f"✨ Use /shorten to shorten another URL."
            )
        else:
            await update.message.reply_text(
                "⚠️ URL shortening services are currently unavailable. Please try again later."
            )

    except Exception as e:
        logger.error(f"Error shortening URL: {e}")
        await update.message.reply_text(
            "❌ An error occurred while shortening your URL. Please try again."
        )

# ============ IMAGE CONVERTER ============

async def convert_image(update: Update, file_id: str, target_format: str) -> None:
    """Convert an image to the target format."""
    try:
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🔄 Converting your image to {target_format.upper()}... Please wait."
        )

        # Get the file from Telegram
        file = await update.message.bot.get_file(file_id)
        image_bytes = await file.download_as_bytearray()

        # Open and convert image
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Convert to RGB if necessary (for JPEG support)
            if target_format.lower() in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Save to bytes
            output = io.BytesIO()
            if target_format.lower() == 'jpg':
                target_format = 'JPEG'
            img.save(output, format=target_format.upper())
            output.seek(0)

        # Send converted image back
        await update.message.reply_photo(
            photo=output,
            caption=f"✅ **Image Converted Successfully!**\n\n"
                    f"📁 Format: {target_format.upper()}\n"
                    f"📐 Size: {img.size[0]} x {img.size[1]} pixels\n\n"
                    f"🔄 Use /convert to convert another image."
        )

        # Delete processing message
        await processing_msg.delete()

    except Exception as e:
        logger.error(f"Error converting image: {e}")
        await update.message.reply_text(
            "❌ Failed to convert the image. Please make sure it's a valid image file and try again."
        )

# ============ AI IMAGE GENERATOR ============

async def generate_ai_image(update: Update, prompt: str) -> None:
    """Generate an image using AI (placeholder - can be integrated with various APIs)."""
    try:
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🎨 Generating your AI artwork...\n\n"
            f"📝 Prompt: \"{prompt[:100]}\"\n"
            f"⏳ This may take up to 30 seconds..."
        )

        # Option 1: Using Gemini API (if available)
        if GEMINI_API_KEY:
            # You can integrate with Google's Gemini Pro Vision here
            # For now, we'll use a placeholder
            pass

        # Option 2: Using Pollinations.ai (free, no API key needed)
        response = requests.get(
            f'https://image.pollinations.ai/prompt/{prompt}',
            params={
                'width': 1024,
                'height': 1024,
                'nologo': 'true'
            },
            timeout=30
        )

        if response.status_code == 200:
            image_data = io.BytesIO(response.content)
            await update.message.reply_photo(
                photo=image_data,
                caption=f"🎨 **AI Image Generated!**\n\n"
                        f"📝 Prompt: \"{prompt}\"\n"
                        f"🤖 Generated by Pollinations.ai\n\n"
                        f"✨ Use /generate to create more artwork!"
            )
        else:
            # Fallback: Generate a simple image with caption
            await update.message.reply_text(
                f"🎨 **AI Image Generation**\n\n"
                f"📝 Prompt: \"{prompt}\"\n\n"
                f"🔜 Full AI image generation with high-quality models coming soon!\n"
                f"📧 Contact the developer to integrate premium AI models."
            )

        # Delete processing message
        await processing_msg.delete()

    except Exception as e:
        logger.error(f"Error generating AI image: {e}")
        await update.message.reply_text(
            "❌ Failed to generate AI image. Please try again later.\n\n"
            "💡 Tip: Try a shorter or more specific prompt."
        )

# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with a menu when /start is issued."""
    user = update.effective_user
    welcome_message = (
        f"🎨 **Welcome to ArtSpark8Bot!**\n\n"
        f"Hello {user.first_name}! I'm your creative AI assistant. Here's what I can do:\n\n"
        "🔗 **/shorten** - Shorten long URLs instantly\n"
        "🖼️ **/convert** - Convert images between formats\n"
        "🎨 **/generate** - Generate images with AI\n"
        "🆘 **/help** - Show this menu\n\n"
        "Just send me a link and I'll shorten it for you!"
    )

    # Create inline keyboard menu
    keyboard = [
        [
            InlineKeyboardButton("🔗 Shorten URL", callback_data='shorten'),
            InlineKeyboardButton("🖼️ Convert Image", callback_data='convert')
        ],
        [
            InlineKeyboardButton("🎨 Generate Art", callback_data='generate'),
            InlineKeyboardButton("🆘 Help", callback_data='help')
        ],
        [
            InlineKeyboardButton("📢 About", callback_data='about')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    help_text = (
        "🆘 **ArtSpark8Bot Help Menu**\n\n"
        "**Commands:**\n"
        "/start - Show welcome menu\n"
        "/shorten - Shorten a URL\n"
        "/convert - Convert images between formats\n"
        "/generate - Generate AI images from text prompts\n"
        "/help - Show this help menu\n\n"
        "**How to use:**\n"
        "1️⃣ Click a button or type a command\n"
        "2️⃣ Follow the instructions\n"
        "3️⃣ Get your result instantly!\n\n"
        "**Supported image formats:**\n"
        "PNG, JPG, JPEG, WebP, HEIC, and more!\n\n"
        "💡 Tip: You can also click the buttons below!"
    )
    await update.message.reply_text(help_text)

async def shorten_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Instruct the user on how to shorten a URL."""
    await update.message.reply_text(
        "🔗 **URL Shortener**\n\n"
        "Please send me the URL you want to shorten.\n\n"
        "📝 **Example:** `https://www.example.com/very-long-url`\n\n"
        "✅ Valid URLs start with `http://` or `https://`"
    )
    # Set flag for URL shortening mode
    user_id = update.effective_user.id
    user_sessions[user_id] = {'mode': 'awaiting_url'}

async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show image conversion options."""
    keyboard = [
        [
            InlineKeyboardButton("PNG → JPG", callback_data='convert_png_jpg'),
            InlineKeyboardButton("JPG → PNG", callback_data='convert_jpg_png')
        ],
        [
            InlineKeyboardButton("WebP → PNG", callback_data='convert_webp_png'),
            InlineKeyboardButton("HEIC → JPG", callback_data='convert_heic_jpg')
        ],
        [
            InlineKeyboardButton("🔄 All Formats", callback_data='convert_all'),
            InlineKeyboardButton("↩️ Back to Menu", callback_data='back_to_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🖼️ **Image Converter**\n\n"
        "Select the conversion type you need:\n\n"
        "📤 Then upload the image you want to convert.\n"
        "✅ Supports multiple formats!\n\n"
        "⚠️ **Note:** The image will be sent back to you in the selected format.",
        reply_markup=reply_markup
    )

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show AI image generation options."""
    keyboard = [
        [
            InlineKeyboardButton("🎨 Text to Image", callback_data='generate_text'),
            InlineKeyboardButton("✨ Creative Art", callback_data='generate_creative')
        ],
        [
            InlineKeyboardButton("🖼️ Upscale Image", callback_data='generate_upscale'),
            InlineKeyboardButton("↩️ Back to Menu", callback_data='back_to_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎨 **AI Image Generator**\n\n"
        "Create amazing images using AI!\n\n"
        "🔮 **Features:**\n"
        "• Generate images from text descriptions\n"
        "• Create creative digital artwork\n"
        "• Upscale and enhance images\n\n"
        "🚀 **How to use:**\n"
        "1. Select an option below\n"
        "2. Describe what you want to generate\n"
        "3. Wait a few seconds for the AI to create your image\n\n"
        "💡 *Get creative and describe your vision!*",
        reply_markup=keyboard
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send about information."""
    about_text = (
        "📢 **About ArtSpark8Bot**\n\n"
        "🤖 **Version:** 2.0.0\n"
        "👨‍💻 **Developer:** ArtSpark Team\n"
        "🏗️ **Built with:** Python + Telegram Bot API\n"
        "🚀 **Deployed on:** Railway\n\n"
        "**Features:**\n"
        "✅ URL Shortener\n"
        "✅ Image Converter\n"
        "✅ AI Image Generation\n"
        "✅ Fast & Reliable\n\n"
        "📧 **Support:** Contact @ArtSparkSupport\n"
        "⭐ **GitHub:** github.com/artspark/ArtSpark8Bot\n\n"
        "Made with ❤️ for the Telegram community"
    )
    await update.message.reply_text(about_text)

# ============ MESSAGE HANDLER ============

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages."""
    user_id = update.effective_user.id
    message_text = update.message.text
    photo = update.message.photo

    # Check if user is in URL-shortening mode
    if user_id in user_sessions and user_sessions[user_id].get('mode') == 'awaiting_url':
        if message_text and message_text.startswith(('http://', 'https://')):
            await shorten_url(update, message_text)
            user_sessions[user_id] = {}  # Reset mode
        else:
            await update.message.reply_text(
                "❌ That doesn't look like a valid URL.\n\n"
                "Please send a link starting with `http://` or `https://`"
            )
        return

    # Check if user is in image upload mode
    if user_id in user_sessions and user_sessions[user_id].get('mode') == 'awaiting_image':
        if photo:
            # Get the highest resolution photo
            file_id = photo[-1].file_id
            target_format = user_sessions[user_id].get('target_format', 'PNG')
            await convert_image(update, file_id, target_format)
            user_sessions[user_id] = {}  # Reset mode
        else:
            await update.message.reply_text(
                "❌ Please upload an image to convert.\n\n"
                "📤 Send a photo or document with an image."
            )
        return

    # Check if user is in AI generation mode
    if user_id in user_sessions and user_sessions[user_id].get('mode') == 'awaiting_prompt':
        if message_text:
            await generate_ai_image(update, message_text)
            user_sessions[user_id] = {}  # Reset mode
        else:
            await update.message.reply_text(
                "❌ Please send a text description of the image you want to generate."
            )
        return

    # Default response for unknown messages
    await update.message.reply_text(
        "🤔 I'm not sure what you want me to do with that.\n\n"
        "Try using the **/start** command to see all available features!\n"
        "Or click the menu buttons below."
    )

# ============ BUTTON CLICK HANDLER ============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button clicks."""
    query = update.callback_query
    await query.answer()  # Acknowledge the click

    user_id = update.effective_user.id
    data = query.data

    if data == 'shorten':
        await query.edit_message_text(
            "🔗 **URL Shortener**\n\n"
            "Please send me the URL you want to shorten.\n\n"
            "📝 **Example:** `https://www.example.com/very-long-url`\n\n"
            "✅ I'll send you back a short link instantly!"
        )
        user_sessions[user_id] = {'mode': 'awaiting_url'}

    elif data == 'convert':
        keyboard = [
            [
                InlineKeyboardButton("PNG → JPG", callback_data='convert_png_jpg'),
                InlineKeyboardButton("JPG → PNG", callback_data='convert_jpg_png')
            ],
            [
                InlineKeyboardButton("WebP → PNG", callback_data='convert_webp_png'),
                InlineKeyboardButton("HEIC → JPG", callback_data='convert_heic_jpg')
            ],
            [
                InlineKeyboardButton("🔄 All Formats", callback_data='convert_all'),
                InlineKeyboardButton("↩️ Back to Menu", callback_data='back_to_menu')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🖼️ **Image Converter**\n\n"
            "Select a conversion format above, then upload your image:\n\n"
            "Supported formats: PNG, JPG, JPEG, WebP, HEIC\n"
            "📤 Just send me a photo or image file!",
            reply_markup=reply_markup
        )

    elif data == 'generate':
        keyboard = [
            [
                InlineKeyboardButton("🎨 Text to Image", callback_data='generate_text'),
                InlineKeyboardButton("✨ Creative Art", callback_data='generate_creative')
            ],
            [
                InlineKeyboardButton("🖼️ Upscale Image", callback_data='generate_upscale'),
                InlineKeyboardButton("↩️ Back to Menu", callback_data='back_to_menu')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🎨 **AI Image Generator**\n\n"
            "Choose your option above to start creating!\n\n"
            "💡 **Tips for best results:**\n"
            "• Be descriptive in your prompt\n"
            "• Mention style, colors, and mood\n"
            "• Keep it under 100 characters for speed\n\n"
            "🚀 **Let's get creative!**",
            reply_markup=reply_markup
        )

    elif data in ['generate_text', 'generate_creative']:
        await query.edit_message_text(
            "🎨 **AI Image Generation**\n\n"
            "Please describe what you want me to create:\n\n"
            "📝 **Example prompts:**\n"
            "• \"A serene sunset over mountains with golden clouds\"\n"
            "• \"A cyberpunk cityscape with neon lights\"\n"
            "• \"A cute cat wearing a wizard hat, digital art\"\n\n"
            "✨ Be creative and specific!"
        )
        user_sessions[user_id] = {'mode': 'awaiting_prompt'}

    elif data == 'generate_upscale':
        await query.edit_message_text(
            "🖼️ **Upscale Image**\n\n"
            "Send me an image and I'll enhance and upscale it!\n\n"
            "✨ **Features:**\n"
            "• 2x to 4x upscaling\n"
            "• Quality enhancement\n"
            "• Noise reduction\n\n"
            "📤 Just upload the image you want to upscale!"
        )
        user_sessions[user_id] = {'mode': 'awaiting_upscale'}

    elif data.startswith('convert_'):
        # Parse the conversion format
        format_parts = data.split('_')
        if len(format_parts) >= 3:
            source = format_parts[1].upper()
            target = format_parts[2].upper()
            if target == 'JPG':
                target = 'JPEG'

            await query.edit_message_text(
                f"🔄 **Image Conversion:** {source} → {target}\n\n"
                f"Please upload the image you want to convert.\n\n"
                f"📤 Send a photo or image file.\n"
                f"🖼️ I'll convert it to {target} format."
            )
            user_sessions[user_id] = {
                'mode': 'awaiting_image',
                'target_format': target,
                'source_format': source
            }

    elif data == 'convert_all':
        await query.edit_message_text(
            "🔄 **All Format Converter**\n\n"
            "Send me any image and I'll convert it to your desired format!\n\n"
            "📤 Upload your image now\n"
            "💬 Then tell me the format you want\n\n"
            "Supported: PNG, JPG, WebP, HEIC"
        )
        user_sessions[user_id] = {'mode': 'awaiting_all_convert'}

    elif data == 'help':
        help_text = (
            "🆘 **ArtSpark8Bot Help**\n\n"
            "**Commands:**\n"
            "/start - Show main menu\n"
            "/shorten - Shorten a URL\n"
            "/convert - Convert images\n"
            "/generate - Generate AI images\n"
            "/help - Show this menu\n"
            "/about - About this bot\n\n"
            "**Quick Start:**\n"
            "1. Click a button below\n"
            "2. Follow the instructions\n"
            "3. Get your result!\n\n"
            "❓ Need help? Contact @ArtSparkSupport"
        )
        await query.edit_message_text(help_text)

    elif data == 'about':
        about_text = (
            "📢 **About ArtSpark8Bot**\n\n"
            "🤖 Version: 2.0.0\n"
            "👨‍💻 Developer: ArtSpark Team\n"
            "🚀 Deployed on Railway\n\n"
            "**Features:**\n"
            "✅ URL Shortener\n"
            "✅ Image Converter\n"
            "✅ AI Image Generation\n"
            "✅ Fast & Reliable\n\n"
            "Made with ❤️ for the Telegram community"
        )
        await query.edit_message_text(about_text)

    elif data == 'back_to_menu':
        keyboard = [
            [
                InlineKeyboardButton("🔗 Shorten URL", callback_data='shorten'),
                InlineKeyboardButton("🖼️ Convert Image", callback_data='convert')
            ],
            [
                InlineKeyboardButton("🎨 Generate Art", callback_data='generate'),
                InlineKeyboardButton("🆘 Help", callback_data='help')
            ],
            [
                InlineKeyboardButton("📢 About", callback_data='about')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🎨 **Welcome to ArtSpark8Bot!**\n\n"
            "Choose an option below to get started:",
            reply_markup=reply_markup
        )

# ============ ERROR HANDLER ============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An unexpected error occurred. Please try again later or contact support."
        )

# ============ MAIN FUNCTION ============

def main() -> None:
    """Start the bot."""
    try:
        # Create the Application
        application = Application.builder().token(TOKEN).build()

        # Register command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("shorten", shorten_command))
        application.add_handler(CommandHandler("convert", convert_command))
        application.add_handler(CommandHandler("generate", generate_command))
        application.add_handler(CommandHandler("about", about_command))

        # Register message handler for text and photos
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handle_message
        ))
        application.add_handler(MessageHandler(
            filters.PHOTO | filters.Document.IMAGE,
            handle_message
        ))

        # Register button callback handler
        application.add_handler(CallbackQueryHandler(button_callback))

        # Register error handler
        application.add_error_handler(error_handler)

        # Start the bot (polling mode - works with Railway)
        logger.info("🚀 ArtSpark8Bot started successfully!")
        logger.info(f"🤖 Bot @{os.environ.get('BOT_USERNAME', 'ArtSpark8Bot')} is running")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    main()
