import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER = os.getenv("BLOB_CONTAINER")
EMPTY_PBIX_NAME = os.getenv("EMPTY_PBIX_NAME")

POWERBI_SCOPE = [

    "https://analysis.windows.net/powerbi/api/.default"
]

POWERBI_API = "https://api.powerbi.com/v1.0/myorg"



