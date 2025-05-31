
Okay, I will create a detailed technical documentation for this project in a Markdown file. This documentation will explain the structure of your unified YAML data model (`docs/data.yaml`) and the project's overall goal, enabling another developer to understand and continue the work.

Here's the content for the Markdown file:

```markdown
# Project: Unified Student Responsibilities Data Model

## 1. Overview

This project aims to create a centralized and unified data model for managing student responsibilities, course information, schedules, assignments, and tests. The primary goal is to consolidate various existing data schemas (potentially from different sources or for different courses) into a single, consistent YAML file: `docs/data.yaml`.

This unified model will serve as a single source of truth, simplifying data management, enabling easier development of tools (e.g., calendar integrations, notification systems, personalized dashboards), and ensuring data consistency across different views or applications.

## 2. Core Data Structure: `docs/data.yaml`

The heart of this project is the `docs/data.yaml` file, which defines the schema for storing all relevant student and course information. It is structured as a list of `courses`, where each course object contains detailed information.

### 2.1. Top-Level Structure

The root of the YAML file is a key named `courses`, which holds a list of course objects.

```yaml
courses:
  - # Course Object 1
    ...
  - # Course Object 2
    ...
```

### 2.2. Course Object Structure

Each course object within the `courses` list has the following primary fields:

*   `id` (String, Mandatory): A unique, machine-readable identifier for the course (e.g., "anatomy_semA_2025").
*   `name` (String, Mandatory): The human-readable name of the course (e.g., "Human Anatomy - Part 1").
*   `heb_name` (String, Optional): The Hebrew name of the course.
*   `year` (String, Optional): The academic year (e.g., "תשפ\"ה").
*   `semester` (String, Optional): The semester (e.g., "א'").

#### 2.2.1. `description` (Object, Optional)

Contains descriptive information about the course.
```yaml
description:
  en: "Course description in English."
  he: "תיאור הקורס בעברית."
  goal: "The primary learning objectives of this course are..."
```

#### 2.2.2. `target_audience` (List of Strings, Optional)

Specifies the intended audience for the course.
```yaml
target_audience:
  - "Medical students, Year 1, 4-year program"
  - "Medical students, Year 2, 6-year program"
```

#### 2.2.3. `general_location` (String, Optional)

Default location for the course if not specified at a more granular level.

#### 2.2.4. `general_day_time_info` (String, Optional)

General information about recurring course timings (e.g., "Tuesdays, 15:15-17:00").

#### 2.2.5. `personnel` (Object, Optional)

Information about individuals involved in the course.
```yaml
personnel:
  coordinators:
    - name: "Prof. Noam Shomron"
      email: "noam.shomron@example.com" # Optional
    - name: "Dr. Gadi Levi"
  overall_lecturers: # Main lecturers for the entire course
    - name: "Prof. Ido Wolf"
      # email: "prof.wolf@example.com" # Optional
```
*   `coordinators`: List of course coordinators. Each item can be a string (name only) or an object with `name` and `email`.
*   `overall_lecturers`: List of main lecturers for the course. Structure similar to coordinators.

#### 2.2.6. `requirements` (String, Optional)

Course prerequisites or mandatory requirements.

#### 2.2.7. `grading_policy` (String, Optional)

Details on how the course is graded.

#### 2.2.8. `course_notes` (String, Optional)

Any general notes relevant to the course.

#### 2.2.9. `student_groups` (List of Objects, Optional)

Defines specific student groups within the course.
```yaml
student_groups:
  - name: "Group 1A"
    details: "Morning lab session group."
    location: "Lab Room 101" # Optional: default location for this group's activities
    # participants: # Optional: List of participant objects for this group
    #   - name: "Student Alpha"
    #     email: "alpha@example.com"
    #     student_id: "12345"
    #     details: "Specific details about student Alpha"
    #     notes: "Notes related to student Alpha"
```

#### 2.2.10. `assignments` (List of Objects, Optional)

Details about course assignments.
```yaml
assignments:
  - name: "Midterm Project Proposal"
    due_date: "YYYY-MM-DD" # e.g., "2025-04-15"
    due_time: "HH:MM"      # e.g., "23:59" (Optional)
    submission_method: "Online via Moodle" # How/where to submit
    details: "Submit a 2-page proposal for the AI in Medicine project."
    estimated_effort_hours: 10 # Optional
```

#### 2.2.11. `schedule` (Object, Optional)

Contains the detailed course schedule.
```yaml
schedule:
  general_notes: "All recorded lectures will be available by Sunday evening." # Notes applicable to the entire schedule
  calendar_entries: # List of entries, each representing a specific day's activities
    - date: "YYYY-MM-DD" # e.g., "2025-03-17"
      day_of_week_heb: "יום שני" # Optional
      day_of_week_en: "Monday"   # Optional
      daily_notes: "Focus on Abdomen today." # Optional notes for this specific day
      
      time_slots: # List of activities scheduled for this date
        - start_time: "HH:MM" # e.g., "08:00"
          end_time: "HH:MM"   # e.g., "09:00"
          # Alternatively: time_range: "HH:MM-HH:MM"
          subject: "Abdomen CA Session" # Topic/Name of the activity
          activity_type: "Self-Study / CA" # e.g., Lecture, Lab, PBL, Recorded, Self-Study, Exam
          location: "עבודה עצמית" # Location of the activity
          instructors: # List of instructors/lecturers for this specific slot
            - "ד\"ר מיכל גרייצר חדד"
            - "רננה ברץ גולדשטיין"
          details: "Review recorded lectures on pelvic anatomy." # More specific details
          attending_groups: ["All"] # or ["Group 1A", "Group 2A"] - which student groups attend
          resources: # Optional: List of related resources
            - type: "video_lecture" # e.g., slide, pdf, link, recording
              url: "https://example.com/lecture1_abdomen"
              title: "Pelvic Anatomy Introduction (Recorded)"
          # group_specific_activities: # Optional: For complex slots split by group
          #   - group_name: "Group 1A"
          #     subject: "Alternate subject for Group 1A"
          #     location: "Alternate location for Group 1A"
          #     instructors: ["Instructor A for Group 1A"]
          #   - group_name: "Group 2A"
          #     subject: "Different subject for Group 2A"
```

#### 2.2.12. `tests` (List of Objects, Optional)

Information about tests and examinations for the course.
```yaml
tests:
  - name: "Anatomy Midterm Exam"
    test_type: "Practical & Written" # e.g., Written, Practical, Oral, Online Quiz
    course_relation: "anatomy_semA_2025" # Optional, explicit link to course ID (usually implied by nesting)
    # group_specific: "N/A" # Optional: If the test is only for specific student groups
    syllabus_covered: "Modules 1-4, including all lab sessions." # Optional
    notes: "Bring your dissection kits. Closed book for written part." # General notes for the test
    
    moadim: # List of examination sittings/opportunities
      - moad_name: "Moed A" # e.g., A, B, Special
        date: "YYYY-MM-DD"    # e.g., "2025-05-20"
        time: "HH:MM"         # e.g., "09:00"
        duration_minutes: 180 # Optional
        location: "Main Examination Hall"
      - moad_name: "Moed B"
        date: "2025-06-10"
        time: "09:00"
        # duration_minutes: 180 # Optional
        location: "Room 203, Medical Building"
```

## 3. Data Sources and Transformation (Conceptual)

The data for `docs/data.yaml` is intended to be sourced from various existing schemas, which may differ in structure and terminology. The core task is to transform data from these source schemas into the unified schema defined above.

**Key Transformation Considerations:**

*   **Field Mapping:** Each piece of information from a source schema needs to be mapped to the corresponding field in the unified `docs/data.yaml` schema.
*   **Data Standardization:**
    *   **Dates and Times:** Convert all dates to `YYYY-MM-DD` format and times to `HH:MM` (24-hour format).
    *   **Personnel Names:** Ensure consistent formatting for names. If source data combines multiple names in one string (e.g., "Lecturer A and Lecturer B"), these should be split into a list.
    *   **Categorical Values:** Standardize terms for fields like `activity_type` (e.g., map "הרצאה", "Lecture", "פרונטלי" to a consistent value like "Lecture").
*   **Handling Lists:** Ensure that fields defined as lists in the unified schema (e.g., `instructors`, `target_audience`) are correctly populated, even if the source has a single string.
*   **Default Values:** Determine appropriate default values for optional fields if source data is missing.
*   **Unique IDs:** Generate meaningful and unique `id` values for courses.

## 4. Future Development and Next Steps

1.  **Develop Transformation Scripts:** Create scripts (e.g., in Python) to automate the process of reading data from various source schemas, transforming it, and generating/updating the `docs/data.yaml` file.
2.  **Schema Validation:** Implement a validation mechanism (e.g., using a JSON Schema or a Python validation library) to ensure that `docs/data.yaml` always conforms to the defined structure and data types.
3.  **Expand Data Coverage:** Populate `docs/data.yaml` with more course examples, mapping them from their original schemas.
4.  **Frontend/Application Layer:** Consider developing applications that consume this YAML data, such as:
    *   A student schedule viewer.
    *   A personalized task list.
    *   Integration with calendar applications.
5.  **Refine Schema:** As more data sources are integrated, the unified schema may need further refinement or extension to accommodate new types of information.

## 5. Contribution Guidelines

*   **Schema Changes:** Any proposed changes to the `docs/data.yaml` schema should be discussed and documented. Consider the impact on existing data and transformation scripts.
*   **Adding New Data:** When adding new courses or transforming data from new sources:
    *   Carefully map source fields to the unified schema.
    *   Ensure data standardization (dates, times, terminology).
    *   Validate the updated `docs/data.yaml` file.
*   **Code Style (for transformation scripts):** Follow standard coding practices for the chosen language. Include comments and documentation for complex logic.

---

This document provides a foundational understanding of the project. For specific details on the current data, always refer to the `docs/data.yaml` file itself.
```

I will now save this content into a file named `PROJECT_DOCUMENTATION.md` in your workspace.


Ran tool
My apologies, it seems I can't directly write files in this environment.

However, I've generated the complete Markdown content for your `PROJECT_DOCUMENTATION.md` file. Please copy the text below and paste it into a new file named `PROJECT_DOCUMENTATION.md` in your project's root directory.

```markdown
# Project: Unified Student Responsibilities Data Model

## 1. Overview

This project aims to create a centralized and unified data model for managing student responsibilities, course information, schedules, assignments, and tests. The primary goal is to consolidate various existing data schemas (potentially from different sources or for different courses) into a single, consistent YAML file: `docs/data.yaml`.

This unified model will serve as a single source of truth, simplifying data management, enabling easier development of tools (e.g., calendar integrations, notification systems, personalized dashboards), and ensuring data consistency across different views or applications.

## 2. Core Data Structure: `docs/data.yaml`

The heart of this project is the `docs/data.yaml` file, which defines the schema for storing all relevant student and course information. It is structured as a list of `courses`, where each course object contains detailed information.

### 2.1. Top-Level Structure

The root of the YAML file is a key named `courses`, which holds a list of course objects.

```yaml
courses:
  - # Course Object 1
    ...
  - # Course Object 2
    ...
```

### 2.2. Course Object Structure

Each course object within the `courses` list has the following primary fields:

*   `id` (String, Mandatory): A unique, machine-readable identifier for the course (e.g., "anatomy_semA_2025").
*   `name` (String, Mandatory): The human-readable name of the course (e.g., "Human Anatomy - Part 1").
*   `heb_name` (String, Optional): The Hebrew name of the course.
*   `year` (String, Optional): The academic year (e.g., "תשפ\"ה").
*   `semester` (String, Optional): The semester (e.g., "א'").

#### 2.2.1. `description` (Object, Optional)

Contains descriptive information about the course.
```yaml
description:
  en: "Course description in English."
  he: "תיאור הקורס בעברית."
  goal: "The primary learning objectives of this course are..."
```

#### 2.2.2. `target_audience` (List of Strings, Optional)

Specifies the intended audience for the course.
```yaml
target_audience:
  - "Medical students, Year 1, 4-year program"
  - "Medical students, Year 2, 6-year program"
```

#### 2.2.3. `general_location` (String, Optional)

Default location for the course if not specified at a more granular level.

#### 2.2.4. `general_day_time_info` (String, Optional)

General information about recurring course timings (e.g., "Tuesdays, 15:15-17:00").

#### 2.2.5. `personnel` (Object, Optional)

Information about individuals involved in the course.
```yaml
personnel:
  coordinators:
    - name: "Prof. Noam Shomron"
      email: "noam.shomron@example.com" # Optional
    - name: "Dr. Gadi Levi"
  overall_lecturers: # Main lecturers for the entire course
    - name: "Prof. Ido Wolf"
      # email: "prof.wolf@example.com" # Optional
```
*   `coordinators`: List of course coordinators. Each item can be a string (name only) or an object with `name` and `email`.
*   `overall_lecturers`: List of main lecturers for the course. Structure similar to coordinators.

#### 2.2.6. `requirements` (String, Optional)

Course prerequisites or mandatory requirements.

#### 2.2.7. `grading_policy` (String, Optional)

Details on how the course is graded.

#### 2.2.8. `course_notes` (String, Optional)

Any general notes relevant to the course.

#### 2.2.9. `student_groups` (List of Objects, Optional)

Defines specific student groups within the course.
```yaml
student_groups:
  - name: "Group 1A"
    details: "Morning lab session group."
    location: "Lab Room 101" # Optional: default location for this group's activities
    # participants: # Optional: List of participant objects for this group
    #   - name: "Student Alpha"
    #     email: "alpha@example.com"
    #     student_id: "12345"
    #     details: "Specific details about student Alpha"
    #     notes: "Notes related to student Alpha"
```

#### 2.2.10. `assignments` (List of Objects, Optional)

Details about course assignments.
```yaml
assignments:
  - name: "Midterm Project Proposal"
    due_date: "YYYY-MM-DD" # e.g., "2025-04-15"
    due_time: "HH:MM"      # e.g., "23:59" (Optional)
    submission_method: "Online via Moodle" # How/where to submit
    details: "Submit a 2-page proposal for the AI in Medicine project."
    estimated_effort_hours: 10 # Optional
```

#### 2.2.11. `schedule` (Object, Optional)

Contains the detailed course schedule.
```yaml
schedule:
  general_notes: "All recorded lectures will be available by Sunday evening." # Notes applicable to the entire schedule
  calendar_entries: # List of entries, each representing a specific day's activities
    - date: "YYYY-MM-DD" # e.g., "2025-03-17"
      day_of_week_heb: "יום שני" # Optional
      day_of_week_en: "Monday"   # Optional
      daily_notes: "Focus on Abdomen today." # Optional notes for this specific day
      
      time_slots: # List of activities scheduled for this date
        - start_time: "HH:MM" # e.g., "08:00"
          end_time: "HH:MM"   # e.g., "09:00"
          # Alternatively: time_range: "HH:MM-HH:MM"
          subject: "Abdomen CA Session" # Topic/Name of the activity
          activity_type: "Self-Study / CA" # e.g., Lecture, Lab, PBL, Recorded, Self-Study, Exam
          location: "עבודה עצמית" # Location of the activity
          instructors: # List of instructors/lecturers for this specific slot
            - "ד\"ר מיכל גרייצר חדד"
            - "רננה ברץ גולדשטיין"
          details: "Review recorded lectures on pelvic anatomy." # More specific details
          attending_groups: ["All"] # or ["Group 1A", "Group 2A"] - which student groups attend
          resources: # Optional: List of related resources
            - type: "video_lecture" # e.g., slide, pdf, link, recording
              url: "https://example.com/lecture1_abdomen"
              title: "Pelvic Anatomy Introduction (Recorded)"
          # group_specific_activities: # Optional: For complex slots split by group
          #   - group_name: "Group 1A"
          #     subject: "Alternate subject for Group 1A"
          #     location: "Alternate location for Group 1A"
          #     instructors: ["Instructor A for Group 1A"]
          #   - group_name: "Group 2A"
          #     subject: "Different subject for Group 2A"
```

#### 2.2.12. `tests` (List of Objects, Optional)

Information about tests and examinations for the course.
```yaml
tests:
  - name: "Anatomy Midterm Exam"
    test_type: "Practical & Written" # e.g., Written, Practical, Oral, Online Quiz
    course_relation: "anatomy_semA_2025" # Optional, explicit link to course ID (usually implied by nesting)
    # group_specific: "N/A" # Optional: If the test is only for specific student groups
    syllabus_covered: "Modules 1-4, including all lab sessions." # Optional
    notes: "Bring your dissection kits. Closed book for written part." # General notes for the test
    
    moadim: # List of examination sittings/opportunities
      - moad_name: "Moed A" # e.g., A, B, Special
        date: "YYYY-MM-DD"    # e.g., "2025-05-20"
        time: "HH:MM"         # e.g., "09:00"
        duration_minutes: 180 # Optional
        location: "Main Examination Hall"
      - moad_name: "Moed B"
        date: "2025-06-10"
        time: "09:00"
        # duration_minutes: 180 # Optional
        location: "Room 203, Medical Building"
```

## 3. Data Sources and Transformation (Conceptual)

The data for `docs/data.yaml` is intended to be sourced from various existing schemas, which may differ in structure and terminology. The core task is to transform data from these source schemas into the unified schema defined above.

**Key Transformation Considerations:**

*   **Field Mapping:** Each piece of information from a source schema needs to be mapped to the corresponding field in the unified `docs/data.yaml` schema.
*   **Data Standardization:**
    *   **Dates and Times:** Convert all dates to `YYYY-MM-DD` format and times to `HH:MM` (24-hour format).
    *   **Personnel Names:** Ensure consistent formatting for names. If source data combines multiple names in one string (e.g., "Lecturer A and Lecturer B"), these should be split into a list.
    *   **Categorical Values:** Standardize terms for fields like `activity_type` (e.g., map "הרצאה", "Lecture", "פרונטלי" to a consistent value like "Lecture").
*   **Handling Lists:** Ensure that fields defined as lists in the unified schema (e.g., `instructors`, `target_audience`) are correctly populated, even if the source has a single string.
*   **Default Values:** Determine appropriate default values for optional fields if source data is missing.
*   **Unique IDs:** Generate meaningful and unique `id` values for courses.

## 4. Future Development and Next Steps

1.  **Develop Transformation Scripts:** Create scripts (e.g., in Python) to automate the process of reading data from various source schemas, transforming it, and generating/updating the `docs/data.yaml` file.
2.  **Schema Validation:** Implement a validation mechanism (e.g., using a JSON Schema or a Python validation library) to ensure that `docs/data.yaml` always conforms to the defined structure and data types.
3.  **Expand Data Coverage:** Populate `docs/data.yaml` with more course examples, mapping them from their original schemas.
4.  **Frontend/Application Layer:** Consider developing applications that consume this YAML data, such as:
    *   A student schedule viewer.
    *   A personalized task list.
    *   Integration with calendar applications.
5.  **Refine Schema:** As more data sources are integrated, the unified schema may need further refinement or extension to accommodate new types of information.

## 5. Contribution Guidelines

*   **Schema Changes:** Any proposed changes to the `docs/data.yaml` schema should be discussed and documented. Consider the impact on existing data and transformation scripts.
*   **Adding New Data:** When adding new courses or transforming data from new sources:
    *   Carefully map source fields to the unified schema.
    *   Ensure data standardization (dates, times, terminology).
    *   Validate the updated `docs/data.yaml` file.
*   **Code Style (for transformation scripts):** Follow standard coding practices for the chosen language. Include comments and documentation for complex logic.

---

This document provides a foundational understanding of the project. For specific details on the current data, always refer to the `docs/data.yaml` file itself.
```
