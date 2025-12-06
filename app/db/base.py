from sqlalchemy.ext.declarative import declarative_base
from app.db.base_class import Base
from app.models.user import User

Base = declarative_base()

# from app.models.contribution import Contribution
# from app.models.withdrawal import Withdrawal      
# from app.models.contact import Contact