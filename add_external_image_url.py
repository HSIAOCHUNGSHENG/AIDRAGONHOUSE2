import os
from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy import text

# 獲取數據庫連接字符串
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # SQLAlchemy 1.4+ compatibility for postgres URLs
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # 連接數據庫
    engine = create_engine(database_url)
    metadata = MetaData()
    
    try:
        # 反射現有的 portfolio 表
        portfolio = Table('portfolio', metadata, autoload_with=engine)
        
        # 檢查字段是否已存在
        if 'external_image_url' not in portfolio.c:
            # 創建 ALTER TABLE 語句
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE portfolio ADD COLUMN external_image_url VARCHAR(255)")
                )
                conn.commit()
                print("成功添加 external_image_url 字段到 portfolio 表")
        else:
            print("external_image_url 字段已存在於 portfolio 表中")
    except Exception as e:
        print(f"發生錯誤: {e}")
else:
    print("未設置 DATABASE_URL 環境變量")