#!/usr/bin/env python3
"""
数据库迁移命令行工具

使用方法:
  python migrate.py           # 执行迁移
  python migrate.py check     # 检查数据库状态
  python migrate.py rebuild   # 重建数据库（会清空数据，慎用！）
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from migrations.migrate import migrate_database, check_database_status
from database.connection import init_db


def rebuild_database():
    """重建数据库（警告：会清空所有数据）"""
    import os

    db_path = Path("pushmatrix.db")

    if db_path.exists():
        response = input("⚠️ 警告：此操作将删除所有数据！确定继续吗？(yes/no): ")
        if response.lower() != 'yes':
            print("❌ 操作已取消")
            return

        os.remove(db_path)
        print("🗑️ 已删除旧数据库")

    print("🔧 重建数据库...")
    init_db()
    print("✅ 数据库重建完成")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "check":
            check_database_status()
        elif command == "rebuild":
            rebuild_database()
        else:
            print(f"❌ 未知命令: {command}")
            print("\n使用方法:")
            print("  python migrate.py           # 执行迁移")
            print("  python migrate.py check     # 检查数据库状态")
            print("  python migrate.py rebuild   # 重建数据库（会清空数据）")
    else:
        migrate_database()
