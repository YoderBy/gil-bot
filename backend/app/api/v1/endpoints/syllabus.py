from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Dict, Any
import yaml
import os
import logging
from pathlib import Path
logger = logging.getLogger(__name__)

# Assuming your YAML files are in manaul_extraction/pdfs/yamls/ relative to the project root
# Adjust this path if your execution context is different or use settings for a configurable path.
# If backend is run from 'bacsakend' directory:
# backend/app/db/yamls
# backend/app/api/v1/endpoints/syllabus.py
BACKEND_DIR = Path(__file__).parent.parent.parent.parent.parent
SYLLABUS_FILES_DIR = BACKEND_DIR / "app" / "db" / "yamls"

# Assuming SyllabusSummaryResponse looks something like this.
# You might need to define it properly in app.api.v1.schemas
# from app.api.v1.schemas import SyllabusSummaryResponse 
# For now, let's make a placeholder if not available
try:
    from app.api.v1.schemas import SyllabusSummaryResponse
except ImportError:
    from pydantic import BaseModel
    class SyllabusSummaryResponse(BaseModel):
        id: str
        name: Optional[str] = None
        heb_name: Optional[str] = None
        # Add other summary fields if you parse them in get_syllabi


router = APIRouter()

def get_course_id_from_filename(filename: str) -> str:
    return filename.replace(".yaml", "").replace(".yml", "")

@router.get("/", response_model=List[SyllabusSummaryResponse])
async def get_syllabi(search: Optional[str] = None): # Removed db and settings for now
    """
    Get all syllabi with optional search filter from YAML files.
    Lists available YAML files and extracts basic info.
    """
    syllabi_summary = []
    logger.info(f"SYLLABUS_FILES_DIR: {SYLLABUS_FILES_DIR}")
    logger.info(f"os.listdir(SYLLABUS_FILES_DIR): {os.listdir(SYLLABUS_FILES_DIR)}")
    logger.info(f"os.path.exists(SYLLABUS_FILES_DIR): {os.path.exists(SYLLABUS_FILES_DIR)}")
    logger.info(f"os.path.isdir(SYLLABUS_FILES_DIR): {os.path.isdir(SYLLABUS_FILES_DIR)}")

    if not os.path.exists(SYLLABUS_FILES_DIR) or not os.path.isdir(SYLLABUS_FILES_DIR):
        logger.error(f"Syllabus directory not found: {SYLLABUS_FILES_DIR}")
        raise HTTPException(status_code=500, detail=f"Syllabus data directory not configured or not found at {SYLLABUS_FILES_DIR}")

    try:
        for filename in os.listdir(SYLLABUS_FILES_DIR):
            if filename.endswith((".yaml", ".yml")):
                course_id = get_course_id_from_filename(filename)
                file_path = os.path.join(SYLLABUS_FILES_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                        course_data = {}
                        if isinstance(content, list) and len(content) > 0:
                            if isinstance(content[0], dict) and "courses" in content[0] and isinstance(content[0]["courses"], list) and len(content[0]["courses"]) > 0:
                                course_data = content[0]["courses"][0]
                            elif isinstance(content[0], dict):
                                course_data = content[0]
                        elif isinstance(content, dict):
                             if "courses" in content and isinstance(content["courses"], list) and len(content["courses"]) > 0:
                                course_data = content["courses"][0]
                             else: 
                                course_data = content

                        name = course_data.get("name")
                        heb_name = course_data.get("heb_name")
                        
                        if search:
                            if not ( (name and search.lower() in name.lower()) or \
                                     (heb_name and search.lower() in heb_name.lower()) or \
                                     (search.lower() in course_id.lower()) ):
                                continue
                        
                        syllabi_summary.append(SyllabusSummaryResponse(id=course_id, name=name, heb_name=heb_name))
                except Exception as e:
                    logger.error(f"Error processing file {filename}: {e}")
                    syllabi_summary.append(SyllabusSummaryResponse(id=course_id, name=f"Error loading {course_id}", heb_name=""))
        return syllabi_summary
    except Exception as e:
        logger.error(f"Error listing syllabi: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing syllabi: {str(e)}")


@router.get("/{syllabus_id}", response_model=Dict[str, Any])
async def get_syllabus(syllabus_id: str):
    """
    Get syllabus by ID from YAML file.
    The syllabus_id is the filename without .yaml extension.
    """
    file_path = os.path.join(SYLLABUS_FILES_DIR, f"{syllabus_id}.yaml")
    if not os.path.exists(file_path):
        file_path_yml = os.path.join(SYLLABUS_FILES_DIR, f"{syllabus_id}.yml")
        if not os.path.exists(file_path_yml):
            raise HTTPException(status_code=404, detail=f"Syllabus '{syllabus_id}' not found.")
        file_path = file_path_yml
            
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and "courses" in content[0] and isinstance(content[0]["courses"], list) and len(content[0]["courses"]) > 0 :
                     return content[0]["courses"][0]
                elif isinstance(content[0], dict):
                    return content[0]
                else:
                    raise HTTPException(status_code=500, detail="Syllabus file has unexpected structure (list, but not dict items).")
            elif isinstance(content, dict):
                if "courses" in content and isinstance(content["courses"], list) and len(content["courses"]) > 0:
                    return content["courses"][0]
                else:
                    return content
            else:
                raise HTTPException(status_code=500, detail="Syllabus file has unexpected structure (not a list or dict).")
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML for syllabus {syllabus_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing syllabus file: {syllabus_id}")
    except Exception as e:
        logger.error(f"Error reading syllabus {syllabus_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{syllabus_id}", response_model=Dict[str, Any])
async def update_syllabus(syllabus_id: str, syllabus_data: Dict[str, Any] = Body(...)):
    """
    Update syllabus by ID by overwriting its YAML file.
    The syllabus_id is the filename without .yaml extension.
    The request body should be the full syllabus content as JSON.
    """
    filename = f"{syllabus_id}.yaml"
    file_path = os.path.join(SYLLABUS_FILES_DIR, filename)

    if not os.path.exists(SYLLABUS_FILES_DIR):
         os.makedirs(SYLLABUS_FILES_DIR, exist_ok=True)
         logger.info(f"Created syllabus directory: {SYLLABUS_FILES_DIR}")

    data_to_write = syllabus_data

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data_to_write, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        logger.info(f"Syllabus '{syllabus_id}' updated successfully at {file_path}")
        return syllabus_data 
    except Exception as e:
        logger.error(f"Error writing syllabus {syllabus_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not update syllabus: {str(e)}")

# Optional: Add POST for creating new syllabi and DELETE for removing them
# For POST, you'd typically generate a new ID (filename) or take one from the payload.
# For DELETE, you'd remove the file. 