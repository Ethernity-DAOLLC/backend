import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import engine
from app.db.base import Base
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    try:
        logger.info("🔧 Creating database tables...")
        logger.info(f"📍 Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'local'}")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully!")
        logger.info("📋 Tables created:")
        for table_name in Base.metadata.tables.keys():
            logger.info(f"   - {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        logger.exception(e)
        return False

def drop_tables():
    try:
        logger.warning("⚠️  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ All tables dropped")
        return True
    except Exception as e:
        logger.error(f"❌ Error dropping tables: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Database table management")
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Drop all tables before creating (DANGEROUS!)'
    )
    args = parser.parse_args()
    
    if args.drop:
        response = input("⚠️  This will DELETE ALL DATA. Are you sure? (yes/no): ")
        if response.lower() == 'yes':
            drop_tables()
        else:
            logger.info("Operation cancelled")
            sys.exit(0)
    success = create_tables()
    sys.exit(0 if success else 1)