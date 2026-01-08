import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings
from app.db.base import Base

print("Testing Alembic configuration...")
print("\n1. DATABASE_URL:")
print(f"   {settings.DATABASE_URL[:50]}...")

print("\n2. Tables detected:")
tables = list(Base.metadata.tables.keys())
for table in tables:
    print(f"   ✅ {table}")

print(f"\n3. Total tables: {len(tables)}")

if len(tables) > 0:
    print("\n✅ Configuration OK - Ready for migration")
else:
    print("\n❌ No tables detected - Check app/db/base.py")