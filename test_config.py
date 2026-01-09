import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, check_connection
from sqlalchemy import inspect, text
import importlib.util

def print_header(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_success(text: str):
    print(f"✅ {text}")

def print_error(text: str):
    print(f"❌ {text}")

def print_warning(text: str):
    print(f"⚠️  {text}")

def print_info(text: str):
    print(f"ℹ️  {text}")

def check_database_connection():
    print_header("1. DATABASE CONNECTION")
    db_url = settings.DATABASE_URL
    if "@" in db_url:
        parts = db_url.split("@")
        masked = parts[0].split(":")[:-1]
        masked_url = f"{':'.join(masked)}:***@{parts[1]}"
    else:
        masked_url = db_url[:50] + "..."
    print_info(f"Connection string: {masked_url}")
    print_info(f"Database type: {'Supabase' if settings.is_supabase else 'PostgreSQL'}")

    try:
        is_connected = check_connection()
        if is_connected:
            print_success("Database connection successful")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print_info(f"PostgreSQL version: {version.split(',')[0]}")
            
            return True
        else:
            print_error("Database connection failed")
            return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

def check_models_imported():
    print_header("2. MODEL IMPORTS")
    expected_models = [
        'Contact',
        'User', 
        'Survey',
        'SurveyFollowUp',
        'FaucetRequest'
    ]
    all_imported = True
    
    for model_name in expected_models:
        table_name = model_name.lower() + 's' if model_name != 'SurveyFollowUp' else 'survey_follow_ups'
        if model_name == 'FaucetRequest':
            table_name = 'faucet_requests'
        
        if table_name in Base.metadata.tables:
            print_success(f"{model_name} -> {table_name}")
        else:
            print_error(f"{model_name} NOT FOUND (expected table: {table_name})")
            all_imported = False
    return all_imported

def check_sqlalchemy_metadata():
    print_header("3. SQLALCHEMY METADATA")
    tables = list(Base.metadata.tables.keys())
    
    if not tables:
        print_error("No tables detected in metadata")
        print_warning("Check that app/db/base.py imports all models")
        return False
    
    print_success(f"Found {len(tables)} tables:")
    for table_name in sorted(tables):
        table = Base.metadata.tables[table_name]
        columns = len(table.columns)
        indexes = len(table.indexes)
        print(f"   📋 {table_name}: {columns} columns, {indexes} indexes")
    return True

def check_database_schema():
    print_header("4. DATABASE SCHEMA")
    
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            print_warning("No tables exist in database yet")
            print_info("This is normal for a fresh database")
            print_info("Run 'alembic upgrade head' to create tables")
            return True
        
        print_success(f"Found {len(existing_tables)} existing tables:")
        for table_name in sorted(existing_tables):
            print(f"   📊 {table_name}")

        if 'alembic_version' in existing_tables:
            print_success("Alembic version table exists")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                if version:
                    print_info(f"Current migration version: {version}")
                else:
                    print_warning("No migrations applied yet")
        else:
            print_warning("Alembic not initialized in database")
            print_info("Run 'alembic upgrade head' to initialize")
        
        return True
        
    except Exception as e:
        print_error(f"Error inspecting database: {str(e)}")
        return False

def check_alembic_setup():
    print_header("5. ALEMBIC CONFIGURATION")
    alembic_ini = Path("alembic.ini")
    if alembic_ini.exists():
        print_success("alembic.ini found")
    else:
        print_error("alembic.ini NOT FOUND")
        print_info("Run: alembic init alembic")
        return False

    alembic_dir = Path("alembic")
    if alembic_dir.exists():
        print_success("alembic/ directory found")
        env_py = alembic_dir / "env.py"
        if env_py.exists():
            print_success("alembic/env.py found")
        else:
            print_error("alembic/env.py NOT FOUND")
            return False

        versions_dir = alembic_dir / "versions"
        if versions_dir.exists():
            migrations = list(versions_dir.glob("*.py"))
            migration_count = len([m for m in migrations if m.name != "__pycache__"])
            
            if migration_count > 0:
                print_success(f"Found {migration_count} migration(s)")
                for migration in sorted(migrations)[:5]:  # Show first 5
                    if migration.name != "__pycache__":
                        print(f"   📝 {migration.name}")
            else:
                print_warning("No migrations found yet")
                print_info("Run: alembic revision --autogenerate -m 'Initial schema'")
        else:
            print_error("alembic/versions/ directory NOT FOUND")
            return False
    else:
        print_error("alembic/ directory NOT FOUND")
        print_info("Run: alembic init alembic")
        return False
    
    return True

def check_dependencies():
    print_header("6. DEPENDENCIES")
    required_packages = {
        'sqlalchemy': 'SQLAlchemy',
        'alembic': 'Alembic',
        'psycopg': 'psycopg (PostgreSQL driver)',
        'pydantic': 'Pydantic',
        'fastapi': 'FastAPI'
    }
    
    all_installed = True
    
    for package, name in required_packages.items():
        spec = importlib.util.find_spec(package)
        if spec is not None:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown')
                print_success(f"{name}: {version}")
            except:
                print_success(f"{name}: installed")
        else:
            print_error(f"{name}: NOT INSTALLED")
            all_installed = False
    
    return all_installed

def main():
    print("\n" + "🔍" * 35)
    print("     PRE-MIGRATION VALIDATION SCRIPT")
    print("🔍" * 35)
    checks = [
        ("Database Connection", check_database_connection),
        ("Model Imports", check_models_imported),
        ("SQLAlchemy Metadata", check_sqlalchemy_metadata),
        ("Database Schema", check_database_schema),
        ("Alembic Setup", check_alembic_setup),
        ("Dependencies", check_dependencies),
    ]
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_error(f"Error in {check_name}: {str(e)}")
            results[check_name] = False
    print_header("SUMMARY")
    passed = sum(results.values())
    total = len(results)
    
    for check_name, passed_check in results.items():
        status = "✅ PASS" if passed_check else "❌ FAIL"
        print(f"{status}: {check_name}")
    print("\n" + "=" * 70)
    
    if passed == total:
        print_success(f"All checks passed ({passed}/{total})")
        print_success("✨ Ready to create migration!")
        print_info("\nNext steps:")
        print("   1. alembic revision --autogenerate -m 'Initial schema'")
        print("   2. alembic upgrade head")
        return 0
    else:
        print_error(f"Some checks failed ({passed}/{total} passed)")
        print_warning("Fix the issues above before creating migrations")
        return 1

if __name__ == "__main__":
    exit(main())