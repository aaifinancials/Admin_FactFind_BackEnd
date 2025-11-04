from fastapi import APIRouter, HTTPException
from config.database import anaya_registrations
from models.anaya_models import ContactModel


router = APIRouter()

@router.post('/anaya/submit')
async def contact_submit(req: ContactModel):
    try:
        data = req.dict()
        result = await anaya_registrations.insert_one(data)
        if result.inserted_id:
            return {"success": True, "message": "Form submitted successfully!"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save form")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error {str(e)}")
    


    