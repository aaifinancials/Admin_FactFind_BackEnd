import uuid
from fastapi import APIRouter, HTTPException, Form, BackgroundTasks
from models.user_models import Token, RefreshTokenRequest
from schemas.user_auth import *
from config.database import users_collection
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

router = APIRouter(tags=["Authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        data={"sub": user.email, "roles": user.roles},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "roles": user.roles},
        expires_delta=refresh_token_expires
    )

    return Token(
        access_token=access_token, 
        refresh_token=refresh_token, 
        token_type="bearer", 
        expires_in=ACCESS_TOKEN_EXPIRE_SECONDS, 
        roles=user.roles
    )

@router.post("/token/refresh", response_model=Token)
async def refresh_access_token(request: RefreshTokenRequest):
    try:
        refresh_token = request.refresh_token
        
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        token_type = payload.get("scope")
        if token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        user = await users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        access_token_expires = timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": user["email"], "roles": user["roles"]},
            expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user["email"], "roles": user["roles"]},
            expires_delta=refresh_token_expires
        )

        return Token(
            access_token=access_token, 
            refresh_token=new_refresh_token, 
            token_type="bearer", 
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS, 
            roles=user["roles"]
        )

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")