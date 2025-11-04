import asyncio
import uuid
from getpass import getpass
from passlib.context import CryptContext
from datetime import datetime
from config.database import users_collection
from schemas.user_auth import hash_password

async def create_admin_user():
    print("🔐 Admin User Creation")
    email = input("Email: ").strip().lower()
    name = input("Name: ").strip()
    contactnumber = input("Contact Number: ").strip()
    password = getpass("Password: ").strip()
    confirm_password = getpass("Confirm Password: ").strip()

    if password != confirm_password:
        print("❌ Passwords do not match.")
        return

    existing_user = await users_collection.find_one({"email": email})
    if existing_user:
        print("❌ User with this email already exists.")
        return

    user_data = {
        "_id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "contactnumber": contactnumber,
        "password": hash_password(password),
        "referralId": "ADMIN",
        "roles": ["admin", "user", "customer"],
        "created_at": datetime.utcnow(),
    }

    await users_collection.insert_one(user_data)
    print("✅ Admin user created successfully.")

if __name__ == "__main__":
    asyncio.run(create_admin_user())
