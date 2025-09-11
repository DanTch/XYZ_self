# در ابتدای فایل handlers.py
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode
from telegram.error import Forbidden
from database import Database
from keyboards import *
from config import *
import os
from utils import format_user_info, calculate_referral_bonus
from datetime import datetime

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
            try:
                await context.bot.send_message(ADMIN_ID, user_details, reply_markup=markup)
            except Forbidden:
                pass
        
        # ارسال پیام به دعوت‌کننده
        if invited_by:
            inviter = db.get_user(invited_by)
            if inviter:
                try:
                    await context.bot.send_message(
                        invited_by,
                        f"کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به عضویت کرد.\n\n"
                        f"🎁 3 امتیاز به شما اضافه شد.\n"
                        f"موجودی جدید: {inviter[4] + REFERRAL_BONUS}"
                    )
                except Forbidden:
                    pass
    
    # ارسال پیام خوشامدگویی
    try:
        with open(WELCOME_IMAGE_PATH, 'rb') as photo:
            await update.message.reply_photo(
                photo,
                caption=f"به ربات XYZ سلف خوش آمدید\n\n"
                       f"برای کار کردن با ربات از دستورات زیر استفاده کنید\n\n"
                       f"Dev : @Danyal_net",
                reply_markup=main_menu()
            )
    except:
        await update.message.reply_text(
            f"به ربات XYZ سلف خوش آمدید\n\n"
            f"برای کار کردن با ربات از دستورات زیر استفاده کنید\n\n"
            f"Dev : @Danyal_net",
            reply_markup=main_menu()
        )

async def vip_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        await query.answer()
        chat_id = query.from_user.id
        message = query.message
    else:
        chat_id = update.message.from_user.id
        message = update.message
    
    user = db.get_user(chat_id)
    
    if query and query.data == "what_is_self":
        # نمایش توضیحات کامل سلف
        explanation_text = """
🤖 <b>سلف چیست؟</b>

سلف یک ربات است که بر روی اکانت تلگرام شما قرار میگیرد و قابلیت‌هایی را فراهم می‌کند که کاربران معمولی تلگرام ندارند. با داشتن سلف، شما یک پله از کاربران عادی جلوتر هستید!

📋 <b>قابلیت‌های پرکاربردی سلف:</b>

• 🔇 <b>سکوت دادن در پیوی</b>: می‌توانید فردی را در پیوی سکوت دهید (بدون بلاک کردن)
• 💾 <b>سیو تایم دار</b>: ذخیره خودکار عکس و فیلم با زمان‌بندی مشخص
• 🔄 <b>سیو بعد از پاک</b>: ذخیره محتوا حتی بعد از پاک شدن در چت
• 📝 <b>فهمیدن متن ادیت شده</b>: مشاهده متن قبل از ویرایش
• 👁️ <b>فهمیدن متن پاک شده</b>: مشاهده پیام‌های حذف شده
• 😈 <b>تنظیم دشمن</b>: فحش خودکار به افراد نامطلوب
• 😄 <b>تنظیم دشمنک</b>: فحش دوستانه به دوستان (برای سرگرمی)
• ⏰ <b>ساعت در کنار اسم</b>: ساعت زنده که هر دقیقه آپدیت می‌شود
• 📅 <b>ساعت و تاریخ در بیو</b>: تاریخ و ساعت زنده در بیوگرافی
• 💾 <b>سیو از محدودیت‌ها</b>: ذخیره از چت‌ها و محتواهای محدود (مثل SCAM)

🌟 <b>با سلف VIP چه مزایایی دارید؟</b>

✅ پشتیبانی فعال و 24 ساعته
✅ کمترین پینگ و تاخیر در اجرای دستورات
✅ دسترسی به قابلیت‌های انحصاری و پیشرفته
✅ بدون هیچگونه تبلیغات مزاحم
✅ به‌روزرسانی رایگان و دائمی

برای بازگشت به منوی اصلی روی دکمه زیر کلیک کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("خرید سلف vip 🔥", callback_data="buy_vip")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await safe_edit_message_text(query, explanation_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(explanation_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return
    
    elif query and query.data == "buy_vip":
        # بررسی موجودی کاربر
        if user[4] < VIP_POINTS:
            insufficient_points_text = f"""
❌ <b>موجودی کافی ندارید!</b>

📊 <b>وضعیت امتیاز شما:</b>
• امتیاز مورد نیاز: {VIP_POINTS} امتیاز
• امتیاز فعلی شما: {user[4]} امتیاز
• کمبود: {VIP_POINTS - user[4]} امتیاز

💡 <b>راه‌های افزایش امتیاز:</b>
• از دوستان خود با لینک دعوت دعوت کنید ({REFERRAL_BONUS} امتیاز به از هر نفر)
• امتیاز خریداری کنید (از بخش خرید امتیاز)
• در صورت خرید کاربران دعوت شده توسط شما، پاداش دریافت کنید

🔗 <b>لینک دعوت شما:</b>
https://t.me/{context.bot.username}?start={chat_id}
            """
            
            keyboard = [
                [InlineKeyboardButton("خرید امتیاز 💎", callback_data="buy_points")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if query:
                await query.answer("موجودی کافی ندارید!", show_alert=True)
                await safe_edit_message_text(query, insufficient_points_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await message.reply_text(insufficient_points_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            return
        
        # نمایش پیام پردازش
        processing_text = """
⏳ <b>در حال پردازش درخواست شما...</b>
لطفاً چند لحظه صبر کنید، درخواست شما در حال بررسی است.
        """
        
        keyboard = [
            [InlineKeyboardButton("لغو", callback_data="cancel_vip")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await safe_edit_message_text(query, processing_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(processing_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        # شبیه‌سازی پردازش
        await asyncio.sleep(2)
        
        # کسر امتیاز و ثبت درخواست
        db.add_points(chat_id, -VIP_POINTS)
        db.cursor.execute(
            "UPDATE users SET vip_purchase_count = vip_purchase_count + 1 WHERE user_id = ?",
            (chat_id,)
        )
        db.conn.commit()
        
        # ارسال به ادمین
        try:
            admin_message = f"""
🆕 <b>درخواست جدید سلف VIP</b>

👤 <b>مشخصات کاربر:</b>
• آیدی: {chat_id}
• نام: {user[1]} {user[2]}
• یوزرنیم: @{user[3] if user[3] else 'ندارد'}

📋 <b>جزئیات درخواست:</b>
• نوع درخواست: سلف VIP
• امتیاز کسر شده: {VIP_POINTS}
• زمان درخواست: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            await context.bot.send_message(ADMIN_ID, admin_message, parse_mode=ParseMode.HTML)
        except Forbidden:
            pass
        
        # محاسبه پاداش دعوت‌کنندگان
        bonuses = calculate_referral_bonus(chat_id, VIP_REFERRAL_BONUS, db)
        for inviter_id, points in bonuses.items():
            db.add_points(inviter_id, points)
            inviter = db.get_user(inviter_id)
            
            # ارسال پیام به دعوت‌کننده
            try:
                bonus_message = f"""
🎉 <b>تبریک! پاداش دریافت کردید</b>

کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به خرید سلف VIP کرد!

💰 <b>جزئیات پاداش:</b>
• مبلغ پاداش: {points} امتیاز
• نوع خرید: سلف VIP
• موجودی جدید: {inviter[4] + points} امتیاز

🙏 از همراهی شما سپاسگزاریم!
                """
                await context.bot.send_message(inviter_id, bonus_message, parse_mode=ParseMode.HTML)
            except Forbidden:
                pass
        
        # پیام تأیید نهایی به کاربر
        success_text = """
✅ <b>درخواست شما با موفقیت ثبت شد!</b>

🎉 <b>پنل نمایندگی شما در حال ساخت است</b>

📋 <b>اطلاعات تکمیلی:</b>
• کد پیگیری: {str(user_id)[-6:]}
• زمان ساخت: 24-48 ساعت کاری
• پشتیبانی: 24 ساعته

🔧 <b>مراحل بعدی:</b>
• به زودی با شما تماس خواهیم گرفت
• اطلاعات لازم برای راه‌اندازی پنل دریافت می‌شود
• دسترسی‌های پنل مدیریت برای شما فعال خواهد شد
• آموزش کامل استفاده از پنل ارائه می‌شود

🌟 <b>از انتخاب شما سپاسگزاریم!</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await safe_edit_message_text(query, success_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def buy_points_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        await query.answer()
        print(f"داده کالبک دریافت شده: {query.data}")  # لاگ برای دیباگ
    
    if query and query.data == "buy_points":
        print("در حال نمایش منوی خرید امتیاز...")  # لاگ برای دیباگ
        await show_buy_points_menu(update, context)
        return SELECTING_POINTS
    
    if query and query.data.startswith("buy_"):
        print(f"در حال پردازش خرید: {query.data}")  # لاگ برای دیباگ
        
        # بررسی آیا داده کالبک با الگوی عددی مطابقت دارد
        import re
        if re.match(r'^buy_\d+$', query.data):
            try:
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
                    ]),
                    parse_mode=ParseMode.HTML
                )
                
                print(f"وضعیت کاربر {user_id} به AWAITING_PAYMENT تغییر کرد")  # لاگ برای دیباگ
                return AWAITING_PAYMENT
                
            except (IndexError, ValueError) as e:
                print(f"خطا در پردازش خرید: {e}")  # لاگ خطا
                await query.edit_message_text("خطا در پردازش درخواست. لطفا دوباره تلاش کنید.")
                return ConversationHandler.END
        
        elif query.data == "buy_custom":
            print("در حال درخواست خرید امتیاز دلخواه...")  # لاگ برای دیباگ
            await query.edit_message_text("مقدار امتیاز مورد نظر را وارد کنید:")
            # تنظیم وضعیت کاربر به صورت دستی
            context.user_data['state'] = CUSTOM_POINTS
            return CUSTOM_POINTS
        
        else:
            print(f"داده کالبک ناشناخته: {query.data}")  # لاگ برای دیباگ
            await query.edit_message_text("داده کالبک ناشناخته است.")
            return ConversationHandler.END



async def payment_received(update: Update, context: CallbackContext):
    print("payment_received فراخوانی شد")  # لاگ برای دیباگ
    
    user_id = update.message.from_user.id
    photo_file_id = update.message.photo[-1].file_id
    
    print(f"عکس دریافت شده از کاربر {user_id}")  # لاگ برای دیباگ
    
    # بررسی وجود پرداخت در انتظار
    payment_data = context.user_data.get("pending_payment")
    if not payment_data:
        print("هیچ پرداخت در انتظاری وجود ندارد")  # لاگ برای دیباگ
        await update.message.reply_text("شما در حال انتظار پرداخت نیستید. لطفاً از منوی اصلی اقدام کنید.")
        return ConversationHandler.END
    
    print(f"پرداخت در انتظار پیدا شد: {payment_data}")  # لاگ برای دیباگ
    
    try:
        # ذخیره پرداخت در دیتابیس
        db.add_pending_payment(
            payment_data["user_id"],
            payment_data["amount"],
            photo_file_id
        )
        
        print("پرداخت در دیتابیس ذخیره شد")  # لاگ برای دیباگ
        
        # ارسال به ادمین برای تأیید
        try:
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
            print("پیام به ادمین ارسال شد")  # لاگ برای دیباگ
        except Exception as e:
            print(f"خطا در ارسال به ادمین: {e}")  # لاگ خطا
        
        await update.message.reply_text(
            "✅ فیش پرداخت شما با موفقیت دریافت شد\n"
            "پس از بررسی توسط ادمین، امتیازها به حساب شما اضافه خواهد شد."
        )
        
        # پاک کردن پرداخت در انتظار
        if "pending_payment" in context.user_data:
            del context.user_data["pending_payment"]
        
    except Exception as e:
        print(f"خطا در پردازش پرداخت: {e}")  # لاگ خطا
        await update.message.reply_text(
            "❌ خطایی در پردازش پرداخت رخ داد\n"
            "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
    
    return ConversationHandler.END

    
async def debug_payment_status(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    payment_data = context.user_data.get("pending_payment")
    
    if payment_data:
        await update.message.reply_text(
            f"وضعیت پرداخت:\n"
            f"مبلغ: {payment_data['amount']}\n"
            f"کاربر: {payment_data['user_id']}"
        )
    else:
        await update.message.reply_text("هیچ پرداخت در انتظاری وجود ندارد")

async def cancel_payment_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    print(f"درخواست لغو پرداخت از کاربر {user_id}")  # لاگ برای دیباگ
    
    # پاک کردن پرداخت در انتظار
    if "pending_payment" in context.user_data:
        del context.user_data["pending_payment"]
    
    await query.edit_message_text(
        "❌ پرداخت لغو شد\n"
        "می‌توانید از منوی اصلی اقدامات دیگر را انجام دهید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ])
    )
    
    return ConversationHandler.END


async def back_to_main_handler(update: Update, context: CallbackContext):
    """این تابع دکمه بازگشت به منوی اصلی را مدیریت می‌کند"""
    query = update.callback_query
    await query.answer()
    
    try:
        # تلاش برای ویرایش پیام فعلی
        await safe_edit_message_text(
            query,
            "منوی اصلی:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👻 سلف 𝐕𝐢𝐩 👻", callback_data="vip_menu")],
                [InlineKeyboardButton("💎 پنل نمایندگی 💎", callback_data="reseller_menu")],
                [InlineKeyboardButton("💍 خرید امتیاز 💍", callback_data="buy_points")],
                [InlineKeyboardButton("💎 حساب کاربری 💎", callback_data="account")]
            ])
        )
    except Exception as e:
        print(f"خطا در ویرایش پیام: {e}")
        # اگر ویرایش پیام ممکن نبود، یک پیام جدید ارسال کن
        try:
            await query.message.reply_text(
                "منوی اصلی:",
                reply_markup=main_menu()
            )
        except Exception as e2:
            print(f"خطا در ارسال پیام جدید: {e2}")
            # اگر آن هم ممکن نبود، به کاربر اطلاع بده
            await query.message.reply_text("خطایی در بازگشت به منوی اصلی رخ داد. لطفاً از دستور /start استفاده کنید.")


async def admin_confirm_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
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
            
            try:
                await context.bot.send_message(user_id, "پرداخت شما با موفقیت تأیید شد. امتیازها به حساب شما اضافه گردید.")
            except Forbidden:
                pass
            if query:
                await query.edit_message_text("پرداخت تأیید شد.")
    
    elif action == "reject":
        db.update_payment_status(user_id, "rejected")
        try:
            await context.bot.send_message(user_id, "پرداخت شما رد شد. لطفاً دوباره تلاش کنید.")
        except Forbidden:
            pass
        if query:
            await query.edit_message_text("پرداخت رد شد.")

async def reseller_handler(update: Update, context: CallbackContext):
    """این تابع منوی پنل نمایندگی را نمایش می‌دهد"""
    query = update.callback_query
    if query:
        await query.answer()
        chat_id = query.from_user.id
        message = query.message
    else:
        chat_id = update.message.from_user.id
        message = update.message
    
    user = db.get_user(chat_id)
    
    if user[4] < RESELLER_POINTS:
        insufficient_points_text = f"""
❌ <b>موجودی کافی ندارید!</b>

📊 <b>وضعیت امتیاز شما:</b>
• امتیاز مورد نیاز: {RESELLER_POINTS} امتیاز
• امتیاز فعلی شما: {user[4]} امتیاز
• کمبود: {RESELLER_POINTS - user[4]} امتیاز

💡 <b>راه‌های افزایش امتیاز:</b>
• از دوستان خود با لینک دعوت دعوت کنید ({REFERRAL_BONUS} امتیاز به از هر نفر)
• امتیاز خریداری کنید (از بخش خرید امتیاز)
• در صورت خرید کاربران دعوت شده توسط شما، پاداش دریافت کنید

🔗 <b>لینک دعوت شما:</b>
https://t.me/{context.bot.username}?start={chat_id}
        """
        
        keyboard = [
            [InlineKeyboardButton("خرید امتیاز 💎", callback_data="buy_points")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.answer("موجودی کافی ندارید!", show_alert=True)
            await safe_edit_message_text(query, insufficient_points_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(insufficient_points_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return
    
    # نمایش منوی پنل نمایندگی
    await show_reseller_menu(update, context)

async def show_reseller_menu(update: Update, context: CallbackContext):
    """این تابع منوی پنل نمایندگی را نمایش می‌دهد"""
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        is_callback = True
    else:
        message = update.message
        is_callback = False
    
    keyboard = [
        [InlineKeyboardButton("پنل نمایندگی چیست 😎؟", callback_data="what_is_reseller")],
        [InlineKeyboardButton("خرید پنل نمایندگی 🔓", callback_data="buy_reseller_panel")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "👻 <b>💎 پنل نمایندگی 💎</b>\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # اگر از طریق CallbackQuery فراخوانی شده باشد، پیام را ویرایش کن
    if is_callback:
        await safe_edit_message_text(query, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


# مثال برای reseller_what_is
async def reseller_what_is(update: Update, context: CallbackContext):
    """این تابع توضیحات پنل نمایندگی را نمایش می‌دهد"""
    query = update.callback_query
    await query.answer()
    
    explanation_text = """
پکیج نمایندگی (۲۰۰ هزار تومان) = (200 امتیاز)

توی این حالت، ما برای شما یه ربات اختصاصی مشابه ربات اصلی می‌سازیم و روی یه سرور جداگانه راه‌اندازی می‌کنیم.
شما پنل کامل مدیریت دارید و می‌تونید برای تا ۲۰ نفر سلف فعال کنید. تمام مراحل راه‌اندازی، پشتیبانی و تنظیمات رو هم ما براتون انجام می‌دیم.
این گزینه مناسب افرادیه که قصد دارن خودشون هم این خدمات رو ارائه بدن یا به فروش برسونن 💰

🌟 <b>ویژگی‌های پنل نمایندگی:</b>

• 🔧 <b>ربات اختصاصی</b>: مشابه ربات اصلی با برند شما
• 🖥️ <b>پنل مدیریت کامل</b>: کنترل کامل بر کاربران و خدمات
• 💰 <b>درآمدزایی مستقل</b>: فروش مستقیم به کاربران با قیمت خودتان
• 🌐 <b>سرور اختصاصی</b>: عملکرد سریع و بدون تداخل
• 👥 <b>ظرفیت 20 کاربر</b>: امکان فعال‌سازی برای حداکثر 20 نفر
• 🛠️ <b>راه‌اندازی رایگان</b>: نصب و تنظیمات توسط تیم ما
• 📞 <b>پشتیبانی 24 ساعته</b>: پشتیبانی شما و کاربرانتان
• 🔄 <b>به‌روزرسانی رایگان</b>: دسترسی به آخرین نسخه‌ها

💎 <b>مزایای ویژه:</b>

✅ کسب درآمد دائمی از فروش سلف
✅ برندینگ شخصی برای کسب‌وکار شما
✅ آموزش کامل استفاده از پنل
✅ پشتیبانی فنی و مشاوره‌ای
✅ امکان تعریف پلن‌های قیمت‌گذاری مختلف
✅ دسترسی به آمار و گزارشات فروش

🎯 <b>این پنل برای چه کسانی مناسب است؟</b>

• افرادی که قصد دارند خدمات سلف را ارائه دهند
• کسانی که به دنبال کسب درآمد آنلاین هستند
• تیم‌هایی که نیاز به مدیریت چند کاربر دارند
• فروشندگانی که می‌خواهند خدمات خود را گسترش دهند

برای بازگشت به منوی اصلی روی دکمه زیر کلیک کنید:
    """
    
    keyboard = [
        [InlineKeyboardButton("خرید پنل نمایندگی 🔓", callback_data="buy_reseller_panel")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await safe_edit_message_text(query, explanation_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def buy_reseller_panel(update: Update, context: CallbackContext):
    """این تابع خرید پنل نمایندگی را مدیریت می‌کند"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = db.get_user(user_id)
    
    # بررسی مجدد موجودی کاربر
    if user[4] < RESELLER_POINTS:
        insufficient_points_text = f"""
❌ <b>موجودی کافی ندارید!</b>

📊 <b>وضعیت امتیاز شما:</b>
• امتیاز مورد نیاز: {RESELLER_POINTS} امتیاز
• امتیاز فعلی شما: {user[4]} امتیاز
• کمبود: {RESELLER_POINTS - user[4]} امتیاز

💡 <b>راه‌های افزایش امتیاز:</b>
• از دوستان خود با لینک دعوت دعوت کنید ({REFERRAL_BONUS} امتیاز به از هر نفر)
• امتیاز خریداری کنید (از بخش خرید امتیاز)
• در صورت خرید کاربران دعوت شده توسط شما، پاداش دریافت کنید

🔗 <b>لینک دعوت شما:</b>
https://t.me/{context.bot.username}?start={user_id}
        """
        
        keyboard = [
            [InlineKeyboardButton("خرید امتیاز 💎", callback_data="buy_points")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(insufficient_points_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return
    
    # نمایش پیام درخواست توکن
    token_request_text = """
⏳ <b>در حال پردازش درخواست شما...</b>

لطفاً توکن ربات خود را ارسال کنید.

🔹 توکن باید از @BotFather دریافت شده باشد
🔹 توکن باید با عدد 1 شروع شود
🔹 طول توکن باید حداقل 30 کاراکتر باشد

پس از ارسال توکن، ساخت پنل شما آغاز می‌شود.
    """
    
    keyboard = [
        [InlineKeyboardButton("لغو", callback_data="cancel_reseller")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(token_request_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    # تنظیم وضعیت کاربر برای انتظار توکن
    context.user_data['state'] = AWAITING_TOKEN
    context.user_data['pending_reseller'] = True
    
    return AWAITING_TOKEN



async def token_received(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    # بررسی وضعیت کاربر
    state = context.user_data.get('state')
    pending_reseller = context.user_data.get('pending_reseller', False)
    
    # اگر کاربر در حالت انتظار توکن نیست
    if state != AWAITING_TOKEN:
        await update.message.reply_text("درخواست نامعتبر است. لطفاً از منوی اصلی اقدام کنید.")
        return ConversationHandler.END
    
    token = update.message.text.strip()
    
    # بررسی اعتبار توکن
    if len(token) < 30:
        await update.message.reply_text(
            "❌ توکن وارد شده معتبر نیست!\n\n"
            "لطفاً توکن صحیح را که از @BotFather دریافت کرده‌اید وارد کنید.\n\n"
            "توکن باید:\n"
            "• با عدد 1 شروع شود\n"
            "• حداقل 30 کاراکتر داشته باشد"
        )
        return AWAITING_TOKEN
    
    # پاک کردن وضعیت کاربر
    context.user_data['state'] = None
    is_reseller = context.user_data.pop('pending_reseller', False)
    
    if is_reseller:
        # پردازش خرید پنل نمایندگی
        user = db.get_user(user_id)
        
        # کسر امتیاز و ثبت درخواست
        db.add_points(user_id, -RESELLER_POINTS)
        db.cursor.execute(
            "UPDATE users SET reseller_purchase_count = reseller_purchase_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        db.conn.commit()
        
        # ارسال به ادمین
        try:
            admin_message = f"""
🆕 <b>درخواست جدید پنل نمایندگی</b>

👤 <b>مشخصات کاربر:</b>
• آیدی: {user_id}
• نام: {user[1]} {user[2]}
• یوزرنیم: @{user[3] if user[3] else 'ندارد'}

📋 <b>جزئیات درخواست:</b>
• نوع درخواست: پنل نمایندگی
• امتیاز کسر شده: {RESELLER_POINTS}
• توکن ربات: {token}
• زمان درخواست: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            await context.bot.send_message(ADMIN_ID, admin_message, parse_mode=ParseMode.HTML)
        except Forbidden:
            pass
        
        # محاسبه پاداش دعوت‌کنندگان
        bonuses = calculate_referral_bonus(user_id, RESELLER_REFERRAL_BONUS, db)
        for inviter_id, points in bonuses.items():
            db.add_points(inviter_id, points)
            inviter = db.get_user(inviter_id)
            
            # ارسال پیام به دعوت‌کننده
            try:
                bonus_message = f"""
🎉 <b>تبریک! پاداش دریافت کردید</b>

کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به خرید پنل نمایندگی کرد!

💰 <b>جزئیات پاداش:</b>
• مبلغ پاداش: {points} امتیاز
• نوع خرید: پنل نمایندگی
• موجودی جدید: {inviter[4] + points} امتیاز

🙏 از همراهی شما سپاسگزاریم!
                """
                await context.bot.send_message(inviter_id, bonus_message, parse_mode=ParseMode.HTML)
            except Forbidden:
                pass
        
        # پیام تأیید نهایی به کاربر
        success_text = f"""
✅ <b>درخواست شما با موفقیت ثبت شد!</b>

🎉 <b>پنل نمایندگی شما در حال ساخت است</b>

📋 <b>اطلاعات تکمیلی:</b>
• کد پیگیری: {str(user_id)[-6:]}
• زمان ساخت: 24-48 ساعت کاری
• پشتیبانی: 24 ساعته

🔧 <b>مراحل بعدی:</b>
• به زودی با شما تماس خواهیم گرفت
• اطلاعات لازم برای راه‌اندازی پنل دریافت می‌شود
• دسترسی‌های پنل مدیریت برای شما فعال خواهد شد
• آموزش کامل استفاده از پنل ارائه می‌شود

🌟 <b>از انتخاب شما سپاسگزاریم!</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
    else:
        # پردازش خرید سلف VIP (کد قبلی)
        user = db.get_user(user_id)
        
        # کسر امتیاز و ثبت درخواست
        db.add_points(user_id, -VIP_POINTS)
        db.cursor.execute(
            "UPDATE users SET vip_purchase_count = vip_purchase_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        db.conn.commit()
        
        # ارسال به ادمین
        try:
            admin_message = f"""
🆕 <b>درخواست جدید سلف VIP</b>

👤 <b>مشخصات کاربر:</b>
• آیدی: {user_id}
• نام: {user[1]} {user[2]}
• یوزرنیم: @{user[3] if user[3] else 'ندارد'}

📋 <b>جزئیات درخواست:</b>
• نوع درخواست: سلف VIP
• امتیاز کسر شده: {VIP_POINTS}
• توکن ربات: {token}
• زمان درخواست: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            await context.bot.send_message(ADMIN_ID, admin_message, parse_mode=ParseMode.HTML)
        except Forbidden:
            pass
        
        # محاسبه پاداش دعوت‌کنندگان
        bonuses = calculate_referral_bonus(user_id, VIP_REFERRAL_BONUS, db)
        for inviter_id, points in bonuses.items():
            db.add_points(inviter_id, points)
            inviter = db.get_user(inviter_id)
            
            # ارسال پیام به دعوت‌کننده
            try:
                bonus_message = f"""
🎉 <b>تبریک! پاداش دریافت کردید</b>

کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به خرید سلف VIP کرد!

💰 <b>جزئیات پاداش:</b>
• مبلغ پاداش: {points} امتیاز
• نوع خرید: سلف VIP
• موجودی جدید: {inviter[4] + points} امتیاز

🙏 از همراهی شما سپاسگزاریم!
                """
                await context.bot.send_message(inviter_id, bonus_message, parse_mode=ParseMode.HTML)
            except Forbidden:
                pass
        
        # پیام تأیید نهایی به کاربر
        success_text = f"""
✅ <b>درخواست شما با موفقیت ثبت شد!</b>

🎉 <b>سلف VIP شما در حال ساخت است</b>

📋 <b>اطلاعات تکمیلی:</b>
• کد پیگیری: {str(user_id)[-6:]}
• زمان ساخت: 1-2 ساعت کاری
• پشتیبانی: 24 ساعته

🔧 <b>مراحل بعدی:</b>
• به زودی با شما تماس خواهیم گرفت
• دسترسی‌های سلف برای شما فعال خواهد شد
• لینک فعالسازی برای شما ارسال می‌شود

🌟 <b>از انتخاب شما سپاسگزاریم!</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
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
    # پاک کردن وضعیت کاربر
    context.user_data['state'] = None
    
    await update.message.reply_text("عملیات لغو شد.", reply_markup=main_menu())
    return ConversationHandler.END

async def custom_points_handler(update: Update, context: CallbackContext):
    print("custom_points_handler فراخوانی شد")  # لاگ برای دیباگ
    
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
        
        # پاک کردن وضعیت دستی
        if 'state' in context.user_data:
            del context.user_data['state']
        
        print(f"وضعیت کاربر {user_id} به AWAITING_PAYMENT تغییر کرد")  # لاگ برای دیباگ
        return AWAITING_PAYMENT
    
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کنید.")
        return CUSTOM_POINTS

async def main_menu_buttons_handler(update: Update, context: CallbackContext):
    """این تابع دکمه‌های اصلی منو را مدیریت می‌کند"""
    text = update.message.text
    user_id = update.message.from_user.id
    
    print(f"دکمه فشرده شده: '{text}' توسط کاربر {user_id}")  # لاگ اصلی
    
    if text == "👻 سلف 𝐕𝐢𝐩 👻":
        print("در حال نمایش منوی VIP...")
        await show_vip_menu(update, context)
    elif text == "🫠 سلف رایگان 🫠":
        print("در حال نمایش سلف رایگان...")
        await free_self_handler(update, context)
    elif text == "🫠 امتیاز رایگان 🫠":
        print("در حال نمایش امتیاز رایگان...")
        await free_self_handler(update, context)
    elif text == "💍 خرید امتیاز 💍":
        print("در حال نمایش منوی خرید امتیاز...")
        await show_buy_points_menu(update, context)
    elif text == "💎 حساب کاربری 💎":
        print("در حال نمایش حساب کاربری...")
        await account_handler(update, context)
    elif text == "💎 پنل نمایندگی 💎":
        print("در حال نمایش پنل نمایندگی...")
        await show_reseller_menu(update, context)  # تغییر این خط
    else:
        print(f"دکمه ناشناخته: '{text}'")
        # پیام پیش‌فرض برای دکمه‌های ناشناخته
        await update.message.reply_text(
            "دکمه ناشناخته است. لطفا از منوی اصلی استفاده کنید.",
            reply_markup=main_menu()
        )


async def show_vip_menu(update: Update, context: CallbackContext):
    """این تابع منوی VIP را نمایش می‌دهد"""
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        is_callback = True
    else:
        message = update.message
        is_callback = False
    
    keyboard = [
        [InlineKeyboardButton("سلف چیست 🤖 ?", callback_data="what_is_self")],
        [InlineKeyboardButton("خرید سلف vip 🔥", callback_data="buy_vip")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "👻 <b>منوی سلف VIP</b>\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    if is_callback:
        await safe_edit_message_text(query, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_buy_points_menu(update: Update, context: CallbackContext):
    """این تابع منوی خرید امتیاز را نمایش می‌دهد"""
    # بررسی اینکه آیا از طریق CallbackQuery فراخوانی شده است یا نه
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        is_callback = True
    else:
        message = update.message
        is_callback = False
    
    keyboard = [
        [
            InlineKeyboardButton("10 امتیاز (10 تومان)", callback_data="buy_10"),
            InlineKeyboardButton("25 امتیاز (25 تومان)", callback_data="buy_25")
        ],
        [
            InlineKeyboardButton("50 امتیاز (45 تومان)", callback_data="buy_50"),
            InlineKeyboardButton("100 امتیاز (95 تومان)", callback_data="buy_100")
        ],
        [
            InlineKeyboardButton("200 امتیاز (180 تومان)", callback_data="buy_200"),
            InlineKeyboardButton("250 امتیاز (200 تومان)", callback_data="buy_250")
        ],
        [
            InlineKeyboardButton("خرید امتیاز دلخواه", callback_data="buy_custom"),
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "💎 <b>منوی خرید امتیاز</b>\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # اگر از طریق CallbackQuery فراخوانی شده باشد، پیام را ویرایش کن
    if is_callback:
        await safe_edit_message_text(query, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)





async def handle_text_messages(update: Update, context: CallbackContext):
    """این تابع پیام‌های متنی را مدیریت می‌کند"""
    user_id = update.message.from_user.id
    text = update.message.text
    
    print(f"پیام دریافت شد: {text} از کاربر {user_id}")  # لاگ برای دیباگ
    
    # اگر کاربر در حالت انتظار توکن است
    if context.user_data.get('state') == AWAITING_TOKEN:
        await token_received(update, context)
        return
    
    # اگر کاربر در حالت وارد کردن امتیاز دلخواه است
    if context.user_data.get('state') == CUSTOM_POINTS:
        await custom_points_handler(update, context)
        return
    
    # اگر پیام با / شروع شده، آن را نادیده بگیر
    if text.startswith('/'):
        return
    
    # بررسی برای دکمه‌های اصلی
    await main_menu_buttons_handler(update, context)

# در handlers.py
async def safe_edit_message_text(query, text, reply_markup=None, parse_mode=None):
    """این تابع پیام را فقط در صورت تفاوت ویرایش می‌کند"""
    try:
        # دریافت پیام فعلی
        current_message = query.message
        
        # مقایسه متن و کیبورد فعلی با جدید
        text_changed = current_message.text != text if current_message.text else True
        markup_changed = current_message.reply_markup != reply_markup if current_message.reply_markup else True
        
        # فقط در صورت تفاوت، پیام را ویرایش کن
        if text_changed or markup_changed:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        print(f"خطا در ویرایش پیام: {e}")



async def debug_conversation(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    print(f"وضعیت مکالمه کاربر {user_id}:")
    print(f"pending_payment: {context.user_data.get('pending_payment')}")
    print(f"conversation_state: {context.user_data.get('conversation_state')}")
    await update.message.reply_text("وضعیت مکالمه در کنسول چاپ شد")