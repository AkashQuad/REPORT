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

    # STEP 1: FORCE IDENTITY RESOLUTION (Microsoft Graph)
    # We hit Graph to get the Service Principal's INTERNAL Object ID.
    # This often forces AAD to 'announce' the SP to other services.
    graph_url = f"https://graph.microsoft.com/v1.0/servicePrincipals?$filter=appId eq '{SP_CLIENT_ID}'"
    graph_resp = requests.get(graph_url, headers=headers)
    
    target_id = SP_CLIENT_ID # Default
    if graph_resp.status_code == 200:
        graph_data = graph_resp.json().get("value", [])
        if graph_data:
            # Some APIs prefer the 'id' (Object ID) over the 'appId' (Client ID)
            target_id = graph_data[0].get("id")

    # STEP 2: TRY ADMIN API (The 'Force' Path)
    # Admin APIs have higher priority in directory lookups
    admin_url = f"https://api.powerbi.com/v1.0/myorg/admin/groups/{workspace_id}/users"
    add_payload = {
        "identifier": SP_CLIENT_ID, # API usually expects Client ID here
        "principalType": "App",
        "groupUserAccessRight": "Admin"
    }

    print(f"DEBUG: Forcing add via Admin API for {SP_CLIENT_ID}")
    resp = requests.post(admin_url, headers=headers, json=add_payload)

    # STEP 3: FALLBACK TO STANDARD API IF ADMIN IS DENIED
    if resp.status_code not in (200, 201):
        print("Admin API failed or no permission. Trying Standard API...")
        standard_url = f"{POWERBI_API}/groups/{workspace_id}/users"
        resp = requests.post(standard_url, headers=headers, json=add_payload)

    # STEP 4: FINAL VALIDATION
    if resp.status_code in (200, 201):
        return {"status": "success", "message": "SP Forcefully Added"}
    
    # If it still fails, it means the Power BI Tenant Setting is blocking it
    # We return the actual error so you can see exactly what Microsoft is rejecting
    raise HTTPException(
        status_code=resp.status_code, 
        detail=f"Microsoft Rejected Force-Add: {resp.text}"
    )
