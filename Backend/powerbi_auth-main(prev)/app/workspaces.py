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
# IMPORTANT: This must be the "Object ID" found in 'Enterprise Applications' 
# in Azure, NOT the 'Application (client) ID'.
SP_OBJECT_ID = os.getenv("SP_OBJECT_ID", "36d789fd-926b-4106-93dc-e3928b36913e")
GRAPH_API= os.getenv("GRAPH_API")

@router.get("/workspaces")
def get_workspaces(request: Request):
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch groups
    ws_resp = requests.get(f"{POWERBI_API}/groups", headers=headers)
    if ws_resp.status_code != 200:
        raise HTTPException(status_code=ws_resp.status_code, detail=ws_resp.text)

    workspaces = ws_resp.json().get("value", [])

    # Enrich workspaces with reports and datasets
    for ws in workspaces:
        workspace_id = ws["id"]
        
        # Reports
        r_resp = requests.get(f"{POWERBI_API}/groups/{workspace_id}/reports", headers=headers)
        ws["reports"] = r_resp.json().get("value", []) if r_resp.status_code == 200 else []
        
        # Datasets
        d_resp = requests.get(f"{POWERBI_API}/groups/{workspace_id}/datasets", headers=headers)
        ws["datasets"] = d_resp.json().get("value", []) if d_resp.status_code == 200 else []

    return {
        "count": len(workspaces),
        "workspaces": workspaces
    }


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


@router.get("/user/me")
def get_user_details(request: Request):
    """
    Fetches the authenticated user's profile details from Microsoft Graph.
    """
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Call the Microsoft Graph /me endpoint
    resp = requests.get(f"{GRAPH_API}/me", headers=headers)

    if resp.status_code != 200:
        # Provide detail if the token lacks 'User.Read' permissions
        try:
            error_info = resp.json()
        except:
            error_info = resp.text
        raise HTTPException(status_code=resp.status_code, detail=error_info)

    user_data = resp.json()

    return {
        "displayName": user_data.get("displayName"),
        "mail": user_data.get("mail") or user_data.get("userPrincipalName"),
        "jobTitle": user_data.get("jobTitle"),
        "id": user_data.get("id"),
        "preferredLanguage": user_data.get("preferredLanguage")
    }


@router.post("/workspaces/add-sp")
def add_service_principal_to_workspace(request: Request, payload: dict = Body(...)):
    """
    Adds the Service Principal to the workspace.
    Requires the user to have 'Admin' rights on the target workspace.
    """
    access_token = request.session.get("access_token")
    workspace_id = payload.get("workspace_id")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # API Endpoint for adding users/principals to a workspace
    users_url = f"{POWERBI_API}/groups/{workspace_id}/users"
    
    # PAYLOAD: Ensure 'identifier' is the Object ID of the Service Principal
    add_payload = {
        "identifier": SP_OBJECT_ID,
        "principalType": "App",
        "groupUserAccessRight": "Admin"
    }

    # Execute request
    resp = requests.post(users_url, headers=headers, json=add_payload)

    # 200, 201 (Created), or 204 (No Content) are all successes for this API
    if resp.status_code in (200, 201, 204):
        return {"status": "success", "message": "Service Principal added to workspace"}
    
    # Detailed error handling
    try:
        error_detail = resp.json()
    except:
        error_detail = resp.text

    # Log specific reasons for 403
    if resp.status_code == 403:
        # Possible reasons: 
        # 1. User calling the API isn't an Admin of the Workspace.
        # 2. The SP_OBJECT_ID is actually a Client ID.
        # 3. Tenant settings haven't propagated yet.
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Forbidden",
                "reason": "Ensure the current user is a Workspace Admin and SP_OBJECT_ID is correct.",
                "ms_response": error_detail
            }
        )

    raise HTTPException(status_code=resp.status_code, detail=error_detail)
