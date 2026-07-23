# ==========================================================
# End Session Helper
# ==========================================================

async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gracefully terminates the conversation session."""
    context.user_data.clear()
    await update.message.reply_text(
        "👋 *Session Ended.*\n\n"
        "Thank you for using the Fieldwork Material Bot!\n"
        "Type /start anytime to start a new session.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


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

    if choice == "🏁 Finish Session":
        return await end_session(update, context)

    await update.message.reply_text("Please use the buttons provided.", reply_markup=AFTER_REGISTER_KEYBOARD)
    return AFTER_REGISTER


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
            rfc_list_formatted = "\n".join([f"• `{rfc}`" for rfc in available_rfcs])
            msg = (
                f"🏬 Warehouse: *{warehouse}*\n\n"
                f"📋 *Available RFC IDs:*\n"
                f"{rfc_list_formatted}\n\n"
                f"👇 *Please type the RFC ID to proceed:*"
            )
        else:
            msg = f"🏬 Warehouse: *{warehouse}*\n⚠️ *No active RFCs available.* Please type the RFC ID directly:"

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

    if choice == "🏁 Finish Session":
        return await end_session(update, context)

    await update.message.reply_text("Please use the buttons provided.", reply_markup=AFTER_REPORT_KEYBOARD)
    return AFTER_REPORT
