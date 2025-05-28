// Corresponds to backend/app/models/syllabus.py StructuredSection
export interface StructuredSection {
    label: string;
    content: string;
}

// Corresponds to backend/app/models/syllabus.py SyllabusVersion
export interface SyllabusVersion {
    version_number: number;
    timestamp: string; // Assuming ISO string format from backend
    structured_data: StructuredSection[];
    editor_id?: string | null;
}

// Corresponds to backend/app/models/syllabus.py Syllabus
export interface Syllabus {
    _id?: string; // Optional _id on the base model
    id?: string; // Typically added after fetching
    filename: string;
    upload_timestamp: string; // Assuming ISO string format
    versions: SyllabusVersion[];
    course_id?: string | null;
    metadata?: Record<string, any>;
}

// Corresponds to backend/app/api/v1/schemas.py SyllabusSummaryResponse
export interface SyllabusSummaryResponse {
    id: string;
    filename: string;
    upload_timestamp: string; // Assuming ISO string format
    latest_version: number;
} 