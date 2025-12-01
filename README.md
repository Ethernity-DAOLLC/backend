# Backend
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.44
psycopg2-binary==2.9.9
alembic==1.17.2

# Blockchain
web3==6.11.3
eth-account==0.10.0

# Análisis
pandas==2.1.3
numpy==1.26.2

# Validación
pydantic==2.5.0
python-dotenv==1.0.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1


## Estructura del Proyecto

backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── models/
│   │   ├── contribution.py  # SQLAlchemy models
│   │   ├── user.py
│   │   └── transaction.py
│   ├── schemas/
│   │   └── schemas.py       # Pydantic models
│   ├── routers/
│   │   ├── analytics.py
│   │   ├── logs.py
│   │   └── contact.py
│   ├── services/
│   │   ├── blockchain.py    # Web3 interactions
│   │   └── calculations.py  # Financial logic
│   └── database.py
├── alembic/                 # Migraciones DB
├── tests/
├── requirements.txt
└── .env