from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from beanie import Document, Link # Import Document for Beanie integration if used

class SyllabusPersonnelItem(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class SyllabusStudentItem(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

class MatzpenGroupItem(BaseModel):
    mentor: Optional[str] = None
    meeting_room: Optional[str] = None
    students: Optional[List[str]] = None

class RrbgGroupItem(BaseModel):
    instructor: Optional[str] = None
    first_meeting_date: Optional[str] = None
    room: Optional[str] = None
    students: Optional[List[str]] = None

class SyllabusStudentGroupItem(BaseModel):
    name: Optional[str] = None
    details: Optional[str] = None
    students: Optional[List[SyllabusStudentItem]] = None
    matzpen_groups: Optional[List[MatzpenGroupItem]] = None
    rrbg_groups: Optional[List[RrbgGroupItem]] = None

class SyllabusAssignmentItem(BaseModel):
    name: Optional[str] = None
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    submission_method: Optional[str] = None
    details: Optional[str] = None

class SyllabusTestMoadItem(BaseModel):
    moad_name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None

class SyllabusTestItem(BaseModel):
    name: Optional[str] = None
    test_type: Optional[str] = None
    notes: Optional[str] = None
    moadim: Optional[List[SyllabusTestMoadItem]] = None

class SyllabusTimeSlotResourceItem(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None

class SyllabusTimeSlotItem(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    subject: Optional[str] = None
    activity_type: Optional[str] = None
    location: Optional[str] = None
    details: Optional[str] = None
    instructors: Optional[List[str]] = None
    attending_groups: Optional[List[str]] = None
    resources: Optional[List[SyllabusTimeSlotResourceItem]] = None

class SyllabusCalendarEntryItem(BaseModel):
    date: Optional[str] = None
    day_of_week_heb: Optional[str] = None
    day_of_week_en: Optional[str] = None
    daily_notes: Optional[str] = None
    time_slots: Optional[List[SyllabusTimeSlotItem]] = None

class LabGroupTableItem(BaseModel):
    table: Optional[int | str] = None
    students: Optional[List[SyllabusStudentItem]] = None

LabGroupCategory = Dict[str, List[LabGroupTableItem]]

class CoursePersonnelItem(BaseModel):
    coordinators: Optional[List[SyllabusPersonnelItem]] = None
    overall_lecturers: Optional[List[SyllabusPersonnelItem]] = None
    rv_lab_coordinator: Optional[SyllabusPersonnelItem] = None

class SyllabusScheduleItem(BaseModel):
    general_notes: Optional[str] = None
    calendar_entries: Optional[List[SyllabusCalendarEntryItem]] = None

class SyllabusCourse(BaseModel):
    id: str
    name: str
    heb_name: str
    year: str
    semester: str
    description: Optional[Dict[str, str]] = None
    personnel: Optional[CoursePersonnelItem] = None
    target_audience: Optional[List[str]] = None
    general_location: Optional[str] = None
    general_day_time_info: Optional[str] = None
    requirements: Optional[str] = None
    grading_policy: Optional[str] = None
    course_notes: Optional[str] = None
    student_groups: Optional[List[SyllabusStudentGroupItem]] = None
    lab_groups: Optional[LabGroupCategory] = None
    assignments: Optional[List[SyllabusAssignmentItem]] = None
    schedule: Optional[SyllabusScheduleItem] = None
    tests: Optional[List[SyllabusTestItem]] = None

class SyllabusSummaryResponse(BaseModel):
    id: str
    name: str
    heb_name: str
    year: str
    semester: str

# New models for document-based versioning
class CourseMeta(BaseModel):
    name: str
    heb_name: str
    year: str
    semester: str

class FieldChange(BaseModel):
    field_path: str
    old_value: Any
    new_value: Any
    change_type: Literal["add", "update", "delete"]

class SyllabusVersion(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    syllabus_id: str
    version: int
    data: SyllabusCourse
    created_at: datetime
    created_by: Optional[str] = None
    change_summary: Optional[str] = None
    changes: Optional[List[FieldChange]] = None

    class Config:
        populate_by_name = True

class SyllabusDocument(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    course_id: str
    current_version: int
    created_at: datetime
    created_by: Optional[str] = None
    metadata: CourseMeta

    class Config:
        populate_by_name = True