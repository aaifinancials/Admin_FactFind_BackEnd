from fastapi import APIRouter, Depends, HTTPException, status
from models.user_models import User
from models.referral_models import ReferralCreate
from config.database import referrals_collection
from uuid import uuid4
from schemas.user_auth import requires_roles
from datetime import datetime, timedelta
from bson import ObjectId
from schemas.send_emails import send_referral_email

router = APIRouter()

@router.post("/submit-referral")
async def submit_referral(
    referral: ReferralCreate,
    current_user: User = Depends(requires_roles(["user"]))
):
    try:
        referral_data = referral.dict()
        referral_data.update({
            "_id": str(uuid4()),
            "referralId": current_user.referralId,
            "created_at": datetime.utcnow(),
            "status": "Pending",
        })

        await referrals_collection.insert_one(referral_data)

        send_referral_email(
            to_email=referral.referralEmail,
            referrer_email=current_user.email,
            referral_id=current_user.referralId
        )
        return {"message": "Referral submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/my-referrals")
async def get_my_referrals(
    current_user: User = Depends(requires_roles(["user"]))
):
    try:
        referrals = await referrals_collection.find({"referralId": current_user.referralId}).to_list(length=None)
        return referrals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching referrals: {str(e)}")


@router.delete('/delete-referral/{id}')
async def delete_referral_by_id(id: str, current_user: User = Depends(requires_roles(["user"]))):
    try:
        referral = await referrals_collection.delete_one({"_id": id, "referralId": current_user.referralId})

        if referral.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Referral not found or unauthorized")

        return {"message": "Referral deleted successfully."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting referral: {str(e)}")