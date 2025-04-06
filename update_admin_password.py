from werkzeug.security import generate_password_hash
import os
import psycopg2
from psycopg2 import sql

# 新管理員密碼
new_password = 'm1234857'

# 生成密碼雜湊
password_hash = generate_password_hash(new_password)

print(f"為密碼 '{new_password}' 生成雜湊值: {password_hash}")

# 連接到數據庫
db_url = os.environ.get('DATABASE_URL')
if db_url:
    # 修正Postgres URL格式（如果需要）
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    # 連接到數據庫並更新管理員密碼
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 更新管理員密碼
        cur.execute("UPDATE admin SET password_hash = %s WHERE id = 1", (password_hash,))
        
        # 確認更新是否成功
        if cur.rowcount > 0:
            print(f"成功更新管理員密碼，影響行數: {cur.rowcount}")
        else:
            print("未能更新任何管理員記錄")
            
        # 提交更改
        conn.commit()
        
        # 關閉游標和連接
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"更新密碼時發生錯誤: {e}")
else:
    print("環境變量 DATABASE_URL 未設置")