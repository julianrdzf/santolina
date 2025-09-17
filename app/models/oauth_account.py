from fastapi_users_db_sqlalchemy import SQLAlchemyBaseOAuthAccountTableUUID
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db import Base

class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    __tablename__ = "oauth_accounts"
    
    # Override the user_id to reference the correct table name
    user_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
