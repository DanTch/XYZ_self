from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from database import Database
from keyboards import admin_menu

# تعریف مستقیم متغیر ADMIN_ID به جای import
# این روش مطمئن‌تر است
ADMIN_ID = 123456789  # آیدی عددی ادمین را اینجا قرار دهید

db = Database()

async def admin_panel(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی ادمین ندارید!")
        return
    
    await update.message.reply_text("پنل مدیریت:", reply_markup=admin_menu())

async def admin_add_points(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_add_points":
        await query.edit_message_text("آیدی کاربر و مقدار امتیاز را با فرمت زیر ارسال کنید:\n\n/add_points user_id points")
        return ADMIN_ADD_POINTS

async def add_points_command(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = int(context.args[0])
        points = int(context.args[1])
        db.add_points(user_id, points)
        await update.message.reply_text(f"امتیاز {points} به کاربر {user_id} اضافه شد.")
    except (IndexError, ValueError):
        await update.message.reply_text("فرمت صحیح: /add_points user_id points")

async def admin_sales_report(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_sales_report":
        # دریافت گزارش فروش
        vip_sales = db.cursor.execute("SELECT SUM(vip_purchase_count) FROM users").fetchone()[0] or 0
        reseller_sales = db.cursor.execute("SELECT SUM(reseller_purchase_count) FROM users").fetchone()[0] or 0
        
        report = (
            "گزارش فروش:\n\n"
            f"👻 فروش سلف VIP: {vip_sales} عدد\n"
            f"💎 فروش پنل نمایندگی: {reseller_sales} عدد"
        )
        
        await query.edit_message_text(report, reply_markup=admin_menu())

async def admin_new_users(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_new_users":
        # دریافت 10 کاربر آخر
        users = db.cursor.execute(
            "SELECT user_id, first_name, username FROM users ORDER BY user_id DESC LIMIT 10"
        ).fetchall()
        
        message = "10 کاربر آخر:\n\n"
        for user in users:
            message += f"• {user[1]} (@{user[2] if user[2] else 'ندارد'}) - {user[0]}\n"
        
        await query.edit_message_text(message, reply_markup=admin_menu())