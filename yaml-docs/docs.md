Okay, Yosef, here is a detailed document outlining the project plan based on our discussion.

---

## Project Plan: Syllabus Query Bot

**Version:** 1.1
**Date:** 2024-12-12 (Updated)

**1. Project Overview**

*   **Goal:** Develop an AI-powered chatbot for students to query course syllabi via WhatsApp, Telegram, and web chat.
*   **Problem Solved:** Provide quick access to specific syllabus information.
*   **Core Technology:** Use LLMs (`o4-mini`, `gpt-4.1`, Generation LLM) managed via `litellm` for syllabus structuring, information retrieval, and answer generation.

**2. Target Audience**

*   **Students:** Primary users (WhatsApp, Telegram, Web Chat).
*   **Course Administrators/Instructors:** Admin UI users for syllabus management and monitoring.

**3. Core Features**

*   **Student-Facing Features:**
    *   Natural language queries about syllabus content.
    *   LLM-generated answers based on retrieved syllabus sections.
*   **Admin-Facing Features (React UI w/ Ant Design):**
    *   Secure login/authentication (Future).
    *   Upload syllabi (PDF, DOCX, JPG, PNG) via `/api/v1/admin/syllabus/upload`.
    *   View list of managed syllabi (`filename`, `upload_timestamp`, `latest_version`).
    *   View and Edit LLM-structured syllabus sections (maintaining version history via `PUT /api/v1/admin/syllabus/{id}`).
    *   View specific syllabus versions (`GET /api/v1/admin/syllabus/{id}/version/{version_number}`).
    *   Monitor conversation logs (Future).
    *   Configure system prompt via UI (Future).

**4. Technical Architecture**

The system employs a hybrid architecture combining cloud services for the frontend and secure self-hosting for the backend and database.

*   **Frontend (Admin & User Web):** Single React/TypeScript application using Ant Design, hosted on Cloudflare Pages. Routing separates Admin (`/admin/*`) and User (`/chat`) interfaces.
*   **Backend:** FastAPI (Python) application using `litellm` for LLM interactions. Handles API endpoints, webhook processing, syllabus structuring, retrieval orchestration, and database interaction.
*   **Database:** MongoDB instance storing syllabus documents, structured data versions, and conversation history.
*   **LLM Interaction:** Multi-stage process using external LLM APIs via `litellm`:
    1.  **Structuring:** On upload, file content (including images) is sent to `o4-mini` with a prompt from `backend/prompts/syllabus_structuring.txt` to extract text and structure it into labeled sections (JSON output).
    2.  **Retrieval:** User query + structured sections (from latest syllabus version in DB) are sent to `gpt-4.1` with a prompt from `backend/prompts/section_retrieval.txt` to identify relevant section content.
    3.  **Generation:** Original query + retrieved section content + system prompt (from DB/settings) are sent to the main Generation LLM (e.g., `gpt-4o-mini` or configured model) for the final answer.
*   **Exposure & Security:** Self-hosted backend exposed via Cloudflare Tunnel.
*   **Containerization:** Backend FastAPI app and MongoDB run as Docker containers via `docker-compose.yml`.

**Diagrammatic Representation (Textual):**

```
+---------------------+      +---------------------+      +-----------------------+
| User (WhatsApp/TG)  |<---->| WhatsApp/TG Platform|<---->|   Cloudflare Tunnel   |
+---------------------+      +---------------------+      +-----------------------+
                                                             |        ^ (Webhook)
                                                             |        | (API Resp)
                                                             v        |
+---------------------+      +---------------------+      +-----------------------+
| User (Web Chat)     |<---->| Cloudflare Pages    |<---->|   Self-Hosted Machine |
|   (React App)       |      | (Frontend Hosting)  |      | (via Cloudflare Tunnel| for API calls) |
+---------------------+      +---------------------+      | +-------------------+ |
                                                             | | cloudflared Daemon| |
+---------------------+      +---------------------+      | +-------------------+ |
| Admin (Web UI)      |<---->| Cloudflare Pages    |<---->|           |           |
|   (React App)       |      | (Frontend Hosting)  |      |           v           |
+---------------------+      +---------------------+      | +-------------------+ |
                                                             | | FastAPI Container | |
                                                             | |  (Backend Logic)  | |
                                                             | +-------------------+ |
                                                             |     |        ^        |
                                                             |     v        |        |
                                                             | +-------------------+ |    +-------------------+
                                                             | | MongoDB Container |<--->| Cloudflare R2     |
                                                             | |    (Database)     | |    | (Optional Files)  |
                                                             | +-------------------+ |    +-------------------+
                                                             |     |        ^        |
                                                             |     v        | (API Calls)
                                                             | +-------------------+ |
                                                             | | External LLM APIs | |
                                                             | | (Retrieval, Gen)  | |
                                                             | +-------------------+ |
                                                             +-----------------------+
```

**5. Technology Stack**

*   **Backend:** Python 3.x, FastAPI, `litellm`, Motor (MongoDB driver), `python-dotenv`, `python-multipart`.
*   **Frontend:** TypeScript, React, Ant Design, React Router DOM.
*   **Database:** MongoDB.
*   **LLM APIs:** OpenAI (`o4-mini`, `gpt-4.1`, potentially others), managed via `litellm`.
*   **Containerization:** Docker, Docker Compose (`docker-compose.yml`, `backend/Dockerfile`).
*   **Infrastructure & Hosting:** Cloudflare Pages, Cloudflare Tunnel, Cloudflare DNS, Self-hosted machine, (Optional) Cloudflare R2, (Optional) Cloudflare Secrets / `.env` file.
*   **Prompt Management:** Text files in `backend/prompts/` directory.

**6. Deployment Strategy**

*   **Frontend:** CI/CD from Git to Cloudflare Pages.
*   **Backend & Database:** Docker containers on self-hosted machine (`docker-compose up`).
*   **Tunnel:** `cloudflared` service connects host to Cloudflare edge.

**7. Data Management**

*   **Syllabus Intake:** Admin uploads files (PDF, DOCX, JPG, PNG) via React UI (`SyllabusManagement.tsx`) to `/api/v1/admin/syllabus/upload`.
*   **Processing:** FastAPI backend calls `process_syllabus_with_llm` service (`o4-mini`) to get structured sections (`[{label: ..., content: ...}]`).
*   **Storage:**
    *   MongoDB `syllabus` collection stores documents containing `filename`, `upload_timestamp`, and a `versions` list.
    *   Each item in `versions` is a `SyllabusVersion` containing `version_number`, `timestamp`, and the `structured_data` (list of `StructuredSection`).
    *   Edits via `PUT /api/v1/admin/syllabus/{id}` append a new `SyllabusVersion` to the list.
    *   Conversation history stored in `messages` collection (structure TBD).
*   **Retrieval:** Chat endpoints fetch the latest `structured_data` from the relevant syllabus in MongoDB, send it with the query to `retrieve_relevant_sections` service (`gpt-4.1`) to get context for the generation LLM.

**8. Potential Challenges & Risks**

*   **Self-Hosting Reliability:** Requires active maintenance (updates, backups).
*   **LLM Structuring Quality:** Output quality of `o4-mini` depends heavily on the prompt and input complexity. May require prompt iteration or fallback mechanisms.
*   **LLM Retrieval Accuracy:** `gpt-4.1` needs to correctly identify relevant sections based on the prompt.
*   **Cost:** LLM API calls for structuring (potentially large inputs) and retrieval add operational cost.
*   **LLM Hallucination:** Generation LLM needs strong prompting to stick to provided context.
*   **Security:** Host OS, container, and API key security are critical.
*   **DOCX Handling:** Current LLM service assumes text extraction for DOCX; might need explicit library integration (`python-docx`) if `o4-mini` doesn't handle it directly in binary format.

**9. Next Steps (Updated Status & Focus)**

1.  **Setup Project Structure:** **(DONE)**
2.  **Initialize Docker Environment:** **(DONE)**
3.  **Initialize FastAPI App:** **(DONE)**
4.  **Setup Cloudflare Tunnel:** **(PARTIAL - Placeholder in compose, requires manual setup)**
5.  **Basic Database Connection:** **(DONE)**
6.  **Define Core Models & Schemas:** **(DONE - Updated for versioning)**
7.  **Implement LLM Services & Prompts:** Integrated `litellm`, created prompts, implemented `process_syllabus_with_llm` (`o4-mini`) and `retrieve_relevant_sections` (`gpt-4.1`). **(DONE)**
8.  **Implement Admin API Endpoints:** Implemented `/syllabus/upload`, `/syllabus`, `/syllabus/{id}`, `/syllabus/{id}/version/{num}`, `PUT /syllabus/{id}`. **(DONE)**
9.  **Develop Frontend Admin UI (Syllabus):** Updated `SyllabusManagement.tsx` to use API endpoints, view list, upload, view/edit latest version via modal using Ant Design. **(DONE)**
10. **Implement Webhook Logic:** Implement TODOs in `backend/app/api/v1/endpoints/webhook.py` to call `process_chat_message` for handling incoming user messages. **(NEXT)**
11. **Implement Message Storage:** Add logic to store conversation turns in MongoDB. **(NEXT)**
12. **Develop Frontend User Chat UI:** Build the `pages/user/Chat.tsx` interface. **(TODO)**
13. **Develop Frontend Admin UI (Other Sections):** Implement Dashboard, Logs, Settings pages functionality. **(TODO)**

---

This document summarizes the updated plan. Please review it, and let me know if any adjustments or clarifications are needed before we proceed further.
