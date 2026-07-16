# Quick Start Guide - Windows Local Hosting

## One-Click Setup

### Option 1: Batch File (Easiest)
1. Double-click `start.bat`
2. The script will automatically:
   - Check Python installation
   - Create virtual environment
   - Install dependencies
   - Start the bot

### Option 2: PowerShell Script (Advanced)
1. Right-click `start.ps1` → "Run with PowerShell"
2. If you get an execution policy error, run this in PowerShell as Administrator:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## Prerequisites

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation!

2. **Bot Token**
   - Get from [@BotFather](https://t.me/BotFather) on Telegram
   - Add to `.env` file (created automatically from `.env.example`)

## First Time Setup

1. Run `start.bat` or `start.ps1`
2. When prompted, edit the `.env` file with your bot token:
   ```
   TOKEN=your_bot_token_here
   OWNER_ID=your_telegram_user_id
   ```
3. Run the script again to start the bot

## Configuration

Edit the `.env` file to configure:
- Bot token and owner ID (required)
- Database settings (PostgreSQL/Redis)
- API keys for various services
- Other bot settings

See `.env.example` for all available options.

## Troubleshooting

### "Python is not recognized"
- Install Python and make sure "Add Python to PATH" is checked
- Or manually add Python to your system PATH

### "Failed to install dependencies"
- Check your internet connection
- Try running: `pip install --upgrade pip` manually
- Some packages may require Visual C++ Build Tools on Windows

### "Module not found" errors
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Bot doesn't start
- Check `.env` file has correct TOKEN and OWNER_ID
- Verify database connection if using PostgreSQL
- Check logs for specific error messages

## Stopping the Bot

Press `Ctrl+C` in the terminal window to stop the bot gracefully.

## Advanced Usage

### Manual Setup
```batch
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run bot
python -m Cutiepii_Robot
```

### Running in Background
Use Windows Task Scheduler or create a service to run the bot in the background.

## Support

For issues and questions:
- Check the main README.md
- Review DOCUMENTATION_INDEX.md
- Check error logs in the terminal
