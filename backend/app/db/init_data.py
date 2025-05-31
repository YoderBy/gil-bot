import os
import yaml
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.syllabus import (
    SyllabusDocument, SyllabusVersion, SyllabusCourse, 
    CourseMeta, FieldChange
)
from app.db.session import database
from app.core.config import settings

logger = logging.getLogger(__name__)

YAMLS_DIR = Path(__file__).parent / "yamls"

async def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        return None

async def create_syllabus_from_yaml(
    db: AsyncIOMotorDatabase, 
    yaml_data: Dict[str, Any], 
    filename: str
) -> bool:
    """Create syllabus document and initial version from YAML data."""
    try:
        # Extract courses from YAML
        courses = yaml_data.get('courses', [])
        if not courses:
            logger.warning(f"No courses found in {filename}")
            return False
        
        # Process first course (assuming one course per file for now)
        course_data = courses[0]
        
        # Create metadata
        metadata = CourseMeta(
            name=course_data.get('name', ''),
            heb_name=course_data.get('heb_name', ''),
            year=course_data.get('year', ''),
            semester=course_data.get('semester', '')
        )
        
        # Check if syllabus already exists
        existing = await db.syllabi.find_one({
            "course_id": course_data.get('id')
        })
        
        if existing:
            # Check if version also exists
            existing_version = await db.syllabus_versions.find_one({
                "syllabus_id": str(existing["_id"]),
                "version": existing.get("current_version", 1)
            })
            
            if existing_version:
                logger.info(f"Syllabus and version already exist for course {course_data.get('id')}")
                return True
            else:
                # Syllabus exists but version is missing - recreate version
                logger.info(f"Syllabus exists but version missing for course {course_data.get('id')}, creating version...")
                syllabus_id = str(existing["_id"])
                syllabus_course = SyllabusCourse(**course_data)
                
                # Create initial version
                version = SyllabusVersion(
                    syllabus_id=syllabus_id,
                    version=existing.get("current_version", 1),
                    data=syllabus_course,
                    created_at=datetime.utcnow(),
                    created_by="system",
                    change_summary="Initial import from YAML"
                )
                
                # Insert version
                await db.syllabus_versions.insert_one(
                    version.model_dump(by_alias=True, exclude={'id'})
                )
                
                logger.info(f"Successfully created missing version for course {course_data.get('id')}")
                return True
        
        # Create syllabus document
        syllabus_doc = SyllabusDocument(
            course_id=course_data.get('id'),
            current_version=1,
            created_at=datetime.utcnow(),
            created_by="system",
            metadata=metadata
        )
        
        # Insert syllabus document
        result = await db.syllabi.insert_one(
            syllabus_doc.model_dump(by_alias=True, exclude={'id'})
        )
        syllabus_id = str(result.inserted_id)
        
        # Create course model
        syllabus_course = SyllabusCourse(**course_data)
        
        # Create initial version
        version = SyllabusVersion(
            syllabus_id=syllabus_id,
            version=1,
            data=syllabus_course,
            created_at=datetime.utcnow(),
            created_by="system",
            change_summary="Initial import from YAML"
        )
        
        # Insert version
        await db.syllabus_versions.insert_one(
            version.model_dump(by_alias=True, exclude={'id'})
        )
        
        logger.info(f"Successfully imported syllabus for course {course_data.get('id')}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating syllabus from {filename}: {e}")
        return False

async def initialize_syllabi(db: AsyncIOMotorDatabase = None):
    """Initialize all syllabi from YAML files."""
    if db is None:
        db = database
    
    logger.info("Starting syllabus initialization...")
    
    # Create indexes
    await db.syllabi.create_index("course_id", unique=True)
    await db.syllabi.create_index("metadata.name")
    await db.syllabi.create_index("metadata.year")
    await db.syllabi.create_index("metadata.semester")
    
    await db.syllabus_versions.create_index([("syllabus_id", 1), ("version", -1)])
    await db.syllabus_versions.create_index("created_at")
    
    # Check if data already exists
    count = await db.syllabi.count_documents({})
    if count > 0:
        logger.info(f"Database already contains {count} syllabi. Skipping initialization.")
        return
    
    # Load all YAML files
    if not YAMLS_DIR.exists():
        logger.warning(f"YAML directory not found: {YAMLS_DIR}")
        return
    
    yaml_files = list(YAMLS_DIR.glob("*.yaml")) + list(YAMLS_DIR.glob("*.yml"))
    
    if not yaml_files:
        logger.warning("No YAML files found to import")
        return
    
    success_count = 0
    for yaml_file in yaml_files:
        yaml_data = await load_yaml_file(yaml_file)
        if yaml_data:
            success = await create_syllabus_from_yaml(db, yaml_data, yaml_file.name)
            if success:
                success_count += 1
    
    logger.info(f"Initialization complete. Imported {success_count}/{len(yaml_files)} syllabi.")

async def main():
    """Run initialization standalone."""
    await initialize_syllabi()

if __name__ == "__main__":
    asyncio.run(main()) 