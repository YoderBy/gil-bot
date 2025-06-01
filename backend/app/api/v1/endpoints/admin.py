from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from bson import ObjectId # Import ObjectId
import yaml

from app.api.v1.schemas import SyllabusSummaryResponse # We need a summary response
from app.core.config import get_settings
from app.db.session import get_db
from app.core.llm_services import process_syllabus_with_llm, answer_question_naively_streamed # Import the new service and refactored function
from fastapi.responses import StreamingResponse # Will be needed for actual streaming
import asyncio # For placeholder streaming if we adapt later
from pydantic import BaseModel, Field

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

class LLMTestRequest(BaseModel):
    syllabus_ids: List[str] # Changed from syllabus_id to syllabus_ids
    user_query: str
    model_name: Optional[str] = "gpt-4o" # Added model_name, with a default
    system_prompt_override: Optional[str] = None
    temperature: Optional[float] = Field(1.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(200, gt=0)

@router.post("/llm/test-naive-stream", response_model=Dict[str, Any])
async def test_llm_naive_stream(
    request_data: LLMTestRequest = Body(...),
    db=Depends(get_db)
):
    logger.info(f"Received LLM test request for syllabi: {request_data.syllabus_ids} with model: {request_data.model_name}")

    full_syllabus_content_parts = []
    for syllabus_id in request_data.syllabus_ids:
        try:
            oid = ObjectId(syllabus_id)
            
            syllabus_doc = await db.syllabi.find_one({"_id": oid})
            if not syllabus_doc:
                logger.warning(f"Syllabus not found for ID: {syllabus_id}")
                if len(request_data.syllabus_ids) == 1:
                    raise HTTPException(status_code=404, detail=f"Syllabus '{syllabus_id}' not found.")
                continue
            
            version_doc = await db.syllabus_versions.find_one({
                "syllabus_id": str(oid),
                "version": syllabus_doc["current_version"]
            })
            
            if not version_doc:
                logger.warning(f"Version data not found for syllabus: {syllabus_id}")
                if len(request_data.syllabus_ids) == 1:
                    raise HTTPException(status_code=404, detail=f"Version data not found for syllabus '{syllabus_id}'")
                continue
            
            content_header = f"--- START SYLLABUS: {syllabus_id} ---\n"
            content_footer = f"--- END SYLLABUS: {syllabus_id} ---\n\n"
            
            yaml_data = {"courses": [version_doc["data"]]}
            yaml_string = yaml.dump(yaml_data, allow_unicode=True, sort_keys=False, Dumper=yaml.SafeDumper)
            
            full_syllabus_content_parts.append(content_header + yaml_string + content_footer)
            logger.info(f"Added syllabus {syllabus_id} to full content")
        except Exception as e:
            logger.error(f"Error processing syllabus {syllabus_id}: {e}")
            if len(request_data.syllabus_ids) == 1:
                raise HTTPException(status_code=500, detail=f"Could not process syllabus: {syllabus_id}")
            continue

    if not full_syllabus_content_parts:
        raise HTTPException(status_code=404, detail="No valid syllabus content could be loaded from the provided IDs.")
    
    full_syllabus_content_str = "\n".join(full_syllabus_content_parts)
    logger.info(f"Full syllabus content: {full_syllabus_content_str[:100] if len(full_syllabus_content_str) > 100 else full_syllabus_content_str}...")
    response_text = await answer_question_naively_streamed(
        user_query=request_data.user_query,
        full_syllabus_content=full_syllabus_content_str,
        model_name=request_data.model_name or "gpt-4o",
        system_prompt_override=request_data.system_prompt_override,
        temperature=request_data.temperature if request_data.temperature is not None else 1.0,
        max_tokens=request_data.max_tokens if request_data.max_tokens is not None else 200
    )
    logger.info(f"Response text: {response_text[:50] if len(response_text) > 50 else response_text}...")
    return {"response": response_text}
