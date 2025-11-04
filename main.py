from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import  user_auth, referrals, admin, user_details, mortgage_applications, save_and_upload
from routes.Reg import reg

app = FastAPI()

app.include_router(user_auth.router)
app.include_router(referrals.router)
app.include_router(admin.router)
app.include_router(user_details.router)
app.include_router(reg.router)
app.include_router(mortgage_applications.router)
app.include_router(save_and_upload.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)