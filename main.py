import logging
from telegram.ext import ApplicationBuilder

# Import conversation handler from your handlers file
# (Rename 'conversation' to whatever your handlers filename is)
from conversation import conversation_handler  

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set your Bot Token directly or load from environment variables
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"


def main():
    """Initializes and runs the Telegram Bot."""
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("Please replace BOT_TOKEN with your actual Bot Token.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register the conversation workflow handler
    app.add_handler(conversation_handler)

    print("🤖 Fieldwork Material Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
