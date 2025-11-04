from pydantic import BaseModel, EmailStr

class ContactModel(BaseModel):
    fullname: str
    company: str | None = None
    email: EmailStr
    phone: str | None = None
    service: str
    budget: str | None = None
    message: str