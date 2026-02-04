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
    access_token = request.session.get("access_token")
    workspace_id = payload.get("workspace_id")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # --- FORCE STEP 1: VERIFY IDENTITY EXISTENCE ---
    # We call the Admin API to get the SP details directly. 
    # If this fails, the issue is 100% in the Tenant Settings.
    verify_url = f"https://api.powerbi.com/v1.0/myorg/admin/servicePrincipals/{SP_CLIENT_ID}"
    verify_resp = requests.get(verify_url, headers=headers)
    
    # If the user is an admin but can't see the SP, the SP isn't in the allowed Security Group.
    if verify_resp.status_code == 404:
        raise HTTPException(
            status_code=403, 
            detail="The Service Principal is not recognized by Power BI. Ensure it is in the correct Security Group."
        )

    # --- FORCE STEP 2: THE ADDITION ---
    users_url = f"{POWERBI_API}/groups/{workspace_id}/users"
    add_payload = {
        "identifier": SP_CLIENT_ID,
        "principalType": "App",
        "groupUserAccessRight": "Admin"
    }

    # Attempt the add
    resp = requests.post(users_url, headers=headers, json=add_payload)

    if resp.status_code in (200, 201, 204):
        return {"status": "success", "message": "SP Forcefully Added"}
    
    # --- FINAL CATCH: IF STILL 403 ---
    if resp.status_code == 403:
        # This is likely the "AAD Sync" bug. To force solve this, the User 
        # MUST have 'Tenant.ReadWrite.All' or be a Power BI Admin.
        raise HTTPException(
            status_code=403, 
            detail="Force-Add Failed: Power BI Service is blocking this App ID. Check Tenant Developer Settings."
        )

    raise HTTPException(status_code=resp.status_code, detail=resp.text)
