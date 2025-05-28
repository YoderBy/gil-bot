from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.api.v1.schemas import ChatRequest, ChatResponse
from app.core.config import get_settings
from app.core.llm_services import process_message
from app.db.session import get_db

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    settings=Depends(get_settings)
):
    """
    Process incoming WhatsApp message.
    """
    try:
        # Process the message using LLM service
        response = await process_message(
            request.message,
            sender_id=request.sender,
            db=db,
            settings=settings
        )
        
        # Save message history in background
        background_tasks.add_task(
            db.messages.insert_one,
            {
                "sender": request.sender,
                "message": request.message,
                "response": response,
                "timestamp": request.timestamp
            }
        )
        
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 