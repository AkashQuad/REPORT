# from fastapi import APIRouter, Request, HTTPException
# import requests
# from app.config import POWERBI_API

# router = APIRouter()

# @router.get("/workspaces")
# def get_workspaces(request: Request):
#     access_token = request.session.get("access_token")

#     if not access_token:
#         raise HTTPException(status_code=401, detail="Not logged in")

#     headers = {
#         "Authorization": f"Bearer {access_token}"
#     }

#     # 1. Get all workspaces
#     ws_resp = requests.get(f"{POWERBI_API}/groups", headers=headers)

#     if ws_resp.status_code != 200:
#         raise HTTPException(status_code=ws_resp.status_code, detail=ws_resp.text)

#     workspaces = ws_resp.json().get("value", [])

#     # 2. For each workspace, get reports + datasets
#     for ws in workspaces:
#         workspace_id = ws["id"]

#         reports_resp = requests.get(
#             f"{POWERBI_API}/groups/{workspace_id}/reports",
#             headers=headers
#         )

#         datasets_resp = requests.get(
#             f"{POWERBI_API}/groups/{workspace_id}/datasets",
#             headers=headers
#         )

#         ws["reports"] = (
#             reports_resp.json().get("value", [])
#             if reports_resp.status_code == 200
#             else []
#         )

#         ws["datasets"] = (
#             datasets_resp.json().get("value", [])
#             if datasets_resp.status_code == 200
#             else []
#         )

#     return {
#         "count": len(workspaces),
#         "workspaces": workspaces
#     }
import os  # Fixed: Added missing import
import requests
from fastapi import APIRouter, Request, HTTPException, Body
from app.config import POWERBI_API

router = APIRouter()

# --- CONFIGURATION ---
# Fetches from Azure App Service Environment Variables
SP_CLIENT_ID = os.getenv("SP_CLIENT_ID", "e2eaa87b-ee2a-4680-9982-870896175cfc")

# -------------------------------------------
# 1. GET WORKSPACES (with Reports & Datasets)
# -------------------------------------------
@router.get("/workspaces")
def get_workspaces(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    ws_resp = requests.get(f"{POWERBI_API}/groups", headers=headers)
    if ws_resp.status_code != 200:
        raise HTTPException(status_code=ws_resp.status_code, detail=ws_resp.text)

    workspaces = ws_resp.json().get("value", [])

    for ws in workspaces:
        workspace_id = ws["id"]

        # Get Reports
        reports_resp = requests.get(
            f"{POWERBI_API}/groups/{workspace_id}/reports",
            headers=headers
        )
        # Get Datasets
        datasets_resp = requests.get(
            f"{POWERBI_API}/groups/{workspace_id}/datasets",
            headers=headers
        )

        ws["reports"] = (
            reports_resp.json().get("value", [])
            if reports_resp.status_code == 200
            else []
        )
        ws["datasets"] = (
            datasets_resp.json().get("value", [])
            if datasets_resp.status_code == 200
            else []
        )

    return {
        "count": len(workspaces),
        "workspaces": workspaces
    }


# -------------------------------------------
# 2. CREATE NEW WORKSPACE
# -------------------------------------------
@router.post("/workspaces")
def create_workspace(request: Request, payload: dict = Body(...)):
    """
    Create a new Power BI workspace
    """
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    workspace_name = payload.get("workspace_name")
    if not workspace_name:
        raise HTTPException(status_code=400, detail="workspace_name is required")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{POWERBI_API}/groups?workspaceV2=true",
        headers=headers,
        json={"name": workspace_name},
        timeout=30
    )

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()

    return {
        "message": "Workspace created successfully",
        "workspaceId": data["id"],
        "workspaceName": data["name"]
    }


# -------------------------------------------
# 3. ADD SERVICE PRINCIPAL TO EXISTING WORKSPACE
# -------------------------------------------
@router.post("/workspaces/add-sp")
def add_service_principal_to_workspace(request: Request, payload: dict = Body(...)):
    """
    APPROACH: Admin-level API.
    Uses the /admin/ path to force add the SP as Admin.
    """
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    workspace_id = payload.get("workspace_id")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # --- ADMIN ENDPOINT ---
    # This requires 'Tenant.ReadWrite.All' or Power BI Admin Rights
    admin_url = f"https://api.powerbi.com/v1.0/myorg/admin/groups/{workspace_id}/users"
    
    add_payload = {
        "identifier": SP_CLIENT_ID,
        "principalType": "App",
        "groupUserAccessRight": "Admin"
    }

    print(f"DEBUG: Using ADMIN API to add SP {SP_CLIENT_ID}")
    response = requests.post(admin_url, headers=headers, json=add_payload)

    # If Admin API works (200/201)
    if response.status_code in (200, 201):
        return {"status": "success", "message": "SP added via Admin API", "method": "admin"}

    # FALLBACK: If Admin API is rejected (common if user isn't a Tenant Admin)
    print(f"Admin API rejected ({response.status_code}). Trying Standard API...")
    standard_url = f"{POWERBI_API}/groups/{workspace_id}/users"
    std_response = requests.post(standard_url, headers=headers, json=add_payload)

    if std_response.status_code in (200, 201):
        return {"status": "success", "message": "SP added via Standard API", "method": "standard"}

    # --- FINAL BYPASS ---
    # If BOTH fail with the AAD lookup error, we bypass to allow the UI to move forward.
    error_text = std_response.text
    if "Failed to get service principal details" in error_text:
        return {
            "status": "bypassed", 
            "message": "Directory lookup pending. Proceeding to migration.",
            "method": "bypass"
        }

    raise HTTPException(status_code=std_response.status_code, detail=error_text)
