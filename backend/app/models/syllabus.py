from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from beanie import Document, Link # Import Document for Beanie integration if used

# Represents one section identified by the LLM
class StructuredSection(BaseModel):
    label: str = Field(..., description="Concise title for the section")
    content: str = Field(..., description="Full text content of the section")

# Represents one version of the processed syllabus
class SyllabusVersion(BaseModel):
    version_number: int = Field(..., description="Sequential version number (starting from 1)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this version was created")
    structured_data: List[StructuredSection] = Field(..., description="The list of sections for this version")
    # Optional: Add who made the change, comments, etc.
    editor_id: Optional[str] = None 

# Main Syllabus Document stored in MongoDB
# If using Beanie ODM, replace BaseModel with Document
class Syllabus(BaseModel): # Change to Document if using Beanie
    filename: str = Field(..., description="Original uploaded filename")
    # Optional: Store original file info if needed (e.g., R2 key)
    # original_file_key: Optional[str] = None 
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Initial upload timestamp")
    # Store processing status if needed
    # status: str = Field(default="uploaded", description="Current status: uploaded, processing, ready, error") 
    versions: List[SyllabusVersion] = Field(default=[], description="History of structured data versions")

    # Optional: Add course association, metadata etc.
    course_id: Optional[str] = None 
    metadata: Optional[Dict[str, Any]] = {}

    class Settings:
        # If using Beanie:
        # name = "syllabus" # MongoDB collection name
        pass 