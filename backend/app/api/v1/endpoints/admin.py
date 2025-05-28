from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from bson import ObjectId # Import ObjectId
import os
import yaml

# Import updated models and schemas
from app.models.syllabus import Syllabus, SyllabusVersion, StructuredSection
from app.api.v1.schemas import SyllabusSummaryResponse # We need a summary response
from app.core.config import get_settings
from app.db.session import get_db
from app.core.llm_services import process_syllabus_with_llm, answer_question_naively_streamed # Import the new service and refactored function
from fastapi.responses import StreamingResponse # Will be needed for actual streaming
import asyncio # For placeholder streaming if we adapt later
from pathlib import Path
from pydantic import BaseModel, Field

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Determine SYLLABUS_FILES_DIR similar to syllabus.py or use a shared config
# Assuming backend is run from 'backend' directory:
BACKEND_DIR = Path(__file__).parent.parent.parent.parent.parent
SYLLABUS_FILES_DIR_ADMIN = BACKEND_DIR / "app" / "db" / "yamls"

class LLMTestRequest(BaseModel):
    syllabus_ids: List[str] # Changed from syllabus_id to syllabus_ids
    user_query: str
    model_name: Optional[str] = "gpt-4o" # Added model_name, with a default
    system_prompt_override: Optional[str] = None
    temperature: Optional[float] = Field(1.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(200, gt=0)

# Placeholder for actual streaming response content later
# class LLMTestStreamResponse(BaseModel):
# token: str

@router.post("/syllabus/upload", response_model=SyllabusSummaryResponse)
async def upload_and_process_syllabus(
    file: UploadFile = File(...),
    db=Depends(get_db),
    settings=Depends(get_settings) # Assuming settings are not needed directly here anymore
):
    """
    Upload a syllabus file, process it with LLM, and save the first version.
    Accepts PDF, DOCX, JPG, PNG.
    """
    allowed_mime_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png"
    ]
    if file.content_type not in allowed_mime_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Supported types: {', '.join(allowed_mime_types)}")

    try:
        file_content = await file.read()
        filename = file.filename
        mime_type = file.content_type

        # Process with LLM
        structured_data_list = await process_syllabus_with_llm(file_content, filename, mime_type)

        if not structured_data_list:
            logger.error(f"LLM processing failed for file: {filename}")
            raise HTTPException(status_code=500, detail="Failed to process syllabus structure with LLM.")

        # Prepare data for MongoDB
        now = datetime.utcnow()
        first_version = SyllabusVersion(
            version_number=1,
            timestamp=now,
            structured_data=[StructuredSection(**item) for item in structured_data_list] # Convert dicts to Pydantic models
            # editor_id could be set if auth is implemented
        )

        new_syllabus_doc = Syllabus(
            filename=filename,
            upload_timestamp=now,
            versions=[first_version]
            # Add course_id or metadata if available from request
        )

        # Insert into database (using Pydantic model directly if not using Beanie)
        # If using Beanie, you'd use new_syllabus_doc.insert()
        insert_result = await db.syllabus.insert_one(new_syllabus_doc.model_dump(by_alias=True))
        created_id = insert_result.inserted_id

        logger.info(f"Successfully processed and saved syllabus: {filename} with ID: {created_id}")

        # Return summary response
        return SyllabusSummaryResponse(
            id=str(created_id),
            filename=filename,
            upload_timestamp=now,
            latest_version=1
        )

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        logger.exception(f"Error during syllabus upload/processing for {file.filename}: {e}") # Log full traceback
        raise HTTPException(status_code=500, detail=f"Internal server error during processing: {e}")

@router.get("/syllabus", response_model=List[SyllabusSummaryResponse])
async def get_syllabi_list(
    db=Depends(get_db)
):
    """
    Get a list of all uploaded syllabi (summary view).
    """
    syllabi_cursor = db.syllabus.find({}, {"filename": 1, "upload_timestamp": 1, "versions": {"$slice": -1}}) # Get only latest version info
    syllabi_list = []
    async for syllabus in syllabi_cursor:
        latest_version = syllabus.get('versions', [{}])[0].get('version_number', 0)
        syllabi_list.append(SyllabusSummaryResponse(
            id=str(syllabus["_id"]),
            filename=syllabus["filename"],
            upload_timestamp=syllabus["upload_timestamp"],
            latest_version=latest_version
        ))
    return syllabi_list

@router.get("/syllabus/{syllabus_id}", response_model=Syllabus)
async def get_syllabus_details(
    syllabus_id: str,
    db=Depends(get_db)
):
    """
    Get full details for a specific syllabus (including all versions).
    """
    try:
        oid = ObjectId(syllabus_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID format.")
        
    syllabus_doc = await db.syllabus.find_one({"_id": oid})
    if not syllabus_doc:
        raise HTTPException(status_code=404, detail="Syllabus not found.")
    
    # Convert _id to string before returning
    syllabus_doc["_id"] = str(syllabus_doc["_id"])
    return Syllabus(**syllabus_doc)

@router.get("/syllabus/{syllabus_id}/version/{version_number}", response_model=SyllabusVersion)
async def get_syllabus_version(
    syllabus_id: str,
    version_number: int,
    db=Depends(get_db)
):
    """
    Get a specific version of a syllabus's structured data.
    """
    try:
        oid = ObjectId(syllabus_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID format.")

    syllabus_doc = await db.syllabus.find_one(
        {"_id": oid, "versions.version_number": version_number},
        {"versions.$": 1} # Project only the matched version
    )
    
    if not syllabus_doc or not syllabus_doc.get('versions'):
        raise HTTPException(status_code=404, detail=f"Syllabus ID {syllabus_id} or version {version_number} not found.")
        
    return SyllabusVersion(**syllabus_doc['versions'][0])

@router.put("/syllabus/{syllabus_id}", response_model=SyllabusSummaryResponse)
async def update_syllabus_version(
    syllabus_id: str,
    updated_sections: List[StructuredSection] = Body(...),
    db=Depends(get_db)
    # Add user auth dependency here later to track editor_id
):
    """
    Save a new version of the structured syllabus data based on admin edits.
    """
    try:
        oid = ObjectId(syllabus_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID format.")

    # Find the existing document to get the next version number
    existing_syllabus = await db.syllabus.find_one({"_id": oid}, {"versions": 1})
    if not existing_syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found.")

    current_versions = existing_syllabus.get('versions', [])
    next_version_number = len(current_versions) + 1
    now = datetime.utcnow()
    
    new_version = SyllabusVersion(
        version_number=next_version_number,
        timestamp=now,
        structured_data=updated_sections
        # editor_id = current_user.id # Get from auth dependency
    )
    
    # Add the new version to the versions list
    update_result = await db.syllabus.update_one(
        {"_id": oid},
        {"$push": {"versions": new_version.model_dump()}}
    )
    
    if update_result.modified_count == 0:
        # This shouldn't happen if find_one succeeded, but good to check
        raise HTTPException(status_code=500, detail="Failed to update syllabus version.")

    logger.info(f"Saved new version {next_version_number} for syllabus ID: {syllabus_id}")

    # Fetch updated summary data to return
    updated_doc = await db.syllabus.find_one({"_id": oid}, {"filename": 1, "upload_timestamp": 1})
    return SyllabusSummaryResponse(
        id=str(oid),
        filename=updated_doc["filename"],
        upload_timestamp=updated_doc["upload_timestamp"],
        latest_version=next_version_number
    )

@router.post("/llm/test-naive-stream", response_model=Dict[str, Any])
async def test_llm_naive_stream(
    request_data: LLMTestRequest = Body(...),
):
    logger.info(f"Received LLM test request for syllabi: {request_data.syllabus_ids} with model: {request_data.model_name}")

    full_syllabus_content_parts = []
    for syllabus_id in request_data.syllabus_ids:
        file_path = SYLLABUS_FILES_DIR_ADMIN / f"{syllabus_id}.yaml"
        if not file_path.exists():
            file_path_yml = SYLLABUS_FILES_DIR_ADMIN / f"{syllabus_id}.yml"
            if not file_path_yml.exists():
                logger.warning(f"Syllabus file not found for ID: {syllabus_id} in test request.")
                # Optionally skip or raise error for individual missing files
                # For now, we'll just skip it if it is part of multiple syllabi request.
                if len(request_data.syllabus_ids) == 1:
                     raise HTTPException(status_code=404, detail=f"Syllabus '{syllabus_id}' not found.")
                continue # Skip this syllabus if multiple are requested and one is missing
            file_path = file_path_yml
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
                # Add a separator or header for each syllabus content if multiple
                content_header = f"--- START SYLLABUS: {syllabus_id} ---\n"
                content_footer = f"--- END SYLLABUS: {syllabus_id} ---\n\n"
                yaml_string = yaml.dump(yaml_data, allow_unicode=True, sort_keys=False, Dumper=yaml.SafeDumper)
                full_syllabus_content_parts.append(content_header + yaml_string + content_footer)
        except Exception as e:
            logger.error(f"Error reading or parsing syllabus file {syllabus_id}: {e}")
            # Optionally skip or raise error
            if len(request_data.syllabus_ids) == 1:
                raise HTTPException(status_code=500, detail=f"Could not read/parse syllabus file: {syllabus_id}")
            continue # Skip this syllabus

    if not full_syllabus_content_parts:
        raise HTTPException(status_code=404, detail="No valid syllabus content could be loaded from the provided IDs.")
    
    full_syllabus_content_str = "\n".join(full_syllabus_content_parts)

    response_text = await answer_question_naively_streamed(
        user_query=request_data.user_query,
        full_syllabus_content=full_syllabus_content_str,
        model_name=request_data.model_name or "gpt-4o", # Ensure default if None
        system_prompt_override=request_data.system_prompt_override,
        temperature=request_data.temperature if request_data.temperature is not None else 1.0, # Ensure default
        max_tokens=request_data.max_tokens if request_data.max_tokens is not None else 200 # Ensure default
    )
    
    return {"response": response_text}

# Remove or update old placeholder endpoints if they exist
# @router.post("/syllabus", response_model=SyllabusResponse) ...
# @router.get("/syllabus", response_model=List[SyllabusResponse]) ... 