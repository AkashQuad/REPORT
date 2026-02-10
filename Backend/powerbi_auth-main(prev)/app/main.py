# import os
# from fastapi import FastAPI, Request
# from starlette.middleware.sessions import SessionMiddleware
# from fastapi.middleware.cors import CORSMiddleware
# from app.auth import router as auth_router
# from app.workspaces import router as workspace_router
# from app.auto_upload import router as auto_upload_router

# app = FastAPI()


# # Important: credentials=True is mandatory for sessions
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "https://1115fb10-6ea8-4052-8d1b-31238016c02e.lovableproject.com",
#         "https://lovable.dev",
#         "https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app"
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # same_site="none" and https_only=True are REQUIRED for cross-domain cookies
# app.add_middleware(
#     SessionMiddleware,
#     secret_key=os.getenv("SESSION_SECRET_KEY", "super-secret-key"),
#     same_site="none",
#     https_only=True,
#     session_cookie="session"
# )

# app.include_router(auth_router)
# app.include_router(workspace_router)
# app.include_router(auto_upload_router)

# @app.get("/")
# def root():
#     return {"status": "Backend running"}


# import os
# from fastapi import FastAPI
# from starlette.middleware.sessions import SessionMiddleware
# from fastapi.middleware.cors import CORSMiddleware

# from app.auth import router as auth_router
# from app.workspaces import router as workspace_router
# from app.auto_upload import router as auto_upload_router

# app = FastAPI()

# # CORS MUST be before SessionMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "https://1115fb10-6ea8-4052-8d1b-31238016c02e.lovableproject.com",
#         "https://lovable.dev",
#         "https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app"
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Session middleware (cross-site compatible)
# app.add_middleware(
#     SessionMiddleware,
#     secret_key=os.getenv("SESSION_SECRET_KEY", "CHANGE_THIS_TO_LONG_RANDOM_SECRET"),
#     same_site="none",
#     https_only=True,
#     session_cookie="session"   # 🔥 ADD THIS BACK
# )

# app.include_router(auth_router)
# app.include_router(workspace_router)
# app.include_router(auto_upload_router)

# @app.get("/")
# def root():
#     return {"status": "Backend running"}


from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
 
from app.auth import router as auth_router
from app.workspaces import router as workspace_router
from app.auto_upload import router as auto_upload_router
from app.user import router as user_router
# from app.powerbi_folder_migration import router as folder_router
 
 
app = FastAPI()
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://1115fb10-6ea8-4052-8d1b-31238016c02e.lovableproject.com",
        "https://lovable.dev",
        "https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key",
    same_site="none",
    https_only=True
    # same_site="lax",
    # https_only=False
 
)
 
app.include_router(auth_router)
app.include_router(workspace_router)
app.include_router(auto_upload_router)
app.include_router(user_router)
 
# app.include_router(folder_router)
 
@app.get("/")
def root():
    return {"status": "Backend running"}
