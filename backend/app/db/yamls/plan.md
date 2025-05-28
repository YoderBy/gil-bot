
Okay, this is a great goal! Allowing users to easily edit and view syllabus data directly through the website will significantly improve the admin experience. Here's a refactor plan to achieve this, keeping your current `AdminLayout.tsx` and YAML data structure in mind:

**Refactoring Plan: Web-Based Syllabus Management**

**I. Core Idea: API-Driven YAML Management**

The fundamental change will be to introduce a backend API that acts as an intermediary between your frontend admin interface and the YAML files. The frontend will no longer directly interact with or assume the structure of YAML files; it will communicate with the API using JSON.

**II. Backend (New or Enhanced)**

You'll need a backend service. If you don't have one, you'll need to create it (e.g., using Node.js/Express, Python/Flask, or any other backend technology you're comfortable with).

1.  **YAML File Storage:**
    *   **Location:** Store all your syllabus YAML files in a dedicated, non-publicly accessible directory on your server (e.g., `project_root/syllabi_data/` or similar). This directory should **not** be within your frontend's `public` folder.
    *   **Organization:** You can keep one YAML file per course as you seem to have now (e.g., `anatomy.yaml`, `ai.yaml`).

2.  **API Endpoints (using JSON for request/response):**
    *   `GET /api/courses`:
        *   **Action:** Reads the `syllabi_data` directory, lists all YAML files (representing courses). It could also parse basic info like `name` and `heb_name` from each YAML to return a more informative list.
        *   **Response:** `[{ "id": "anatomy", "name": "Human Anatomy", "heb_name": "אנטומיה..." }, ...]`
    *   `GET /api/courses/{courseId}`:
        *   **Action:** Reads the specific YAML file (e.g., `anatomy.yaml` if `courseId` is "anatomy"), parses it into a JSON object.
        *   **Response:** The full course data as a JSON object.
    *   `PUT /api/courses/{courseId}`:
        *   **Action:** Receives updated course data as a JSON object in the request body.
        *   **Validation:** **Crucially, validate the incoming JSON structure** against your expected YAML schema. This prevents malformed data from corrupting your YAML files.
        *   Converts the validated JSON back into YAML format.
        *   Overwrites the corresponding YAML file on the server.
        *   **Response:** Success message or the updated JSON data.
    *   `POST /api/courses` (Optional - for creating new courses):
        *   **Action:** Receives new course data as JSON. Validates it. Creates a new YAML file.
        *   **Response:** ID of the newly created course and its data.
    *   `DELETE /api/courses/{courseId}` (Optional - for deleting courses):
        *   **Action:** Deletes the specified YAML file. Implement safeguards (e.g., soft delete or confirmation).
        *   **Response:** Success message.

3.  **Technology Stack:**
    *   **Backend Language/Framework:** Node.js with Express is a common choice for React frontends, but Python (Flask/Django), Ruby on Rails, etc., are all viable.
    *   **YAML Parsing Library:**
        *   Node.js: `js-yaml`
        *   Python: `PyYAML`

**III. Frontend (React Components & Pages)**

Your `frontend/src/components/pages/admin/` directory will house the UI for this.

1.  **`SyllabusManagement.tsx` (Path: `/admin/syllabus` - as per your `AdminLayout.tsx`):**
    *   This will be the main container page.
    *   **Initial View:**
        *   Fetch and display a list of all courses from `GET /api/courses` (e.g., in an Ant Design `Table` or `List`).
        *   Each course in the list should have "View Details" and "Edit" buttons/links.
        *   (Optional) "Add New Course" button.

2.  **Course Detail View (Read-Only):**
    *   When "View Details" is clicked, navigate to a route like `/admin/syllabus/{courseId}` or display details in a modal/drawer.
    *   Fetch course data from `GET /api/courses/{courseId}`.
    *   **Display:** Render the JSON data in a user-friendly, readable format.
        *   You could create specific components to render different parts of the syllabus (e.g., `ScheduleView`, `PersonnelView`).
        *   For rich text fields like descriptions, ensure markdown or HTML is rendered correctly (if you plan to support that).
        *   Provide an "Edit this Course" button.

3.  **Course Edit View/Form:**
    *   When "Edit this Course" is clicked (or "Add New Course"), display a form.
    *   **Form Structure:** This is the most complex part. The form needs to mirror your YAML structure. Ant Design `Form` components will be very helpful.
        *   **Top-level fields:** `id`, `name`, `heb_name`, `year`, `semester`.
        *   **Nested Objects:** For `description`, `personnel`, etc., use nested form sections.
        *   **Arrays of Objects:** For `assignments`, `schedule.calendar_entries`, `personnel.coordinators`, `student_groups.matzpen_groups`, etc., use Ant Design's `Form.List`. This allows users to add, remove, and reorder items dynamically. Each item in the list would itself be a sub-form.
            *   Example for `calendar_entries`: A `Form.List` where each item has fields for `date`, `day_of_week_heb`, and a nested `Form.List` for `time_slots`.
        *   **Rich Text:** For multiline descriptions (`description.he`, `description.en`, `details` fields), consider using a simple rich text editor component or a textarea with good multiline support.
    *   **Data Handling:**
        *   Fetch existing data using `GET /api/courses/{courseId}` to pre-fill the form.
        *   Manage form state using React state (`useState` or `useReducer` for complex forms).
    *   **Submission:**
        *   On submit, gather the form data into a JSON object matching your API's expectation.
        *   Send it to `PUT /api/courses/{courseId}` (or `POST /api/courses` for new).
        *   Handle API responses (success/error) and provide feedback to the user.
    *   **Client-side Validation:** Use Ant Design form validation for immediate feedback on required fields, formats, etc.

4.  **Component Breakdown (Examples):**
    *   `SyllabusTable.tsx`: Displays the list of courses.
    *   `SyllabusForm.tsx`: The main editing form.
        *   `GeneralInfoFormSection.tsx`
        *   `PersonnelFormSection.tsx`
        *   `ScheduleFormSection.tsx` (likely using `Form.List` for `calendar_entries` and `time_slots`)
        *   `AssignmentsFormSection.tsx` (using `Form.List`)
        *   `StudentGroupsFormSection.tsx` (using `Form.List` for groups, and nested `Form.List` for students within groups)
        *   `TestsFormSection.tsx`

**IV. State Management (Frontend):**

*   For local component state (form values, loading states), React's `useState` and `useEffect` are sufficient.
*   If you need to share syllabus data across unrelated components or manage complex asynchronous operations, consider a lightweight state management library like Zustand or Jotai. Redux might be overkill unless the admin panel grows significantly more complex.

**V. User Experience (UX) & UI:**

*   Use Ant Design components for a consistent and professional look.
*   Make forms intuitive. Given the potentially large amount of data, consider:
    *   Using `Tabs` or `Collapse` panels to organize different sections of the syllabus form.
    *   Clear "Add Item" / "Remove Item" buttons for lists.
    *   Modals or drawers for editing complex list items (e.g., a single schedule entry).
*   Provide clear loading states and error messages.
*   Implement "Save", "Cancel", and possibly "Save and Continue Editing" buttons.

**VI. Enhancements (Future):**

1.  **Schema Definition/Validation:**
    *   Define a formal JSON schema for your syllabus data.
    *   Use this schema for robust validation on both the backend (before writing to YAML) and potentially on the frontend (for better form generation/validation).
2.  **Direct YAML Editor (Advanced):**
    *   For power users, you could embed a YAML editor (like a Monaco editor instance configured for YAML) as an alternative way to edit the raw data, but the form-based approach should be the primary method for ease of use.
3.  **Versioning/History:**
    *   The backend could integrate with Git to commit changes to the YAML files, providing a version history. This is more complex but very powerful.
4.  **User Permissions:** If multiple admin roles are needed, implement an authentication and authorization system.

**Immediate Steps:**

1.  **Set up a basic backend server** with a YAML parsing library.
2.  **Implement the `GET /api/courses` and `GET /api/courses/{courseId}` endpoints** to read and serve YAML data as JSON.
3.  **Modify `SyllabusManagement.tsx`** to fetch and display the list of courses.
4.  **Create a basic read-only view** for a single course.
5.  **Start building the `SyllabusForm.tsx`** piece by piece, tackling one section of the YAML at a time.
6.  **Implement the `PUT /api/courses/{courseId}` endpoint** to save changes.

This plan provides a scalable approach. Starting with read functionality and then moving to editing is a good way to manage complexity. The key is the API abstraction over the YAML files.
