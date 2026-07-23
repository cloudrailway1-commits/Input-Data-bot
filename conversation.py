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
    get_available_rfcs_by_warehouse,
    get_rfcs_by_warehouse,
    get_all_warehouses,
    get_available_warehouses,
    find_rfc,
    update_row_answers,
)

from questions import QUESTIONS, TOTAL_QUESTIONS

from keyboards import (
    ROLE_KEYBOARD,
    FINISH_KEYBOARD,
    AFTER_REGISTER_KEYBOARD,
    AFTER_REPORT_KEYBOARD,
    SAME_RFC_KEYBOARD,
    RFC_NOT_FOUND_KEYBOARD,
    NO_RFC_KEYBOARD,
    PREVIEW_KEYBOARD,
    CANCEL_EDIT_KEYBOARD,
    get_warehouse_keyboard,
    get_rfc_keyboard,
)

logger = logging.getLogger(__name__)

# ==========================================================
# Conversation States
# ==========================================================

(
    ROLE,
    NAME,
    WAREHOUSE,
    RFC,
    QUESTION,
    RESTART,
    AFTER_REGISTER,
    AFTER_REPORT,
    RFC_NOT_FOUND,
    PREVIEW,
    EDIT_SELECT,
) = range(11)

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
    role = context.user_data.get("role", "")

    # ------------------------------------------
    # Technician Flow: Select Warehouse
    # ------------------------------------------
    if role == "🛠 Technician":
        warehouses = get_available_warehouses()

        if not warehouses:
            await update.message.reply_text(
                "⚠️ No active Warehouses/RFCs are currently available.\n\n"
                "Please ask the Warehouse Engineer to register an RFC first.",
                reply_markup=NO_RFC_KEYBOARD,
            )
            return WAREHOUSE

        keyboard = get_warehouse_keyboard(warehouses)
        await update.message.reply_text(
            "🏬 *Select Warehouse Category:*",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        return WAREHOUSE

    # ------------------------------------------
    # Warehouse Engineer Flow: Choose or Enter Warehouse
    # ------------------------------------------
    existing_warehouses = get_all_warehouses()
    if existing_warehouses:
        keyboard = get_warehouse_keyboard(existing_warehouses)
        await update.message.reply_text(
            "🏬 *Select Warehouse Category* or type a new Warehouse name directly:",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "🏬 Enter Warehouse Category Name:",
            reply_markup=ReplyKeyboardRemove(),
        )

    return WAREHOUSE


# ==========================================================
# Select/Enter Warehouse & Ask RFC ID
# ==========================================================

async def select_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    warehouse = update.message.text.strip()

    if warehouse == "⬅️ Back to Main Menu":
        context.user_data.clear()
        await update.message.reply_text(
            "📦 *Fieldwork Material Bot*\n\nPlease select your role.",
            parse_mode="Markdown",
            reply_markup=ROLE_KEYBOARD,
        )
        return ROLE

    context.user_data["warehouse"] = warehouse
    role = context.user_data.get("role", "")

    # ------------------------------------------
    # Technician Flow: Display RFC IDs for selected Warehouse
    # ------------------------------------------
    if role == "🛠 Technician":
        available_rfcs = get_available_rfcs_by_warehouse(warehouse)

        if not available_rfcs:
            await update.message.reply_text(
                f"⚠️ No active RFCs found under Warehouse *{warehouse}*.",
                parse_mode="Markdown",
                reply_markup=NO_RFC_KEYBOARD,
            )
            return WAREHOUSE

        keyboard = get_rfc_keyboard(available_rfcs)
        await update.message.reply_text(
            f"📋 *Available RFC IDs for Warehouse [{warehouse}]:*\n\n"
            f"Please select or type the RFC ID you want to work on:",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        return RFC

    # ------------------------------------------
    # Warehouse Engineer Flow: Prompt for new RFC ID
    # ------------------------------------------
    existing_rfcs = get_rfcs_by_warehouse(warehouse)
    formatted_existing = ""
    if existing_rfcs:
        formatted_existing = f"\n\nExisting RFCs in this Warehouse: " + ", ".join([f"`{r}`" for r in existing_rfcs])

    await update.message.reply_text(
        f"🏬 Selected Warehouse: *{warehouse}*{formatted_existing}\n\n"
        f"📄 Enter new RFC ID to register under this Warehouse:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return RFC


# ==========================================================
# Enter / Select RFC
# ==========================================================

async def ask_rfc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()

        if text == "⬅️ Back to Main Menu":
            context.user_data.clear()
            await update.message.reply_text(
                "📦 *Fieldwork Material Bot*\n\nPlease select your role.",
                parse_mode="Markdown",
                reply_markup=ROLE_KEYBOARD,
            )
            return ROLE

        rfc = text.upper()
        role = context.user_data.get("role", "")
        warehouse = context.user_data.get("warehouse", "")

        # ------------------------------------------
        # Warehouse Engineer Flow
        # ------------------------------------------
        if role == "🏭 Warehouse Engineer":
            if rfc_exists(rfc):
                await update.message.reply_text(
                    f"❌ RFC *{rfc}* already exists.\n\nPlease enter a different RFC ID:",
                    parse_mode="Markdown",
                )
                return RFC

            add_rfc(
                rfc=rfc,
                warehouse=warehouse,
                engineer_name=context.user_data.get("name", "Unknown"),
            )

            await update.message.reply_text(
                f"✅ RFC *{rfc}* successfully registered under Warehouse *{warehouse}*!\n\n"
                f"Choose an option below:",
                parse_mode="Markdown",
                reply_markup=AFTER_REGISTER_KEYBOARD,
            )
            return AFTER_REGISTER

        # ------------------------------------------
        # Technician Flow
        # ------------------------------------------
        if not rfc_exists(rfc):
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
        await update.message.reply_text(f"⚠️ Error: {e}")
        return RFC


# ==========================================================
# Handle RFC Not Found Options
# ==========================================================

async def handle_rfc_not_found(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    warehouse = context.user_data.get("warehouse", "")

    if text == "✍️ Try Another RFC":
        available_rfcs = get_available_rfcs_by_warehouse(warehouse)
        if available_rfcs:
            keyboard = get_rfc_keyboard(available_rfcs)
            msg = f"📋 *Available RFC IDs for Warehouse [{warehouse}]:*\n\nSelect or enter RFC ID:"
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await update.message.reply_text("📄 Please enter the RFC ID:", reply_markup=ReplyKeyboardRemove())
        return RFC

    if text == "⬅️ Back to Main Menu":
        context.user_data.clear()
        await update.message.reply_text(
            "📦 *Fieldwork Material Bot*\n\nPlease select your role.",
            parse_mode="Markdown",
            reply_markup=ROLE_KEYBOARD,
        )
        return ROLE

    return await ask_rfc(update, context)


# ==========================================================
# Handle Warehouse After-Register Options
# ==========================================================

async def handle_after_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice == "➕ Add More RFC":
        warehouse = context.user_data.get("warehouse")
        await update.message.reply_text(
            f"Adding another RFC under Warehouse: *{warehouse}*\n\n📄 Enter new RFC ID:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return RFC

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


# ==========================================================
# Show Report Preview
# ==========================================================

async def show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# ==========================================================
# Handle Preview Actions
# ==========================================================

async def handle_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text("Please select an option from the keyboard.", reply_markup=PREVIEW_KEYBOARD)
    return PREVIEW


# ==========================================================
# Select Question to Edit
# ==========================================================

async def handle_edit_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        warehouse = context.user_data.get("warehouse", "")
        available_rfcs = get_available_rfcs_by_warehouse(warehouse)
        if available_rfcs:
            keyboard = get_rfc_keyboard(available_rfcs)
            msg = f"📋 *Available RFC IDs for Warehouse [{warehouse}]:*\n\nSelect or enter RFC ID:"
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
        else:
            msg = "⚠️ No active RFCs available for this warehouse. Select Back to return to Main Menu:"
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=NO_RFC_KEYBOARD)

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
        WAREHOUSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_warehouse)],
        RFC: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_rfc)],
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
