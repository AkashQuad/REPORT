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
from fastapi import APIRouter, Request, HTTPException, Body
from app.config import POWERBI_API

router = APIRouter()

# --- CONFIGURATION ---
# Using your confirmed Application ID statically
STATIC_SP_CLIENT_ID = "e2eaa87b-ee2a-4680-9982-870896175cfc"

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
        # Fetch Reports and Datasets for each workspace
        reports_resp = requests.get(f"{POWERBI_API}/groups/{workspace_id}/reports", headers=headers)
        datasets_resp = requests.get(f"{POWERBI_API}/groups/{workspace_id}/datasets", headers=headers)

        ws["reports"] = reports_resp.json().get("value", []) if reports_resp.status_code == 200 else []
        ws["datasets"] = datasets_resp.json().get("value", []) if datasets_resp.status_code == 200 else []

    return {"count": len(workspaces), "workspaces": workspaces}

# -------------------------------------------
# 2. CREATE NEW WORKSPACE
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

# -------------------------------------------
# 3. ADD SERVICE PRINCIPAL (BYPASS ENDPOINT)
# -------------------------------------------
@router.post("/workspaces/add-any-sp")
def add_custom_service_principal(request: Request, payload: dict = Body(...)):
    """
    Uses the logged-in User's token (Rajashekar) to add the 
    Migration Service Principal to a workspace.
    """
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

    workspace_id = payload.get("workspace_id")
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Use the group users endpoint
    users_url = f"{POWERBI_API}/groups/{workspace_id}/users"

    # payload configuration using static ID
    add_payload = {
        "identifier": STATIC_SP_CLIENT_ID,
        "principalType": "App",
        "groupUserAccessRight": "Admin"
    }

    print(f"DEBUG: Adding SP {STATIC_SP_CLIENT_ID} to workspace {workspace_id}")

    response = requests.post(users_url, headers=headers, json=add_payload)

    if response.status_code not in (200, 201):
        print(f"ERROR from Power BI: {response.status_code} - {response.text}")
        # Return a clean error instead of a crash
        return {
            "status": "error",
            "code": response.status_code,
            "message": response.text
        }

    return {
        "status": "success",
        "message": "Service Principal linked successfully.",
        "workspace_id": workspace_id
    }

# -------------------------------------------
# 4. LEGACY ADD-SP (kept for compatibility)
# -------------------------------------------
@router.post("/workspaces/add-sp")
def add_service_principal_to_workspace(request: Request, payload: dict = Body(...)):
    # Simply redirects to the new bypass logic for consistency
    return add_custom_service_principal(request, payload)
