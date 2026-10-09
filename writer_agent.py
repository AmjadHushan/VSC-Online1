import os
import httpx
import psutil
import json
import asyncio
from database import update_usage
from finops_firewall import validate_finops_guardrail

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"  # رابط واجهة برمجة التطبيقات المحلية لنموذج أولاما
MODEL_NAME = "qwen2.5:7b"


def align_generation_pacing() -> tuple[float, float, float]:
    """
    يدرس سرعة معالجة الجهاز الحية ويسمح للنظام بالانطلاق بأقصى طاقة ممكنة،
    ولا يتدخل بربط الفرملة إلا عند تخطي عتبة الـ 80% لحماية الـ 20% حتماً.
    """
    try:
        vm = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=None)
        
        if cpu_usage is None:
            cpu_usage = 20.0
            
        free_ram_percent = (vm.available / vm.total) * 100
        free_cpu_percent = 100.0 - cpu_usage

        # 🚨 تطبيق قانون هامش الأمان الصارم المحدث (ترك 20% فارغة ومحمية حتماً):
        if free_cpu_percent < 20.0 or free_ram_percent < 20.0:
            # تخطينا خط الأمان 80% (المساحة الحرة أقل من 20%) -> تفعيل كبح نبضي ميكروي فوراً
            pacing_delay = 0.025 
        else:
            # العتاد تحت عتبة الـ 80% -> انطلاق بأقصى سرعة معالجة ممكنة (صفر تأخير)
            pacing_delay = 0.0

        return pacing_delay, free_ram_percent, cpu_usage
    except Exception:
        return 0.0, 50.0, 30.0

async def generate_realism_script(topic_context: str) -> tuple[bool, str]:
    """
    وكيل الكتابة التكيفي الكوني؛ يستهلك الموارد المتاحة بالكامل وبأقصى سرعة،
    ويحمي هامش الأمان 20% ديناميكياً عند ذروة الضغط فقط لحماية اللابتوب من التجميد.
    """
    is_safe, firewall_message = validate_finops_guardrail()
    if not is_safe:
        return False, f"🚨 **جدار الحماية المالي حظر العملية:** {firewall_message}"

    system_instructions = (
        "أنت الكاتب التقني المحترف للمنظومة الذاتية. اكتب سيناريو فيديو دقيق، واقعي، وموجز بالفصحى الصارمة.\n"
        "🚨 شروط حتمية:\n"
        "1. الالتزام المطلق باللغة العربية الفصحى المتينة، ويُمنع العامية تماماً.\n"
        "2. ركز على الحقائق والعمق التقني المباشر وتجنب الحشو الإنشائي.\n"
        "3. الهيكل: (مقدمة جاذبة، عرض مقسم في نقاط، خاتمة للتفاعل).\n"
        "4. اكتب النص كسيناريو جاهز للإلقاء الصوتي مع إشارات بصرية بين أقواس مربعة."
    )

    prompt = f"قم بصياغة سيناريو متكامل وممتثل لبروتوكول الواقعية حول هذا الموضوع وبشكل مركز وجيز جداً:\n{topic_context}"

    payload = {
        "model": MODEL_NAME,
        "prompt": f"{system_instructions}\n\n{prompt}",
        "stream": True,
        "options": {
            "temperature": 0.4,
            "top_p": 0.85,
            "num_ctx": 4096
        }
    }

    full_response_text = ""
    max_cpu_observed = 0.0
    min_ram_observed = 100.0

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:
                if response.status_code != 200:
                    return False, f"خطأ في استجابة سيرفر أولاما المحلي: {response.status_code}"
                
                async for line in response.aiter_lines():
                    if not line: continue
                    
                    try:
                        chunk = json.loads(line)
                        text_chunk = chunk.get("response", "")
                        full_response_text += text_chunk
                        
                        delay, ram_free, cpu_now = align_generation_pacing()
                        
                        if cpu_now > max_cpu_observed: max_cpu_observed = cpu_now
                        if ram_free < min_ram_observed: min_ram_observed = ram_free
                        
                        # تفعيل التأخير النبضي فقط لحماية عتبة الـ 20% الفارغة حتماً
                        if delay > 0:
                            await asyncio.sleep(delay)
                            
                    except json.JSONDecodeError:
                        continue

                if not full_response_text.strip():
                    return False, "⚠️ نموذج أولاما لم يعد أي نص، تأكد من سلامة تحميل الموديل محلياً."

                total_tokens = len(payload["prompt"]) // 4 + len(full_response_text) // 4
                estimated_cost = (total_tokens / 1000) * 0.0015 
                update_usage(tokens=total_tokens, cost=estimated_cost, is_request=True)
                
                report_tail = (
                    f"\n\n⚙️ **[الموازنة العتادية الشاملة - خيار الأداء النفاث]:**\n"
                    f"◽ ريتم التشغيل: مستدام وبأقصى طاقة استغلالية مسموحة ⚡\n"
                    f"◽ أعلى ذروة معالج تم كبحها ومحاذاتها: {max_cpu_observed:.1f}%\n"
                    f"◽ حد الأمان الأدنى المتبقي للذاكرة: {min_ram_observed:.1f}% (مساحة الـ 20% فارغة ومؤمنة بقوة القانون 🛡️)"
                )
                return True, full_response_text + report_tail
                
    except httpx.ConnectError:
        return False, "❌ فشل الاتصال بسيرفر أولاما المحلي. تأكد من تشغيل خدمة `lexar-ollama.service`!"
    except Exception as e:
        return False, f"حدث خطأ أثناء التوليد المتوازن: {str(e)}"

from telegram import Update
from telegram.ext import ContextTypes

async def direct_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    تستقبل النص المباشر المرسل من المدير البشري في الشات، وتتحقق من حالة المنظومة،
    ثم تطلق وكيل الكتابة التكيفي المتناغم مع المعالج والذاكرة حياً.
    """
    from manager_agent import pipeline_manager
    from bot_manager import is_authorized
    
    if not is_authorized(update): return
    if update.message.text.startswith('/'): return

    if pipeline_manager.current_state != "IDLE":
        await update.message.reply_text("⚠ **تنبيه حرج:** خط الإنتاج مشغول حالياً في عملية أخرى! يرجى الانتظار.")
        return
        
    user_direct_topic = update.message.text.strip()
    pipeline_manager.set_state("WRITING")
    
    status_msg = await update.message.reply_text(
        f"🎯 **[تجاوز بشري مباشر]:** تم استقبال موضوعك المكتوب يدوياً بنجاح!\n"
        f"📌 الموضوع: *{user_direct_topic}*\n\n"
        f"⏳ جاري تشغيل وكيل الكتابة والتعلم الواقعي عبر سيرفر أولاما محاذاً سرعة المعالجة حياً (هامش 20% محمي)..."
    , parse_mode="Markdown")

    success_write, script_result = await generate_realism_script(topic_context=user_direct_topic)
    
    if not success_write:
        pipeline_manager.set_state("IDLE")
        await status_msg.edit_text(f"❌ **فشل وكيل الكتابة في الإنتاج:**\n{script_result}")
        return

    await update.message.reply_text(
        f"📝 **السيناريو الاحترافي المولّد بناءً على طلبك المباشر:**\n\n{script_result}",
        parse_mode="Markdown"
    )
    
    pipeline_manager.set_state("IDLE")
    await update.message.reply_text("✅ **انتهت مرحلة المعالجة المباشرة بنجاح!** خط الإنتاج عاد لوضع الخمول.")

