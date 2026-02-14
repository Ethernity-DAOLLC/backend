from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.db.base import Base

def reset_database():
    engine = create_engine(settings.DATABASE_URL)
    print("🔍 Conectando a la base de datos...")
    print(f"📍 Host: {settings.DATABASE_URL.split('@')[1].split('/')[0]}")

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"\n📋 Tablas encontradas: {len(existing_tables)}")
    for table in existing_tables:
        print(f"   - {table}")

    print("\n⚠️  ADVERTENCIA: Esto eliminará TODAS las tablas de la aplicación")
    confirm = input("¿Continuar? (escribe 'SI' para confirmar): ")
    
    if confirm != "SI":
        print("❌ Operación cancelada")
        return

    app_tables = [table.name for table in Base.metadata.sorted_tables]
    app_tables.append('alembic_version') 
    
    print(f"\n🗑️  Eliminando {len(app_tables)} tablas...")
    
    with engine.connect() as conn:
        for table in reversed(app_tables):
            if table in existing_tables:
                try:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                    print(f"   ✅ Eliminada: {table}")
                except Exception as e:
                    print(f"   ⚠️  Error con {table}: {e}")
        try:
            conn.execute(text('DROP TABLE IF EXISTS alembic_version CASCADE'))
            print(f"   ✅ Eliminada: alembic_version")
        except:
            pass
            
        conn.commit()
    
    print("\n✅ Base de datos limpia!")
    print("\n📝 Próximos pasos:")
    print("   1. alembic revision --autogenerate -m 'Initial migration'")
    print("   2. alembic upgrade head")

    inspector = inspect(engine)
    remaining_tables = inspector.get_table_names()
    remaining_app_tables = [t for t in remaining_tables if t in app_tables]
    
    if remaining_app_tables:
        print(f"\n⚠️  Algunas tablas no se pudieron eliminar: {remaining_app_tables}")
    else:
        print("\n✅ Todas las tablas de la aplicación fueron eliminadas correctamente")
if __name__ == "__main__":
    reset_database()