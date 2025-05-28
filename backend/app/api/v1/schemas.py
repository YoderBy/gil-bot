from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Chat schemas
class ChatRequest(BaseModel):
    sender: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatResponse(BaseModel):
    response: str

# Syllabus schemas (Updated)

# Keep StructuredSection if needed for request/response bodies directly
# from app.models.syllabus import StructuredSection 

class SyllabusSummaryResponse(BaseModel):
    id: str = Field(..., description="Course ID, derived from filename")
    name: Optional[str] = None
    heb_name: Optional[str] = None
    # Removed filename, upload_timestamp, latest_version as they are not directly available
    # or relevant for the summary list from YAML files in this new structure.

    class Config:
        # arbitrary_types_allowed = True # If you need more flexibility later
        pass

class StructuredSection(BaseModel):
    label: str
    content: str


class SyllabusVersionResponse(BaseModel):
    version_number: int
    timestamp: datetime
    structured_data: List[StructuredSection]

class SyllabusVersionEditRequest(BaseModel):
    version_number: int
    structured_data: List[StructuredSection]

class SyllabusResponse(BaseModel):
    # This model might need to be re-evaluated or adapted 
    # if it was for MongoDB structure. For now, keeping it.
    # If a single YAML file now represents the full course data, 
    # this might just become Dict[str, Any] or a more detailed Pydantic model
    # matching the full YAML structure.
    filename: str # This could be equivalent to 'id' now
    upload_timestamp: Optional[datetime] = None # These might not be directly in YAML
    versions: Optional[List[SyllabusVersionResponse]] = None # Or a more direct full course structure
    # For a full YAML content, you might have a model like:
    # courses: List[CourseDetailModel] where CourseDetailModel has all course fields.
    # Or, if each file IS the course: id: str, name: str, heb_name: str, schedule: Dict, etc.


# Placeholder for the actual full syllabus structure if needed for PUT requests or detailed GET responses
# This would mirror the structure within your YAML files.
# class FullSyllabusData(BaseModel):
#     id: str
#     name: str
#     heb_name: str
#     year: str
#     semester: str
#     description: Optional[Dict[str, str]] = None
#     personnel: Optional[Dict[str, Any]] = None
#     # ... and all other fields from your YAML structure
#     assignments: Optional[List[Dict[str, Any]]] = None
#     schedule: Optional[Dict[str, Any]] = None
#     tests: Optional[List[Dict[str, Any]]] = None
#     # etc.


# Potentially define request/response schemas for specific versions or edits if needed
# e.g., class SyllabusVersionResponse(SyllabusVersion): ... 

# Remove or comment out old SyllabusCreate/SyllabusResponse if not used
# class SyllabusContent(BaseModel):
#     ...
# class SyllabusCreate(BaseModel):
#     ...
# class SyllabusResponse(SyllabusCreate):
#     ... 