import os
import httpx
from duckduckgo_search import DDGS  # أداة البحث المجانية في الويب
from finops_firewall import check_firewall_status
from database import update_tokens_usage

# جلب الإعدادات والمسارات من ملف .env
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"
MODEL = os.getenv("MODEL_NAME", "qwen2.5:7b")

def fetch_live_web_trends() -> str:
    """البحث في الإنترنت الحقيقي مجاناً عن أحدث ترندات الذكاء الاصطناعي اليوم"""
    try:
        print("🌐 [البحث الحي]: جاري جلب أحدث المقالات والترندات العالمية من الويب حالياً...")
        with DDGS() as ddgs:
            results = ddgs.text("latest Artificial Intelligence technology trends news", max_results=5)
            web_context = ""
            for i, r in enumerate(results, 1):
                web_context += f"📰 خبر {i}: {r['title']} - {r['body']}\n\n"
            return web_context
    except Exception as e:
        print(f"⚠️ فشل جلب البيانات من الويب، سيتم الاعتماد على الذاكرة الداخلية للنموذج: {e}")
        return "لا تتوفر سياقات حية من الويب حالياً."

async def get_trending_topics() -> tuple[bool, str]:
    """استدعاء نموذج Qwen المحلي لرصد وتخطيط 3 مواضيع بناءً على الترند العالمي الحقيقي."""
    # 1. التحقق من حائط الحماية المالي
    firewall_status = check_firewall_status()
    if firewall_status != "SAFE" and firewall_status != "SAFE_TO_RUN":
        return False, f"حائط الحماية المالي أو العتادي نشط: {firewall_status}"

    # 2. جلب البيانات الحقيقية من الإنترنت
    live_context = fetch_live_web_trends()

    # 3. صياغة النص الإرشادي الصارم بفرض اللغة العربية الفصحى ومنع الصينية
    prompt_instruction = (
        "أنت وكيل رصد الاتجاهات والتخطيط الحتمي (Trend Manager Expert).\n"
        f"إليك أحدث الأخبار الحقيقية والمحدثة حالياً المستخرجة من الإنترنت الحقيقي لعام 2026:\n"
        f"«««\n{live_context}\n»»»\n\n"
        "مهمتك: حلل هذه الأخبار الحية واقترح منها 3 مواضيع ساخنة ورائجة جداً ومناسبة لصناعة فيديوهات.\n"
        "اكتب العناوين باختصار وبأسلوب مشوق ومحفز للتفاعل، واشرح فكرة كل موضوع في سطر واحد فقط.\n"
        "🚨 تنبيه صارم وحتمي بخصوص اللغة:\n"
        "يجب أن يكون الرد باللغة العربية الفصحى السليمة بنسبة 100%.\n"
        "يُمنع منعاً باتاً كتابة أي حرف أو كلمة باللغة الصينية أو الإنجليزية أو أي لغة أخرى غير العربية الفصحى.\n"
        "لا تترجم جمل إرشادية، فقط اعطني النقاط الثلاثة مباشرة بالعربية الفصحى."
    )

    payload = {
        "model": MODEL,
        "prompt": prompt_instruction,
        "stream": False,
        "options": {
            "temperature": 0.5
        }
    }

    try:
        print(f"🤖 [وكيل الرصد]: جاري إرسال الترندات الحية لنموذج `{MODEL}` لصياغتها...")
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()

        ai_response = result.get("response", "لم يتم توليد نص.")
        
        prompt_tokens = result.get("prompt_eval_count", 0)
        completion_tokens = result.get("eval_count", 0)
        
        if prompt_tokens == 0 and completion_tokens == 0:
            words_count = len(prompt_instruction.split()) + len(ai_response.split())
            prompt_tokens = int(words_count * 0.3)
            completion_tokens = int(words_count * 0.7)

        update_tokens_usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
        print(f"📊 [وكيل الرصد]: تم تحديث الميزانية بعد استهلاك لـ ({prompt_tokens + completion_tokens}) توكن حقيقي.")
        
        return True, ai_response

    except httpx.ConnectError:
        return False, "❌ خطأ حرج: لم أتمكن من الاتصال بـ Ollama. تأكد من تشغيل خادم أولاما."
    except Exception as e:
        print(f"❌ خطأ داخلي في وكيل الرصد: {e}")
        return False, f"حدث خطأ غير متوقع أثناء استدعاء وكيل الرصد: {e}"

