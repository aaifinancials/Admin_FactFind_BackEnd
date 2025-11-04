from fastapi import APIRouter, Depends, HTTPException, status
from schemas.user_auth import get_current_user
from models.user_models import User, PasswordResetRequest, ResetPasswordRequest, UserInDB, ProfileUpdate
from schemas.user_auth import create_access_token, hash_password, get_user
from config.database import users_collection, SECRET_KEY, ALGORITHM
from typing import Annotated
from schemas.send_emails import send_email, RESET_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from jose import JWTError, jwt


router = APIRouter(prefix="/user")

@router.get('/me', response_model=User)
async def get_user_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user



@router.put("/me", response_model=User)
async def update_user_me(
    update: ProfileUpdate,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
):
    
    updates: dict = {}

    if update.name is not None:
        updates["name"] = update.name.strip()

    if update.contactnumber is not None:
        updates["contactnumber"] = update.contactnumber.strip()

    if not updates:
        return current_user

    result = await users_collection.update_one(
        {"email": current_user.email},
        {"$set": updates}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await get_user(current_user.email)
    return updated_user

@router.post("/password-reset-request")
async def password_reset_request(request: PasswordResetRequest):
    email = request.email.lower()
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get roles array instead of single role
    user_roles = user.get("roles", [])
    access_token_expires = timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={'sub': email, 'roles': user_roles},
        expires_delta=access_token_expires
    )
    reset_link = f"https://aaifinancials.com/reset-password?token={token}"

    send_email(email, reset_link)
    return {"message": "Password reset link sent successfully."}

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")

        user = await users_collection.find_one({'email': email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        hashed_password = hash_password(data.new_password)
        await users_collection.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )

        return {"message": "Password reset successful."}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")