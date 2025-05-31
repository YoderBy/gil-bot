import yaml
import re
import os
from collections import defaultdict

# --- Configuration ---
ACADEMIC_YEAR = 2025  # Default academic year for date conversion (e.g., "17.3" -> "2025-03-17")
SOURCE_DATA_FILE = "docs/data.txt"
OUTPUT_YAML_FILE = "docs/course_data.yaml"

# --- Mappings and Constants ---
HEB_TO_ENG_DAY = {
    "יום ראשון": "Sunday", "יום שני": "Monday", "יום שלישי": "Tuesday",
    "יום רביעי": "Wednesday", "יום חמישי": "Thursday", "יום שישי": "Friday",
    "יום שבת": "Saturday"
}

# --- Helper Functions ---
def parse_time_range_to_start_end(time_str):
    """Converts "8-9" or "08:00-09:00" to ("08:00", "09:00")."""
    if not time_str: return None, None
    parts = time_str.split('-')
    try:
        start_hour_str, *start_minute_str_list = parts[0].split(':')
        start_hour = int(start_hour_str)
        start_minute = int(start_minute_str_list[0]) if start_minute_str_list else 0

        if len(parts) > 1:
            end_hour_str, *end_minute_str_list = parts[1].split(':')
            end_hour = int(end_hour_str)
            end_minute = int(end_minute_str_list[0]) if end_minute_str_list else 0
        else: # If only start time like "8", assume 1 hour duration for end_time. Schema requires end_time.
            end_hour = start_hour + 1
            end_minute = start_minute
        
        return f"{start_hour:02d}:{start_minute:02d}", f"{end_hour:02d}:{end_minute:02d}"
    except ValueError:
        print(f"Warning: Could not parse time range: {time_str}")
        return None, None

def format_date_ddm_to_yyyymmdd(date_str, year):
    """Converts "17.3" to "YYYY-03-17" """
    if not date_str: return None
    try:
        day, month = map(int, date_str.split('.'))
        return f"{year}-{month:02d}-{day:02d}"
    except ValueError:
        print(f"Warning: Could not parse date string: {date_str}")
        return None

def parse_instructors_string(instructor_str):
    """Splits a comma or " / " separated string of instructors into a list."""
    if not instructor_str: return []
    normalized_str = instructor_str.replace(" / ", ", ") # Normalize " / " to ","
    return [name.strip() for name in normalized_str.split(',') if name.strip()]

def get_day_of_week_english(heb_day_str):
    return HEB_TO_ENG_DAY.get(heb_day_str.strip(), None)

def determine_activity_type(subject, location):
    subject_lower = subject.lower() if subject else ""
    location_lower = location.lower() if location else ""

    if "הרצאה" in subject_lower:
        return "Recorded Lecture" if "מוקלט" in subject_lower or "מוקלט" in location_lower else "Lecture"
    if "דיסקציה" in subject_lower or "מעבדת דיסקציה" in location_lower: return "Lab"
    if "pbl" in subject_lower: return "PBL"
    if "עבודה עצמית" in location_lower: return "Self-Study"
    if "ca" in subject_lower and "self-study" not in subject_lower : return "Self-Study / CA"
    if "us" in subject_lower and "חדרי us" not in location_lower: return "Practical Session"
    if "ct" in subject_lower and not any(kw in location_lower for kw in ["119", "דולפי", "כיתה 100"]): return "Practical Session"
    if "חזרה" in subject_lower: return "Review Session"
    if "מוקלט" in location_lower and "הרצאה" not in subject_lower: return "Recorded Material"
    
    return "General Activity" # Default

# --- Main Parsing Logic for source data.txt ---
def parse_source_data(file_path):
    course_id = None
    events = [] # Stores dicts: {day_heb, date_str, time_range_str, subject, location, instructor_str, attending_group}
    student_group_names = set()

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_day_heb = None
    current_date_str_raw = None
    
    slot_time_raw = None
    current_slot_details_type1 = {} # For Type 1 schedule (implicit "All")
    current_slot_details_type2_groups = {} # For Type 2 (group_Xa): { "group_1a": {details}, ... }
    active_group_for_details_type2 = None

    def commit_slot_data():
        nonlocal slot_time_raw, current_slot_details_type1, current_slot_details_type2_groups
        if not slot_time_raw or not (current_slot_details_type1 or current_slot_details_type2_groups):
            return

        if current_slot_details_type1.get("subject"): # Commit Type 1 if data exists
            events.append({
                "day_heb": current_day_heb, "date_str": current_date_str_raw,
                "time_range_str": slot_time_raw, **current_slot_details_type1, "attending_group": None
            })
        
        for group_name, details in current_slot_details_type2_groups.items(): # Commit Type 2 if data exists
            if details.get("subject"):
                events.append({
                    "day_heb": current_day_heb, "date_str": current_date_str_raw,
                    "time_range_str": slot_time_raw, **details, "attending_group": group_name
                })
        
        # Reset for next slot
        slot_time_raw = None
        current_slot_details_type1 = {}
        current_slot_details_type2_groups = {}
        active_group_for_details_type2 = None


    for i, line_raw in enumerate(lines):
        line = line_raw.strip()
        if not line or line.startswith('#'): continue # Skip empty or true comment lines

        # Course ID
        match_course = re.match(r"^course:\s*(.*)", line)
        if match_course:
            if course_id is None: # Take the first one
                course_id = match_course.group(1).strip()
            continue
        
        # Day
        match_day = re.match(r"^\s*-\s*day:\s*([^#]+?)(?:\s*#\s*(.*))?$", line)
        if match_day:
            commit_slot_data() # Commit previous slot before starting new day
            current_day_heb = match_day.group(1).strip()
            current_date_str_raw = None # Reset date context
            continue

        # Date
        match_date = re.match(r"^\s*-\s*date:\s*\"(.*?)\"", line)
        if match_date:
            commit_slot_data() # Commit previous slot before starting new date
            current_date_str_raw = match_date.group(1).strip()
            continue
        
        # Time slot (common for both schedule structures in data.txt)
        match_time = re.match(r"^\s*-\s*time:\s*\"(.*?)\"", line)
        if match_time:
            commit_slot_data() # Commit previous time slot's data
            slot_time_raw = match_time.group(1).strip()
            current_slot_details_type1 = {} # Reset for new time entry
            current_slot_details_type2_groups = {} 
            active_group_for_details_type2 = None
            continue
            
        if not current_day_heb or not current_date_str_raw or not slot_time_raw:
            # Ensure we are within a valid day/date/time context to parse properties
            continue

        # Group specific entry: `group_1a:`
        match_group_key = re.match(r"^\s*(group_\w+):", line)
        if match_group_key:
            active_group_for_details_type2 = match_group_key.group(1).strip()
            student_group_names.add(active_group_for_details_type2)
            if active_group_for_details_type2 not in current_slot_details_type2_groups:
                current_slot_details_type2_groups[active_group_for_details_type2] = {}
            current_slot_details_type1 = {} # Clear type1 details if we switch to group mode for this slot
            continue
        
        # Property line: `subject: "..."`, `location: "..."`, `instructor: "..."`
        match_prop = re.match(r"^\s*(subject|location|instructor):\s*\"(.*?)\"", line)
        if match_prop:
            key, value = match_prop.group(1), match_prop.group(2).strip()
            if active_group_for_details_type2: # Property for a group_Xa block
                current_slot_details_type2_groups[active_group_for_details_type2][key] = value
            else: # Property for a general (Type 1) slot
                current_slot_details_type1[key] = value
                current_slot_details_type2_groups = {} # Clear type2 details if we get a type1 property
            continue

    commit_slot_data() # Commit any remaining data after the loop

    return course_id, events, sorted(list(student_group_names))

# --- Transform to Target YAML Structure ---
def build_yaml_structure(course_id, parsed_events, group_names):
    if not course_id or not parsed_events:
        return None

    course_name_from_id = course_id.replace('-', ' ').title() if course_id else "Unknown Course"
    
    course_data = {
        "id": course_id,
        "name": course_name_from_id,
        # Other top-level course fields from schema (e.g., heb_name, year, semester, description)
        # are not present in data.txt and will be omitted as per user request.
        "schedule": {
            # general_notes: Not available from data.txt
            "calendar_entries": []
        }
    }
    if group_names: # Add student_groups if any were identified
        course_data["student_groups"] = [{"name": name} for name in group_names]

    events_by_date = defaultdict(list)
    for event in parsed_events:
        if not all(k in event for k in ["date_str", "day_heb", "time_range_str", "subject"]):
            print(f"Skipping incomplete raw event data: {event}")
            continue
        formatted_date = format_date_ddm_to_yyyymmdd(event["date_str"], ACADEMIC_YEAR)
        if formatted_date:
            events_by_date[formatted_date].append(event)

    for date_iso, date_events in sorted(events_by_date.items()):
        if not date_events: continue
        day_heb = date_events[0]["day_heb"]
        day_en = get_day_of_week_english(day_heb)
        
        calendar_entry = {"date": date_iso, "day_of_week_heb": day_heb, "time_slots": []}
        if day_en: calendar_entry["day_of_week_en"] = day_en

        for event_detail in date_events:
            start_time, end_time = parse_time_range_to_start_end(event_detail["time_range_str"])
            instructors = parse_instructors_string(event_detail.get("instructor", ""))
            
            time_slot = {"subject": event_detail["subject"]}
            if start_time: time_slot["start_time"] = start_time
            if end_time: time_slot["end_time"] = end_time
            if event_detail.get("location"): time_slot["location"] = event_detail["location"]
            if instructors: time_slot["instructors"] = instructors
            
            activity_type = determine_activity_type(event_detail["subject"], event_detail.get("location"))
            if activity_type: time_slot["activity_type"] = activity_type

            attending_groups = [event_detail["attending_group"]] if event_detail.get("attending_group") else ["All"]
            time_slot["attending_groups"] = attending_groups
            
            # details, resources: Not available from data.txt
            calendar_entry["time_slots"].append(time_slot)
        
        course_data["schedule"]["calendar_entries"].append(calendar_entry)
    
    return {"courses": [course_data]}

# --- Main Execution ---
def main():
    if not os.path.exists(SOURCE_DATA_FILE):
        print(f"Error: Source data file not found at {SOURCE_DATA_FILE}")
        print("Please ensure the file exists and contains the anatomy course data.")
        return

    course_id, parsed_events, student_groups = parse_source_data(SOURCE_DATA_FILE)

    if not course_id :
        print(f"Could not parse course ID from {SOURCE_DATA_FILE}. Aborting.")
        return
    if not parsed_events:
        print(f"No schedule events parsed from {SOURCE_DATA_FILE}. Aborting.")
        return

    print(f"Parsed course ID: {course_id}")
    print(f"Found {len(parsed_events)} raw event entries.")
    if student_groups:
        print(f"Identified student groups: {', '.join(student_groups)}")

    final_yaml_data = build_yaml_structure(course_id, parsed_events, student_groups)

    if final_yaml_data:
        try:
            # Ensure the output directory exists (e.g., if OUTPUT_YAML_FILE includes a path like "output/file.yaml")
            output_dir = os.path.dirname(OUTPUT_YAML_FILE)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(OUTPUT_YAML_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(final_yaml_data, f, allow_unicode=True, sort_keys=False, indent=2, Dumper=yaml.SafeDumper)
            print(f"Data successfully synced to {OUTPUT_YAML_FILE}")
        except Exception as e:
            print(f"Error writing YAML to {OUTPUT_YAML_FILE}: {e}")
    else:
        print("Failed to generate YAML structure. No output file created.")

if __name__ == "__main__":
    main() 