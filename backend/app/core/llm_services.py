import litellm
import os
import json
import logging
from typing import Dict, Any, Optional, List
import base64
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings

# Setup logging
logger = logging.getLogger(__name__)

# Configure LiteLLM (API keys are usually set via environment variables)
# litellm.set_verbose = True # Enable for debugging

# --- Prompt Loading --- 
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def load_prompt(filename: str) -> str:
    """Loads a prompt from the prompts directory."""
    try:
        logger.info(f"Loading prompt from {PROMPTS_DIR / filename}")
        if not (PROMPTS_DIR / filename).exists():
            logger.error(f"Prompt file not found: {filename}")
            logger.error(f"PROMPTS_DIR: {PROMPTS_DIR}, files: \n\n {os.listdir(PROMPTS_DIR)}")
            raise FileNotFoundError(f"Prompt file not found: {filename}")
        with open(PROMPTS_DIR / filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {filename}")
        return "" # Return empty string or raise error
    except Exception as e:
        logger.error(f"Error loading prompt {filename}: {e}")
        return ""


# --- LLM Interaction Functions --- 

async def process_syllabus_with_llm(file_content: bytes, filename: str, mime_type: str) -> Optional[List[Dict[str, str]]]:
    """
    Uses an LLM (like o4-mini with vision) to parse and structure syllabus content.

    Args:
        file_content: Raw bytes of the syllabus file.
        filename: Original name of the file.
        mime_type: Mime type of the file (e.g., 'application/pdf', 'image/jpeg').

    Returns:
        A list of structured sections [{"label": ..., "content": ...}] or None if failed.
    """
    model = "gpt-4o" # As requested
    structuring_prompt = load_prompt("syllabus_structuring.txt")
    if not structuring_prompt:
        return None

    messages = [
        {
            "role": "system",
            "content": structuring_prompt
        },
        {
            "role": "user",
            "content": [] # Content will be added based on mime_type
        }
    ]

    # Prepare content for multimodal input if necessary
    if mime_type.startswith('image/') or mime_type == 'application/pdf':
        # Assuming o4-mini accepts base64 encoded images/pdfs directly in content
        # This follows OpenAI's vision input format, adjust if o4-mini differs
        base64_encoded_data = base64.b64encode(file_content).decode('utf-8')
        messages[1]["content"] = [
            {
                "type": "text",
                "text": f"Please analyze the following syllabus document ({filename}):"
            },
            {
                "type": "image_url", # Treat PDF as image for vision model
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_encoded_data}"
                }
            }
        ]
    elif mime_type.startswith('text/') or mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
         # For DOCX, we might need to extract text first if model doesn't handle it
         # For now, assume we pass raw text or the model handles it.
         # A robust solution would extract text from DOCX here.
         try:
             # Simple text assumption for now
             text_content = file_content.decode('utf-8')
             messages[1]["content"] = [
                 {
                    "type": "text",
                    "text": f"Please analyze the following syllabus document ({filename}):\n\n```\n{text_content}\n```"
                 }
            ]
         except UnicodeDecodeError:
             logger.error(f"Could not decode file {filename} as text. DOCX/other binary handling needed.")
             # Fallback or error handling needed here - maybe try base64 anyway?
             return None
    else:
        logger.warning(f"Unsupported mime_type for LLM processing: {mime_type}")
        return None

    try:
        logger.info(f"Sending syllabus {filename} to {model} for structuring.")
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=1, # Lower temp for structured output
            max_tokens=3000, # Adjust based on expected output size
            response_format={"type": "json_object"} # Request JSON output if model supports it
        )
        
        # Extract JSON content
        response_content = response.choices[0].message.content
        logger.debug(f"Raw LLM structuring response: {response_content}")
        
        structured_data = json.loads(response_content)
        
        # --- Validation with Fallback --- 
        # 1. Check if it's the expected list format
        if isinstance(structured_data, list) and all(isinstance(item, dict) and 'label' in item and 'content' in item for item in structured_data):
            logger.info(f"Successfully parsed structured list for {filename}.")
            return structured_data
        # 2. Fallback: Check if it's a single dictionary with the correct keys
        elif isinstance(structured_data, dict) and 'label' in structured_data and 'content' in structured_data:
            logger.warning(f"LLM output for {filename} was a single object, not a list. Wrapping it.")
            return [structured_data] # Wrap the single object in a list
        # 3. If neither format matches, log error
        else:
            logger.error(f"LLM output for {filename} was not in the expected list or single object format.")
            return None

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from LLM for {filename}: {e}. Response: {response_content}")
        return None
    except Exception as e:
        logger.error(f"Error calling LiteLLM for structuring {filename}: {e}")
        return None

async def retrieve_relevant_sections(user_query: str, syllabus_sections: List[Dict[str, str]]) -> Optional[str]:
    """
    Uses a smaller LLM to identify relevant sections based on a user query.

    Args:
        user_query: The student's question.
        syllabus_sections: The list of structured sections from the syllabus.

    Returns:
        The concatenated content of the relevant sections, or None.
    """
    model = "gpt-4.1" # As requested
    retrieval_prompt_template = load_prompt("section_retrieval.txt")
    if not retrieval_prompt_template:
        return None

    # Format sections for the prompt
    sections_json_str = json.dumps(syllabus_sections, indent=2)
    
    prompt = retrieval_prompt_template.replace("{{USER_QUERY}}", user_query)
    prompt = prompt.replace("{{SYLLABUS_SECTIONS_JSON}}", sections_json_str)

    messages = [
        {"role": "system", "content": "You are an AI assistant helping to find relevant information in syllabus sections."}, # Can refine this later
        {"role": "user", "content": prompt}
    ]

    try:
        logger.info(f"Sending query and sections to {model} for retrieval.")
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=0.1, # Low temp for focused retrieval
            max_tokens=1000 # Adjust based on expected max content size
        )

        response_text = response.choices[0].message.content.strip()
        logger.debug(f"Raw LLM retrieval response: {response_text}")

        # Check if the model indicated no relevant info
        if "no relevant information found" in response_text.lower():
            return None
        else:
            return response_text # Return the identified relevant content

    except Exception as e:
        logger.error(f"Error calling LiteLLM for retrieval: {e}")
        return None

async def answer_question_naively_streamed(
    user_query: str, 
    full_syllabus_content: str,
    model_name: str = "o4-mini", # Added model_name, default to gpt-4o
    system_prompt_override: Optional[str] = None,
    temperature: Optional[float] = 1.0, 
    max_tokens: Optional[int] = 200     
) -> str:
    """
    Answers a question naively based on the full syllabus content, using a specific persona,
    allowing overrides for system prompt, temperature, max_tokens, and model.
    Streams the response and returns the complete answer.
    """
    # GENERATION_MODEL is now passed as model_name
    
    default_system_message_template = load_prompt("naive_question_answering_system.txt")
    user_prompt_template = load_prompt("naive_question_answering_user.txt") 

    if not user_prompt_template:
        logger.error("Naive question answering user prompt template could not be loaded.")
        return "Error: User prompt template missing. Cannot generate answer."
    
    if not default_system_message_template and not system_prompt_override:
        logger.warning("No system prompt provided or loaded. Using a generic one.")
        effective_system_prompt = "You are a helpful AI assistant."
    elif system_prompt_override:
        effective_system_prompt = system_prompt_override
    else:
        effective_system_prompt = default_system_message_template

    final_user_prompt = user_prompt_template.replace("{{USER_QUERY}}", user_query)
    final_user_prompt = final_user_prompt.replace("{{FULL_SYLLABUS_CONTENT}}", full_syllabus_content)

    messages = [
        {"role": "system", "content": effective_system_prompt},
        {"role": "user", "content": final_user_prompt}
    ]

    full_response = ""
    try:
        logger.info(f"Generating naive answer using {model_name} with temp={temperature}, max_tokens={max_tokens} for query: '{user_query[:50]}...'")
        if model_name == "o4-mini":
            response_stream = await litellm.acompletion(
                model=model_name, # Use the passed model_name
                messages=messages,
                stream=False,
                temperature=temperature,
                max_tokens=30000,
                reasoning_effort="high" if model_name == "o4-mini" else None
            )
            full_response = response_stream.choices[0].message.content
            logger.info(f"Full response: {full_response}")
            return full_response
        else:
            response_stream = await litellm.acompletion(
                model=model_name, # Use the passed model_name
                messages=messages,
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        async for chunk in response_stream:
            delta = chunk.choices[0].delta
            content = delta.get("content", None)
            if content:
                full_response += content
        
        logger.info(f"--- Naive Streaming complete for query: '{user_query[:50]}...' ---")
        return full_response

    except litellm.exceptions.ContextWindowExceededError as e:
        logger.error(f"Context window exceeded for model {model_name} during naive answering.")
        logger.error(f"Provided syllabus content length: {len(full_syllabus_content)} characters.")
        logger.error(f"Error details: {e}")
        return "התנצלות, קובץ הנתונים גדול מדי לעיבוד בבת אחת. לא ניתן לענות על השאלה."
    except Exception as e:
        logger.error(f"Error during naive answer generation with {model_name}: {e}")
        return "התנצלות, אירעה שגיאה בעת יצירת התשובה."

# --- Placeholder for Main Processing Logic --- 
# This function will be called by the webhook endpoint later
async def process_chat_message(user_id: str, user_query: str, platform: str, db: Any) -> str:
    """
    Orchestrates the retrieval and generation for an incoming chat message.
    (Placeholder - Needs full implementation)
    """
    logger.info(f"Processing message from {user_id} on {platform}: '{user_query}'")
    
    # 1. Identify the relevant syllabus for the user/context (How? TBD)
    #    For now, assume we just use the *first* syllabus found.
    #    A real system needs mapping (user -> course -> syllabus)
    syllabus_doc = await db.syllabus.find_one({}, sort=[('_id', -1)]) # Get latest syllabus for demo
    if not syllabus_doc or not syllabus_doc.get('versions'):
        return "Sorry, I don't have any syllabus information available right now."
        
    latest_version_data = syllabus_doc['versions'][-1]
    sections = latest_version_data.get('structured_data')
    if not sections:
         return "Sorry, the syllabus data seems incomplete."

    # 2. Call Retrieval LLM
    retrieved_context = await retrieve_relevant_sections(user_query, sections)

    if not retrieved_context:
        return "I couldn't find specific information about that in the syllabus."

    # 3. Call Generation LLM
    generation_model = "gpt-4o-mini" # Use o4-mini for generation too, or configure separately
    system_prompt = "You are a helpful assistant answering questions based *only* on the provided syllabus context. Be concise and accurate. Context:\n---\n{context}\n---"
    
    messages = [
        {"role": "system", "content": system_prompt.format(context=retrieved_context)},
        {"role": "user", "content": user_query}
    ]
    
    try:
        logger.info(f"Sending query and context to {generation_model} for final generation.")
        response = await litellm.acompletion(
            model=generation_model,
            messages=messages,
            temperature=0.5,
            max_tokens=1500
        )
        final_answer = response.choices[0].message.content.strip()
        
        # 4. Store conversation turn (Needs implementation)
        # await store_message_turn(user_id, platform, user_query, retrieved_context, final_answer, db)
        
        return final_answer
        
    except Exception as e:
        logger.error(f"Error during final generation: {e}")
        return "Sorry, I encountered an error generating the final response."


# --- Helper to load settings (if needed, though LiteLLM uses env vars) --- 
# from app.core.config import get_settings
# settings = get_settings()

async def process_message(
    message: str,
    sender_id: str,
    db: AsyncIOMotorDatabase,
    settings: Settings
) -> str:
    """
    Process an incoming message using LLM and return response.
    
    Args:
        message: The message text
        sender_id: Unique ID of the message sender
        db: Database connection
        settings: Application settings
        
    Returns:
        Response text to be sent back to the user
    """
    # TODO: Refactor based on docs/docs.md - Implement Two-Stage LLM Process
    # 1. Retrieval Stage: Use a smaller/cheaper LLM or embedding search 
    #    to find relevant text chunks from the parsed syllabus 
    #    (which should be stored in MongoDB after upload).
    # 2. Generation Stage: Pass the original query + retrieved context 
    #    to the main generation LLM (e.g., settings.GENERATION_LLM_MODEL).
    
    try:
        # Configure OpenAI API key (adjust if using different APIs for retrieval/generation)
        openai.api_key = settings.OPENAI_API_KEY # Assuming OpenAI for generation for now
        
        # Get conversation history
        conversation_history = await get_conversation_history(sender_id, db)
        
        # --- Retrieval Stage (Placeholder) ---
        # Replace get_relevant_syllabus_content with the actual retrieval logic
        # relevant_chunks = await retrieve_relevant_chunks(message, db, settings)
        relevant_content = await get_relevant_syllabus_content(message, db) # Keep existing simple search for now
        
        # --- Generation Stage --- 
        # Construct system message with context (retrieved chunks)
        system_message = "You are Gil, an AI assistant for education. "
        if relevant_content:
            system_message += f"Based on the curriculum: {relevant_content}"
        
        # Create messages for API call
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({"role": "user", "content": msg["message"]})
            if "response" in msg:
                messages.append({"role": "assistant", "content": msg["response"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI API (or the configured Generation LLM API)
        response = await openai.ChatCompletion.acreate(
            model=settings.GENERATION_LLM_MODEL, # Use the generation model
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract and return response text
        response_text = response.choices[0].message.content.strip()
        return response_text
        
    except Exception as e:
        logger.error(f"Error in process_message: {str(e)}")
        return "I'm sorry, I encountered an error processing your message. Please try again later."

async def get_conversation_history(sender_id: str, db: AsyncIOMotorDatabase) -> list:
    """Get recent conversation history for a user."""
    history = await db.messages.find(
        {"sender": sender_id}
    ).sort("timestamp", -1).limit(10).to_list(10)
    
    # Reverse to get chronological order
    history.reverse()
    return history

async def get_relevant_syllabus_content(message: str, db: AsyncIOMotorDatabase) -> Optional[str]:
    """Find relevant syllabus content based on the message.
       *** This is a placeholder - Replace with actual retrieval logic (embeddings/LLM). ***
    """
    # Simple keyword-based search for now
    # In a real implementation, this would use vector embeddings and semantic search
    keywords = message.lower().split()
    
    pipeline = [
        {"$match": {"$text": {"$search": " ".join(keywords)}}},
        {"$limit": 1}
    ]
    
    results = await db.syllabus.aggregate(pipeline).to_list(1)
    
    if results:
        # Format the content
        syllabus = results[0]
        content_summary = f"Title: {syllabus['title']}\nDescription: {syllabus['description']}\n"
        
        for item in syllabus["content"][:3]:  # Limit to first 3 topics
            content_summary += f"Topic: {item['topic']}\n"
        
        return content_summary
    
    return None 