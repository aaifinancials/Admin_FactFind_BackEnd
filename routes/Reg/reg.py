from fastapi import APIRouter
from config.database import registrations
from routes.Reg.reg_model import Registration
from datetime import datetime
import pytz

router = APIRouter()

@router.post("/api/register")
async def register_user(data: Registration):
    # Get UK timezone
    uk_timezone = pytz.timezone("Europe/London")
    current_time = datetime.now(uk_timezone)

    # Convert to ISO format (easier to sort later)
    reg_with_time = data.dict()
    reg_with_time["created_at"] = current_time.isoformat()

    await registrations.insert_one(reg_with_time)
    return {"message": "Registration successful!"}
