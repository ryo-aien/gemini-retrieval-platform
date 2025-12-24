"""Chat routes with File Search integration"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse
from app.services.gemini_service import GeminiService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """Send a chat message with File Search context"""
    try:
        print(f"Chat request: message='{request.message}', store_name='{request.store_name}', selected_docs={request.document_names}")
        service = GeminiService()

        result = await service.chat_with_file_search(
            message=request.message,
            store_name=request.store_name,
            history=request.history,
            document_names=request.document_names
        )

        return ChatResponse(
            message=result["message"],
            citations=result["citations"]
        )

    except Exception as e:
        import traceback
        error_detail = f"Chat error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def send_chat_message_stream(request: ChatRequest):
    """Send a chat message with streaming response"""
    try:
        print(f"Chat stream request: message='{request.message}', store_name='{request.store_name}', selected_docs={request.document_names}")
        service = GeminiService()

        async def generate():
            async for chunk in service.chat_stream_with_file_search(
                message=request.message,
                store_name=request.store_name,
                history=request.history,
                document_names=request.document_names
            ):
                yield chunk

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        import traceback
        error_detail = f"Chat stream error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))
