"""Document management routes"""
from fastapi import APIRouter, HTTPException

from app.services.file_search_service import FileSearchService

router = APIRouter()


@router.delete("/documents/{document_id:path}")
async def delete_document(document_id: str):
    """Delete a document from File Search Store"""
    try:
        service = FileSearchService()
        # Document ID should include full path: fileSearchStores/{store_id}/documents/{doc_id}
        document_name = document_id
        if not document_name.startswith("fileSearchStores/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid document ID format. Expected: fileSearchStores/{store_id}/documents/{doc_id}"
            )

        print(f"Deleting document: {document_name}")
        success = await service.delete_document(document_name)
        return {"success": success, "document_name": document_name}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Delete document error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operations/{operation_id:path}")
async def get_operation_status(operation_id: str):
    """Get the status of a long-running operation"""
    try:
        service = FileSearchService()
        # Operation ID should include full path
        operation_name = operation_id
        if not operation_name.startswith("fileSearchStores/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid operation ID format"
            )

        print(f"Getting operation status: {operation_name}")
        operation = await service.get_operation_status(operation_name)
        return operation
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Get operation error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))
