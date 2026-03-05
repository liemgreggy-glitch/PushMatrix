"""
数据库迁移工具
自动检测并添加缺失的字段
"""
import re
import sqlite3
import os
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "pushmatrix.db"

# 所有应该存在的字段定义
REQUIRED_COLUMNS = {
    'accounts': {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'phone': 'VARCHAR(20) NOT NULL UNIQUE',
        'username': 'VARCHAR(50)',
        'first_name': 'VARCHAR(100)',
        'last_name': 'VARCHAR(100)',
        'session_string': 'TEXT',
        'api_id': 'INTEGER',
        'api_hash': 'VARCHAR(100)',
        'status': 'VARCHAR(20) DEFAULT "offline"',
        'is_spam': 'BOOLEAN DEFAULT 0',
        'is_banned': 'BOOLEAN DEFAULT 0',
        'proxy_id': 'INTEGER',
        'group_id': 'INTEGER',
        'two_fa_enabled': 'BOOLEAN DEFAULT 0',
        'two_fa': 'VARCHAR(255)',
        'health_score': 'INTEGER DEFAULT 0',
        'country': 'VARCHAR(50)',
        'country_flag': 'VARCHAR(10)',
        'country_code': 'VARCHAR(5)',
        'telegram_id': 'INTEGER',
        'registered_months': 'INTEGER',
        'tags': 'TEXT',
        'remark': 'TEXT',
        'restriction_status': 'VARCHAR(20)',
        'restriction_raw_reply': 'TEXT',
        'restriction_expire_time': 'VARCHAR(10)',
        'restriction_checked_at': 'DATETIME',
        'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'last_used_at': 'DATETIME',
    }
}


_SAFE_IDENTIFIER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _validate_identifier(name):
    """确保标识符只包含安全字符，防止 SQL 注入"""
    if not _SAFE_IDENTIFIER_RE.match(name):
        raise ValueError(f"不安全的标识符: {name!r}")


def get_existing_columns(cursor, table_name):
    """获取表中现有的字段"""
    _validate_identifier(table_name)
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1]: row[2] for row in cursor.fetchall()}  # {column_name: type}


def add_missing_columns(cursor, table_name, required_columns):
    """添加缺失的字段"""
    _validate_identifier(table_name)
    existing_columns = get_existing_columns(cursor, table_name)
    added_columns = []

    for column_name, column_type in required_columns.items():
        _validate_identifier(column_name)
        if column_name not in existing_columns:
            # 提取类型（去除 DEFAULT 等约束）
            clean_type = column_type.split('DEFAULT')[0].strip()
            default_value = ''

            # 提取默认值
            if 'DEFAULT' in column_type:
                default_part = column_type.split('DEFAULT')[1].strip()
                default_value = f' DEFAULT {default_part}'

            try:
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {clean_type}{default_value}"
                cursor.execute(sql)
                added_columns.append(column_name)
                print(f"✅ 添加字段: {table_name}.{column_name} ({clean_type})")
            except sqlite3.OperationalError as e:
                print(f"⚠️ 跳过字段 {column_name}: {e}")

    return added_columns


def migrate_database(db_path=None):
    """执行数据库迁移"""
    path = Path(db_path) if db_path else DATABASE_PATH

    if not path.exists():
        print("❌ 数据库文件不存在，请先运行应用初始化数据库")
        return False

    print("🔧 开始数据库迁移...")
    print(f"📁 数据库路径: {path}")

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
        if not cursor.fetchone():
            print("❌ accounts 表不存在，请先运行应用初始化数据库")
            return False

        # 迁移 accounts 表
        print("\n📋 检查 accounts 表...")
        added = add_missing_columns(cursor, 'accounts', REQUIRED_COLUMNS['accounts'])

        conn.commit()

        if added:
            print(f"\n✅ 迁移成功！添加了 {len(added)} 个字段:")
            for col in added:
                print(f"   - {col}")
        else:
            print("\n✅ 数据库已是最新版本，无需迁移")

        return True

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def check_database_status(db_path=None):
    """检查数据库状态"""
    path = Path(db_path) if db_path else DATABASE_PATH

    if not path.exists():
        print("❌ 数据库文件不存在")
        return

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    print("\n📊 数据库状态检查:")
    print(f"📁 路径: {path}")
    print(f"📏 大小: {path.stat().st_size / 1024:.2f} KB")

    # 检查表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n📋 表数量: {len(tables)}")

    for (table_name,) in tables:
        _validate_identifier(table_name)
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   - {table_name}: {count} 条记录")

        if table_name == 'accounts':
            existing_columns = get_existing_columns(cursor, table_name)
            required_columns = set(REQUIRED_COLUMNS['accounts'].keys())
            missing_columns = required_columns - set(existing_columns.keys())

            print(f"\n   字段检查:")
            print(f"   - 现有字段: {len(existing_columns)}")
            print(f"   - 需要字段: {len(required_columns)}")

            if missing_columns:
                print(f"   ⚠️ 缺失字段: {', '.join(missing_columns)}")
            else:
                print(f"   ✅ 所有字段完整")

    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_database_status()
    else:
        migrate_database()
        print("\n" + "=" * 60)
        check_database_status()
