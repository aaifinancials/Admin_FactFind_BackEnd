from pydantic import BaseModel, EmailStr
from typing import Optional

class ReferralCreate(BaseModel):
    firstName: str
    lastName: str
    referralPhone: Optional[str] = None
    referralEmail: EmailStr
    purpose: str
    comment: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str