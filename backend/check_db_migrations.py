import sqlite3
import os
from pathlib import Path
from open_webui.env import DATA_DIR

def check_db_migrations():
    """检查数据库中的迁移记录"""
    db_path = Path(DATA_DIR) / "webui.db"
    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return
    
    print(f"数据库路径: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查alembic_version表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        if not cursor.fetchone():
            print("alembic_version表不存在，可能未初始化数据库")
            return
        
        # 查询当前版本
        cursor.execute("SELECT version_num FROM alembic_version")
        versions = cursor.fetchall()
        
        if not versions:
            print("数据库中未记录任何迁移版本")
        else:
            print(f"数据库中记录的版本:")
            for version in versions:
                print(f"- {version[0]}")
        
        conn.close()
    except Exception as e:
        print(f"查询数据库时出错: {e}")

if __name__ == "__main__":
    check_db_migrations() 