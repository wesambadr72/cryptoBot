# Crypto Assistant Bot 🚀

A Telegram bot built with Python to help users track cryptocurrency news, set price alerts, manage portfolios, and simulate trades.

## Features 🌟

- `/start` - Start the bot and see available commands
- `/help` - Display help information
- `/news` - Get the latest cryptocurrency news
- `/alert` - Set up price alerts for specific cryptocurrencies

## Prerequisites 📋

Before running the bot, make sure you have:

- Python 3.8 or higher installed
- A Telegram account
- A bot token from [@BotFather](https://t.me/BotFather)

## Installation 🔧

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cryptoBot.git
cd cryptoBot
```

2. Create a virtual environment (recommended):
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

3. Install required packages:
```bash
pip install python-telegram-bot python-dotenv
```

4. Set up your environment variables:
   - Create a `.env` file in the project root
   - Add your Telegram bot token:
     ```
     TELEGRAM_TOKEN=your_bot_token_here
     ```

## Running the Bot 🚀

1. Make sure your virtual environment is activated
2. Run the bot:
```bash
python bot.py
```

## Project Structure 📁

```
cryptoBot/
├── .env                # Environment variables (not in git)
├── .gitignore         # Git ignore file
├── LICENSE            # MIT License
├── README.md          # This file
└── bot.py            # Main bot code
```

## Contributing 🤝

Feel free to fork this project and submit pull requests. You can also open issues for bugs or feature requests.

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security Notes 🔒

- Never commit your `.env` file or share your bot token
- The bot currently runs in simulation mode and doesn't handle real cryptocurrency transactions
- Always verify transactions and double-check financial information

## Future Enhancements 🎯

- add volume and liquidity to alerts messages


## Support 💬

If you need help or have questions, you can:
- Open an issue in this repository
- Contact the developer through Telegram
- Check the Telegram Bot API documentation
