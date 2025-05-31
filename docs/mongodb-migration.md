# MongoDB Migration Guide

## Overview

The syllabus system has been migrated from file-based YAML storage to a MongoDB document-based system with full version control and change tracking.

## Database Structure

### Collections

1. **syllabi** - Main syllabus documents
   ```json
   {
     "_id": ObjectId,
     "course_id": "0111.2126.01",
     "current_version": 1,
     "created_at": ISODate,
     "created_by": "system",
     "metadata": {
       "name": "Introduction to Pharmacology",
       "heb_name": "מבוא לפרמקולוגיה",
       "year": "תשפ\"ה",
       "semester": "b"
     }
   }
   ```

2. **syllabus_versions** - Version history with full data snapshots
   ```json
   {
     "_id": ObjectId,
     "syllabus_id": "ObjectId reference",
     "version": 1,
     "data": { /* Full SyllabusCourse object */ },
     "created_at": ISODate,
     "created_by": "user_id",
     "change_summary": "Initial import from YAML",
     "changes": [ /* Array of FieldChange objects */ ]
   }
   ```

## Key Features

### 1. Automatic Data Import
- On first startup, the system automatically imports all YAML files from `backend/app/db/yamls/`
- Each YAML file creates a syllabus document with an initial version
- Duplicate imports are prevented by checking course IDs

### 2. Version Control
- Every edit creates a new version
- Complete snapshot stored for each version
- Changes are tracked at field level
- Version comparison available via API

### 3. Change Tracking
- Field-level change detection using DeepDiff
- Changes categorized as: add, update, delete
- Human-readable change summaries
- Full audit trail maintained

## API Endpoints

### Syllabus Management

1. **List Syllabi**
   ```
   GET /api/v1/syllabus?search=term&year=2024&semester=a
   ```

2. **Get Syllabus**
   ```
   GET /api/v1/syllabus/{id}?version=2
   ```
   Returns current version by default, or specific version if specified.

3. **Update Syllabus**
   ```
   PUT /api/v1/syllabus/{id}
   Body: {
     ...syllabus_data,
     change_summary: "Updated schedule"
   }
   ```

4. **Get Version History**
   ```
   GET /api/v1/syllabus/{id}/versions
   ```

5. **Compare Versions**
   ```
   GET /api/v1/syllabus/{id}/diff/{version1}/{version2}
   ```

## Deployment

### Development
```bash
docker-compose up
```

### Production
1. Set proper MongoDB credentials in `.env`
2. Configure volume for data persistence:
   ```yaml
   volumes:
     mongo_data:
       driver_opts:
         type: none
         o: bind
         device: /path/to/mongo/data
   ```
3. Enable authentication and configure backups

## Migration from File System

### Initial Import
1. Place YAML files in `backend/app/db/yamls/`
2. Start the application
3. Check logs for import status

### Handling Existing Data
- If syllabi already exist in DB, import is skipped
- To reimport, clear the database first
- Course IDs must be unique

## Backup Strategy

### MongoDB Backup
```bash
# Backup
mongodump --db=gil_whatsapp_bot --out=/backup/$(date +%Y%m%d)

# Restore
mongorestore --db=gil_whatsapp_bot /backup/20240101
```

### Version Export
Export specific versions as YAML:
```python
# Example script to export current versions
async def export_current_versions():
    syllabi = await db.syllabi.find()
    for syllabus in syllabi:
        version = await db.syllabus_versions.find_one({
            "syllabus_id": str(syllabus["_id"]),
            "version": syllabus["current_version"]
        })
        # Save version["data"] as YAML
```

## Future Enhancements

1. **User Authentication**
   - Track who makes changes
   - Role-based permissions
   - Edit approval workflow

2. **Advanced Features**
   - Real-time collaboration
   - Conflict resolution for concurrent edits
   - Webhook notifications for changes
   - Full-text search with Elasticsearch

3. **Performance Optimization**
   - Redis caching for frequently accessed syllabi
   - Partial updates for large documents
   - Compressed storage for old versions

## Troubleshooting

### MongoDB Authentication Issues

If you see authentication errors in the logs:

1. **For Development** (No Authentication):
   - The default `docker-compose.yml` runs MongoDB without authentication
   - No credentials needed in `.env`

2. **For Production** (With Authentication):
   - Use `docker-compose.prod.yml`
   - Create a `.env` file with:
     ```env
     MONGO_USER=your_db_user
     MONGO_PASSWORD=your_db_password
     MONGO_ROOT_USER=root
     MONGO_ROOT_PASSWORD=your_root_password
     ```

3. **Reset MongoDB** (if needed):
   ```bash
   # Stop containers
   docker-compose down
   
   # Remove MongoDB volume
   docker volume rm gil-bot-clean_mongo_data
   
   # Start fresh
   docker-compose up
   ```

## Environment Configuration

Create a `.env` file in the project root:

```env
# Application Settings
DEBUG=True
APP_NAME=Gil-WhatsApp-Bot

# MongoDB Settings (Development - No Auth)
MONGODB_HOST=mongo
MONGODB_PORT=27017
MONGODB_DB_NAME=gil_whatsapp_bot

# MongoDB Settings (Production - With Auth)
# MONGO_USER=gil_user
# MONGO_PASSWORD=secure_password_here

# LLM Settings
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4
``` 