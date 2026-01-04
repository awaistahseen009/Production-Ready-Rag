from app.repository.user_repository import UserRepository
from sqlalchemy.orm import Session
from app.schemas.user import UserLoginSchema , UserRegistrationSchema , UserUpdateSchema, UserToken
from app.core.security.hashHandler import HashHelper
from app.core.security.authHandler import AuthHandler
from fastapi import HTTPException
from app.model.user import User
import uuid
class UserService:
    def __init__(self , session:Session):
        self._user_repo = UserRepository(session=session)

    def signup(self, user_details:UserRegistrationSchema):
        if self._user_repo.user_exists_by_email(email=user_details.email):
            raise HTTPException(status_code=400, detail="User with this account already exists , Please Login")
        hashed_password = HashHelper.get_password_hash(plain_password=user_details.password)
        user_details.password = hashed_password
        return self._user_repo.create_user(user_details)
    
    def login(self , login_details:UserLoginSchema):
        if not self._user_repo.user_exists_by_email(email=login_details.email):
            raise HTTPException(status_code=400, detail="Credentials Incorrect")
        user:User = self._user_repo.get_user_by_email(email=login_details.email)
        if HashHelper.verify_password(login_details.password, user.password):
            token = AuthHandler.sign_jwt(user_id=user.id)
            if token:
                return UserToken(token = token)
            raise HTTPException(status_code=500, detail="Unable to process request")
        raise HTTPException(status_code=400, detail="Please check your Credentials")
    
    def get_user_by_id(self , user_id:uuid.UUID):
        user = self._user_repo.get_user_by_id(user_id)
        if user:
            return user
        raise HTTPException(status_code=400, detail="User is not available")


