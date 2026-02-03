from fastapi import APIRouter, Request, HTTPException, Body
import requests
from app.config import POWERBI_API

router = APIRouter()

@router.post("/workspaces/{workspace_id}/add-app")
def add_azure_app_to_workspace(
    workspace_id: str,
    request: Request,
    payload: dict = Body(...)
):
    access_token = request.session.get("access_token")

    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    client_id = payload.get("client_id")
    role = payload.get("role", "Admin")

    if not client_id:
        raise HTTPException(status_code=400, detail="client_id is required")

    if role not in ["Admin", "Member", "Contributor", "Viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    url = f"{POWERBI_API}/groups/{workspace_id}/users"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    body = {
        "identifier": client_id,
        "groupUserAccessRight": role,
        "principalType": "App"
    }

    resp = requests.post(url, headers=headers, json=body)

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {
        "message": "Azure App added to workspace",
        "workspace_id": workspace_id,
        "client_id": client_id,
        "role": role
    }
