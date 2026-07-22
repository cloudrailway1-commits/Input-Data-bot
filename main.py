from telegram.ext import Application
from config import BOT_TOKEN
from conversation import conversation_handler


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Register Conversation Handler
    app.add_handler(conversation_handler)

    print("=" * 50)
    print("     Fieldwork Material Bot Started")
    print("=" * 50)
    print("Bot is running...")
    print("Press CTRL + C to stop.\n")

    app.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()