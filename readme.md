# 🔮 Rosary Bot

Automated daily meditation summaries from the "Rosary in a Year" podcast, delivered to Telegram.

## 📖 Overview

Rosary Bot automatically downloads, transcribes, and summarizes daily episodes from the "Rosary in a Year" podcast by Fr. Mark-Mary Ames, CFR. Each morning, you'll receive a concise, hand-copyable summary of the meditation content directly in Telegram.

## ✨ Features

- **📡 Automatic RSS monitoring** - Fetches latest episodes daily
- **🎤 Audio transcription** - Uses OpenAI Whisper API or local Whisper
- **✂️ Smart content extraction** - Skips repetitive intros, focuses on meditation
- **🤖 AI summarization** - GPT-4o Mini creates 8 bullet points with key insights
- **🎨 Artwork detection** - Identifies and includes artwork references
- **📱 Telegram delivery** - Sends formatted summaries to your phone
- **🧹 Automatic cleanup** - Removes files after successful delivery
- **⏰ Scheduled execution** - Runs daily via cron at 6:00 AM

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token
- OpenAI API Key
- macOS with Homebrew (for ffmpeg)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd rosary-bot
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install ffmpeg (for local Whisper)**

   ```bash
   brew install ffmpeg
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Configure Telegram bot**

   - Message @BotFather on Telegram
   - Create a new bot and get the token
   - Start a chat with your bot
   - Get your user ID from @userinfobot

6. **Test the bot**
   ```bash
   python main.py
   ```

### Environment Variables

Create a `.env` file with:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_USER_ID=your_telegram_user_id
OPENAI_API_KEY=your_openai_api_key
```

## 📁 Project Structure

```
rosary-bot/
├── main.py                 # Main orchestration script
├── config.py              # Configuration management
├── rss_handler.py         # RSS feed handling
├── audio_processor.py     # Audio download & transcription
├── summarizers.py         # AI summarization methods
├── telegram_bot.py        # Telegram messaging
├── cleanup.py             # File cleanup management
├── run_rosary_bot.sh      # Cron wrapper script
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── .env                   # Environment variables (create this)
└── downloads/             # Temporary files (auto-created)
```

## ⚙️ Configuration

### Basic Settings (config.py)

```python
# File Settings
DOWNLOAD_DIR = "downloads"
SAVE_TRANSCRIPTS = True
SAVE_SUMMARIES = True
CLEANUP_FILES = True        # Delete files after successful delivery

# OpenAI Settings
OPENAI_MODELS = ["gpt-4o-mini"]  # Cost-effective model
WHISPER_MODEL = "base"           # Local Whisper model size

# RSS Settings
RSS_URL = "https://feeds.fireside.fm/rosaryinayear/rss"
SKIP_INTRO_EPISODE = True   # Skip episode 0 (intro)
```

## 🔄 Scheduling

### Set up daily cron job

1. **Edit crontab**

   ```bash
   EDITOR=nano crontab -e
   ```

2. **Add these lines:**

   ```bash
   PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin
   0 6 * * * /path/to/your/rosary-bot/run_rosary_bot.sh
   ```

3. **Verify crontab**
   ```bash
   crontab -l
   ```

### Remove after 20 days

```bash
crontab -e
# Delete or comment out the rosary bot line
```

## 📱 Output Format

Each summary includes:

```markdown
🔮 Day 169- The Faithful "Yes"
📅 Wed, 18 Jun 2025 03:15:00 -0400

🙏 Meditation Summary

• Artwork: The Annunciation by Fra Angelico
• Mary's response to Gabriel shows perfect trust in God's plan
• The Incarnation begins with Mary's faithful "yes" to divine invitation
• We are called to imitate Mary's openness to God's will
• Prayer helps us discern and respond to God's call with faith
• The angel's reverent approach teaches us proper attitude in prayer
• Mary's humility demonstrates how to receive God's grace
• Trust in divine providence brings peace in uncertainty
• Each "yes" to God opens new possibilities for grace

_Simple summary for hand copying and reflection_
```

## 💰 Cost Analysis

### OpenAI API Usage (Recommended)

- **Transcription**: ~$0.006 per episode (Whisper API)
- **Summarization**: ~$0.0008 per episode (GPT-4o Mini)
- **Total per episode**: ~$0.007 (less than 1 cent)
- **20 days**: ~$0.14 (14 cents)
- **1 year**: ~$2.55

### Local Processing (Free Alternative)

- **Transcription**: Free (local Whisper + ffmpeg)
- **Summarization**: ~$0.0008 per episode (GPT-4o Mini)
- **Total per episode**: ~$0.0008
- **20 days**: ~$0.016 (1.6 cents)

## 🔧 Troubleshooting

### Common Issues

**FFmpeg not found in cron**

- Ensure PATH is set in crontab
- Verify ffmpeg location: `which ffmpeg`

**Telegram "chat not found"**

- Start a conversation with your bot first
- Send `/start` to activate the bot

**OpenAI quota exceeded**

- Check billing at https://platform.openai.com/account/billing
- Add credits or wait for quota reset

**RSS feed issues**

- Check internet connectivity
- Verify RSS URL is accessible

### Logs

Check logs for debugging:

```bash
tail -f logs/rosary_bot.log
```

## 🧪 Testing

### Manual Testing

```bash
# Test full workflow
python main.py

# Test individual components
python -c "from rss_handler import get_latest_episode; print(get_latest_episode())"
python -c "from telegram_bot import test_telegram_connection; test_telegram_connection()"
```

### Cron Testing

```bash
# Test wrapper script
./run_rosary_bot.sh

# Test with cron environment
env -i PATH=/usr/bin:/bin ./run_rosary_bot.sh
```

## 🔄 Maintenance

### Cleanup Old Files

```bash
python -c "from cleanup import cleanup_old_files; cleanup_old_files(days_old=7)"
```

### Storage Information

```bash
python -c "from cleanup import get_storage_info; print(get_storage_info())"
```

### Update Dependencies

```bash
pip install -r requirements.txt --upgrade
```

## 📜 License

This project is for personal use. Please respect the podcast's copyright and terms of service.

## 🙏 Acknowledgments

- **Fr. Mark-Mary Ames, CFR** - Host of "Rosary in a Year" podcast
- **Ascension Press** - Publisher of the podcast
- **OpenAI** - Whisper and GPT models
- **Telegram** - Messaging platform

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review logs in `logs/rosary_bot.log`
3. Verify configuration in `config.py`
4. Test individual components

---

_Built with ❤️ for daily spiritual growth and meditation_
