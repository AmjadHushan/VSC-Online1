import os
import asyncio
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
# استيراد حائط الحماية وقاعدة البيانات المالية من نفس مجلد الفلاشة
from finops_firewall import check_firewall_status
from database import update_tokens_usage, init_db
import sqlite3
from datetime import datetime

# استيراد الوكيل المدير المركزي وإدارة الحالات
from manager_agent import pipeline_manager, STATE_TREND_SEARCHING, STATE_WRITING, STATE_COMPLIANCE_CHECK, STATE_WAITING_FOR_APPROVAL, STATE_IDLE

# استيراد دالة وكيل رصد وتخطيط المواضيع الساخنة الحقيقية
from trend_agent import get_trending_topics
from writer_agent import generate_realism_script, direct_topic_handler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from telegram.ext import MessageHandler, filters

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def is_authorized(update: Update) -> bool:
    return str(update.effective_chat.id) == str(CHAT_ID).strip()

# وظيفة برمجية لتحديث ملف .env تلقائياً عند تغيير الإعدادات
def update_env_file(key: str, value: str):
    try:
        env_lines = []
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                env_lines = f.readlines()
        updated = False
        with open(".env", "w") as f:
            for line in env_lines:
                if line.startswith(f"{key}="):
                    f.write(f"{key}={value}\n")
                    updated = True
                else:
                    f.write(line)
            if not updated:
                f.write(f"{key}={value}\n")
    except Exception as e:
        print(f"⚠️ فشل حفظ التعديل في ملف .env: {e}")

# أمر البداية (/start)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    await update.message.reply_text(
        "🤖 **واجهة التحكم البشرية الآمنة (HCI) نشطة وممتثلة بالكامل!**\n\n"
        "📊 **أوامر المراقبة المالية:**\n"
        "🔹 `/budget` - عرض تقرير الاستهلاك الحالي والميزانية.\n"
        "🔹 `/test_firewall` - محاكاة استهلاك لفحص حائط الحماية.\n\n"
        "⚙️ **أوامر الإدارة والتعديل المباشر:**\n"
        "🔹 `/set_budget [الرقم]` - تعديل الحد الأقصى للتوكنز.\n"
        "🔹 `/set_requests [الرقم]` - تعديل حد الاستدعاءات اليومي.\n"
        "🔹 `/reset_budget` - تصفير استهلاك اليوم الحالي يدوياً.",
        parse_mode="Markdown"
    )

# أمر عرض الميزانية الحالي (/budget) مع دعم التنبيه عند 80%
async def show_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    
    usage = get_today_usage()
    max_tokens = int(os.getenv("MAX_DAILY_TOKENS", 50000))
    max_requests = int(os.getenv("MAX_DAILY_REQUESTS", 100))
    
    # حساب النسبة المئوية للاستهلاك لتنبيه المستخدم تدريجياً
    token_percentage = (usage['total_tokens'] / max_tokens) * 100
    status_emoji = "🟢"
    if token_percentage >= 100: status_emoji = "🔴"
    elif token_percentage >= 80: status_emoji = "🟡 (تنبيه: اقتربت من الحد الأقصى)"

    await update.message.reply_text(
        f"📊 **تقرير الميزانية الحالي (FinOps):** {status_emoji}\n\n"
        f"🔹 التوكنز المستهلكة اليوم: `{usage['total_tokens']}` / {max_tokens} ({token_percentage:.1f}%)\n"
        f"🔹 عدد الطلبات المنفذة: `{usage['total_requests']}` / {max_requests}\n"
        f"🔹 التكلفة التقديرية الحالية: `${usage['estimated_cost']:.4f}`",
        parse_mode="Markdown"
    )

# أمر تعديل حد التوكنز اليومي (/set_budget)
async def set_budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ صيغة خاطئة. مثال: `/set_budget 70000`")
        return
    
    new_limit = context.args[0]
    os.environ["MAX_DAILY_TOKENS"] = new_limit
    update_env_file("MAX_DAILY_TOKENS", new_limit)
    await update.message.reply_text(f"✅ تم تحديث الميزانية بنجاح! الحد اليومي الجديد للتوكنز: `{new_limit}`")

# أمر تعديل حد الطلبات اليومي (/set_requests)
async def set_requests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ صيغة خاطئة. مثال: `/set_requests 150`")
        return
    
    new_limit = context.args[0]
    os.environ["MAX_DAILY_REQUESTS"] = new_limit
    update_env_file("MAX_DAILY_REQUESTS", new_limit)
    await update.message.reply_text(f"✅ تم تحديث النظام! حد الطلبات اليومي الجديد: `{new_limit}` طلب.")

# أمر تصفير الميزانية يدوياً (/reset_budget)
async def reset_budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    
    today = datetime.now().strftime("%Y-%m-%d")
    DB_PATH = os.path.join(os.path.dirname(__file__), "finops_budget.db")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_usage WHERE date = ?", (today,))
        conn.commit()
        conn.close()
        await update.message.reply_text("🔄 **تم إعادة تصفير استهلاك الميزانية لليوم بنجاح!** يمكنك البدء من جديد الآن.")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل تصفير قاعدة البيانات: {e}")

# أمر الفحص التجريبي المحدث لحائط الحماية (/test_firewall)
async def test_firewall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return

    firewall_status = check_firewall_status()
    if firewall_status != "SAFE" and firewall_status != "SAFE_TO_RUN":
        return
    await update.message.reply_text("⏳ جاري إضافة 20,000 توكن محاكاة لاستدعاء النموذج...")
    update_tokens_usage(prompt_tokens=10000, completion_tokens=10000)

    await update.message.reply_text("⏳ محاكاة استدعاء للنموذج... جاري إضافة 20,000 توكن...")
update_tokens_usage(prompt_tokens=10000, completion_tokens=10000)
    
    # تحقق إضافي بعد التحديث لرصد التنبيه التدريجي عند 80%
    #usage = get_today_usage()
    #max_tokens = int(os.getenv("MAX_DAILY_TOKENS", 50000))
    #if (usage['total_tokens'] / max_tokens) >= 0.8 and usage['total_tokens'] < max_tokens:
    #    await update.message.reply_text("⚠️ **تنبيه حائط الحماية (Soft Ceiling):** استهلاكك تخطى 80% من الميزانية المتاحة لليوم!")
    #else:
    #    await update.message.reply_text("✅ تم تحديث الاستهلاك بنجاح.")

# أمر عرض حالة المنظومة الحالية (/status)
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    report = pipeline_manager.get_status_report()
    await update.message.reply_text(report, parse_mode="Markdown")

# أمر محاكاة تشغيل خط الإنتاج بالكامل (/run_pipeline)
async def run_pipeline_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    if pipeline_manager.current_state != STATE_IDLE:
        await update.message.reply_text("⚠ **تنبيه:** خط الإنتاج يعمل حالياً بالفعل ولا يمكن بدء دورة جديدة الآن!")
        return

    status_msg = await update.message.reply_text("🚀 **بدء تشغيل خط الإنتاج الآلي... جاري جلب المقالات الحية...**")
    pipeline_manager.set_state(STATE_TREND_SEARCHING)
    
    success, trend_result = await get_trending_topics()
    if not success:
        pipeline_manager.set_state(STATE_IDLE)
        await update.message.reply_text(f"❌ **توقف خط الإنتاج:**\n{trend_result}")
        return

    pipeline_manager.set_state(STATE_WAITING_FOR_APPROVAL)
    keyboard = [
        [InlineKeyboardButton("🔥 اختر الموضوع الأول وابدأ الكتابة", callback_data="trend_1")],
        [InlineKeyboardButton("💡 اختر الموضوع الثاني وابدأ الكتابة", callback_data="trend_2")],
        [InlineKeyboardButton("🚀 اختر الموضوع الثالث وابدأ الكتابة", callback_data="trend_3")]
    ]
    await update.message.reply_text(
        f"📋 **تقرير وكيل رصد المواضيع:**\n\n{trend_result}\n\n🚨 **بانتظار استجابتك البشرية الصارمة لتحديد مسار الكتابة:**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def pipeline_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    if not is_authorized(update): return

    if pipeline_manager.current_state != STATE_WAITING_FOR_APPROVAL:
        await query.edit_message_text("⚠ **عذراً:** هذه الدورة منتهية أو أن النظام ليس في حالة انتظار موافقة حالياً.")
        return

    pipeline_manager.set_state(STATE_WRITING)
    await query.edit_message_text(text=f"🟢 **تم استقبال اختيارك البشري بنجاح!**\n\n{pipeline_manager.get_status_report()}\n⏳ جاري استدعاء وكيل الكتابة والتعلم الواقعي عبر Ollama...")

    chosen_topic = f"الموضوع المختار برقم المعالج الحتمي: ({query.data})"
    
    success_write, script_result = await generate_realism_script(topic_context=chosen_topic)
    if not success_write:
        pipeline_manager.set_state(STATE_IDLE)
        await query.message.reply_text(f"❌ **فشل وكيل الكتابة في الإنتاج:**\n{script_result}")
        return

    await query.message.reply_text(
        f"📝 **السيناريو الاحترافي المولّد من (AI Writer Expert):**\n\n{script_result}",
        parse_mode="Markdown"
    )
    
    pipeline_manager.set_state(STATE_IDLE)
    await query.message.reply_text("✅ **انتهت مرحلة الكتابة الذاتية بنجاح!** المنظومة الآن خاملة بانتظار أوامرك القادمة.")


def main():
    print("🛰️ جاري بدء تشغيل البوت الممتثل بالكامل للمواصفات الاستراتيجية على الفلاشة...")
    init_db()
    pipeline_manager.set_state("IDLE")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("budget", show_budget))
    app.add_handler(CommandHandler("set_budget", set_budget_command))
    app.add_handler(CommandHandler("set_requests", set_requests_command))
    app.add_handler(CommandHandler("reset_budget", reset_budget_command))
    app.add_handler(CommandHandler("test_firewall", test_firewall_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("run_pipeline", run_pipeline_command))
    app.add_handler(CallbackQueryHandler(pipeline_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_topic_handler))

    app.run_polling(drop_pending_updates=True)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_topic_handler))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

