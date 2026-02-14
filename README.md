# Ethernity DAO - Backend API

Backend API para la plataforma Ethernity DAO. Sistema de gestión de usuarios con autenticación Web3 (zero-knowledge), contribuciones, análisis blockchain y sistema de contacto.

## 🚀 Tech Stack

- **Framework:** FastAPI 0.115.0
- **Database:** PostgreSQL + SQLAlchemy 2.0
- **Blockchain:** Web3.py 7.6.0
- **Migrations:** Alembic
- **Server:** Uvicorn (ASGI)
- **Python:** 3.11+

## 📋 Features

- ✅ Autenticación Web3 (zero-knowledge con wallet)
- ✅ Gestión de usuarios y asociación de emails
- ✅ Sistema de contacto con notificaciones por email
- ✅ Interacción con contratos inteligentes
- ✅ Analytics y estadísticas
- ✅ Panel de administración
- ✅ API RESTful documentada (Swagger/OpenAPI)

## 📁 Estructura del Proyecto

# ============================================================================
# ESTRUCTURA FINAL DE DIRECTORIOS
# ============================================================================

ethernity-dao-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── contact.py
│   │           ├── users.py
│   │           ├── survey.py
│   │           ├── stats.py
│   │           ├── funds.py       
│   │           ├── tokens.py      
│   │           ├── governance.py  
│   │           ├── protocols.py   
│   │           ├── treasury.py   
│   │           ├── preferences.py
│   │           ├── analytics.py   
│   │           └── notifications.py 
│   │
│   ├── blockchain/               
│   │   ├── __init__.py
│   │   ├── web3_client.py
│   │   ├── contract_manager.py
│   │   └── event_listener.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            
│   │   ├── enums.py             
│   │   ├── constants.py          
│   │   ├── helpers.py        
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   ├── security.py
│   │   └── exceptions.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             
│   │   ├── base_class.py
│   │   ├── session.py
│   │   └── init_db.py
│   │
│   ├── models/
│   │   ├── __init__.py          
│   │   ├── user.py              
│   │   ├── contact.py
│   │   ├── survey.py
│   │   ├── faucet_request.py
│   │   ├── token.py             
│   │   ├── personal_fund.py     
│   │   ├── governance.py          
│   │   ├── protocol.py          
│   │   ├── preferences.py        
│   │   ├── treasury.py         
│   │   ├── blockchain.py      
│   │   ├── notification.py      
│   │   └── analytics.py          
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── contact.py
│   │   ├── survey.py
│   │   ├── fund.py                
│   │   ├── token.py             
│   │   ├── governance.py          
│   │   ├── protocol.py         
│   │   ├── preferences.py      
│   │   ├── treasury.py           
│   │   ├── blockchain.py          
│   │   ├── notification.py       
│   │   └── analytics.py          
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base_service.py
│   │   ├── user_service.py
│   │   ├── contact_service.py
│   │   ├── survey_service.py
│   │   ├── email_service.py
│   │   ├── fund_service.py      
│   │   ├── token_service.py     
│   │   ├── governance_service.py  
│   │   ├── protocol_service.py    
│   │   ├── preference_service.py 
│   │   ├── treasury_service.py    
│   │   ├── blockchain_service.py  
│   │   ├── analytics_service.py  
│   │   └── notification_service.py 
│   │
│   └── tasks/                    
│       ├── __init__.py
│       ├── celery_app.py
│       ├── blockchain_tasks.py
│       ├── notification_tasks.py
│       ├── analytics_tasks.py
│       └── contact_tasks.py      
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/                         
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_funds.py
│   ├── test_tokens.py
│   └── test_governance.py
│
├── contracts.json                
├── requirements.txt               
├── requirements-dev.txt           
├── Dockerfile                     
├── docker-compose.yml            
├── .env                          
├── .gitignore                     
├── alembic.ini
└── README.md


## 🛠️ Setup Local

### 1. Clonar repositorio
```bash
git clone https://github.com/tu-usuario/ethernity-backend.git
cd ethernity-backend
```

### 2. Crear virtual environment
```bash
python -m venv venv

# Activar en Linux/Mac:
source venv/bin/activate

# Activar en Windows:
venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus valores
```

Variables requeridas:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/ethernity_db
PROJECT_NAME=Ethernity DAO API
ENVIRONMENT=development
DEBUG=True
API_V1_STR=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### 5. Crear base de datos
```bash
# Crear database en PostgreSQL
createdb ethernity_db

# O desde psql:
psql -U postgres
CREATE DATABASE ethernity_db;
```

### 6. Ejecutar migraciones
```bash
alembic upgrade head
```

### 7. Ejecutar servidor
```bash
# Desarrollo
uvicorn main:app --reload --port 8000

# Producción
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 📡 API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |
| GET | `/api/stats` | Get platform statistics |

### User Endpoints (`/api/v1/users`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/email` | Associate email with wallet |
| POST | `/register` | Register new user |
| POST | `/login/{address}` | Update last login (zero-knowledge) |
| GET | `/wallet/{address}` | Get user by wallet address |

### Contact Endpoints (`/api/v1/contact`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Submit contact form |
| GET | `/messages` | Get all messages (Admin) |
| GET | `/messages/{id}` | Get specific message (Admin) |
| PATCH | `/messages/{id}/read` | Mark as read (Admin) |
| DELETE | `/messages/{id}` | Delete message (Admin) |
| POST | `/messages/{id}/reply` | Reply to message (Admin) |
| GET | `/stats` | Contact statistics (Admin) |

### Admin Endpoints

Requieren autenticación con Bearer token.

## 🔐 Autenticación

### Zero-Knowledge Authentication (Web3)

1. Usuario conecta su wallet (MetaMask, WalletConnect, etc.)
2. Frontend envía wallet address al backend
3. Backend crea/actualiza usuario automáticamente
4. No se requiere password tradicional

### Admin Authentication
```bash
Authorization: Bearer {ADMIN_TOKEN}
```

## 🗄️ Database Models

### User Model
```python
- id: Integer (PK)
- wallet_address: String (unique)
- email: String (unique, nullable)
- username: String (unique, nullable)
- full_name: String
- email_verified: Boolean
- accepts_marketing: Boolean
- accepts_notifications: Boolean
- preferred_language: String
- registration_date: DateTime
- last_login: DateTime
- is_active: Boolean
- is_banned: Boolean
```

### Contact Model
```python
- id: Integer (PK)
- name: String
- email: String
- subject: String
- message: Text
- ip_address: String
- user_agent: Text
- timestamp: DateTime
- is_read: Boolean
- admin_notes: Text
```

## 🚀 Deployment (Railway)

### 1. Conectar con GitHub
```bash
git add .
git commit -m "Deploy backend"
git push origin main
```

### 2. Configurar Railway

1. Crear nuevo proyecto en Railway
2. Conectar con GitHub repository
3. Agregar PostgreSQL database
4. Configurar variables de entorno
5. Deploy automático

### 3. Variables de entorno en Railway
```bash
DATABASE_URL=postgresql://...  # Auto-generado por Railway
PROJECT_NAME=Ethernity DAO API
VERSION=1.0.0
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
API_V1_STR=/api/v1
BACKEND_CORS_ORIGINS=["https://tu-frontend.vercel.app"]
ADMIN_EMAIL=admin@ethernity.com
ADMIN_PASSWORD=secure_password
ADMIN_TOKEN=secure_token_here
```

### 4. Start Command

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## 🧪 Testing
```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app tests/

# Tests específicos
pytest tests/test_users.py
```

## 📝 Migrations
```bash
# Crear nueva migración
alembic revision --autogenerate -m "Add user table"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver historial
alembic history
```

## 📚 Documentación API

Una vez ejecutando el servidor:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/api/v1/openapi.json

## 🔧 Development

### Formateo de código
```bash
# Black
black app/

# Isort
isort app/
```

### Linting
```bash
# Flake8
flake8 app/

# MyPy (type checking)
mypy app/
```

## 📊 Monitoring

### Logs

Los logs se configuran en `main.py`:
```python
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Health Check
```bash
curl https://backend-production-a4b5.up.railway.app/health
```

## 🤝 Contributing

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 License

[MIT License](LICENSE)

## 🔗 Links

- **Production API:** https://backend-production-a4b5.up.railway.app
- **Frontend:** https://tu-frontend.vercel.app
- **Documentation:** https://backend-production-a4b5.up.railway.app/docs

## 👥 Team

Ethernity DAO Team

## 📞 Support

Para soporte técnico, contactar a: support@ethernity.com