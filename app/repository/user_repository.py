from app.repository.base_repository import BaseRepository
from app.schemas.user import UserLoginSchema , UserRegistrationSchema, UserUpdateSchema
from app.model.user import User
import uuid
class UserRepository(BaseRepository):

    def create_user(self, user_data: UserRegistrationSchema):
        new_user = User(**user_data.model_dump(
            exclude_none=True,
            exclude=["confirm_password"]
        ))
        self.session.add(instance=new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user
    
    def user_exists_by_email(self , email:str):
        user = self.session.query(User).filter_by(email = email).first()
        return bool(user)
    
    def get_user_by_email(self , email:str):
        user = self.session.query(User).filter_by(email = email).first()
        return user
    def get_user_by_id(self, user_id : uuid.UUID) -> User:
        user = self.session.query(User).filter_by(id=user_id).first()
        return user