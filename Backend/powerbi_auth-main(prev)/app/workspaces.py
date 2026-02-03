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
SP_CLIENT_ID = os.getenv("SP_CLIENT_ID", "")

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
    Checks if a specific Service Principal exists in a workspace.
    If not, adds it as an Admin.
    Expected payload: { "workspace_id": "UUID-HERE" }
    """
    print(f"DEBUG: Attempting to add SP with ID: {SP_CLIENT_ID}")
    # Defensive check: Ensure SP_CLIENT_ID was actually loaded from ENV
    
    if not SP_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Server configuration error: SP_CLIENT_ID not set.")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    workspace_id = payload.get("workspace_id")
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # A. Check for existence by listing current users
    users_url = f"{POWERBI_API}/groups/{workspace_id}/users"
    users_resp = requests.get(users_url, headers=headers)

    if users_resp.status_code != 200:
        raise HTTPException(status_code=users_resp.status_code, detail=f"Error fetching users: {users_resp.text}")

    current_users = users_resp.json().get("value", [])

    # Check if our SP Client ID matches any identifier in the group
    already_exists = any(u.get("identifier", "").lower() == SP_CLIENT_ID.lower() for u in current_users)

    if already_exists:
        return {
            "status": "success",
            "message": "already exist",
            "workspace_id": workspace_id,
            "service_principal": SP_CLIENT_ID
        }

    # B. Add the Service Principal if it doesn't exist
    add_payload = {
        "identifier": SP_CLIENT_ID,
        "principalType": "App",        # Required for Service Principals
        "groupUserAccessRight": "Admin"
    }

    add_resp = requests.post(users_url, headers=headers, json=add_payload)

    if add_resp.status_code not in (200, 201):
        raise HTTPException(status_code=add_resp.status_code, detail=f"Failed to add SP: {add_resp.text}")

    return {
        "status": "success",
        "message": "Service Principal added successfully",
        "workspace_id": workspace_id,
        "service_principal": SP_CLIENT_ID
    }
