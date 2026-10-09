import sqlite3
import os
from datetime import datetime

DB_NAME = "finops_budget.db"

def init_db():
    """تأسيس وتأمين جداول قاعدة البيانات لحماية الميزانية وحفظ حالات المنظومة حياً"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. جدول تتبع الإنفاق اليومي واستهلاك التوكنز لنموذج Qwen المحلي
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_budget (
            date TEXT PRIMARY KEY,
            tokens_consumed INTEGER DEFAULT 0,
            words_generated INTEGER DEFAULT 0,
            estimated_cost_usd REAL DEFAULT 0.0,
            cost_limit_usd REAL DEFAULT 10.0
        )
    ''')
    
    # 2. جدول إدارة حالات طابور الإنتاج (Pipeline States) لتنسيق عمل الوكلاء
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_status (
            key TEXT PRIMARY KEY,
            current_state TEXT,
            last_updated TEXT,
            metadata TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def update_tokens_usage(tokens_count, words_count, is_qwen_local=True):
    """تحديث العداد العتادي والمالي اللحظي لليوم الحالي (نموذج Qwen المحلي تكلفته 0$)"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # بما أن Qwen يعمل محلياً فالتكلفة صفر، وإذا انتقلنا للسحابي مستقبلاً تحسب التكلفة تلقائياً
    estimated_cost = 0.0 if is_qwen_local else (tokens_count * 0.000002)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO daily_budget (date, tokens_consumed, words_generated, estimated_cost_usd, cost_limit_usd)
        VALUES (?, ?, ?, ?, 10.0)
        ON CONFLICT(date) DO UPDATE SET
            tokens_consumed = tokens_consumed + ?,
            words_generated = words_generated + ?,
            estimated_cost_usd = estimated_cost_usd + ?
    ''', (today, tokens_count, words_count, estimated_cost, tokens_count, words_count, estimated_cost))
    
    conn.commit()
    conn.close()

def is_budget_safe():
    """مستشعر الأمان المالي اللحظي: يفحص الميزانية الحالية ويعود بحالة الأمان ونسبة الاستهلاك"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT estimated_cost_usd, cost_limit_usd FROM daily_budget WHERE date = ?", (today,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return "SAFE", 0.0, 10.0
        
    current_cost, cost_limit = row
    
    if current_cost >= cost_limit:
        return "CRITICAL_SHUTDOWN", current_cost, cost_limit
    elif current_cost >= (cost_limit * 0.8):
        return "WARNING_80", current_cost, cost_limit
        
    return "SAFE", current_cost, cost_limit

if __name__ == "__main__":
    init_db()
    print("✅ تم تأسيس البنية التحتية لحائط الصد المالي finops_budget.db المتوافق مع Qwen بنجاح.")


