from azure.storage.blob import BlobServiceClient
from app.config import AZURE_STORAGE_CONNECTION_STRING, BLOB_CONTAINER, EMPTY_PBIX_NAME

def download_empty_pbix():
    blob_service = BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )

    container = blob_service.get_container_client(BLOB_CONTAINER)
    blob = container.get_blob_client(EMPTY_PBIX_NAME)

    download_stream = blob.download_blob()
    return download_stream.readall()
