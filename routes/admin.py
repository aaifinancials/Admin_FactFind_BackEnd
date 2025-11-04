from fastapi import APIRouter, HTTPException, Depends, Query, status as http_status
from bson import ObjectId
from config.database import users_collection, referrals_collection, mortgage_applications_collection
from models.referral_models import StatusUpdate
from models.user_models import _normalize_status, ALLOWED_REFERRAL_STATUSES
from schemas.user_auth import requires_roles
from datetime import datetime
from typing import Optional


router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(requires_roles(["admin"]))]
    )

def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/users/{role}")
async def get_all_users(role: str):
    users_cursor = users_collection.find({"roles": role})
    users = [fix_id(user) async for user in users_cursor]
    return users

@router.put("/users/{user_id}")
async def update_user(user_id: str, body: dict):
    name = body.get("name")
    contactnumber = body.get("contactnumber")

    updates = {}
    if isinstance(name, str):
        updates["name"] = name.strip()
    if isinstance(contactnumber, str):
        updates["contactnumber"] = contactnumber.strip()

    if not updates:
        raise HTTPException(status_code=400, detail="No updatable fields provided.")

    result = await users_collection.update_one({"_id": user_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    user = await users_collection.find_one({"_id": user_id}, {"password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return fix_id(user)

@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = await users_collection.delete_one({"_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


@router.get("/referrals/{referral_id}")
async def get_referrals_by_referral_id(referral_id: str):
    referrals_cursor = referrals_collection.find({"referralId": referral_id})
    referrals = [fix_id(ref) async for ref in referrals_cursor]
    return referrals


@router.patch("/referrals/{referral_id}/status")
async def update_referral_status(referral_id: str, update: StatusUpdate):
    result = await referrals_collection.update_one(
        {"_id": referral_id},
        {"$set": {"status": update.status}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Referral not found or already up to date")

    return {"message": "Referral status updated successfully"}


@router.get("/referrals")
async def list_referrals(status: Optional[str] = Query(
    None,
    description="Filter by status: Pending | Approved | Rejected"
)):
    query = {}
    if status is not None:
        norm = _normalize_status(status)
        if norm not in ALLOWED_REFERRAL_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_REFERRAL_STATUSES))
            raise HTTPException(status_code=400, detail=f"Invalid status. Allowed values: {allowed}")
        query["status"] = norm

    pipeline = [
        {"$match": query},
        {"$sort": {"created_at": -1, "_id": -1}},
        {
            "$lookup": {
                "from": users_collection.name,
                "localField": "referralId",
                "foreignField": "referralId",
                "as": "referrer"
            }
        },
        {"$unwind": {"path": "$referrer", "preserveNullAndEmptyArrays": True}},
        {
        "$set": {
            "referrerName": "$referrer.name",
            "referrerEmail": "$referrer.email",
            }
        },
        {"$unset": "referrer"},
    ]

    cursor = referrals_collection.aggregate(pipeline)
    items = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)

    return items


@router.get("/customer-applications/{userId}")
async def get_customer_applications(userId: str):
    if not userId:
        raise HTTPException(status_code=401, detail='User not found or authorized')
    
    applications = await mortgage_applications_collection.find({"user_id": userId}).to_list(length=None)
    if not applications:
        raise HTTPException(status_code=404, detail="User not found.")
    
    for doc in applications:
        doc["_id"] = str(doc["_id"])
    
    return applications

    