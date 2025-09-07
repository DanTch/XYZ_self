from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode
from database import Database
from keyboards import *
from config import *
import os
from utils import format_user_info, calculate_referral_bonus  # اصلاح شد

db = Database()

# حالت‌های مکالمه
SELECTING_POINTS, AWAITING_PAYMENT, AWAITING_TOKEN, CUSTOM_POINTS = range(4)

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = user.id
    
    # بررسی لینک دعوت
    invited_by = None
    if context.args:
        try:
            invited_by = int(context.args[0])
        except ValueError:
            pass
    
    # افزودن کاربر به دیتابیس
    is_new = db.add_user(
        chat_id,
        user.first_name,
        user.last_name,
        user.username,
        invited_by
    )
    
    if is_new:
        # ارسال نوتیفیکیشن به ادمین
        user_details = f"🍔 کاربر جدید {chat_id} به ربات اضافه شد.\n\n"
        user_details += f"ایدی عددی کاربر: {chat_id}\n"
        user_details += f"نام: {user.first_name if user.first_name else 'نامشخص'}\n"
        user_details += f"نام خانوادگی: {user.last_name if user.last_name else 'نامشخص'}\n"
        
        if user.username:
            user_details += f"یوزرنیم: @{user.username}"
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Go to chat", url=f"https://t.me/{user.username}")]
            ])
            await context.bot.send_message(ADMIN_ID, user_details, reply_markup=markup)
        else:
            user_details += f"🔥 User ID: [{user.id}](tg://user?id={user.id})"
            await context.bot.send_message(ADMIN_ID, user_details, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        
        # ارسال پیام به دعوت‌کننده
        if invited_by:
            inviter = db.get_user(invited_by)
            if inviter:
                await context.bot.send_message(
                    invited_by,
                    f"کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به عضویت کرد.\n\n"
                    f"🎁 3 امتیاز به شما اضافه شد.\n"
                    f"موجودی جدید: {inviter[4] + REFERRAL_BONUS}"
                )
    
    # ارسال پیام خوشامدگویی
    with open(WELCOME_IMAGE_PATH, 'rb') as photo:
        await update.message.reply_photo(
            photo,
            caption=f"به ربات XYZ سلف خوش آمدید\n\n"
                   f"برای کار کردن با ربات از دستورات زیر استفاده کنید\n\n"
                   f"Dev : @Danyal_net",
            reply_markup=main_menu()
        )

async def vip_handler(update: Update, context: CallbackContext):
    # بررسی اینکه آیا update از نوع callback_query است یا message
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        chat_id = query.from_user.id
        message = query.message
    else:
        chat_id = update.message.from_user.id
        message = update.message
    
    user = db.get_user(chat_id)
    
    if user[4] >= VIP_POINTS:
        # کسر امتیاز و ثبت درخواست
        db.add_points(chat_id, -VIP_POINTS)
        db.cursor.execute(
            "UPDATE users SET vip_purchase_count = vip_purchase_count + 1 WHERE user_id = ?",
            (chat_id,)
        )
        db.conn.commit()
        
        # ارسال به ادمین
        await context.bot.send_message(
            ADMIN_ID,
            f"درخواست سلف VIP جدید:\n\n"
            f"کاربر: {chat_id}\n"
            f"یوزرنیم: @{user[3] if user[3] else 'ندارد'}"
        )
        
        # محاسبه پاداش دعوت‌کنندگان
        bonuses = calculate_referral_bonus(chat_id, VIP_REFERRAL_BONUS, db)  # اصلاح شد
        for inviter_id, points in bonuses.items():
            db.add_points(inviter_id, points)
            inviter = db.get_user(inviter_id)
            await context.bot.send_message(
                inviter_id,
                f"کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به خرید سلف VIP کرد.\n\n"
                f"🎁 {points} امتیاز به شما اضافه شد.\n"
                f"موجودی جدید: {inviter[4] + points}"
            )
        
        # ارسال پاسخ به کاربر
        if update.callback_query:
            await query.edit_message_text("درخواست شما با موفقیت ثبت شد! به زودی با شما تماس خواهیم گرفت.")
        else:
            await message.reply_text("درخواست شما با موفقیت ثبت شد! به زودی با شما تماس خواهیم گرفت.")
    else:
        if update.callback_query:
            await query.answer("امتیاز کافی ندارید!", show_alert=True)
        else:
            await message.reply_text("امتیاز کافی ندارید!")

async def buy_points_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("buy_"):
        amount = int(query.data.split("_")[1])
        user_id = query.from_user.id
        
        # ذخیره درخواست پرداخت
        context.user_data["pending_payment"] = {
            "amount": amount,
            "user_id": user_id
        }
        
        await query.edit_message_text(
            f"لطفا مبلغ {amount} تومان را به شماره کارت زیر واریز کنید:\n\n"
            f"شماره کارت: {CARD_NUMBER}\n"
            f"به نام: {CARD_OWNER}\n\n"
            f"پس از واریز، فیش پرداخت را ارسال کنید.\n\n"
            f"⏰ مهلت پرداخت: 15 دقیقه",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("لغو خرید", callback_data="cancel_payment")]
            ])
        )
        return AWAITING_PAYMENT
    
    elif query.data == "buy_custom":
        await query.edit_message_text("مقدار امتیاز مورد نظر را وارد کنید:")
        return CUSTOM_POINTS

async def show_buy_points_menu(update: Update, context: CallbackContext):  # تابع جدید
    await update.message.reply_text(
        "لطفا امتیاز مورد نظر خود را از بین گزینه‌های انتخاب کنید",
        reply_markup=buy_points_menu()
    )

async def payment_received(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    photo_file_id = update.message.photo[-1].file_id
    
    # ذخیره پرداخت در دیتابیس
    payment_data = context.user_data.get("pending_payment")
    if payment_data:
        db.add_pending_payment(
            payment_data["user_id"],
            payment_data["amount"],
            photo_file_id
        )
        
        # ارسال به ادمین برای تأیید
        await context.bot.send_photo(
            ADMIN_ID,
            photo_file_id,
            caption=f"درخواست پرداخت جدید\n"
                   f"کاربر: {user_id}\n"
                   f"مبلغ: {payment_data['amount']} تومان",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("تأیید", callback_data=f"confirm_{user_id}")],
                [InlineKeyboardButton("رد", callback_data=f"reject_{user_id}")]
            ])
        )
        
        await update.message.reply_text("فیش پرداخت شما برای تأیید به ادمین ارسال شد.")
        del context.user_data["pending_payment"]
    
    return ConversationHandler.END

async def admin_confirm_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    action, user_id = query.data.split("_")
    user_id = int(user_id)
    
    if action == "confirm":
        # افزودن امتیاز به کاربر
        payment = db.cursor.execute(
            "SELECT amount FROM pending_payments WHERE user_id = ? AND status = 'pending'",
            (user_id,)
        ).fetchone()
        
        if payment:
            db.add_points(user_id, payment[0])
            db.update_payment_status(payment[0], "confirmed")
            
            await context.bot.send_message(user_id, "پرداخت شما با موفقیت تأیید شد. امتیازها به حساب شما اضافه گردید.")
            await query.edit_message_text("پرداخت تأیید شد.")
    
    elif action == "reject":
        db.update_payment_status(user_id, "rejected")
        await context.bot.send_message(user_id, "پرداخت شما رد شد. لطفاً دوباره تلاش کنید.")
        await query.edit_message_text("پرداخت رد شد.")

async def reseller_handler(update: Update, context: CallbackContext):
    # بررسی اینکه آیا update از نوع callback_query است یا message
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        chat_id = query.from_user.id
    else:
        chat_id = update.message.from_user.id
    
    user = db.get_user(chat_id)
    
    if user[4] >= RESELLER_POINTS:
        # کسر امتیاز و درخواست توکن
        db.add_points(chat_id, -RESELLER_POINTS)
        db.cursor.execute(
            "UPDATE users SET reseller_purchase_count = reseller_purchase_count + 1 WHERE user_id = ?",
            (chat_id,)
        )
        db.conn.commit()
        
        if update.callback_query:
            await query.edit_message_text("توکن ربات خود را ارسال کنید:")
        else:
            await update.message.reply_text("توکن ربات خود را ارسال کنید:")
        return AWAITING_TOKEN
    else:
        if update.callback_query:
            await query.answer("امتیاز کافی ندارید!", show_alert=True)
        else:
            await update.message.reply_text("امتیاز کافی ندارید!")

async def token_received(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    token = update.message.text
    
    # ارسال به ادمین
    await context.bot.send_message(
        ADMIN_ID,
        f"درخواست ساخت پنل نمایندگی:\n\n"
        f"کاربر: {user_id}\n"
        f"یوزرنیم: @{update.message.from_user.username if update.message.from_user.username else 'ندارد'}\n"
        f"توکن: {token}"
    )
    
    # محاسبه پاداش دعوت‌کنندگان
    bonuses = calculate_referral_bonus(user_id, RESELLER_REFERRAL_BONUS, db)  # اصلاح شد
    for inviter_id, points in bonuses.items():
        db.add_points(inviter_id, points)
        inviter = db.get_user(inviter_id)
        await context.bot.send_message(
            inviter_id,
            f"کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به خرید پنل نمایندگی کرد.\n\n"
            f"🎁 {points} امتیاز به شما اضافه شد.\n"
            f"موجودی جدید: {inviter[4] + points}"
        )
    
    await update.message.reply_text("درخواست شما با موفقیت ثبت شد! به زودی با شما تماس خواهیم گرفت.")
    return ConversationHandler.END

async def account_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = db.get_user(user_id)
    referrals = db.get_referrals(user_id)
    referrals_count = len(referrals)
    
    message = format_user_info(user, referrals_count)
    message += "\n\n👥 کاربران دعوت شده:\n"
    
    for ref in referrals:
        message += f"• {ref[1]} (@{ref[2] if ref[2] else 'ندارد'})\n"
    
    await update.message.reply_text(message, reply_markup=main_menu())

async def free_self_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = db.get_user(user_id)
    
    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
    
    message = (
        "شما میتوانید علاوه بر خرید امتیاز، با دعوت کردن دوستانتان به ربات سلف vip را به صورت رایگان دریافت کنید.\n\n"
        "لیست پاداش ها:\n"
        f"• دعوت کاربر: {REFERRAL_BONUS} امتیاز\n"
        f"• خرید سلف vip توسط کاربران: {VIP_REFERRAL_BONUS} امتیاز\n"
        f"• خرید پنل نمایندگی از طرف کاربران: {RESELLER_REFERRAL_BONUS} امتیاز\n\n"
        f"لینک دعوت شما:\n{referral_link}"
    )
    
    await update.message.reply_text(message, reply_markup=main_menu())

async def cancel_handler(update: Update, context: CallbackContext):
    await update.message.reply_text("عملیات لغو شد.", reply_markup=main_menu())
    return ConversationHandler.END

async def custom_points_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    
    try:
        points = int(text)
        if points <= 0:
            await update.message.reply_text("لطفاً یک عدد مثبت وارد کنید.")
            return CUSTOM_POINTS
        
        # ذخیره درخواست پرداخت
        context.user_data["pending_payment"] = {
            "amount": points,
            "user_id": user_id
        }
        
        await update.message.reply_text(
            f"لطفا مبلغ {points} تومان را به شماره کارت زیر واریز کنید:\n\n"
            f"شماره کارت: {CARD_NUMBER}\n"
            f"به نام: {CARD_OWNER}\n\n"
            f"پس از واریز، فیش پرداخت را ارسال کنید.\n\n"
            f"⏰ مهلت پرداخت: 15 دقیقه",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("لغو خرید", callback_data="cancel_payment")]
            ])
        )
        return AWAITING_PAYMENT
    
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کنید.")
        return CUSTOM_POINTS