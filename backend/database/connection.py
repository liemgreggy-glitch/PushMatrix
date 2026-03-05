from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models import account, proxy, task, message_log, statistics  # noqa: F401
    Base.metadata.create_all(bind=engine)


def check_and_migrate():
    """检查并自动迁移数据库，确保所有字段存在"""
    from pathlib import Path

    # Only applicable for SQLite databases
    if "sqlite" not in settings.database_url:
        init_db()
        return

    # Derive the file path from the database URL using SQLAlchemy's URL parsing
    from sqlalchemy.engine import make_url
    db_url = make_url(settings.database_url)
    db_file = db_url.database
    db_path = Path(db_file) if db_file else None

    if not db_path or not db_path.exists():
        print("📂 数据库不存在，创建新数据库...")
        init_db()
        return

    # Ensure tables exist
    init_db()

    # Check for missing columns
    inspector = inspect(engine)

    if 'accounts' not in inspector.get_table_names():
        return

    existing_columns = {col['name'] for col in inspector.get_columns('accounts')}
    from migrations.migrate import REQUIRED_COLUMNS
    required_columns = set(REQUIRED_COLUMNS.get('accounts', {}).keys()) - {'id'}
    missing_columns = required_columns - existing_columns

    if missing_columns:
        print(f"⚠️ 检测到缺失字段: {', '.join(missing_columns)}")
        print("🔧 正在执行自动迁移...")

        from migrations.migrate import migrate_database
        if migrate_database(db_path):
            print("✅ 数据库迁移成功")
        else:
            print("❌ 数据库迁移失败，请手动执行: python backend/migrate.py")
    else:
        print("✅ 数据库字段完整")
