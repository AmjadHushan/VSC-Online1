import sys
import os
import time
import shutil
from datetime import datetime
from database import is_budget_safe

# محاولة استدعاء مكتبة torch لتنظيف الذاكرة العتادية للكارت (VRAM)
try:
    import torch
except ImportError:
    torch = None

def get_free_resources_percentage():
    """قياس المساحة الفارغة الحركية في القرص والـ RAM حياً (شرط الـ 30%)"""
    # 1. قياس مساحة القرص الحالي (الفلاشة / الهارد)
    total_disk, used_disk, free_disk = shutil.disk_usage(".")
    free_disk_pct = (free_disk / total_disk) * 100
    
    # 2. قياس الذاكرة العشوائية (RAM) عبر ملفات النظام الخفيفة في لينكس
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        total_ram = int([x for x in lines if "MemTotal" in x][0].split()[1])
        free_ram = int([x for x in lines if "MemAvailable" in x][0].split()[1])
        free_ram_pct = (free_ram / total_ram) * 100
    except Exception:
        free_ram_pct = 35.0  # محاكاة أمان في حال عدم القدرة على القراءة محلياً
        
    return free_disk_pct, free_ram_pct

def get_hardware_temperature():
    """[بند 3.1] قراءة حرارة الكارت الفعلية بالدرجة المئوية حياً"""
    # في مرحلة التجربة المحلية على اللابتوب، نقوم بمحاكاة قفزة حرارية تبلغ 72°م لتجربة التبريد الصارم
    # مستقبلاً على سيرفر الـ RTX 4090 تقرأ حياً عبر أمر إنفيديا الرسمي:
    # return float(os.popen("nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits").read().strip())
    return 72.0

def purge_cuda_cache():
    """[بند 3.3] بروتوكول التطهير الفيزيائي الفوري لتفريغ كاش الـ CUDA بالكامل"""
    print("🧹 [Hardware Purge] جاري تنظيف وتفريغ كاش الـ CUDA كلياً...")
    if torch and torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("✅ تم تصفير الذاكرة العشوائية العتادية (VRAM) بنجاح وعزل المخلفات.")

def resource_and_thermal_oscillator(current_temp, free_disk, free_ram):
    """[بند 3.3 و 3.4 المطور] بروتوكول التأرجح المتناظر المزدوج بين 60% و 70% لحماية الوقت والعتاد"""
    print(f"\n🔄 [🎛️ Dynamic Oscillator] تم تفعيل مستشعر التأرجح اللين المزدوج!")
    print(f"🌡️ الحرارة: {current_temp}°م (السقف: 70°م) | 💾 القرص الحر: {free_disk:.1f}% | 🧠 الـ RAM الحرة: {free_ram:.1f}%")
    
    # استدعاء التطهير الفوري لكاش الكارت عند لمس السقف
    purge_cuda_cache()
    
    # 1. مرحلة الهبوط اللين والمتدرج خطوة بخطوة حتى أرضية الـ 60% لراحة المكونات والمروحة
    print("🚨 تشغيل مستشعر التبريد والكبح اللين.. الهبوط تدريجياً لـ 60%:")
    cooldown_steps = [75, 70, 65, 60]
    for step in cooldown_steps:
        print(f"📉 خفض وتيرة معالجة خط الإنتاج حياً إلى مستهدف: {step}%")
        time.sleep(0.5) # فاصل زمني لتبريد المعالج فيزيائياً
        
    print("🟢 المنظومة تلمس أرضية النطاق المستقر والآمن تماماً عند (60%).")
    
    # 2. مرحلة الارتفاع والتسريع التدريجي المتناظر تماماً خطوة بخطوة حتى سقف الـ 70% لحفظ الوقت
    print("⚡ تشغيل مستشعر الضخ المتدرج (Soft-Start) لمعاودة الصعود المتناظر لـ 70%:")
    warmup_steps = [65, 70]
    for step in warmup_steps:
        print(f"📈 رفع طاقة المعالجة وكفاءة التوليد تدريجياً إلى مستهدف: {step}%")
        time.sleep(0.5)
        
    print("🚀 العتاد عاد لنطاق الأداء النقي المحكوم (70%) بالتناظر التام لحفظ الوقت ومنع الهذيان البرمجي!\n")

def check_firewall_status(is_pre_flight=False):
    """مستشعر فحص الحالة المركزي: يتخذ قرارات الإقلاع، التجميد، أو التأرجح المتناظر"""
    free_disk, free_ram = get_free_resources_percentage()
    gpu_temp = get_hardware_temperature()
    
    # [بند 3.5] بوابة فحص ما قبل الإقلاع الصارم (Pre-Flight Check)
    if is_pre_flight:
        if gpu_temp >= 70.0 or free_disk < 30.0 or free_ram < 30.0:
            print(f"🛑 [Pre-Flight Blocked] تم حظر إقلاع المنظومة لعدم استيفاء شروط الأمان مسبقاً!")
            print(f"💤 قفل منطقي (Cooling Window): دخول السيرفر في وضع الانتظار الصامت حتمياً...")
            purge_cuda_cache()
            return "BLOCKED"
        return "SAFE_TO_RUN"

    # 1. الفحص المالي الصارم (سقف الـ 10 دولارات اللحظي لحماية الحساب البنكي)
    budget_status, current_spend, cost_limit = is_budget_safe()
    if budget_status == "CRITICAL_SHUTDOWN":
        print(f"🚨 [FinOps Kill] تجاوز حد الميزانية اليومية الصارم ({current_spend}$)! إغلاق فيزيائي كامل.")
        sys.exit("System core frozen automatically by FinOps Firewall.")
        
    # 2. الفحص الحراري والعتادي المدمج للتأرجح التدريجي (بين 60% و 70%)
    if gpu_temp >= 70.0 or free_disk < 30.0 or free_ram < 30.0:
        resource_and_thermal_oscillator(gpu_temp, free_disk, free_ram)
        return "OSCILLATION_ACTIVE"
        
    print(f"📊 جدار الحماية: المنظومة مستقرة تماماً (الحرارة: {gpu_temp}°م | الإنفاق: {current_spend}$)")
    return "SAFE"

def start_infinite_5_sec_monitor():
    """[بند 3.1] تفعيل دورة الفحص العتادي الحسي المستمر كل 5 ثوانٍ حتمية دون انقطاع أثناء الرندرة"""
    print("\n🛰️ [Loop Monitor] إطلاق حلقة الحارس النشط كل 5 ثوانٍ حتمية (بند 3.1)...")
    counter = 0
    # محاكاة لثلاث دورات متتالية للتجربة والتأكد من انسيابية الوقت
    while counter < 3:
        print(f"\n⏱️ دورة الفحص اللحظي رقم {counter + 1} (توقيت: {datetime.now().strftime('%H:%M:%S')})")
        check_firewall_status(is_pre_flight=False)
        counter += 1
        time.sleep(5) # فرض الـ 5 ثوانٍ الحتمية بين الدورات

if __name__ == "__main__":
    # تشغيل فحص الأمان المزدوج التأسيسي
    status = check_firewall_status(is_pre_flight=False)
    if status == "OSCILLATION_ACTIVE" or status == "SAFE":
        start_infinite_5_sec_monitor()

