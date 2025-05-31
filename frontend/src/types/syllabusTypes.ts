
export interface SyllabusPersonnelItem {
    name?: string;
    email?: string; // Optional email for coordinators
}

export interface SyllabusStudentItem {
    first_name?: string;
    last_name?: string;
    email?: string;
}

export interface SyllabusStudentGroupItem {
    name?: string;
    details?: string;
    students?: SyllabusStudentItem[];
    matzpen_groups?: Array<{
        mentor?: string;
        meeting_room?: string;
        students?: string[];
    }>;
    rrbg_groups?: Array<{
        instructor?: string;
        first_meeting_date?: string;
        room?: string;
        students?: string[];
    }>;
}

export interface SyllabusAssignmentItem {
    name?: string;
    due_date?: string;
    due_time?: string;
    submission_method?: string;
    details?: string;
}

export interface SyllabusTestMoadItem {
    moad_name?: string;
    date?: string;
    time?: string;
    location?: string;
}

export interface SyllabusTestItem {
    name?: string;
    test_type?: string;
    notes?: string;
    moadim?: SyllabusTestMoadItem[];
}

export interface SyllabusTimeSlotResourceItem {
    type?: string;
    title?: string;
    url?: string;
}

export interface SyllabusTimeSlotItem {
    start_time?: string;
    end_time?: string;
    subject?: string;
    activity_type?: string;
    location?: string;
    details?: string;
    instructors?: string[];
    attending_groups?: string[];
    resources?: SyllabusTimeSlotResourceItem[];
}

export interface SyllabusCalendarEntryItem {
    date?: string;
    day_of_week_heb?: string;
    day_of_week_en?: string;
    daily_notes?: string;
    time_slots?: SyllabusTimeSlotItem[];
}

export interface LabGroupTableItem {
    table?: number | string; // Table number/identifier
    students?: SyllabusStudentItem[];
}

export interface LabGroupCategory {
    // Represents group_a, group_b etc.
    // Each key (like 'group_a') would hold an array of LabGroupTableItem
    [groupCategoryKey: string]: LabGroupTableItem[];
}

export interface SyllabusCourse {
    id: string;
    name: string;
    heb_name: string;
    year: string;
    semester: string;
    description?: { [key: string]: string };
    personnel?: {
        coordinators?: SyllabusPersonnelItem[];
        overall_lecturers?: SyllabusPersonnelItem[];
        rv_lab_coordinator?: SyllabusPersonnelItem[]; // For Neuroanatomy example
    };
    target_audience?: string[];
    general_location?: string;
    general_day_time_info?: string;
    requirements?: string;
    grading_policy?: string;
    course_notes?: string;
    student_groups?: SyllabusStudentGroupItem[];
    lab_groups?: LabGroupCategory; // Added lab_groups
    assignments?: SyllabusAssignmentItem[];
    schedule?: {
        general_notes?: string;
        calendar_entries?: SyllabusCalendarEntryItem[]
    };
    tests?: SyllabusTestItem[];
}

export interface SyllabusSummaryResponse {
    id: string;
    name: string;
    heb_name: string;
    year: string;
    semester: string;
}

