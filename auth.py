from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from passlib.context import CryptContext
import os

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory storage for demonstration purposes
fake_users_db = {
    "mspl": {
        "username": "mspl",
        "full_name": "mspl",
        "email": "mspl@gmail.com",
        "hashed_password": pwd_context.hash("mspl"),
        "disabled": False,
    }
}

class User(BaseModel):
    username: str
    email: str = None
    full_name: str = None
    disabled: bool = None

class UserInDB(User):
    hashed_password: str

class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("SECRET_KEY", "supersecret")

@AuthJWT.load_config
def get_config():
    return Settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

@router.get("/test-get")
async def test_get():
    return {"message": "hello world"}

@router.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), Authorize: AuthJWT = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400, 
            detail="Incorrect username or password"
        )

    access_token = Authorize.create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}




#@router.get('/me', response_model=User)
#def read_users_me(Authorize: AuthJWT = Depends()):
#    Authorize.jwt_required()
#
#    current_user = Authorize.get_jwt_subject()
#    user = get_user(fake_users_db, current_user)
#    if user is None:
#        raise HTTPException(status_code=404, detail="User not found")
#    return user
