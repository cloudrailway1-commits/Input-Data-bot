import logging
from telegram import (
    Update,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
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
    is_rfc_available,
    get_available_rfcs_by_warehouse,
    get_rfcs_by_warehouse,
    find_rfc,
    update_row_answers,
    delete_rfc,
)

from questions import QUESTIONS, TOTAL_QUESTIONS

from keyboards import (
    ROLE_KEYBOARD,
    FINISH_KEYBOARD,
    REGISTER_PREVIEW_KEYBOARD,
    AFTER_REPORT_KEYBOARD,
    RFC_NOT_FOUND_KEYBOARD,
    PREVIEW_KEYBOARD,
    CANCEL_EDIT_KEYBOARD,
    TECHNICIAN_RFC_KEYBOARD,
    FIXED_WAREHOUSES,
    get_warehouse_keyboard,
)

logger = logging.getLogger(__name__)

# Dynamic Keyboard for Warehouse Engineer After Register (Includes Edit Last RFC option)
AFTER_REGISTER_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["➕ Add More RFC", "✏️ Edit Last RFC"],
        ["🏬 Change Warehouse", "⬅️ Back to Main Menu"],
        ["🏁 Finish Session"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# ==========================================================
# Conversation States
# ==========================================================

(
    ROLE,
    NAME,
    WAREHOUSE,
    RFC,
    REGISTER_PREVIEW,
    EDIT_LAST_RFC,
    QUESTION,
    RESTART,
    AFTER_REGISTER,
    AFTER_REPORT,
    RFC_NOT_FOUND,
    PREVIEW,
    EDIT_SELECT,
) = range(13)


# ==========================================================
# Helper Functions
# ==========================================================

async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gracefully ends the session and cleans user data."""
    context.user_data.clear()
    await update.message.reply_text(
        "👋 *Session Ended.*\n\n"
        "Thank you for using Fieldwork Material Bot!\n"
        "Type /start anytime to begin again.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def show_warehouse_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the warehouse button menu."""
    keyboard = get_warehouse_keyboard()
    await update.message.reply_text(
        "🏬 *Select Warehouse / SO Location:*",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return WAREHOUSE


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

    if role not in ["🏭 Warehouse Engineer", "🛠 Technician"]:
        await update.message.reply_text(
            "Please select one of the available buttons.",
            reply_markup=ROLE_KEYBOARD,
        )
        return ROLE

    context.user_data["role"] = role

    if role == "🏭 Warehouse Engineer":
        prompt = "👤 Enter Engineer / Admin Name:"
    else:
        prompt = "👤 Enter Technician Name:"

    await update.message.reply_text(
        prompt,
        reply_markup=ReplyKeyboardRemove(),
    )

    return NAME


# ==========================================================
# Enter Name & Show Warehouse Category Selection
# ==========================================================

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text("Name cannot be empty.\nPlease enter your name.")
        return NAME

    context.user_data["name"] = name
    return await show_warehouse_selection(update, context)


# ==========================================================
# Select Warehouse & Request RFC ID
# ==========================================================

async def select_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    warehouse = update.message.text.strip()

    if warehouse == "⬅️ Back to Main Menu":
        return await start(update, context)

    if warehouse not in FIXED_WAREHOUSES:
        await update.message.reply_text(
            "⚠️ *Invalid Warehouse Selection.*\n"
            "Please choose a warehouse by tapping one of the buttons below:",
            parse_mode="Markdown",
            reply_markup=get_warehouse_keyboard(),
        )
        return WAREHOUSE

    context.user_data["warehouse"] = warehouse
    role = context.user_data.get("role", "")

    # ------------------------------------------
    # Technician Flow: Show active RFC list
    # ------------------------------------------
    if role == "🛠 Technician":
        available_rfcs = get_available_rfcs_by_warehouse(warehouse)

        if not available_rfcs:
            msg = (
                f"🏬 Warehouse: *{warehouse}*\n"
                f"⚠️ *No active RFCs currently available for this warehouse.*\n\n"
                f"Please type the RFC ID manually, or choose an option below:"
            )
        else:
            rfc_list_formatted = "\n".join([f"• `{rfc}`" for rfc in available_rfcs])
            msg = (
                f"🏬 Warehouse: *{warehouse}*\n\n"
                f"📋 *Available RFC IDs:*\n"
                f"{rfc_list_formatted}\n\n"
                f"👇 *Please type the RFC ID to proceed, or choose an option below:*"
            )

        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=TECHNICIAN_RFC_KEYBOARD,
        )
        return RFC

    # ------------------------------------------
    # Warehouse Engineer Flow: Prompt for new RFC ID
    # ------------------------------------------
    existing_rfcs = get_rfcs_by_warehouse(warehouse)
    formatted_existing = ""
    if existing_rfcs:
        formatted_existing = f"\n\nExisting RFCs in this Warehouse:\n" + "\n".join([f"• `{r}`" for r in existing_rfcs])

    await update.message.reply_text(
        f"🏬 Selected Warehouse: *{warehouse}*{formatted_existing}\n\n"
        f"📄 Enter new RFC ID to register under this Warehouse:",
        parse_mode="Markdown",
        reply_markup=TECHNICIAN_RFC_KEYBOARD,
    )
    return RFC


# ==========================================================
# Enter / Validate RFC
# ==========================================================

async def ask_rfc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()

        if text == "⬅️ Back to Main Menu":
            return await start(update, context)

        if text == "🏬 Change Warehouse":
            return await show_warehouse_selection(update, context)

        rfc = text.upper()
        role = context.user_data.get("role", "")
        warehouse = context.user_data.get("warehouse", "")

        # ------------------------------------------
        # Warehouse Engineer Flow (Single-Use Validation Added)
        # ------------------------------------------
        if role == "🏭 Warehouse Engineer":
            if rfc_exists(rfc):
                if not is_rfc_available(rfc):
                    msg = (
                        f"⚠️ RFC *{rfc}* has already been used and submitted by a technician.\n\n"
                        f"RFC IDs are single-use only and cannot be re-registered. Please enter a different RFC ID:"
                    )
                else:
                    msg = (
                        f"❌ RFC *{rfc}* is already registered and pending in the system.\n\n"
                        f"Please enter a different RFC ID:"
                    )

                await update.message.reply_text(
                    msg,
                    parse_mode="Markdown",
                    reply_markup=TECHNICIAN_RFC_KEYBOARD,
                )
                return RFC

            context.user_data["pending_rfc"] = rfc

            # Display confirmation preview for Warehouse Engineer
            preview_msg = (
                f"📝 *NEW RFC REGISTRATION PREVIEW*\n"
                f"----------------------------------\n"
                f"👤 *Engineer:* {context.user_data.get('name', 'Unknown')}\n"
                f"🏬 *Warehouse:* {warehouse}\n"
                f"📄 *RFC ID:* `{rfc}`\n"
                f"----------------------------------\n"
                f"Please confirm or edit before submitting:"
            )

            await update.message.reply_text(
                preview_msg,
                parse_mode="Markdown",
                reply_markup=REGISTER_PREVIEW_KEYBOARD,
            )
            return REGISTER_PREVIEW

        # ------------------------------------------
        # Technician Flow
        # ------------------------------------------
        if not is_rfc_available(rfc):
            if rfc_exists(rfc):
                await update.message.reply_text(
                    f"⚠️ RFC *{rfc}* has already been used and submitted.\n\n"
                    "RFC IDs are single-use only. Please select an option below:",
                    parse_mode="Markdown",
                    reply_markup=RFC_NOT_FOUND_KEYBOARD,
                )
            else:
                await update.message.reply_text(
                    f"❌ RFC *{rfc}* not found under Warehouse *{warehouse}*.\n\n"
                    "Please select an option below:",
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
            reply_markup=ReplyKeyboardRemove(),
        )

        return QUESTION

    except Exception as e:
        logger.error(f"Error in ask_rfc: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")
        return RFC


# ==========================================================
# Handle Warehouse Register Preview Options
# ==========================================================

async def handle_register_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    warehouse = context.user_data.get("warehouse", "")
    rfc = context.user_data.get("pending_rfc", "")

    if text == "✅ Confirm & Submit":
        if rfc_exists(rfc):
            if not is_rfc_available(rfc):
                msg = f"⚠️ RFC *{rfc}* was already submitted by a technician during confirmation.\n\nPlease enter a new RFC ID:"
            else:
                msg = f"❌ RFC *{rfc}* already exists in the system.\n\nPlease enter a different RFC ID:"

            await update.message.reply_text(
                msg,
                parse_mode="Markdown",
                reply_markup=TECHNICIAN_RFC_KEYBOARD,
            )
            return RFC

        add_rfc(
            rfc=rfc,
            warehouse=warehouse,
            engineer_name=context.user_data.get("name", "Unknown"),
        )

        # Store last added RFC for quick editing if needed later
        context.user_data["last_added_rfc"] = rfc

        # Retrieve the updated RFC list for this warehouse
        all_rfcs = get_rfcs_by_warehouse(warehouse)
        formatted_list = "\n".join([f"• `{r}`" for r in all_rfcs]) if all_rfcs else "None"

        await update.message.reply_text(
            f"✅ RFC *{rfc}* successfully registered under Warehouse *{warehouse}*!\n\n"
            f"📋 *Updated RFC List in {warehouse}:*\n"
            f"{formatted_list}\n\n"
            f"Choose an option below:",
            parse_mode="Markdown",
            reply_markup=AFTER_REGISTER_KEYBOARD,
        )
        return AFTER_REGISTER

    if text == "✏️ Edit RFC ID":
        await update.message.reply_text(
            f"✏️ Please type the new RFC ID for Warehouse *{warehouse}*:",
            parse_mode="Markdown",
            reply_markup=TECHNICIAN_RFC_KEYBOARD,
        )
        return RFC

    if text == "❌ Cancel Registration":
        context.user_data.pop("pending_rfc", None)
        await update.message.reply_text(
            "❌ RFC registration cancelled.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await start(update, context)

    await update.message.reply_text(
        "Please select an option from the keyboard below.",
        reply_markup=REGISTER_PREVIEW_KEYBOARD,
    )
    return REGISTER_PREVIEW


# ==========================================================
# Handle Post-Registration Edit (Edit Last RFC)
# ==========================================================

async def handle_edit_last_rfc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_rfc = update.message.text.strip().upper()
    warehouse = context.user_data.get("warehouse", "")
    last_rfc = context.user_data.get("last_added_rfc", "")

    if new_rfc == "⬅️ BACK TO MAIN MENU":
        return await start(update, context)

    if new_rfc == "🏬 CHANGE WAREHOUSE":
        return await show_warehouse_selection(update, context)

    # Validate duplicate/used RFC
    if rfc_exists(new_rfc) and new_rfc != last_rfc:
        if not is_rfc_available(new_rfc):
            msg = f"⚠️ RFC *{new_rfc}* has already been used and submitted.\n\nRFC IDs are single-use only. Type a different replacement RFC ID:"
        else:
            msg = f"❌ RFC *{new_rfc}* already exists in the database.\n\nPlease enter a different replacement RFC ID:"

        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=CANCEL_EDIT_KEYBOARD,
        )
        return EDIT_LAST_RFC

    # Replace old RFC entry with the updated one
    delete_rfc(last_rfc)
    add_rfc(
        rfc=new_rfc,
        warehouse=warehouse,
        engineer_name=context.user_data.get("name", "Unknown"),
    )

    context.user_data["last_added_rfc"] = new_rfc

    # Get updated RFC list
    all_rfcs = get_rfcs_by_warehouse(warehouse)
    formatted_list = "\n".join([f"• `{r}`" for r in all_rfcs]) if all_rfcs else "None"

    await update.message.reply_text(
        f"✅ RFC updated from `{last_rfc}` to *{new_rfc}* for Warehouse *{warehouse}*!\n\n"
        f"📋 *Updated RFC List in {warehouse}:*\n"
        f"{formatted_list}\n\n"
        f"Choose an option below:",
        parse_mode="Markdown",
        reply_markup=AFTER_REGISTER_KEYBOARD,
    )
    return AFTER_REGISTER


# ==========================================================
# Handle Warehouse After-Register Options
# ==========================================================

async def handle_after_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    warehouse = context.user_data.get("warehouse")

    if choice == "➕ Add More RFC":
        existing_rfcs = get_rfcs_by_warehouse(warehouse)
        formatted_existing = ""
        if existing_rfcs:
            formatted_existing = f"\n\nExisting RFCs in this Warehouse:\n" + "\n".join([f"• `{r}`" for r in existing_rfcs])

        await update.message.reply_text(
            f"Adding another RFC under Warehouse: *{warehouse}*{formatted_existing}\n\n📄 Enter new RFC ID:",
            parse_mode="Markdown",
            reply_markup=TECHNICIAN_RFC_KEYBOARD,
        )
        return RFC

    if choice == "✏️ Edit Last RFC":
        last_rfc = context.user_data.get("last_added_rfc", "N/A")
        await update.message.reply_text(
            f"✏️ *Editing Last Registered RFC*\n\n"
            f"Current RFC ID: `{last_rfc}`\n"
            f"Warehouse: *{warehouse}*\n\n"
            f"Type the replacement RFC ID:",
            parse_mode="Markdown",
            reply_markup=CANCEL_EDIT_KEYBOARD,
        )
        return EDIT_LAST_RFC

    if choice == "🏬 Change Warehouse":
        return await show_warehouse_selection(update, context)

    if choice == "⬅️ Back to Main Menu":
        return await start(update, context)

    if choice == "🏁 Finish Session":
        return await end_session(update, context)

    await update.message.reply_text("Please use the buttons provided.", reply_markup=AFTER_REGISTER_KEYBOARD)
    return AFTER_REGISTER


# ==========================================================
# Handle RFC Not Found Options
# ==========================================================

async def handle_rfc_not_found(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "✍️ Try Another RFC":
        await update.message.reply_text(
            "📄 Please type the RFC ID again:",
            reply_markup=TECHNICIAN_RFC_KEYBOARD,
        )
        return RFC

    if text == "🏬 Change Warehouse":
        return await show_warehouse_selection(update, context)

    if text == "⬅️ Back to Main Menu":
        return await start(update, context)

    return await ask_rfc(update, context)


# ==========================================================
# Ask Material Questions
# ==========================================================

async def ask_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        answer = update.message.text.strip()

        if context.user_data.get("editing_index") is not None:
            idx = context.user_data["editing_index"]
            context.user_data["answers"][idx] = answer
            context.user_data["editing_index"] = None
            await update.message.reply_text("✅ Answer updated successfully!")
            return await show_preview(update, context)

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

        return await show_preview(update, context)

    except Exception as e:
        logger.error(f"Error in ask_questions: {e}")
        await update.message.reply_text("⚠️ An error occurred while processing your input. Please try typing your answer again.")
        return QUESTION


# ==========================================================
# Show Report Preview
# ==========================================================

async def show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        warehouse = context.user_data.get("warehouse", "N/A")
        rfc = context.user_data.get("rfc", "N/A")
        name = context.user_data.get("name", "N/A")
        answers = context.user_data.get("answers", [])

        preview_lines = [
            "📋 *REPORT PREVIEW*",
            "----------------------------------",
            f"👤 *Technician:* {name}",
            f"🏬 *Warehouse:* {warehouse}",
            f"📄 *RFC ID:* {rfc}",
            "----------------------------------",
        ]

        for i, ans in enumerate(answers):
            q_label = QUESTIONS[i][0]
            preview_lines.append(f"*{i + 1}. {q_label}:*\n└ {ans}")

        preview_lines.append("----------------------------------")
        preview_lines.append("Please verify your answers before submitting:")

        await update.message.reply_text(
            "\n".join(preview_lines),
            parse_mode="Markdown",
            reply_markup=PREVIEW_KEYBOARD,
        )
        return PREVIEW

    except Exception as e:
        logger.error(f"Error in show_preview: {e}")
        await update.message.reply_text("⚠️ Unable to render report preview.", reply_markup=PREVIEW_KEYBOARD)
        return PREVIEW


# ==========================================================
# Handle Preview Actions
# ==========================================================

async def handle_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()

        if text == "✅ Confirm & Submit":
            return await finish(update, context)

        if text == "✏️ Edit Answers":
            options = "\n".join(
                [f"{i + 1}. {QUESTIONS[i][0]}" for i in range(TOTAL_QUESTIONS)]
            )
            await update.message.reply_text(
                f"✏️ *Which answer would you like to edit?*\n\n"
                f"{options}\n\n"
                f"Type the question number (1-{TOTAL_QUESTIONS}):",
                parse_mode="Markdown",
                reply_markup=CANCEL_EDIT_KEYBOARD,
            )
            return EDIT_SELECT

        if text == "❌ Cancel Report":
            context.user_data.clear()
            await update.message.reply_text(
                "❌ Report submission cancelled.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return await start(update, context)

        await update.message.reply_text(
            "Please select an option from the keyboard.", 
            reply_markup=PREVIEW_KEYBOARD
        )
        return PREVIEW

    except Exception as e:
        logger.error(f"Error in handle_preview: {e}")
        await update.message.reply_text(
            "⚠️ An unexpected error occurred while processing your selection.\n"
            "Resetting to main menu...",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await start(update, context)


# ==========================================================
# Select Question to Edit
# ==========================================================

async def handle_edit_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()

        if text == "❌ Cancel Editing":
            return await show_preview(update, context)

        if text.isdigit():
            num = int(text)
            if 1 <= num <= TOTAL_QUESTIONS:
                idx = num - 1
                context.user_data["editing_index"] = idx
                question = QUESTIONS[idx][0]
                current_ans = context.user_data["answers"][idx]

                await update.message.reply_text(
                    f"Editing Question {num}:\n*{question}*\n\n"
                    f"Current Answer: _{current_ans}_\n\n"
                    f"Please enter your new answer:",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardRemove(),
                )
                return QUESTION

        await update.message.reply_text(
            f"⚠️ Invalid choice. Please enter a number between 1 and {TOTAL_QUESTIONS}:",
            reply_markup=CANCEL_EDIT_KEYBOARD,
        )
        return EDIT_SELECT

    except Exception as e:
        logger.error(f"Error in handle_edit_selection: {e}")
        return await show_preview(update, context)


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
        logger.error(f"Error in finish: {e}")
        await update.message.reply_text(f"❌ Failed to save report.\n\n{e}", reply_markup=FINISH_KEYBOARD)
        context.user_data.clear()
        return RESTART


# ==========================================================
# Handle Technician After-Report Options
# ==========================================================

async def handle_after_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice in ["📋 Submit Another Report", "📄 Use Different RFC"]:
        context.user_data.pop("rfc", None)
        context.user_data["answers"] = []
        context.user_data["question_index"] = 0

        warehouse = context.user_data.get("warehouse", "")
        available_rfcs = get_available_rfcs_by_warehouse(warehouse)

        if available_rfcs:
            rfc_list_formatted = "\n".join([f"• `{rfc}`" for rfc in available_rfcs])
            msg = (
                f"🏬 Warehouse: *{warehouse}*\n\n"
                f"📋 *Available RFC IDs:*\n"
                f"{rfc_list_formatted}\n\n"
                f"👇 *Please type the RFC ID to proceed, or choose an option below:*"
            )
        else:
            msg = (
                f"🏬 Warehouse: *{warehouse}*\n"
                f"⚠️ *No active RFCs available.* Please type the RFC ID directly, or choose an option below:"
            )

        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=TECHNICIAN_RFC_KEYBOARD,
        )
        return RFC

    if choice == "🏬 Change Warehouse":
        return await show_warehouse_selection(update, context)

    if choice == "⬅️ Back to Main Menu":
        return await start(update, context)

    if choice == "🏁 Finish Session":
        return await end_session(update, context)

    await update.message.reply_text("Please use the buttons provided.", reply_markup=AFTER_REPORT_KEYBOARD)
    return AFTER_REPORT


# ==========================================================
# Restart Menu
# ==========================================================

async def restart_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice == "🔄 New Report":
        return await start(update, context)

    if choice == "❌ Exit":
        return await end_session(update, context)

    await update.message.reply_text("Please use one of the buttons below.", reply_markup=FINISH_KEYBOARD)
    return RESTART


# ==========================================================
# Cancel Command (/cancel)
# ==========================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await end_session(update, context)


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
        WAREHOUSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_warehouse)],
        RFC: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_rfc)],
        REGISTER_PREVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_register_preview)],
        EDIT_LAST_RFC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_last_rfc)],
        QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_questions)],
        RESTART: [MessageHandler(filters.TEXT & ~filters.COMMAND, restart_menu)],
        AFTER_REGISTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_after_register)],
        AFTER_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_after_report)],
        RFC_NOT_FOUND: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rfc_not_found)],
        PREVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_preview)],
        EDIT_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_selection)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
    allow_reentry=True,
)
