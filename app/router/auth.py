from fastapi import APIRouter, Depends
from app.schemas.user import UserLoginSchema, UserRegistrationSchema, UserUpdateSchema, UserToken, UserOutput
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.service.user_service import UserService
from app.core.database import get_db
auth_router = APIRouter()

@auth_router.post("/login", status_code=200, response_model=UserToken)
def login(login_details:UserLoginSchema, session:Session = Depends(get_db)):
    try:
        return UserService(session).login(login_details)
    except Exception as e:
        print(e)
        raise e

@auth_router.post("/signup", status_code=201, response_model=UserOutput)
def signup(signup_details:UserRegistrationSchema, session:Session = Depends(get_db)):
    try:
        return UserService(session).signup(signup_details)
    except Exception as e:
        print(e)
        raise e