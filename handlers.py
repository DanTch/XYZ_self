from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode
from telegram.error import Forbidden
from database import Database
from keyboards import *
from config import *
import os
from utils import format_user_info, calculate_referral_bonus

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
🤖 **سلف چیست؟**

سلف یک ربات است که بر روی اکانت تلگرام شما قرار میگیرد و قابلیت‌هایی را فراهم می‌کند که کاربران معمولی تلگرام ندارند. با داشتن سلف، شما یک پله از کاربران عادی جلوتر هستید!

📋 **قابلیت‌های پرکاربردی سلف:**

• 🔇 **سکوت دادن در پیوی**: می‌توانید فردی را در پیوی سکوت دهید (بدون بلاک کردن)
• 💾 **سیو تایم دار**: ذخیره خودکار عکس و فیلم با زمان‌بندی مشخص
• 🔄 **سیو بعد از پاک**: ذخیره محتوا حتی بعد از پاک شدن در چت
• 📝 **فهمیدن متن ادیت شده**: مشاهده متن قبل از ویرایش
• 👁️ **فهمیدن متن پاک شده**: مشاهده پیام‌های حذف شده
• 😈 **تنظیم دشمن**: فحش خودکار به افراد نامطلوب
• 😄 **تنظیم دشمنک**: فحش دوستانه به دوستان (برای سرگرمی)
• ⏰ **ساعت در کنار اسم**: ساعت زنده که هر دقیقه آپدیت می‌شود
• 📅 **ساعت و تاریخ در بیو**: تاریخ و ساعت زنده در بیوگرافی
• 💾 **سیو از محدودیت‌ها**: ذخیره از چت‌ها و محتواهای محدود (مثل SCAM)

🌟 **با سلف VIP چه مزایایی دارید؟**

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
            await query.edit_message_text(explanation_text, reply_markup=reply_markup)
        else:
            await message.reply_text(explanation_text, reply_markup=reply_markup)
        return
    
    elif query and query.data == "buy_vip":
        # بررسی موجودی کاربر
        if user[4] < VIP_POINTS:
            insufficient_points_text = f"""
❌ **موجودی کافی ندارید!**

📊 **وضعیت امتیاز شما:**
• امتیاز مورد نیاز: {VIP_POINTS} امتیاز
• امتیاز فعلی شما: {user[4]} امتیاز
• کمبود: {VIP_POINTS - user[4]} امتیاز

💡 **راه‌های افزایش امتیاز:**
• از دوستان خود با لینک دعوت دعوت کنید ({REFERRAL_BONUS} امتیاز به از هر نفر)
• امتیاز خریداری کنید (از بخش خرید امتیاز)
• در صورت خرید کاربران دعوت شده توسط شما، پاداش دریافت کنید

🔗 **لینک دعوت شما:**
https://t.me/{context.bot.username}?start={chat_id}
            """
            
            keyboard = [
                [InlineKeyboardButton("خرید امتیاز 💎", callback_data="buy_points")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if query:
                await query.answer("موجودی کافی ندارید!", show_alert=True)
                await query.edit_message_text(insufficient_points_text, reply_markup=reply_markup)
            else:
                await message.reply_text(insufficient_points_text, reply_markup=reply_markup)
            return
        
        # نمایش پیام پردازش
        processing_text = """
⏳ **در حال پردازش درخواست شما...**
لطفاً چند لحظه صبر کنید، درخواست شما در حال بررسی است.
        """
        
        keyboard = [
            [InlineKeyboardButton("لغو", callback_data="cancel_vip")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(processing_text, reply_markup=reply_markup)
        else:
            await message.reply_text(processing_text, reply_markup=reply_markup)
        
        # شبیه‌سازی پردازش
        import asyncio
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
🆕 **درخواست جدید سلف VIP**

👤 **مشخصات کاربر:**
• آیدی: {chat_id}
• نام: {user[1]} {user[2]}
• یوزرنیم: @{user[3] if user[3] else 'ندارد'}

📋 **جزئیات درخواست:**
• نوع درخواست: سلف VIP
• امتیاز کسر شده: {VIP_POINTS}
• زمان درخواست: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            await context.bot.send_message(ADMIN_ID, admin_message)
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
🎉 **تبریک! پاداش دریافت کردید**

کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به خرید سلف VIP کرد!

💰 **جزئیات پاداش:**
• مبلغ پاداش: {points} امتیاز
• نوع خرید: سلف VIP
• موجودی جدید: {inviter[4] + points} امتیاز

🙏 از همراهی شما سپاسگزاریم!
                """
                await context.bot.send_message(inviter_id, bonus_message)
            except Forbidden:
                pass
        
        # پیام تأیید نهایی به کاربر
        success_text = """
✅ **درخواست شما با موفقیت ثبت شد!**

🎉 **سلف VIP شما در حال ساخت است**

📋 **اطلاعات تکمیلی:**
• کد پیگیری: {str(chat_id)[-6:]}
• زمان ساخت: 1-2 ساعت کاری
• پشتیبانی: 24 ساعته

🔧 **مراحل بعدی:**
• به زودی با شما تماس خواهیم گرفت
• دسترسی‌های سلف برای شما فعال خواهد شد
• لینک فعالسازی برای شما ارسال می‌شود

🌟 **از انتخاب شما سپاسگزاریم!**
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(success_text, reply_markup=reply_markup)
        else:
            await message.reply_text(success_text, reply_markup=reply_markup)


            
async def buy_points_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        await query.answer()
    
    if query and query.data == "buy_points":
        await show_buy_points_menu(update, context)
        return SELECTING_POINTS  # برگرداندن وضعیت صحیح
    
    if query and query.data.startswith("buy_"):
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
        return AWAITING_PAYMENT  # برگرداندن وضعیت انتظار پرداخت
    
    elif query and query.data == "buy_custom":
        await query.edit_message_text("مقدار امتیاز مورد نظر را وارد کنید:")
        return CUSTOM_POINTS



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
        [InlineKeyboardButton("10 امتیاز (10 تومان)", callback_data="buy_10")],
        [InlineKeyboardButton("25 امتیاز (25 تومان)", callback_data="buy_25")],
        [InlineKeyboardButton("50 امتیاز (45 تومان)", callback_data="buy_50")],
        [InlineKeyboardButton("100 امتیاز (85 تومان)", callback_data="buy_100")],
        [InlineKeyboardButton("250 امتیاز (200 تومان)", callback_data="buy_250")],
        [InlineKeyboardButton("خرید امتیاز دلخواه", callback_data="buy_custom")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "💎 **منوی خرید امتیاز**\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # اگر از طریق CallbackQuery فراخوانی شده باشد، پیام را ویرایش کن
    if is_callback:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await message.reply_text(text, reply_markup=reply_markup)
        

async def payment_received(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    photo_file_id = update.message.photo[-1].file_id
    
    print(f"عکس دریافت شده از کاربر {user_id}")  # لاگ برای دیباگ
    
    # بررسی وجود پرداخت در انتظار
    payment_data = context.user_data.get("pending_payment")
    if not payment_data:
        print("هیچ پرداخت در انتظاری وجود ندارد")
        await update.message.reply_text("هیچ پرداخت در انتظاری وجود ندارد. لطفاً از منوی اصلی اقدام کنید.")
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
        del context.user_data["pending_payment"]
        
    except Exception as e:
        print(f"خطا در پردازش پرداخت: {e}")  # لاگ خطا
        await update.message.reply_text(
            "❌ خطایی در پردازش پرداخت رخ داد\n"
            "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
    
    return ConversationHandler.END

async def cancel_payment_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
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
        if query:
            await query.answer("موجودی کافی ندارید!", show_alert=True)
        else:
            await message.reply_text("❌ موجودی کافی ندارید!\n\n"
                                  f"امتیاز مورد نیاز: {RESELLER_POINTS}\n"
                                  f"امتیاز شما: {user[4]}\n\n"
                                  "برای افزایش امتیاز می‌توانید:\n"
                                  "• از دوستان خود دعوت کنید\n"
                                  "• امتیاز خریداری کنید")
        return
    
    # نمایش پیام تحلیل و پردازش
    if query:
        await query.edit_message_text(
            "⏳ در حال تحلیل درخواست شما...\n"
            "لطفاً چند لحظه صبر کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("لغو", callback_data="cancel_reseller_purchase")]
            ])
        )
    else:
        await message.reply_text(
            "⏳ در حال تحلیل درخواست شما...\n"
            "لطفاً چند لحظه صبر کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("لغو", callback_data="cancel_reseller_purchase")]
            ])
        )
    
    # شبیه‌سازی پردازش
    import asyncio
    await asyncio.sleep(2)
    
    # کسر امتیاز و درخواست توکن
    db.add_points(chat_id, -RESELLER_POINTS)
    db.cursor.execute(
        "UPDATE users SET reseller_purchase_count = reseller_purchase_count + 1 WHERE user_id = ?",
        (chat_id,)
    )
    db.conn.commit()
    
    if query:
        await query.edit_message_text(
            "✅ درخواست شما با موفقیت ثبت شد!\n\n"
            "🔹 لطفاً توکن ربات خود را ارسال کنید\n"
            "🔹 توکن باید از @BotFather دریافت شده باشد\n"
            "🔹 پس از ارسال توکن، ساخت پنل شما آغاز می‌شود"
        )
    else:
        await message.reply_text(
            "✅ درخواست شما با موفقیت ثبت شد!\n\n"
            "🔹 لطفاً توکن ربات خود را ارسال کنید\n"
            "🔹 توکن باید از @BotFather دریافت شده باشد\n"
            "🔹 پس از ارسال توکن، ساخت پنل شما آغاز می‌شود"
        )
    
    # تنظیم وضعیت کاربر برای انتظار توکن
    context.user_data['state'] = AWAITING_TOKEN
    
    return AWAITING_TOKEN

async def token_received(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    # بررسی وضعیت کاربر
    state = context.user_data.get('state')
    
    # اگر کاربر در حالت انتظار توکن نیست
    if state != AWAITING_TOKEN:
        await update.message.reply_text("درخواست نامعتبر است. لطفاً از منوی اصلی اقدام کنید.")
        return ConversationHandler.END
    
    token = update.message.text.strip()
    
    # بررسی اعتبار توکن
    if not token.startswith('1') or len(token) < 30:
        await update.message.reply_text(
            "❌ توکن وارد شده معتبر نیست!\n\n"
            "لطفاً توکن صحیح را که از @BotFather دریافت کرده‌اید وارد کنید."
        )
        return AWAITING_TOKEN
    
    # پاک کردن وضعیت کاربر
    context.user_data['state'] = None
    
    # ارسال به ادمین
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"درخواست ساخت پنل نمایندگی:\n\n"
            f"کاربر: {user_id}\n"
            f"یوزرنیم: @{update.message.from_user.username if update.message.from_user.username else 'ندارد'}\n"
            f"توکن: {token}"
        )
    except Forbidden:
        pass
    
    # محاسبه پاداش دعوت‌کنندگان
    bonuses = calculate_referral_bonus(user_id, RESELLER_REFERRAL_BONUS, db)
    for inviter_id, points in bonuses.items():
        db.add_points(inviter_id, points)
        inviter = db.get_user(inviter_id)
        try:
            await context.bot.send_message(
                inviter_id,
                f"کاربری که با کد دعوت شما وارد ربات شده بود، اقدام به خرید پنل نمایندگی کرد.\n\n"
                f"🎁 {points} امتیاز به شما اضافه شد.\n"
                f"موجودی جدید: {inviter[4] + points}"
            )
        except Forbidden:
            pass
    
    # ارسال پیام تأیید به کاربر
    await update.message.reply_text(
        "✅ توکن شما با موفقیت دریافت شد!\n\n"
        "🔹 پنل نمایندگی شما در حال ساخت است\n"
        "🔹 به زودی با شما تماس خواهیم گرفت\n"
        "🔹 مدت زمان ساخت: 24-48 ساعت\n\n"
        "📋 کد پیگیری شما: " + str(user_id)[-6:]
    )
    
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
        await reseller_handler(update, context)
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
        "👻 **منوی سلف VIP**\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    if is_callback:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await message.reply_text(text, reply_markup=reply_markup)



# تابع جدید برای مدیریت پیام‌های متنی
async def handle_text_messages(update: Update, context: CallbackContext):
    """این تابع پیام‌های متنی را مدیریت می‌کند"""
    user_id = update.message.from_user.id
    text = update.message.text
    
    print(f"پیام دریافت شد: {text} از کاربر {user_id}")  # اضافه کردن لاگ برای دیباگ
    
    # اگر کاربر در حالت انتظار توکن است
    if context.user_data.get('state') == AWAITING_TOKEN:
        await token_received(update, context)
        return
    
    # اگر پیام با / شروع شده، آن را نادیده بگیر
    if text.startswith('/'):
        return
    
    # بررسی برای دکمه‌های اصلی
    await main_menu_buttons_handler(update, context)