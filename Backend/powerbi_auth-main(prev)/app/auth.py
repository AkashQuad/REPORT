from fastapi import APIRouter, HTTPException, Request

from fastapi.responses import RedirectResponse

import msal

from app.config import CLIENT_ID, CLIENT_SECRET, TENANT_ID, REDIRECT_URI, POWERBI_SCOPE



router = APIRouter()

REQUIRED_SCOPES = list(set(POWERBI_SCOPE + ["openid", "profile", "User.Read"]))

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
        scopes=REQUIRED_SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    if "access_token" not in token:
        raise HTTPException(status_code=400, detail=token)

    # Store token (optional backup)
    request.session["access_token"] = token["access_token"]

    # User info from ID token (NO GRAPH)
    claims = token.get("id_token_claims")

    if not claims:
        raise HTTPException(status_code=400, detail="No id_token_claims returned")

    user_payload = {
        "name": claims.get("name"),
        "email": claims.get("preferred_username"),
        "oid": claims.get("oid"),
        "tenant": claims.get("tid"),
        "jobTitle": claims.get("jobTitle", "")
    }

    # Also store in session if needed later
    request.session["user"] = user_payload

    # Send user directly to frontend
    encoded_user = quote(json.dumps(user_payload))

    return RedirectResponse(
        f"https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app/powerbi-auth-success?user={encoded_user}"
    )


# from fastapi import APIRouter, HTTPException, Request
# from fastapi.responses import RedirectResponse
# import msal
# import json
# from urllib.parse import quote

# from app.config import CLIENT_ID, CLIENT_SECRET, TENANT_ID, REDIRECT_URI, POWERBI_SCOPE

# router = APIRouter()

# # ONLY Power BI scopes
# # REQUIRED_SCOPES = POWERBI_SCOPE
# REQUIRED_SCOPES = list(set(POWERBI_SCOPE + ["openid", "profile", "User.Read"]))

# msal_app = msal.ConfidentialClientApplication(
#     CLIENT_ID,
#     authority=f"https://login.microsoftonline.com/{TENANT_ID}",
#     client_credential=CLIENT_SECRET,
# )


# @router.get("/login")
# def login(request: Request):

#     request.session.clear()

#     auth_url = msal_app.get_authorization_request_url(
#         scopes=REQUIRED_SCOPES,
#         redirect_uri=REDIRECT_URI,
#     )

#     return RedirectResponse(auth_url)


# @router.get("/auth/callback")
# def auth_callback(request: Request, code: str):

#     token = msal_app.acquire_token_by_authorization_code(
#         code=code,
#         scopes=REQUIRED_SCOPES,
#         redirect_uri=REDIRECT_URI,
#     )

#     if "access_token" not in token:
#         raise HTTPException(status_code=400, detail=token)

#     # Store token (optional backup)
#     request.session["access_token"] = token["access_token"]

#     # User info from ID token (NO GRAPH)
#     claims = token.get("id_token_claims")

#     if not claims:
#         raise HTTPException(status_code=400, detail="No id_token_claims returned")

#     user_payload = {
#         "name": claims.get("name"),
#         "email": claims.get("preferred_username"),
#         "oid": claims.get("oid"),
#         "tenant": claims.get("tid"),
#         "jobTitle": claims.get("jobTitle", "")
#     }

#     # Also store in session if needed later
#     request.session["user"] = user_payload

#     # Send user directly to frontend
#     encoded_user = quote(json.dumps(user_payload))

#     return RedirectResponse(
#         f"https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app/powerbi-auth-success?user={encoded_user}"
#     )


# from fastapi import APIRouter, HTTPException, Request
# from fastapi.responses import RedirectResponse
# import msal
# import json
# from urllib.parse import quote

# from app.config import (
#     CLIENT_ID,
#     CLIENT_SECRET,
#     TENANT_ID,
#     REDIRECT_URI,
#     POWERBI_SCOPE,
# )

# router = APIRouter()

# # ---------------------------------------------------
# # REQUIRED SCOPES
# # ---------------------------------------------------
# # Power BI delegated scope + OpenID scopes
# REQUIRED_SCOPES = list(set(
#     POWERBI_SCOPE + ["openid", "profile", "email"]
# ))

# # ---------------------------------------------------
# # MSAL CLIENT
# # ---------------------------------------------------
# msal_app = msal.ConfidentialClientApplication(
#     client_id=CLIENT_ID,
#     authority=f"https://login.microsoftonline.com/{TENANT_ID}",
#     client_credential=CLIENT_SECRET,
# )

# # ---------------------------------------------------
# # LOGIN ENDPOINT
# # ---------------------------------------------------
# @router.get("/login")
# def login(request: Request):
#     # Clear existing session
#     request.session.clear()

#     auth_url = msal_app.get_authorization_request_url(
#         scopes=REQUIRED_SCOPES,
#         redirect_uri=REDIRECT_URI,
#         prompt="select_account",
#     )

#     return RedirectResponse(auth_url)


# # ---------------------------------------------------
# # AUTH CALLBACK
# # ---------------------------------------------------
# @router.get("/auth/callback")
# def auth_callback(request: Request, code: str):

#     token = msal_app.acquire_token_by_authorization_code(
#         code=code,
#         scopes=REQUIRED_SCOPES,
#         redirect_uri=REDIRECT_URI,
#     )

#     # Handle MSAL errors
#     if "error" in token:
#         raise HTTPException(
#             status_code=400,
#             detail={
#                 "error": token.get("error"),
#                 "description": token.get("error_description"),
#             },
#         )

#     if "access_token" not in token:
#         raise HTTPException(status_code=400, detail="No access token returned")

#     # Store access token in session (short-lived)
#     request.session["access_token"] = token["access_token"]

#     # Extract ID token claims
#     claims = token.get("id_token_claims")
#     if not claims:
#         raise HTTPException(status_code=400, detail="No id_token_claims returned")

#     # User payload (NO Microsoft Graph)
#     user_payload = {
#         "name": claims.get("name"),
#         "email": claims.get("preferred_username") or claims.get("email"),
#         "oid": claims.get("oid"),
#         "tenant": claims.get("tid"),
#     }

#     # Save user info in session
#     request.session["user"] = user_payload

#     # Encode payload for frontend redirect
#     encoded_user = quote(json.dumps(user_payload))

#     # Redirect to frontend
#     return RedirectResponse(
#         f"https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app/"
#         f"powerbi-auth-success?user={encoded_user}"
#     )

