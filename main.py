# در فایل main.py، بعد از وارد کردن ماژول‌ها
import logging
import asyncio
import sys
import os

# اضافه کردن مسیر پروژه به sys.path برای پیدا کردن ماژول‌های محلی
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, PicklePersistence, filters
from handlers import *
from admin import *
from database import Database
from config import BOT_TOKEN

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# غیرفعال کردن لاگ‌های httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def main():
    try:
        # ایجاد دیتابیس
        db = Database()
        
        # ایجاد application با persistence
        persistence = PicklePersistence(filepath='bot_data')
        app = Application.builder().token(BOT_TOKEN).persistence(persistence).build()
        
        # دستورات اصلی
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("admin", admin_panel))
        app.add_handler(CommandHandler("add_points", add_points_command))
        app.add_handler(CommandHandler("debug", debug_conversation))
        
        # کالبک‌های اصلی
        app.add_handler(CallbackQueryHandler(vip_handler, pattern='^(what_is_self|buy_vip)$'))
        app.add_handler(CallbackQueryHandler(buy_points_handler, pattern='^buy_points$'))
        app.add_handler(CallbackQueryHandler(admin_confirm_payment, pattern='^(confirm|reject)_'))
        app.add_handler(CallbackQueryHandler(reseller_handler, pattern='^buy_reseller$'))
        app.add_handler(CallbackQueryHandler(admin_add_points, pattern='^admin_add_points$'))
        app.add_handler(CallbackQueryHandler(admin_sales_report, pattern='^admin_sales_report$'))
        app.add_handler(CallbackQueryHandler(admin_new_users, pattern='^admin_new_users$'))
        app.add_handler(CallbackQueryHandler(back_to_main_handler, pattern='^back_to_main$'))
        # در main.py، بعد از هندلرهای اصلی
        app.add_handler(CallbackQueryHandler(show_vip_menu, pattern='^vip_menu$'))
        app.add_handler(CallbackQueryHandler(show_buy_points_menu, pattern='^buy_points$'))
        app.add_handler(CallbackQueryHandler(account_handler, pattern='^account$'))
        app.add_handler(CallbackQueryHandler(reseller_handler, pattern='^reseller$'))
        
        # در main.py
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(buy_points_handler, pattern='^buy_points$'),
                CallbackQueryHandler(reseller_handler, pattern='^buy_reseller_panel$')
            ],
            states={
                SELECTING_POINTS: [
                    CallbackQueryHandler(buy_points_handler, pattern=r'^buy_\d+$'),
                    CallbackQueryHandler(buy_points_handler, pattern='^buy_custom$')
                ],
                AWAITING_PAYMENT: [
                    MessageHandler(filters.PHOTO, payment_received),
                    CallbackQueryHandler(cancel_payment_handler, pattern='^cancel_payment$')
                ],
                AWAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, token_received)],
                CUSTOM_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_points_handler)]
            },
            fallbacks=[
                CommandHandler('cancel', cancel_handler),
                CallbackQueryHandler(cancel_payment_handler, pattern='^cancel_payment$')
            ],
            per_message=True,  # تغییر این مقدار
            name="payment_conversation",
            persistent=True
        )

        # اضافه کردن ConversationHandler با اولویت بالا
        app.add_handler(conv_handler)

        # سپس هندلرهای دیگر
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

        # در main.py، بعد از تعریف ConversationHandler
        # اضافه کردن هندلر مستقل برای عکس‌ها
        app.add_handler(MessageHandler(filters.PHOTO, payment_received))

        # اضافه کردن هندلر کالبک برای دکمه‌های عددی
        app.add_handler(CallbackQueryHandler(buy_points_handler, pattern=r'^buy_\d+$'))
        app.add_handler(CallbackQueryHandler(buy_points_handler, pattern='^buy_custom$'))
        app.add_handler(CallbackQueryHandler(buy_points_handler, pattern='^buy_points$'))
        app.add_handler(CommandHandler("debug_payment", debug_payment_status))

        # در main.py، بعد از هندلرهای اصلی
        app.add_handler(CallbackQueryHandler(reseller_what_is, pattern='^what_is_reseller$'))
        app.add_handler(CallbackQueryHandler(buy_reseller_panel, pattern='^buy_reseller_panel$'))
        app.add_handler(CallbackQueryHandler(show_reseller_menu, pattern='^reseller_menu$'))

        # در main.py، بعد از هندلرهای اصلی
        app.add_handler(CallbackQueryHandler(reseller_what_is, pattern='^what_is_reseller$'))
        app.add_handler(CallbackQueryHandler(buy_reseller_panel, pattern='^buy_reseller_panel$'))
        app.add_handler(CallbackQueryHandler(show_reseller_menu, pattern='^reseller_menu$'))
                
        # شروع ربات
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        # نگه داشتن ربات در حال اجرا
        logger.info("Bot started successfully!")
        
        # منتظر ماندن برای دریافت سیگنال توقف
        stop_signal = asyncio.Event()
        await stop_signal.wait()
        
        # توقف ربات
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == '__main__':
    try:
        # ایجاد حلقه رویداد جدید
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        # بستن حلقه رویداد
        try:
            loop.close()
        except:
            pass