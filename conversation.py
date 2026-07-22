import logging
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
    get_all_rfcs_with_warehouse,
    find_rfc,
    update_row_answers,
)

from questions import QUESTIONS, TOTAL_QUESTIONS

from keyboards import (
    ROLE_KEYBOARD,
    FINISH_KEYBOARD,
    AFTER_REGISTER_KEYBOARD,
    AFTER_REPORT_KEYBOARD,
    SAME_DIFFERENT_KEYBOARD,
    SAME_RFC_KEYBOARD,
    RFC_NOT_FOUND_KEYBOARD, 
)

logger = logging.getLogger(__name__)

# ==========================================================
# Conversation States
# ==========================================================

ROLE, NAME, RFC, QUESTION, RESTART, AFTER_REGISTER, AFTER_REPORT, RFC_NOT_FOUND = range(8)

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

    if role == "🏭 Warehouse Engineer":
        prompt = "🏢 Enter Warehouse Name:"
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
    role = context.user_data.get("role", "")

    # For Technician: Show available list before prompting for RFC ID
    if role == "🛠 Technician":
        available_list = get_available_rfcs()

        if available_list:
            formatted_list = "\n".join(
                [f"• *{item[0]}* — Warehouse: {item[1]}" for item in available_list]
            )
            msg = (
                f"📋 *Available RFCs & Warehouses:*\n\n"
                f"{formatted_list}\n\n"
                f"📄 Please enter the RFC ID you want to work on:"
            )
        else:
            msg = (
                "⚠️ No active RFCs are currently available.\n\n"
                "Please ask the Warehouse Engineer to register an RFC first."
            )
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        return RFC

    # For Warehouse Engineer
    await update.message.reply_text("📄 Enter new RFC ID to register:")
    return RFC


# ==========================================================
# Enter RFC
# ==========================================================

async def ask_rfc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rfc = update.message.text.strip().upper()
        role = context.user_data.get("role", "")

        # Warehouse Engineer Flow
        if role == "🏭 Warehouse Engineer":
            if rfc_exists(rfc):
                await update.message.reply_text(
                    "❌ RFC already exists.\n\nPlease enter another RFC."
                )
                return RFC

            add_rfc(
                rfc,
                context.user_data.get("name", "Unknown"),
            )

            all_rfcs = get_all_rfcs_with_warehouse()
            formatted_list = "\n".join(
                [f"• *{item[0]}* — Warehouse: {item[1]}" for item in all_rfcs]
            )

            await update.message.reply_text(
                f"✅ RFC *{rfc}* successfully registered!\n\n"
                f"📋 *Current Registered RFCs & Warehouses:*\n"
                f"{formatted_list}\n\n"
                f"Choose an option below:",
                parse_mode="Markdown",
                reply_markup=AFTER_REGISTER_KEYBOARD,
            )

            return AFTER_REGISTER

        # Technician Flow
        if not rfc_exists(rfc):
            await update.message.reply_text(
                f"❌ RFC *{rfc}* not found in the sheet.\n\n"
                "Please choose an option below or type another RFC ID directly:",
                parse_mode="Markdown",
                reply_markup=RFC_NOT_FOUND_KEYBOARD,
            )
            return RFC_NOT_FOUND

        context.user_data["rfc"] = rfc
        context.user_data["answers"] = []
        context.user_data["question_index"] = 0

        question = QUESTIONS[0][0]

        await update.message.reply_text(
            f"✅ RFC ID *{rfc}* verified.\n\n"
            f"Question 1/{TOTAL_QUESTIONS}\n\n"
            f"{question}:",
            parse_mode="Markdown",
        )

        return QUESTION

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")
        return RFC

# ==========================================================
# Handle RFC Not Found Options
# ==========================================================

async def handle_rfc_not_found(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "✍️ Try Another RFC":
        available_list = get_available_rfcs()
        if available_list:
            formatted_list = "\n".join(
                [f"• *{item[0]}* — Warehouse: {item[1]}" for item in available_list]
            )
            msg = f"📋 *Available RFCs & Warehouses:*\n\n{formatted_list}\n\n📄 Enter RFC ID:"
        else:
            msg = "📄 Please enter the RFC ID:"

        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return RFC

    if text == "🔄 Change Name":
        await update.message.reply_text(
            "👤 Enter Technician Name:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return NAME

    if text == "⬅️ Back to Main Menu":
        context.user_data.clear()
        await update.message.reply_text(
            "📦 *Fieldwork Material Bot*\n\nPlease select your role.",
            parse_mode="Markdown",
            reply_markup=ROLE_KEYBOARD,
        )
        return ROLE

    # If the user directly typed an RFC ID instead of clicking a button:
    context.user_data["typed_rfc"] = text
    return await ask_rfc(update, context)


# ==========================================================
# Handle Warehouse After-Register Options
# ==========================================================

async def handle_after_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice == "➕ Add More RFC":
        await update.message.reply_text(
            f"Current Warehouse Name: *{context.user_data.get('name')}*\n\n"
            "Do you want to use the same Warehouse name or a different one?",
            parse_mode="Markdown",
            reply_markup=SAME_DIFFERENT_KEYBOARD,
        )
        return AFTER_REGISTER

    if choice == "🔄 Use Same Name":
        await update.message.reply_text("📄 Enter new RFC ID to register:", reply_markup=ReplyKeyboardRemove())
        return RFC

    if choice == "✍️ Use Different Name":
        await update.message.reply_text("🏢 Enter Warehouse / Engineer Name:", reply_markup=ReplyKeyboardRemove())
        return NAME

    if choice == "⬅️ Back to Main Menu":
        context.user_data.clear()
        await update.message.reply_text(
            "📦 *Fieldwork Material Bot*\n\nPlease select your role.",
            parse_mode="Markdown",
            reply_markup=ROLE_KEYBOARD,
        )
        return ROLE

    await update.message.reply_text("Please use the buttons provided.", reply_markup=AFTER_REGISTER_KEYBOARD)
    return AFTER_REGISTER


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
        rfc = context.user_data.get("rfc")
        technician_name = context.user_data.get("name", "")
        answers = context.user_data.get("answers", [])

        row = find_rfc(rfc)

        if row is None:
            await update.message.reply_text("❌ RFC no longer exists.", reply_markup=FINISH_KEYBOARD)
            context.user_data.clear()
            return RESTART

        update_row_answers(
            row=row,
            technician=technician_name,
            answers=answers,
        )

        await update.message.reply_text(
            f"✅ Report submitted successfully for Technician *{technician_name}*!\n\n"
            f"Choose what to do next:",
            parse_mode="Markdown",
            reply_markup=AFTER_REPORT_KEYBOARD,
        )

        return AFTER_REPORT

    except Exception as e:
        await update.message.reply_text(f"❌ Failed to save report.\n\n{e}", reply_markup=FINISH_KEYBOARD)
        context.user_data.clear()
        return RESTART


# ==========================================================
# Handle Technician After-Report Options
# ==========================================================

async def handle_after_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice == "📋 Submit Another Report":
        await update.message.reply_text(
            f"Current RFC ID: *{context.user_data.get('rfc')}*\n\n"
            "Do you want to work on the same RFC or select a different one?",
            parse_mode="Markdown",
            reply_markup=SAME_RFC_KEYBOARD,
        )
        return AFTER_REPORT

    if choice == "📑 Use Same RFC":
        context.user_data["answers"] = []
        context.user_data["question_index"] = 0
        question = QUESTIONS[0][0]

        await update.message.reply_text(
            f"Question 1/{TOTAL_QUESTIONS}\n\n{question}:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return QUESTION

    if choice == "📄 Use Different RFC":
        available_list = get_available_rfcs()
        if available_list:
            formatted_list = "\n".join([f"• *{item[0]}* — Warehouse: {item[1]}" for item in available_list])
            msg = f"📋 *Available RFCs & Warehouses:*\n\n{formatted_list}\n\n📄 Enter RFC ID:"
        else:
            msg = "⚠️ No active RFCs available. Enter RFC ID manually:"

        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        return RFC

    if choice == "⬅️ Back to Main Menu":
        context.user_data.clear()
        await update.message.reply_text(
            "📦 *Fieldwork Material Bot*\n\nPlease select your role.",
            parse_mode="Markdown",
            reply_markup=ROLE_KEYBOARD,
        )
        return ROLE

    await update.message.reply_text("Please use the buttons provided.", reply_markup=AFTER_REPORT_KEYBOARD)
    return AFTER_REPORT


# ==========================================================
# Restart Menu
# ==========================================================

async def restart_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice == "🔄 New Report":
        context.user_data.clear()
        await update.message.reply_text(
            "📦 *Fieldwork Material Bot*\n\nPlease select your role.",
            parse_mode="Markdown",
            reply_markup=ROLE_KEYBOARD,
        )
        return ROLE

    if choice == "❌ Exit":
        context.user_data.clear()
        await update.message.reply_text(
            "👋 Thank you for using Fieldwork Material Bot.\n\nType /start whenever you want to submit another report.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    await update.message.reply_text("Please use one of the buttons below.", reply_markup=FINISH_KEYBOARD)
    return RESTART


# ==========================================================
# Cancel
# ==========================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Operation cancelled.\n\nType /start to begin again.",
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
        ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_role)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
        RFC: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_rfc)],
        QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_questions)],
        RESTART: [MessageHandler(filters.TEXT & ~filters.COMMAND, restart_menu)],
        AFTER_REGISTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_after_register)],
        AFTER_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_after_report)],
        RFC_NOT_FOUND: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rfc_not_found)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
    allow_reentry=True,
)
