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


# import os
# from dotenv import load_dotenv

# load_dotenv()

# CLIENT_ID = os.getenv("CLIENT_ID")
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# TENANT_ID = os.getenv("TENANT_ID")
# REDIRECT_URI = os.getenv("REDIRECT_URI")

# AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
# BLOB_CONTAINER = os.getenv("BLOB_CONTAINER")
# EMPTY_PBIX_NAME = os.getenv("EMPTY_PBIX_NAME")

# # --------------------------------------------------
# # Power BI NAMED SCOPES (for interactive MSAL login)
# # DO NOT use .default here
# # --------------------------------------------------

# POWERBI_SCOPE = [
#     "https://analysis.windows.net/powerbi/api/App.Read.All",
#     "https://analysis.windows.net/powerbi/api/Capacity.Read.All",
#     "https://analysis.windows.net/powerbi/api/Connection.Read.All",
#     "https://analysis.windows.net/powerbi/api/Dashboard.ReadWrite.All",
#     "https://analysis.windows.net/powerbi/api/Dataset.Read.All",
#     "https://analysis.windows.net/powerbi/api/Dataset.ReadWrite.All",
#     "https://analysis.windows.net/powerbi/api/Item.Read.All",
#     "https://analysis.windows.net/powerbi/api/Report.Read.All",
#     "https://analysis.windows.net/powerbi/api/Report.ReadWrite.All",
#     "https://analysis.windows.net/powerbi/api/Workspace.Read.All",
#     "https://analysis.windows.net/powerbi/api/Workspace.ReadWrite.All",
# ]

# POWERBI_API = "https://api.powerbi.com/v1.0/myorg"




