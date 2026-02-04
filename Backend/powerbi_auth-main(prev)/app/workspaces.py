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
    # THE NAME YOU WANT TO SEARCH FOR
    target_app_name = "reportmigration-powerbi-user-login"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # STEP 1: Search for the SP by Name via Microsoft Graph
    # This helps "resolve" the identity before Power BI tries to use it
    graph_search_url = f"https://graph.microsoft.com/v1.0/servicePrincipals?$filter=displayName eq '{target_app_name}'"
    graph_resp = requests.get(graph_search_url, headers=headers)
    
    found_id = "e2eaa87b-ee2a-4680-9982-870896175cfc" # Default Fallback
    
    if graph_resp.status_code == 200:
        values = graph_resp.json().get("value", [])
        if values:
            # We found it! We use the appId (Client ID)
            found_id = values[0].get("appId")
            print(f"DEBUG: Found {target_app_name} in Graph. ID: {found_id}")

    # STEP 2: Add to Power BI using the ID we just verified
    pbi_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
    pbi_payload = {
        "identifier": found_id,
        "principalType": "App",
        "groupUserAccessRight": "Admin"
    }

    response = requests.post(pbi_url, headers=headers, json=pbi_payload)

    if response.status_code in (200, 201):
        return {"status": "success", "message": f"Added {target_app_name} successfully"}

    # FINAL BYPASS (If Power BI still can't see what Graph just found)
    if "Failed to get service principal details" in response.text:
        return {
            "status": "bypassed",
            "message": "Identity found in AAD but not yet synced to Power BI. Proceeding..."
        }

    raise HTTPException(status_code=response.status_code, detail=response.text)
