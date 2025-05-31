from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.syllabus import (
    SyllabusDocument, SyllabusVersion, SyllabusCourse,
    CourseMeta, FieldChange, SyllabusSummaryResponse
)
from app.db.session import get_db
from app.core.utils import detect_changes

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[SyllabusSummaryResponse])
async def get_syllabi(
    search: Optional[str] = None,
    year: Optional[str] = None,
    semester: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all syllabi with optional filters."""
    query = {}
    
    # Build search query
    if search:
        query["$or"] = [
            {"metadata.name": {"$regex": search, "$options": "i"}},
            {"metadata.heb_name": {"$regex": search, "$options": "i"}},
            {"course_id": {"$regex": search, "$options": "i"}}
        ]
    
    if year:
        query["metadata.year"] = year
    
    if semester:
        query["metadata.semester"] = semester
    
    syllabi = []
    cursor = db.syllabi.find(query)
    
    async for doc in cursor:
        syllabi.append(SyllabusSummaryResponse(
            id=str(doc["_id"]),
            name=doc["metadata"]["name"],
            heb_name=doc["metadata"]["heb_name"],
            year=doc["metadata"]["year"],
            semester=doc["metadata"]["semester"]
        ))
    
    return syllabi

@router.get("/{syllabus_id}", response_model=SyllabusCourse)
async def get_syllabus(
    syllabus_id: str,
    version: Optional[int] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get syllabus by ID, optionally at a specific version."""
    try:
        oid = ObjectId(syllabus_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID format")
    
    # Get the syllabus document
    syllabus_doc = await db.syllabi.find_one({"_id": oid})
    if not syllabus_doc:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    
    # Determine which version to get
    target_version = version if version else syllabus_doc["current_version"]
    
    # Get the version data
    version_doc = await db.syllabus_versions.find_one({
        "syllabus_id": str(oid),
        "version": target_version
    })
    
    if not version_doc:
        raise HTTPException(
            status_code=404, 
            detail=f"Version {target_version} not found for syllabus"
        )
    
    return version_doc["data"]

@router.get("/{syllabus_id}/versions", response_model=List[Dict[str, Any]])
async def get_syllabus_versions(
    syllabus_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get version history for a syllabus."""
    try:
        oid = ObjectId(syllabus_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID format")
    
    # Check syllabus exists
    syllabus_doc = await db.syllabi.find_one({"_id": oid})
    if not syllabus_doc:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    
    # Get all versions
    versions = []
    cursor = db.syllabus_versions.find(
        {"syllabus_id": str(oid)},
        {"data": 0}  # Exclude the full data for performance
    ).sort("version", -1)
    
    async for version in cursor:
        versions.append({
            "version": version["version"],
            "created_at": version["created_at"],
            "created_by": version.get("created_by", "unknown"),
            "change_summary": version.get("change_summary", "")
        })
    
    return versions

@router.put("/{syllabus_id}", response_model=Dict[str, Any])
async def update_syllabus(
    syllabus_id: str,
    syllabus_data: SyllabusCourse = Body(...),
    change_summary: Optional[str] = Body(None),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update syllabus by creating a new version."""
    try:
        oid = ObjectId(syllabus_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID format")
    
    # Get current syllabus
    syllabus_doc = await db.syllabi.find_one({"_id": oid})
    if not syllabus_doc:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    
    # Get current version data
    current_version_doc = await db.syllabus_versions.find_one({
        "syllabus_id": str(oid),
        "version": syllabus_doc["current_version"]
    })
    
    if not current_version_doc:
        raise HTTPException(status_code=500, detail="Current version data not found")
    
    # Detect changes
    changes = detect_changes(current_version_doc["data"], syllabus_data.model_dump())
    
    if not changes:
        return {"message": "No changes detected", "version": syllabus_doc["current_version"]}
    
    # Create new version
    new_version_number = syllabus_doc["current_version"] + 1
    new_version = SyllabusVersion(
        syllabus_id=str(oid),
        version=new_version_number,
        data=syllabus_data,
        created_at=datetime.utcnow(),
        created_by="user",  # TODO: Get from auth context
        change_summary=change_summary or f"Updated {len(changes)} fields",
        changes=changes
    )
    
    # Insert new version
    await db.syllabus_versions.insert_one(
        new_version.model_dump(by_alias=True, exclude={'id'})
    )
    
    # Update syllabus document
    await db.syllabi.update_one(
        {"_id": oid},
        {
            "$set": {
                "current_version": new_version_number,
                "metadata.name": syllabus_data.name,
                "metadata.heb_name": syllabus_data.heb_name,
                "metadata.year": syllabus_data.year,
                "metadata.semester": syllabus_data.semester
            }
        }
    )
    
    return {
        "message": "Syllabus updated successfully",
        "version": new_version_number,
        "changes": len(changes)
    }

@router.get("/{syllabus_id}/diff/{version1}/{version2}")
async def get_version_diff(
    syllabus_id: str,
    version1: int,
    version2: int,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get differences between two versions."""
    try:
        oid = ObjectId(syllabus_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID format")
    
    # Get both versions
    v1_doc = await db.syllabus_versions.find_one({
        "syllabus_id": str(oid),
        "version": version1
    })
    v2_doc = await db.syllabus_versions.find_one({
        "syllabus_id": str(oid),
        "version": version2
    })
    
    if not v1_doc or not v2_doc:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    
    # Calculate diff
    changes = detect_changes(v1_doc["data"], v2_doc["data"])
    
    return {
        "from_version": version1,
        "to_version": version2,
        "changes": changes
    } 