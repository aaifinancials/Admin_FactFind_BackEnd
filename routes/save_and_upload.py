from fastapi import APIRouter, UploadFile, Depends, HTTPException, Request, Form, File
from typing import List
from fastapi.responses import JSONResponse
from uuid import uuid4
from datetime import datetime
from config.database import mortgage_applications_collection
from schemas.user_auth import get_current_user
from models.user_models import User
from schemas.gdrive_upload import get_drive_service, get_customer_folder, get_root_folder, upload_file_to_drive
from bson import ObjectId
import json

router = APIRouter()


@router.post("/submit_mortgage_with_docs")
async def submit_mortgage_with_docs(
    request: Request,
    id_proof: UploadFile | None = None,
    address_proof: UploadFile | None = None,
    bank_statement: UploadFile | None = None,
    payslip: UploadFile | None = None,
    current_user: User = Depends(get_current_user),
):
    try:
        form_data = await request.form()
        form_dict = dict(form_data)
        full_name = form_dict.get("customerName")
        email = form_dict.get("customerEmail")
        phone = form_dict.get("customerPhone")

        if not (full_name and email and phone):
            raise HTTPException(status_code=400, detail="Missing required fields")

        customerId = str(uuid4())

        drive = get_drive_service()
        root_folder_id = get_root_folder(drive)
        customer_folder_id = get_customer_folder(drive, root_folder_id, customerId)

        uploaded_files = {}
        for key, file in {"id_proof": id_proof, "address_proof": address_proof, "bank_statement": bank_statement, "payslip": payslip}.items():
            if file:
                uploaded_files[key] = await upload_file_to_drive(drive, customer_folder_id, file)

        mongo_form_data = {k: v for k, v in form_dict.items() if not hasattr(v, "filename")}
        application_data = {
            "customerId": customerId,
            "submitted_by": current_user.email,
            "uploaded_files": uploaded_files,
            "form_data": mongo_form_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "submitted"
        }

        result = await mortgage_applications_collection.insert_one(application_data)

        return {
            "message": "Mortgage application submitted successfully",
            "application_id": str(result.inserted_id),
            "customerId": customerId,
            "uploaded_files": uploaded_files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting application: {str(e)}")


@router.put("/update-mortgage-with-docs/{application_id}")
async def update_mortgage_with_docs(
    application_id: str,
    form_data: str = Form(...),
    files: List[UploadFile] = File([]),
    file_keys: List[str] = Form([]),
    current_user: User=Depends(get_current_user)
):
    try:
        data = json.loads(form_data)

        # Step 1: Update form data
        await mortgage_applications_collection.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": {"form_data": data, "updated_at": datetime.utcnow()}}
        )

        # Step 2: Handle file updates
        if files:
            app_doc = await mortgage_applications_collection.find_one({"_id": ObjectId(application_id)})
            customer_id = app_doc["customerId"]

            drive_service = get_drive_service()
            root_folder_id = get_root_folder(drive_service)
            customer_folder_id = get_customer_folder(drive_service, root_folder_id, customer_id)

            uploaded_files = app_doc.get("uploaded_files", {})

            for file, key in zip(files, file_keys):
                # Step 2A: Move old file to Trash (if it exists)
                old_file_info = uploaded_files.get(key)
                if old_file_info and "google_drive_id" in old_file_info:
                    try:
                        drive_service.files().update(
                            fileId=old_file_info["google_drive_id"],
                            body={"trashed": True}
                        ).execute()
                        print(f"🗑️ Moved old file '{old_file_info['file_name']}' to Trash.")
                    except Exception as trash_err:
                        print(f"⚠️ Could not move old file to Trash: {trash_err}")

                # Step 2B: Upload new file directly to Drive
                uploaded_file_info = await upload_file_to_drive(drive_service, customer_folder_id, file)
                uploaded_files[key] = uploaded_file_info

            # Step 3: Update DB
            await mortgage_applications_collection.update_one(
                {"_id": ObjectId(application_id)},
                {"$set": {"uploaded_files": uploaded_files}}
            )

        return JSONResponse({
            "status": "success",
            "message": "Application updated successfully! Old files moved to Trash."
        })

    except Exception as e:
        print(f"❌ Error updating mortgage: {e}")
        return JSONResponse({"status": "error", "message": str(e)})