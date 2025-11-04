from pydantic import BaseModel

class Registration(BaseModel):
    fullname: str
    email: str
    phone: str | None = None
    mortgageType: str