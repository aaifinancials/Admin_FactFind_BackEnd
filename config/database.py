from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import find_dotenv, load_dotenv
import os

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

MONGO_URL = os.getenv("MONGO_URL")
ANAYA_MONGO_URL = os.getenv("ANAYA_MONGO_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client.mortgage

db_client_2 = AsyncIOMotorClient(ANAYA_MONGO_URL)
db2 = db_client_2.Anaya_Data

users_collection = db.users_collection
referrals_collection = db.referrals_collection
verification_collection = db.verification_collection

registrations = db.registrations
mortgage_applications_collection = db.mortgage_applications_collection
customer_documents_collection = db.customer_documents

anaya_registrations = db2.registrations


