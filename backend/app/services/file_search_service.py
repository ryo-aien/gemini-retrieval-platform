"""Gemini File Search Store service"""
import os
import time
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.schemas import (
    FileSearchStoreResponse,
    DocumentResponse,
    OperationResponse,
    DocumentState,
)


class FileSearchService:
    """Service for interacting with Gemini File Search API"""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta"

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests"""
        return {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_store(self, display_name: str) -> FileSearchStoreResponse:
        """Create a new File Search Store"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/fileSearchStores",
                headers=self._get_headers(),
                json={"displayName": display_name}
            )
            response.raise_for_status()
            data = response.json()

            return FileSearchStoreResponse(
                name=data["name"],
                display_name=data.get("displayName", display_name),
                create_time=data.get("createTime"),
                update_time=data.get("updateTime"),
                active_documents_count=int(data.get("activeDocumentsCount", 0)),
                pending_documents_count=int(data.get("pendingDocumentsCount", 0)),
                failed_documents_count=int(data.get("failedDocumentsCount", 0)),
                size_bytes=int(data.get("sizeBytes", 0)),
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def list_stores(self, page_size: int = 20, page_token: Optional[str] = None) -> Dict[str, Any]:
        """List File Search Stores"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {"pageSize": page_size}
            if page_token:
                params["pageToken"] = page_token

            response = await client.get(
                f"{self.BASE_URL}/fileSearchStores",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            data = response.json()

            stores = []
            for store_data in data.get("fileSearchStores", []):
                stores.append(FileSearchStoreResponse(
                    name=store_data["name"],
                    display_name=store_data.get("displayName", ""),
                    create_time=store_data.get("createTime"),
                    update_time=store_data.get("updateTime"),
                    active_documents_count=int(store_data.get("activeDocumentsCount", 0)),
                    pending_documents_count=int(store_data.get("pendingDocumentsCount", 0)),
                    failed_documents_count=int(store_data.get("failedDocumentsCount", 0)),
                    size_bytes=int(store_data.get("sizeBytes", 0)),
                ))

            return {
                "stores": stores,
                "next_page_token": data.get("nextPageToken")
            }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def delete_store(self, store_name: str, force: bool = True) -> bool:
        """Delete a File Search Store"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.BASE_URL}/{store_name}",
                headers=self._get_headers(),
                params={"force": str(force).lower()}
            )
            response.raise_for_status()
            return True

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def upload_file(
        self,
        store_name: str,
        file_path: str,
        display_name: str,
        mime_type: str,
        chunk_size: int = 800,
        chunk_overlap: int = 400,
        custom_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> OperationResponse:
        """Upload a file to File Search Store"""
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Prepare metadata
            metadata = {
                "displayName": display_name,
                "mimeType": mime_type,
                "chunkingConfig": {
                    "chunkSize": chunk_size,
                    "chunkOverlap": chunk_overlap
                }
            }
            if custom_metadata:
                metadata["customMetadata"] = custom_metadata

            # Read file
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Upload using multipart/form-data
            files = {
                "file": (display_name, file_content, mime_type)
            }
            data = {
                "metadata": str(metadata)  # JSON string
            }

            # Use X-Goog-Upload-Protocol for resumable uploads
            headers = {
                "X-Goog-Api-Key": self.api_key,
            }

            response = await client.post(
                f"{self.UPLOAD_URL}/{store_name}:uploadToFileSearchStore",
                headers=headers,
                files=files,
                data=data
            )
            response.raise_for_status()
            operation_data = response.json()

            return OperationResponse(
                name=operation_data["name"],
                done=operation_data.get("done", False),
                metadata=operation_data.get("metadata"),
                response=operation_data.get("response"),
                error=operation_data.get("error")
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_operation_status(self, operation_name: str) -> OperationResponse:
        """Get the status of a long-running operation"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/{operation_name}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

            return OperationResponse(
                name=data["name"],
                done=data.get("done", False),
                metadata=data.get("metadata"),
                response=data.get("response"),
                error=data.get("error")
            )

    async def poll_operation(
        self,
        operation_name: str,
        timeout: int = 300,
        poll_interval: int = 2
    ) -> DocumentResponse:
        """Poll an operation until it completes"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            operation = await self.get_operation_status(operation_name)

            if operation.done:
                if operation.error:
                    raise Exception(f"Operation failed: {operation.error}")

                response_data = operation.response
                if not response_data:
                    raise Exception(f"Operation completed but no response data: {operation}")

                print(f"Operation response data: {response_data}")  # Debug log

                # Handle different response formats
                # UploadToFileSearchStoreResponse uses 'documentName' instead of 'name'
                doc_name = response_data.get("documentName") or response_data.get("name", "")
                size_bytes = response_data.get("sizeBytes")
                if isinstance(size_bytes, str):
                    size_bytes = int(size_bytes) if size_bytes.isdigit() else None

                # Extract display name from document name
                display_name = doc_name.split("/")[-1] if doc_name else ""

                return DocumentResponse(
                    name=doc_name,
                    display_name=display_name,
                    state=DocumentState.ACTIVE,  # Assume ACTIVE after successful upload
                    size_bytes=size_bytes,
                    mime_type=response_data.get("mimeType"),
                    create_time=response_data.get("createTime"),
                    update_time=response_data.get("updateTime")
                )

            await asyncio.sleep(poll_interval)

        raise TimeoutError(f"Operation {operation_name} timed out after {timeout} seconds")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def list_documents(
        self,
        store_name: str,
        page_size: int = 20,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """List documents in a File Search Store"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {"pageSize": page_size}
            if page_token:
                params["pageToken"] = page_token

            url = f"{self.BASE_URL}/{store_name}/documents"
            print(f"Requesting documents from: {url} with params: {params}")  # Debug log

            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params
            )

            # Log response details before raising
            if response.status_code >= 400:
                print(f"Error response status: {response.status_code}")
                print(f"Error response body: {response.text}")

            response.raise_for_status()
            data = response.json()

            documents = []
            for doc_data in data.get("documents", []):
                documents.append(DocumentResponse(
                    name=doc_data["name"],
                    display_name=doc_data.get("displayName", ""),
                    state=DocumentState(doc_data.get("state", "STATE_PENDING")),
                    size_bytes=doc_data.get("sizeBytes"),
                    mime_type=doc_data.get("mimeType"),
                    create_time=doc_data.get("createTime"),
                    update_time=doc_data.get("updateTime")
                ))

            return {
                "documents": documents,
                "next_page_token": data.get("nextPageToken")
            }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def delete_document(self, document_name: str, force: bool = True) -> bool:
        """Delete a document from File Search Store"""
        url = f"{self.BASE_URL}/{document_name}"
        print(f"Deleting document from: {url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try with force=true query parameter
            response = await client.delete(
                url,
                headers=self._get_headers(),
                params={"force": str(force).lower()}
            )

            if response.status_code >= 400:
                print(f"Delete error {response.status_code}: {response.text}")

            response.raise_for_status()
            return True
