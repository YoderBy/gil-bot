
Okay, Yosef, here is a detailed document outlining the project plan based on our discussion.

---

## Project Plan: Syllabus Query Bot

**Version:** 1.0
**Date:** 2024-12-12

**1. Project Overview**

*   **Goal:** To develop an AI-powered chatbot that allows students to easily query information contained within course syllabi. The primary interaction channels will be WhatsApp and Telegram, with a secondary web-based chat interface.
*   **Problem Solved:** Students often struggle to quickly find specific information (dates, assignments, policies, contact info) buried within lengthy syllabus documents. This bot aims to provide instant, accurate answers derived directly from the official course materials.
*   **Core Technology:** The system will leverage Large Language Models (LLMs) to understand student queries and retrieve/generate relevant information from parsed syllabus content.

**2. Target Audience**

*   **Students:** Primary users who will interact with the bot via WhatsApp, Telegram, or a dedicated web chat to ask questions about their course syllabi.
*   **Course Administrators/Instructors:** Secondary users who will use a dedicated Admin web interface to upload syllabi, manage bot settings, test functionality, and monitor interactions.

**3. Core Features**

*   **Student-Facing Features (WhatsApp/Telegram/Web Chat):**
    *   Ask natural language questions about syllabus content (e.g., "When is the midterm?", "What is the late submission policy?", "What are the professor's office hours?").
    *   Receive concise answers generated by an LLM, based on information retrieved from the relevant syllabus.
    *   (Future Enhancement) Proactive reminders for deadlines or events mentioned in the syllabus.
*   **Admin-Facing Features (Web Interface):**
    *   Secure login/authentication.
    *   Upload new course syllabi (PDF, DOCX, etc.).
    *   View list of managed syllabi and their processing status.
    *   Test the bot's responses for specific syllabi.
    *   Monitor conversation logs between students and the bot (anonymized if necessary).
    *   Configure system-level settings, primarily editing the main system prompt used by the generation LLM.

**4. Technical Architecture**

The system employs a hybrid architecture combining cloud services for the frontend and secure self-hosting for the backend and database.

*   **Frontend (Admin & User Web):** Two separate React applications hosted on Cloudflare Pages. These communicate with the backend via API calls over HTTPS.
*   **Backend:** A FastAPI (Python) application responsible for API endpoints, webhook handling, business logic, database interaction, and LLM orchestration.
*   **Database:** A MongoDB instance storing application data.
*   **LLM Interaction:** A two-stage process using external LLM APIs:
    1.  **Retrieval:** User query + syllabus text chunks are sent to a designated smaller LLM API to identify the most relevant text sections.
    2.  **Generation:** The original query + the retrieved context are sent to a primary Generation LLM API (Claude/ChatGPT) to synthesize the final answer.
*   **Exposure & Security:** The self-hosted backend is exposed securely to the internet using Cloudflare Tunnel, eliminating the need for open inbound ports on the host machine's firewall. Cloudflare also provides DNS and potential CDN/WAF capabilities.
*   **Containerization:** The backend FastAPI application and the MongoDB database will run as Docker containers managed via Docker Compose on the self-hosted machine.

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

*   **Backend:** Python 3.x, FastAPI
*   **Frontend:** JavaScript/TypeScript, React
*   **Database:** MongoDB
*   **LLM APIs:** Specific smaller LLM for Retrieval, OpenAI API (ChatGPT) / Anthropic API (Claude) for Generation
*   **Containerization:** Docker, Docker Compose
*   **Infrastructure & Hosting:**
    *   Cloudflare Pages (Frontend)
    *   Cloudflare Tunnel (Backend Exposure)
    *   Cloudflare DNS
    *   Self-hosted machine (Old Computer running Linux/Windows/macOS with Docker)
    *   (Optional) Cloudflare R2 (Object Storage for original syllabus files)
    *   (Optional) Cloudflare Secrets (or local environment variables / .env file)

**6. Deployment Strategy**

*   **Frontend:** Continuous deployment from a Git repository (e.g., GitHub) to Cloudflare Pages.
*   **Backend & Database:** Docker containers defined in `docker-compose.yml` run on the designated self-hosted machine.
*   **Tunnel:** The `cloudflared` service (run as a container or host process) establishes the persistent connection to Cloudflare. Tunnel configuration and DNS are managed via Cloudflare dashboard or `cloudflared` CLI.

**7. Data Management**

*   **Syllabus Intake:** Admin uploads files via the React UI. The FastAPI backend receives the file.
*   **Processing:** The backend parses the text content from the uploaded file (handling different formats like PDF, DOCX). The text is broken down into manageable chunks.
*   **Storage:**
    *   Original files may be stored in Cloudflare R2 (optional).
    *   Parsed text chunks and associated metadata (filename, course association) are stored in MongoDB.
    *   Conversation history (user ID, platform, query, retrieved context refs, response) is stored in MongoDB.
    *   System settings (e.g., current system prompt) are stored in MongoDB.
*   **Retrieval:** During a query, relevant text chunks are fetched from MongoDB to be sent to the Retrieval LLM.

**8. Potential Challenges & Risks**

*   **Self-Hosting Reliability:** Dependency on the uptime, stability, and performance of the old computer and home internet connection. Requires manual maintenance (OS updates, Docker updates, backups).
*   **LLM-based Retrieval Performance:** Latency and cost associated with using an LLM for the retrieval step need evaluation. May require optimization or adjustments to the strategy.
*   **LLM Accuracy & Hallucination:** Ensuring the Generation LLM sticks to the provided context and doesn't invent information requires careful prompt engineering.
*   **Parsing Complexity:** Handling diverse and poorly formatted syllabus documents can be challenging.
*   **Security:** While Cloudflare Tunnel significantly improves security over open ports, maintaining the security of the host OS and containers remains crucial. Secure handling of API keys is essential.

**9. Next Steps (Recommendation)**

1.  **Setup Project Structure:** Create the main directories (`backend/`, `frontend/admin/`, `frontend/user/`, `docs/`).
2.  **Initialize Docker Environment:** Create the initial `docker-compose.yml` defining the `backend`, `mongo`, and potentially `cloudflared` services. Create a basic `Dockerfile` for the backend.
3.  **Initialize FastAPI App:** Create the basic FastAPI application structure within `backend/app/` (`main.py`, placeholder routers).
4.  **Setup Cloudflare Tunnel:** Create the tunnel and configure DNS as a proof-of-concept.
5.  **Basic Database Connection:** Implement basic MongoDB connection logic within FastAPI using Motor or Beanie.
6.  **Define Core Models:** Draft Pydantic models for API endpoints and MongoDB documents (Syllabus, Conversation, Settings).

---

This document summarizes our current plan. Please review it, and let me know if any adjustments or clarifications are needed before we proceed further.
