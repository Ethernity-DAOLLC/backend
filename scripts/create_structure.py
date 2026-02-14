#!/usr/bin/env python3
"""
Setup completo del backend - Crea estructura y archivos necesarios
Uso: python setup_complete.py
"""
import os
from pathlib import Path

def create_file(path: Path, content: str):
    """Crear archivo solo si no existe"""
    if path.exists():
        print(f"⏭️  Ya existe: {path}")
        return False
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"✅ Creado: {path}")
    return True

def main():
    print("🚀 Inicializando backend completo...\n")
    
    base = Path(".")
    
    # Archivos a crear
    files = {
        # __init__.py vacíos
        "app/__init__.py": "",
        "app/api/__init__.py": "",
        "app/api/v1/__init__.py": "",
        "app/api/v1/endpoints/__init__.py": "",
        "app/core/__init__.py": "",
        "app/db/__init__.py": "",
        "app/models/__init__.py": "",
        "app/schemas/__init__.py": "",
        "app/services/__init__.py": "",
        "app/utils/__init__.py": "",
        "tests/__init__.py": "",
        
        # Si no existe .env, crear desde ejemplo
        ".env": """ENVIRONMENT=development
DEBUG=True

# SQLite para desarrollo (cambiar a PostgreSQL después)
DATABASE_URL=sqlite:///./retirement_fund.db

FRONTEND_URL=http://localhost:5173
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

LOG_LEVEL=DEBUG
API_V1_STR=/api/v1
PROJECT_NAME=Retirement Fund API
VERSION=1.0.0
DESCRIPTION=API para gestión de fondo de retiro en blockchain
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
""",
    }
    
    created = 0
    for file_path, content in files.items():
        if create_file(base / file_path, content):
            created += 1
    
    print(f"\n✅ Setup completo! ({created} archivos creados)")
    
    # Verificar archivos importantes
    print("\n🔍 Verificando archivos importantes...")
    important = [
        "app/main.py",
        "app/core/config.py",
        "app/db/session.py",
        "app/db/base.py",
        "app/models/contribution.py",
    ]
    
    missing = []
    for file in important:
        path = base / file
        if path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ FALTA: {file}")
            missing.append(file)
    
    if missing:
        print("\n⚠️  Archivos faltantes detectados!")
        print("   Debes copiar el contenido de los artifacts que te di")
        print("   Archivos que faltan:")
        for f in missing:
            print(f"   - {f}")
    else:
        print("\n✅ Todos los archivos importantes están presentes")
    
    print("\n📋 Próximos pasos:")
    print("   1. Verifica que todos los archivos importantes existen")
    print("   2. Edita .env si necesitas cambiar algo")
    print("   3. Ejecuta: python -c \"from app.db.session import engine; from app.db.base import Base; Base.metadata.create_all(bind=engine)\"")
    print("   4. Ejecuta: uvicorn app.main:app --reload")
    print("   5. Abre: http://localhost:8000/docs")

if __name__ == "__main__":
    main()