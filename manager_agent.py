import os
import asyncio
from datetime import datetime

# تعريف الحالات الخمسة الأساسية للمنظومة بناءً على مواصفات الجيت هوب
STATE_IDLE = "IDLE"                             # خامل / جاهز للاستقبال
STATE_TREND_SEARCHING = "TREND_SEARCHING"       # جاري رصد المواضيع الرائجة
STATE_WRITING = "WRITING"                       # جاري كتابة وصياغة السيناريو
STATE_COMPLIANCE_CHECK = "COMPLIANCE_CHECK"     # جاري فحص الامتثال الشرعي والقانوني
STATE_WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL" # في انتظار موافقة المدير البشري

class ManagerAgent:
    def __init__(self):
        # الحالة الافتراضية عند بدء التشغيل هي الخمول
        self.current_state = STATE_IDLE
        self.last_update = datetime.now()

    def set_state(self, new_state: str) -> str:
        """
        تغيير حالة المنظومة وتحديث طابع الوقت.
        ترجع نصاً يوضح الانتقال لطباعته أو إرساله لتليجرام.
        """
        allowed_states = [
            STATE_IDLE, 
            STATE_TREND_SEARCHING, 
            STATE_WRITING, 
            STATE_COMPLIANCE_CHECK, 
            STATE_WAITING_FOR_APPROVAL
        ]
        
        if new_state in allowed_states:
            old_state = self.current_state
            self.current_state = new_state
            self.last_update = datetime.now()
            log_msg = f"🔄 [المدير المركزي]: تم تغيير الحالة من ({old_state}) إلى ◀ ({new_state})"
            print(log_msg)
            return log_msg
        else:
            raise ValueError(f"❌ حالة غير معرفة: {new_state}")

    def get_status_report(self) -> str:
        """توليد تقرير نصي جذاب ومناسب لإرساله لواجهة تليجرام HCI"""
        emojis = {
            STATE_IDLE: "💤 خامل وجاهز لأوامرك",
            STATE_TREND_SEARCHING: "🔍 جاري رصد وتخطيط المواضيع الساخنة (Trend Agent)...",
            STATE_WRITING: "📝 جاري صياغة وكتابة السيناريو الاحترافي (AI Writer)...",
            STATE_COMPLIANCE_CHECK: "⚖️ جاري فحص الالتزام الشرعي والقانوني (Compliance)...",
            STATE_WAITING_FOR_APPROVAL: "⏳ تم الإنتاج! في انتظار مراجعتك وموافقتك النهائية ليتسنى لنا النشر..."
        }
        
        duration = (datetime.now() - self.last_update).seconds
        
        report = (
            f"🧠 **تقرير حالة الوكيل المدير المركزي:**\n\n"
            f"🔹 **الحالة الحالية:** {emojis.get(self.current_state, self.current_state)}\n"
            f"🔹 **الوقت المستغرق في الحالة:** `{duration}` ثانية\n"
            f"🔹 **آخر تحديث:** `{self.last_update.strftime('%H:%M:%S')}`"
        )
        return report

# إنشاء نسخة مفردة (Singleton) من المدير ليتم استدعاؤها في كافة أجزاء المشروع بنفس الحالة
pipeline_manager = ManagerAgent()

