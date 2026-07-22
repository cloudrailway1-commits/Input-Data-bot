from telegram import (
    Update,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import (
    add_rfc,
    rfc_exists,
    get_available_rfcs,
    find_rfc,
    update_row_answers,
)

from questions import QUESTIONS, TOTAL_QUESTIONS

from keyboards import (
    ROLE_KEYBOARD,
    FINISH_KEYBOARD,
)

# ==========================================================
# Conversation States
# ==========================================================

ROLE, NAME, RFC, QUESTION, RESTART = range(5)

# ==========================================================
# /start
# ==========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "📦 *Fieldwork Material Bot*\n\n"
        "Welcome.\n\n"
        "Please select your role.",
        parse_mode="Markdown",
        reply_markup=ROLE_KEYBOARD,
    )

    return ROLE


# ==========================================================
# Choose Role
# ==========================================================

async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = update.message.text.strip()

    if role not in [
        "🏭 Warehouse Engineer",
        "🛠 Technician",
    ]:
        await update.message.reply_text(
            "Please select one of the available buttons.",
            reply_markup=ROLE_KEYBOARD,
        )
        return ROLE

    context.user_data["role"] = role

    # Prompt user for name based on selected role
    if role == "🏭 Warehouse Engineer":
        prompt = "🏢 Enter Warehouse / Engineer Name:"
    else:
        prompt = "👤 Enter Technician Name:"

    await update.message.reply_text(
        prompt,
        reply_markup=ReplyKeyboardRemove(),
    )

    return NAME


# ==========================================================
# Enter Name
# ==========================================================

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "Name cannot be empty.\nPlease enter your name."
        )
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text(
        "📄 Enter RFC ID:"
    )

    return RFC


# ==========================================================
# Enter RFC
# ==========================================================

async def ask_rfc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rfc = update.message.text.strip().upper()
    role = context.user_data["role"]

    # ------------------------------------------
    # Warehouse Engineer
    # ------------------------------------------
    if role == "🏭 Warehouse Engineer":
        if rfc_exists(rfc):
            await update.message.reply_text(
                "❌ RFC already exists.\n\nPlease enter another RFC."
            )
            return RFC

        add_rfc(
            rfc,
            context.user_data["name"],
        )

        await update.message.reply_text(
            "✅ RFC successfully registered.\n\n"
            "What would you like to do next?",
            reply_markup=FINISH_KEYBOARD,
        )

        context.user_data.clear()
        return RESTART

    # ------------------------------------------
    # Technician
    # ------------------------------------------
    if not rfc_exists(rfc):
        # Fetch available RFCs & Warehouses to show the technician
        available_list = get_available_rfcs()

        if available_list:
            formatted_list = "\n".join(
                [f"• *{item[0]}* — Warehouse: {item[1]}" for item in available_list]
            )
            msg = (
                f"❌ RFC *{rfc}* not found.\n\n"
                f"📋 *Available RFCs & Warehouses:*\n"
                f"{formatted_list}\n\n"
                f"Please enter a valid RFC ID:"
            )
        else:
            msg = (
                f"❌ RFC *{rfc}* not found, and no active RFCs are currently available.\n\n"
                f"Please ask the Warehouse Engineer to register it first."
            )

        await update.message.reply_text(msg, parse_mode="Markdown")
        return RFC

    # RFC exists -> proceed to material questions
    context.user_data["rfc"] = rfc
    context.user_data["answers"] = []
    context.user_data["question_index"] = 0

    question = QUESTIONS[0][0]

    await update.message.reply_text(
        f"✅ RFC ID *{rfc}* verified.\n\n"
        f"Question 1/{TOTAL_QUESTIONS}\n\n"
        f"{question}:",
        parse_mode="Markdown"
    )

    return QUESTION


# ==========================================================
# Ask Material Questions
# ==========================================================

async def ask_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()

    context.user_data["answers"].append(answer)
    context.user_data["question_index"] += 1

    index = context.user_data["question_index"]

    if index < TOTAL_QUESTIONS:
        question = QUESTIONS[index][0]

        await update.message.reply_text(
            f"Question {index + 1}/{TOTAL_QUESTIONS}\n\n"
            f"{question}:"
        )
        return QUESTION

    return await finish(update, context)


# ==========================================================
# Finish Report
# ==========================================================

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        row = find_rfc(context.user_data["rfc"])

        if row is None:
            await update.message.reply_text(
                "❌ RFC no longer exists.",
                reply_markup=FINISH_KEYBOARD,
            )
            context.user_data.clear()
            return RESTART

        update_row_answers(
            row=row,
            technician=context.user_data["name"],
            answers=context.user_data["answers"],
        )

        await update.message.reply_text(
            "✅ Report submitted successfully!\n\n"
            "Choose your next action.",
            reply_markup=FINISH_KEYBOARD,
        )

        context.user_data.clear()
        return RESTART

    except Exception as e:
        await update.message.reply_text(
            f"❌ Failed to save report.\n\n{e}",
            reply_markup=FINISH_KEYBOARD,
        )
        context.user_data.clear()
        return RESTART


# ==========================================================
# Restart Menu
# ==========================================================

async def restart_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice == "🔄 New Report":
        context.user_data.clear()
        await update.message.reply_text(
            "📦 *Fieldwork Material Bot*\n\n"
            "Please choose your role.",
            parse_mode="Markdown",
            reply_markup=ROLE_KEYBOARD,
        )
        return ROLE

    if choice == "❌ Exit":
        context.user_data.clear()
        await update.message.reply_text(
            "👋 Thank you for using Fieldwork Material Bot.\n\n"
            "Type /start whenever you want to submit another report.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Please use one of the buttons below.",
        reply_markup=FINISH_KEYBOARD,
    )
    return RESTART


# ==========================================================
# Cancel
# ==========================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Operation cancelled.\n\n"
        "Type /start to begin again.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ==========================================================
# Conversation Handler
# ==========================================================

conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
    ],
    states={
        ROLE: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                choose_role,
            )
        ],
        NAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                ask_name,
            )
        ],
        RFC: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                ask_rfc,
            )
        ],
        QUESTION: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                ask_questions,
            )
        ],
        RESTART: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                restart_menu,
            )
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
    allow_reentry=True,
)
