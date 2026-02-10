from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import msal
from app.config import CLIENT_ID, CLIENT_SECRET, TENANT_ID, REDIRECT_URI, POWERBI_SCOPE

router = APIRouter()

msal_app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    client_credential=CLIENT_SECRET
)

@router.get("/login")
def login(request: Request):
    request.session.clear()
    auth_url = msal_app.get_authorization_request_url(
        scopes=POWERBI_SCOPE,
        redirect_uri=REDIRECT_URI
    )
    return RedirectResponse(auth_url)

@router.get("/auth/callback")
def auth_callback(request: Request, code: str):
    token = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=POWERBI_SCOPE,
        redirect_uri=REDIRECT_URI
    )

    if "access_token" not in token:
        raise HTTPException(status_code=400, detail=token)

    # Store token in session
    request.session["access_token"] = token["access_token"]
    # request.session["user"] = token.get("id_token_claims")


    # Redirect to frontend success page
    return RedirectResponse(
        "https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app/powerbi-auth-success"
    )

# newwly added to get detailes
@router.get("/auth/me")
def me(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401)

    return {
        "name": user.get("name"),
        "email": user.get("preferred_username"),
        "oid": user.get("oid"),
        "tenant": user.get("tid"),
    }
    
