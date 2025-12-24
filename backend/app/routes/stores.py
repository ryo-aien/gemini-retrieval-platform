"""File Search Store management routes"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List

from app.models.schemas import (
    FileSearchStoreCreate,
    FileSearchStoreResponse,
    ErrorResponse,
)
from app.services.file_search_service import FileSearchService
from app.utils.storage import save_upload_file, delete_temp_file, validate_file_type

router = APIRouter()


@router.post("/stores", response_model=FileSearchStoreResponse)
async def create_store(store_data: FileSearchStoreCreate):
    """Create a new File Search Store"""
    try:
        service = FileSearchService()
        store = await service.create_store(store_data.display_name)
        return store
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stores")
async def list_stores(page_size: int = 20, page_token: Optional[str] = None):
    """List all File Search Stores"""
    try:
        service = FileSearchService()
        result = await service.list_stores(page_size, page_token)
        return result
    except ValueError as e:
        # API key not set
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.delete("/stores/{store_id}")
async def delete_store(store_id: str, force: bool = True):
    """Delete a File Search Store"""
    try:
        service = FileSearchService()
        # Construct full store name if needed
        store_name = store_id if store_id.startswith("fileSearchStores/") else f"fileSearchStores/{store_id}"
        success = await service.delete_store(store_name, force)
        return {"success": success, "store_name": store_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stores/{store_id}/upload")
async def upload_document(
    store_id: str,
    file: UploadFile = File(...),
    chunk_size: int = Form(800),
    chunk_overlap: int = Form(400),
):
    """Upload a document to File Search Store"""
    try:
        # Save uploaded file temporarily
        file_info = await save_upload_file(file)

        # Validate file type
        if not validate_file_type(file_info["original_filename"], file_info["mime_type"]):
            await delete_temp_file(file_info["temp_path"])
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_info['mime_type']}"
            )

        # Upload to Gemini
        service = FileSearchService()
        store_name = store_id if store_id.startswith("fileSearchStores/") else f"fileSearchStores/{store_id}"

        operation = await service.upload_file(
            store_name=store_name,
            file_path=file_info["temp_path"],
            display_name=file_info["original_filename"],
            mime_type=file_info["mime_type"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Poll operation until completion
        document = await service.poll_operation(operation.name)

        # Clean up temporary file
        await delete_temp_file(file_info["temp_path"])

        return {
            "document": document,
            "operation_name": operation.name
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Upload error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        # Clean up temp file on error
        if 'file_info' in locals():
            await delete_temp_file(file_info.get("temp_path", ""))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stores/{store_id}/documents")
async def list_documents(
    store_id: str,
    page_size: int = 20,
    page_token: Optional[str] = None
):
    """List documents in a File Search Store"""
    try:
        service = FileSearchService()
        store_name = store_id if store_id.startswith("fileSearchStores/") else f"fileSearchStores/{store_id}"
        print(f"Listing documents for store: {store_name}")  # Debug log
        result = await service.list_documents(store_name, page_size, page_token)
        return result
    except Exception as e:
        import traceback
        error_detail = f"List documents error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        # Return empty list if documents endpoint fails (e.g., new store with no documents)
        # This prevents the UI from breaking on initial load
        if "400" in str(e) or "404" in str(e):
            print("Returning empty documents list due to API error")
            return {"documents": [], "next_page_token": None}
        raise HTTPException(status_code=500, detail=str(e))
