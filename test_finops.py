import os
from database import init_db, update_tokens_usage
from finops_firewall import check_firewall_status

# 1. تصفير وتنظيف قاعدة البيانات لإجراء فحص مطهّر ومطابق للمواصفات
if os.path.exists("finops_budget.db"):
    os.remove("finops_budget.db")
init_db()

print("\n--- 🧪 بدء الفحص الأول المطور: آلية التأرجح لضمان كفاءة الوقت والإنتاج ---")

print("\n1️⃣ الحالة الأولى: إنتاج طبيعي ومستقر محلياً (ضمن منطقة الأمان الخضراء):")
update_tokens_usage(tokens_count=50000, words_count=1000, is_qwen_local=True)
check_firewall_status()

print("\n2️⃣ الحالة الثانية: ضغط واستهلاك يبلغ 82% (تفعيل الهبوط التدريجي حتى أرضية الـ 60% ثم معاودة الارتفاع):")
# ضخ توكنز لتصل الميزانية إلى 8.2 دولار لتفعيل المستشعر
update_tokens_usage(tokens_count=4100000, words_count=82000, is_qwen_local=False)
check_firewall_status()

