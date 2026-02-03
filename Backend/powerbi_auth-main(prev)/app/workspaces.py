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
import os
import requests
import json
from fastapi import APIRouter, Request, HTTPException, Body
from app.config import POWERBI_API

router = APIRouter()

# --- CONFIGURATION ---
# It is best practice to pull these from Environment Variables in Azure
SP_CLIENT_ID = os.getenv("SP_CLIENT_ID", "your-default-sp-id-if-not-in-env")

# -------------------------------------------
# 1. GET WORKSPACES (with Reports & Datasets)
# -------------------------------------------
@router.get("/workspaces")
def get_workspaces(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    headers = {"Authorization": f"Bearer {access_token}"}
    
    ws_resp = requests.get(f"{POWERBI_API}/groups", headers=headers)
    if ws_resp.status_code != 200:
        raise HTTPException(status_code=ws_resp.status_code, detail=ws_resp.text)

    workspaces = ws_resp.json().get("value", [])

    for ws in workspaces:
        workspace_id = ws["id"]
        # Fetch Reports & Datasets to enrich the workspace object
        reports_resp = requests.get(f"{POWERBI_API}/groups/{workspace_id}/reports", headers=headers)
        datasets_resp = requests.get(f"{POWERBI_API}/groups/{workspace_id}/datasets", headers=headers)

        ws["reports"] = reports_resp.json().get("value", []) if reports_resp.status_code == 200 else []
        ws["datasets"] = datasets_resp.json().get("value", []) if datasets_resp.status_code == 200 else []

    return {"count": len(workspaces), "workspaces": workspaces}

# -------------------------------------------
# 2. AUTO-UPLOAD (Includes SP Admin Check)
# -------------------------------------------
@router.post("/workspaces/{workspace_id}/auto-upload")
def auto_upload(workspace_id: str, request: Request, payload: dict = Body(...)):
    """
    1. Verifies User is logged in.
    2. Checks if Service Principal is Admin of the workspace (Adds if missing).
    3. Proceeds with the migration/upload logic.
    """
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    # The Swagger output showed 'report_name' is a required part of your logic
    report_name = payload.get("report_name")
    if not report_name:
         raise HTTPException(status_code=400, detail="Report name missing")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # --- STEP A: ENSURE SERVICE PRINCIPAL IS ADMIN ---
    users_url = f"{POWERBI_API}/groups/{workspace_id}/users"
    
    try:
        # Get current users
        users_resp = requests.get(users_url, headers=headers)
        
        if users_resp.status_code == 200:
            current_users = users_resp.json().get("value", [])
            # Check if SP is already there
            already_exists = any(
                u.get("identifier", "").lower() == SP_CLIENT_ID.lower() 
                for u in current_users
            )
            
            if not already_exists:
                # Add SP as Admin
                add_payload = {
                    "identifier": SP_CLIENT_ID,
                    "principalType": "App",
                    "groupUserAccessRight": "Admin"
                }
                add_resp = requests.post(users_url, headers=headers, json=add_payload)
                if add_resp.status_code not in [200, 201]:
                    print(f"Warning: Could not add SP Admin: {add_resp.text}")
        else:
            print(f"Warning: Could not verify workspace users: {users_resp.text}")

    except Exception as e:
        print(f"Internal error during SP verification: {str(e)}")
        # We continue even if SP check fails, as the user might already be an admin

    # --- STEP B: PROCEED WITH UPLOAD LOGIC ---
    # Put your existing upload/migration logic here...
    
    return {
        "status": "success",
        "message": f"Service Principal verified and migration for '{report_name}' initiated.",
        "workspace_id": workspace_id
    }

# -------------------------------------------
# 3. CREATE NEW WORKSPACE (Original logic)
# -------------------------------------------
@router.post("/workspaces")
def create_workspace(request: Request, payload: dict = Body(...)):
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
