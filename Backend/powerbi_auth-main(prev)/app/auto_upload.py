from fastapi import APIRouter, Request, HTTPException, Body
import requests
import time

from app.config import POWERBI_API
from app.blob import download_empty_pbix

router = APIRouter()

@router.post("/workspaces/{workspace_id}/auto-upload")
def auto_upload(
    workspace_id: str,
    request: Request,
    payload: dict = Body(...)
):
    # 1. Get access token from session
    access_token = request.session.get("access_token")

    if not access_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    # 2. Get report name from frontend payload
    report_name = payload.get("report_name")
    if not report_name:
        raise HTTPException(status_code=400, detail="Report name missing")

    # 3. Download PBIX template
    pbix_bytes = download_empty_pbix()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    files = {
        "file": (f"{report_name}.pbix", pbix_bytes, "application/vnd.ms-powerbi.pbix")
    }

    # 4. Upload PBIX to Power BI workspace
    upload_url = (
        f"{POWERBI_API}/groups/{workspace_id}/imports"
        f"?datasetDisplayName={report_name}"
        "&nameConflict=CreateOrOverwrite"
    )

    resp = requests.post(upload_url, headers=headers, files=files)

    if resp.status_code not in (200, 201, 202):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    # 5. Try to fetch the report ID (Power BI is async, so we retry)
    reports_url = f"{POWERBI_API}/groups/{workspace_id}/reports"

    report_id = None

    for _ in range(5):  # Retry for ~10 seconds total
        reports_resp = requests.get(reports_url, headers=headers)

        if reports_resp.ok:
            reports = reports_resp.json().get("value", [])

            for r in reports:
                if r["name"].lower() == report_name.lower():
                    report_id = r["id"]
                    break

        if report_id:
            break

        time.sleep(2)

    # 6. Return response to frontend
    return {
        "message": "Report uploaded successfully",
        "workspace_id": workspace_id,
        "report_name": report_name,
        "report_id": report_id,
    }
