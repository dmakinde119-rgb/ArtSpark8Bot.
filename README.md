# 🎨 ArtSpark8Bot

A powerful multi-functional Telegram bot with URL shortening, AI image generation, and image conversion.

## ✨ Features

### 🔗 URL Shortener
- Shorten long URLs instantly
- Multiple fallback services (is.gd, TinyURL)
- Custom short codes
- No API key required

### 🎨 AI Image Generator
- Generate images from text prompts
- Multiple generation modes
- Powered by Pollinations.ai
- Free and unlimited

### 🖼️ Image Converter (Coming Soon)
- Convert between formats
- PNG, JPG, WebP, HEIC support
- High quality output

## 🚀 Quick Deploy

### 1. Create Bot on Telegram
- Open Telegram
- Search for `@BotFather`
- Send `/newbot`
- Name: `ArtSpark8Bot`
- Username: `ArtSpark8Bot`
- Copy the token

### 2. Deploy on Railway
- Go to [Railway.app](https://railway.app)
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose your repository

### 3. Set Environment Variables
| Key | Value |
|-----|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token |
| `PYTHON_VERSION` | `3.11.0` |

### 4. Deploy!
Railway will automatically deploy your bot.

## 📋 Commands

- `/start` - Show main menu
- `/help` - Show help
- `/shorten` - Shorten a URL
- `/generate` - Generate AI images
- `/convert` - Convert images
- `/about` - About the bot
- `/cancel` - Cancel current operation

## 🛠️ Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/ArtSpark8Bot.git
cd ArtSpark8Bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env

# Run bot
python bot.py
