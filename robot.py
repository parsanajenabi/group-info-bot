import os
import json
import time
import datetime
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus

# ====== تنظیمات ======
DATA_FILE = "group_data.json"
BLOCKED_WORDS_FILE = "words.txt"
MAX_WARNINGS = 3
MUTE_DURATION = 600  # ثانیه (10 دقیقه)

# ====== بارگذاری دیتابیس ======
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            database = json.load(f)
        if "groups" not in database:
            database["groups"] = {}
    except:
        database = {"groups": {}}
else:
    database = {"groups": {}}

# ====== ذخیره دیتابیس ======
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

# ====== بارگذاری کلمات ممنوعه ======
def load_blocked_words():
    if os.path.exists(BLOCKED_WORDS_FILE):
        with open(BLOCKED_WORDS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

blocked_words = load_blocked_words()

# ====== بررسی ادمین بودن ======
async def check_admin(bot, chat_id, user_id=None):
    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            return False
        if not bot_member.can_restrict_members:
            return False
        if user_id:
            user_member = await bot.get_chat_member(chat_id, user_id)
            if user_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return False
        return True
    except Exception as e:
        print(f"خطا در بررسی ادمین: {str(e)}")
        return False

# ====== مدیریت اخطار ======
async def handle_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        message_text = update.message.text

        # ایجاد ساختار گروه در دیتابیس
        if str(chat.id) not in database["groups"]:
            database["groups"][str(chat.id)] = {"warnings": {}, "history": []}
        if "warnings" not in database["groups"][str(chat.id)]:
            database["groups"][str(chat.id)]["warnings"] = {}
        if "history" not in database["groups"][str(chat.id)]:
            database["groups"][str(chat.id)]["history"] = []

        # افزایش اخطار
        if str(user.id) not in database["groups"][str(chat.id)]["warnings"]:
            database["groups"][str(chat.id)]["warnings"][str(user.id)] = 0
        database["groups"][str(chat.id)]["warnings"][str(user.id)] += 1
        current_warnings = database["groups"][str(chat.id)]["warnings"][str(user.id)]

        # ذخیره تاریخچه
        database["groups"][str(chat.id)]["history"].append({
            "user_id": user.id,
            "username": user.username or "",
            "first_name": user.first_name,
            "text": message_text,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        save_data()

        # بررسی تعداد اخطار و میوت کردن
        if current_warnings >= MAX_WARNINGS:
            if await check_admin(context.bot, chat.id, user.id):
                try:
                    await context.bot.restrict_chat_member(
                        chat_id=chat.id,
                        user_id=user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=int(time.time()) + MUTE_DURATION
                    )
                    # صفر کردن اخطار
                    database["groups"][str(chat.id)]["warnings"][str(user.id)] = 0

                    # 🆕 حذف تاریخچه اخطارهای همین کاربر
                    database["groups"][str(chat.id)]["history"] = [
                        h for h in database["groups"][str(chat.id)]["history"] if h["user_id"] != user.id
                    ]

                    save_data()
                    await update.message.reply_text(f"⛔ کاربر {user.first_name} میوت شد و تاریخچه اخطارهایش پاک شد!")
                except Exception as e:
                    await update.message.reply_text(f"خطا در میوت: {str(e)}")
            else:
                await update.message.reply_text("⚠️ دسترسی میوت ندارم!")
        else:
            await update.message.reply_text(
                f"⚠️ اخطار به {user.first_name}\n"
                f"اخطارها: {current_warnings}/{MAX_WARNINGS}"
            )
    except Exception as e:
        print(f"خطا در handle_warning: {str(e)}")
        await update.message.reply_text("⚠️ خطایی در پردازش اخطار رخ داد")

# ====== بررسی پیام‌ها ======
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
        text = update.message.text.lower()
        if any(word.lower() in text for word in blocked_words):
            await handle_warning(update, context)
    except Exception as e:
        print(f"خطا در check_message: {str(e)}")

# ====== ریست دستی اخطار ======
async def reset_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await update.message.reply_text("فقط ادمین‌ها می‌توانند این کار را انجام دهند!")
            return

        if context.args:
            target = context.args[0].replace("@", "")
            if str(chat.id) in database["groups"]:
                for user_id in database["groups"][str(chat.id)].get("warnings", {}):
                    if target.lower() in [str(user_id), target.lower()]:
                        database["groups"][str(chat.id)]["warnings"][user_id] = 0
                        save_data()
                        await update.message.reply_text(f"اخطارهای کاربر ریست شد")
                        return
            await update.message.reply_text("کاربر یافت نشد")
        else:
            await update.message.reply_text("لطفاً یوزرنیم کاربر را وارد کنید")
    except Exception as e:
        print(f"خطا در reset_warnings: {str(e)}")
        await update.message.reply_text(f"خطا: {str(e)}")

# ====== نمایش تاریخچه ======
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if str(chat.id) not in database["groups"] or "history" not in database["groups"][str(chat.id)]:
        await update.message.reply_text("📂 هیچ تاریخچه‌ای ثبت نشده است.")
        return
    history_list = database["groups"][str(chat.id)]["history"]
    if not history_list:
        await update.message.reply_text("📂 هیچ اخطاری ثبت نشده است.")
        return
    last_entries = history_list[-10:]
    msg = "📜 تاریخچه اخطارها:\n\n"
    for entry in last_entries:
        msg += f"👤 {entry['first_name']} (@{entry['username']})\n"
        msg += f"📅 {entry['date']}\n"
        msg += f"💬 {entry['text']}\n"
        msg += "—" * 20 + "\n"
    await update.message.reply_text(msg)

# ====== پاک کردن اخطارها هر 24 ساعت ======
async def clear_warnings_job(context: ContextTypes.DEFAULT_TYPE):
    global database
    for group_id in database.get("groups", {}):
        database["groups"][group_id]["warnings"] = {}
    save_data()
    print("✅ همه اخطارها پاک شدند")

# ====== راه‌اندازی ربات ======
def main():
    TOKEN = "Your token"
    app = Application.builder().token(TOKEN).build()

    # Job هر 24 ساعت
    job_queue = app.job_queue
    job_queue.run_repeating(clear_warnings_job, interval=84600, first=0)

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_message))
    app.add_handler(CommandHandler("reset", reset_warnings))
    app.add_handler(CommandHandler("history", show_history))

    app.add_error_handler(lambda update, context: print(f"خطا رخ داد: {context.error}"))

    print("ربات فعال شد...")
    app.run_polling()

if __name__ == "__main__":
    main()