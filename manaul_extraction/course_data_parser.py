import yaml
import re
import os
from collections import defaultdict
import datetime
from abc import ABC, abstractmethod

# --- Configuration ---
ACADEMIC_YEAR = 2025  # Default academic year for date conversion

# --- Mappings and Constants ---
HEB_DAY_TO_ENG_DAY = {
    "יום ראשון": "Sunday", "יום שני": "Monday", "יום שלישי": "Tuesday",
    "יום רביעי": "Wednesday", "יום חמישי": "Thursday", "יום שישי": "Friday",
    "יום שבת": "Saturday"
}

# Based on Python's datetime.weekday() (Monday=0, ..., Sunday=6)
PYTHON_WEEKDAY_TO_HEB = {
    0: "יום שני", 1: "יום שלישי", 2: "יום רביעי", 3: "יום חמישי",
    4: "יום שישי", 5: "יום שבת", 6: "יום ראשון"
}
PYTHON_WEEKDAY_TO_ENG = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
    4: "Friday", 5: "Saturday", 6: "Sunday"
}

# --- Generic Helper Functions ---
def parse_time_range_to_start_end(time_str):
    if not time_str: return None, None
    parts = str(time_str).split('-')
    try:
        start_hour_str, *start_minute_str_list = parts[0].split(':')
        start_hour = int(start_hour_str)
        start_minute = int(start_minute_str_list[0]) if start_minute_str_list else 0

        if len(parts) > 1:
            end_hour_str, *end_minute_str_list = parts[1].split(':')
            end_hour = int(end_hour_str)
            end_minute = int(end_minute_str_list[0]) if end_minute_str_list else 0
        else:
            end_hour = start_hour + 1
            end_minute = start_minute
        return f"{start_hour:02d}:{start_minute:02d}", f"{end_hour:02d}:{end_minute:02d}"
    except ValueError:
        print(f"Warning: Could not parse time range: {time_str}")
        return None, None

def format_source_date_to_yyyymmdd(date_str, base_year):
    if not date_str: return None
    try:
        parts = str(date_str).split('.')
        day = int(parts[0])
        month = int(parts[1])
        year_val = base_year
        if len(parts) > 2 and parts[2]:
            year_str = parts[2]
            if len(year_str) == 2:
                year_val = (base_year // 100) * 100 + int(year_str)
            elif len(year_str) == 4:
                year_val = int(year_str)
            else: raise ValueError("Invalid year format in date")
        return f"{year_val}-{month:02d}-{day:02d}"
    except (ValueError, IndexError) as e:
        print(f"Warning: Could not parse date string '{date_str}': {e}")
        return None

def parse_instructors_string(instructor_str):
    if not instructor_str: return []
    normalized_str = str(instructor_str).replace(" / ", ", ").replace(" ו ", ", ")
    return [name.strip() for name in normalized_str.split(',') if name.strip() and name.strip().lower() != "null"]

def determine_activity_type(subject, location, activity_type_hint=None):
    hint_lower = str(activity_type_hint).lower() if activity_type_hint else ""
    subject_lower = str(subject).lower() if subject else ""
    location_lower = str(location).lower() if location else ""

    if hint_lower:
        if "מעבדה" in hint_lower: return "Lab"
        if "cbl" in hint_lower: return "PBL" # Assuming CBL is a type of PBL for the schema
        if "הרצאה" in hint_lower: return "Lecture"
        if "צפייה בווידאו" in hint_lower or "וידאו" in hint_lower : return "Recorded Material"
        if "תרגול" in hint_lower: return "Tutorial" # Example, adjust as needed

    if "הרצאה" in subject_lower:
        return "Recorded Lecture" if "מוקלט" in subject_lower or "מוקלט" in location_lower else "Lecture"
    if "דיסקציה" in subject_lower or "מעבדת דיסקציה" in location_lower: return "Lab"
    if "pbl" in subject_lower: return "PBL"
    if "עבודה עצמית" in location_lower: return "Self-Study"
    if "ca" in subject_lower and "self-study" not in subject_lower : return "Self-Study / CA"
    if "us" in subject_lower and ("חדרי us" in location_lower or "us" in subject_lower) : return "Practical Session" # Broader US match
    if "ct" in subject_lower : return "Practical Session"
    if "חזרה" in subject_lower: return "Review Session"
    if "מוקלט" in location_lower and "הרצאה" not in subject_lower: return "Recorded Material"
    if "cbl" in subject_lower: return "PBL"

    return "General Activity"

# --- Abstract Base Parser ---
class BaseDataParser(ABC):
    @abstractmethod
    def parse_course_data(self, course_block_lines):
        """Parses a block of lines for a single course.
        Returns: (course_id_str, course_name_str, list_of_raw_event_dicts, student_group_names_set)
        raw_event_dict structure:
        {
            "raw_date_str": "12.5.25",
            "raw_time_str": "08-10",
            "raw_day_heb": "יום שני" (optional),
            "subject": "Event Subject",
            "location": "Event Location" (optional),
            "instructors_str": "Dr. One, Dr. Two" (optional),
            "attending_group_name": "group_A" (optional, None for all),
            "activity_type_hint": "מעבדה" (optional),
            "details_str": "Additional notes, reading pages" (optional)
        }
        """
        pass

    def _extract_yaml_like_structure(self, lines, start_index=0):
        # Basic YAML-like list/dict parsing helper. This can be significantly improved for robustness.
        # This is a simplified parser focusing on the known structures in data.txt.
        # It assumes a certain level of well-formedness (consistent indentation for structure).
        # For complex general YAML, a proper library should be used on pre-processed text.
        
        structure = [] # If top level is a list
        # Or structure = {} # If top level is a dict
        # Current implementation will return a list of items (dates, events etc.)
        
        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('#'):
                i += 1
                continue

            # This is highly simplified and context-dependent for the specific txt format
            # Regex for key: "value" or key: (if value is on next line or structured)
            # Example: "- date: "12.5.25"" or "  events:" (followed by list)
            
            # Simplified: try to match known patterns
            # Match list item: "- key: value" or just "- value" for simple lists
            match_list_item_kv = re.match(r"^-\s*(\w+):\s*(?:\"(.*?)\"|(.*))", line)
            match_list_item_simple = re.match(r"^-\s*(?:\"(.*?)\"|(.*))", line)
            
            # Match dict item: "key: value" or "key:" (followed by structure)
            match_dict_item_kv = re.match(r"^(\w+):\s*(?:\"(.*?)\"|(.*))", line)
            
            # Placeholder for actual parsing logic - specific to each parser's needs
            # This generic helper is too complex to implement fully here without more context
            # on how it would be used by different parsers for their varied structures.
            # Parsers will implement their own line-by-line logic.
            i += 1
        return structure # or dict


# --- Anatomy Data Parser ---
class AnatomyDataParser(BaseDataParser):
    def parse_course_data(self, course_block_lines):
        course_id = None
        raw_events = []
        student_group_names = set()
        
        current_day_heb = None
        current_date_str_raw = None
        slot_time_raw = None
        current_slot_details_type1 = {}
        current_slot_details_type2_groups = {}
        active_group_for_details_type2 = None

        first_course_line = course_block_lines[0].strip()
        match_course_obj = re.match(r"^course:\s*(.*?)(?:\s*#.*)?$", first_course_line)
        if match_course_obj:
            course_id = match_course_obj.group(1).strip()
        else:
            # Fallback or error if the first line isn't the course ID for this parser
            print(f"Warning: AnatomyDataParser expected 'course:' line, got: {first_course_line}")
            # Try to find course ID in subsequent lines if necessary for more flexible anatomy files
            # For now, assumes it is the first line passed in course_block_lines.
            pass

        def commit_slot_data_anatomy():
            nonlocal slot_time_raw, current_slot_details_type1, current_slot_details_type2_groups, active_group_for_details_type2
            if not slot_time_raw or not (current_slot_details_type1 or current_slot_details_type2_groups):
                return

            if current_slot_details_type1.get("subject"):
                raw_events.append({
                    "raw_date_str": current_date_str_raw,
                    "raw_time_str": slot_time_raw,
                    "raw_day_heb": current_day_heb,
                    "subject": current_slot_details_type1.get("subject"),
                    "location": current_slot_details_type1.get("location"),
                    "instructors_str": current_slot_details_type1.get("instructor"),
                    "attending_group_name": None # Implicitly "All"
                })
            
            for group_name, details in current_slot_details_type2_groups.items():
                if details.get("subject"):
                    student_group_names.add(group_name)
                    raw_events.append({
                        "raw_date_str": current_date_str_raw,
                        "raw_time_str": slot_time_raw,
                        "raw_day_heb": current_day_heb,
                        "subject": details.get("subject"),
                        "location": details.get("location"),
                        "instructors_str": details.get("instructor"),
                        "attending_group_name": group_name
                    })
            
            slot_time_raw = None
            current_slot_details_type1 = {}
            current_slot_details_type2_groups = {}
            active_group_for_details_type2 = None

        # Start from 1 if first line was course_id, or 0 if course_id handled differently
        for line_raw in course_block_lines[1:]:
            line = line_raw.strip()
            if not line or line.startswith('#'): continue

            match_day = re.match(r"^-\s*day:\s*([^#]+?)(?:\s*#.*)?$", line)
            if match_day:
                commit_slot_data_anatomy()
                current_day_heb = match_day.group(1).strip()
                current_date_str_raw = None 
                continue

            match_date = re.match(r"^-\s*date:\s*\"(.*?)\"", line)
            if match_date:
                commit_slot_data_anatomy()
                current_date_str_raw = match_date.group(1).strip()
                continue
            
            match_time = re.match(r"^-\s*time:\s*\"(.*?)\"", line)
            if match_time:
                commit_slot_data_anatomy()
                slot_time_raw = match_time.group(1).strip()
                current_slot_details_type1 = {}
                current_slot_details_type2_groups = {}
                active_group_for_details_type2 = None
                continue
                
            if not current_day_heb or not current_date_str_raw or not slot_time_raw: continue

            match_group_key = re.match(r"^\s*(group_\w+):", line)
            if match_group_key:
                active_group_for_details_type2 = match_group_key.group(1).strip()
                if active_group_for_details_type2 not in current_slot_details_type2_groups:
                    current_slot_details_type2_groups[active_group_for_details_type2] = {}
                current_slot_details_type1 = {}
                continue
            
            match_prop = re.match(r"^\s*(subject|location|instructor):\s*\"(.*?)\"", line)
            if match_prop:
                key, value = match_prop.group(1), match_prop.group(2).strip()
                if active_group_for_details_type2:
                    current_slot_details_type2_groups[active_group_for_details_type2][key] = value
                else:
                    current_slot_details_type1[key] = value
                    current_slot_details_type2_groups = {}
                continue
        commit_slot_data_anatomy()
        return course_id, course_id, raw_events, student_group_names # Using course_id as name_hint

# --- Neuroanatomy Data Parser ---
class NeuroanatomyDataParser(BaseDataParser):
    def parse_course_data(self, course_block_lines):
        course_id_str = None # Will be derived from course_name_str later if needed
        course_name_str = None
        raw_events = []
        student_group_names = set()

        # Course Name (and potential ID)
        first_line = course_block_lines[0].strip()
        match_course = re.match(r"^course:\s*(.*?)(?:\s*#.*)?$", first_line)
        if match_course:
            course_name_str = match_course.group(1).strip()
            # Simplistic ID generation for now. Could be made more robust.
            course_id_str = course_name_str.lower().replace(' ', '-').replace('#', '').replace('\"','').replace('תשפ״ה','2025').replace('סמסטר-ב׳','sem-b')
            course_id_str = re.sub(r'[^a-z0-9\-א-ת]', '', course_id_str) # Keep Hebrew, alphanumeric, hyphen

        current_date_str_raw = None
        # Tracks indentation to understand structure for 'events' and 'activities'
        # This parsing needs to be more robust for complex structures like Neuroanatomy
        # Using a state machine or more detailed regexes per level would be better.
        # For now, relying on keyword matching and line iteration context.

        # This simplified parser iterates line by line, keeping track of current date and event context.
        # It will rely on specific keywords ('date:', 'events:', 'hours:', 'activities:', 'group:')
        # and associated indentation or line patterns.

        i = 1 # Start parsing from the line after "course: ..."
        while i < len(course_block_lines):
            line = course_block_lines[i].strip()
            original_line = course_block_lines[i]
            indentation = len(original_line) - len(original_line.lstrip(' '))

            if not line or line.startswith('#'):
                i += 1
                continue

            match_date = re.match(r"^-\s*date:\s*\"(.*?)\"", line)
            if match_date:
                current_date_str_raw = match_date.group(1).strip()
                i += 1
                continue # Next lines should be events under this date
            
            if not current_date_str_raw: # Skip lines if not under a date context
                i += 1
                continue

            # Look for events or activities blocks under a date
            # This simplified parser looks for hour slots directly or activities within hour slots.
            # A proper YAML parser or more structured regex would be better for arbitrary depth.

            # Simple event (hours, topic, lecturer)
            match_hours = re.match(r"^-\s*hours:\s*\"?(.*?)\"?", line)
            if match_hours:
                current_hours_raw = match_hours.group(1).strip()
                if not current_hours_raw or current_hours_raw.lower() == 'null': 
                    # Check if this 'null' hours has a topic on the next line (special case from data)
                    if i + 1 < len(course_block_lines):
                        next_line_stripped = course_block_lines[i+1].strip()
                        match_topic_after_null_hours = re.match(r"^topic:\s*\"?(.*?)\"?", next_line_stripped)
                        if match_topic_after_null_hours:
                            # This is a special case: hourless event implies it's tied to previous block or general for the day
                            # For now, we will still create an event but time will be null
                            event_data = {"raw_date_str": current_date_str_raw, "raw_time_str": None}
                            self._parse_neuro_event_properties(course_block_lines, i + 1, event_data, indentation + 2) # Assume properties are more indented
                            raw_events.append(event_data)
                            i = event_data.get("_next_idx", i + 2) # Move past parsed properties
                            continue
                    i += 1
                    continue

                # Check for simple event properties or an 'activities' block for this hour
                # This requires looking ahead or parsing sub-blocks.
                # Simple event:
                event_data = {"raw_date_str": current_date_str_raw, "raw_time_str": current_hours_raw}
                next_idx_after_props = self._parse_neuro_event_properties(course_block_lines, i + 1, event_data, indentation + 2) 

                if "activities" in event_data: # Activities block found under this hour
                    # event_data["activities"] is a list of activity dicts
                    for act in event_data["activities"]:
                        student_group_names.add(act.get("attending_group_name"))
                        raw_events.append(act)
                    i = next_idx_after_props
                elif event_data.get("subject"): # Simple event parsed
                    raw_events.append(event_data)
                    i = next_idx_after_props
                else: # No subject, maybe just an empty hour slot or formatting issue
                    i += 1
                continue
            i += 1 # Fallback increment

        return course_id_str, course_name_str, raw_events, student_group_names

    def _parse_neuro_event_properties(self, lines, start_idx, event_data, expected_indent):
        # Parses properties for a single event or an activities block.
        # Populates event_data directly.
        # Returns the index of the line after the parsed block.
        idx = start_idx
        activities_list = []
        in_activities_block = False
        current_activity_data = None

        while idx < len(lines):
            line_raw = lines[idx]
            line = line_raw.strip()
            current_indent = len(line_raw) - len(line_raw.lstrip(' '))

            if not line or line.startswith('#'):
                idx += 1
                continue
            
            if current_indent < expected_indent and (in_activities_block or not line.startswith('-')):
                 # Dedent signifies end of current block, unless it's a new list item for activities
                if in_activities_block and current_activity_data:
                    activities_list.append(current_activity_data)
                    current_activity_data = None
                break 

            match_topic = re.match(r"^topic:\s*\"?(.*?)\"?", line)
            match_lecturer = re.match(r"^lecturer:\s*\"?(.*?)\"?", line)
            match_reading = re.match(r"^reading_pages:\s*\"?(.*?)\"?", line)
            match_notes = re.match(r"^notes:\s*\"?(.*?)\"?", line)
            match_location = re.match(r"^location:\s*\"?(.*?)\"?", line)
            match_activities_header = re.match(r"^activities:$", line)
            match_activity_group_item = re.match(r"^-\s*group:\s*\"?(.*?)\"?", line) if in_activities_block else None
            match_activity_type = re.match(r"^type:\s*\"?(.*?)\"?", line) if in_activities_block and current_activity_data else None
            match_activity_details = re.match(r"^details:\s*\"?(.*?)\"?", line) if in_activities_block and current_activity_data else None
            match_activity_specific_hours = re.match(r"^specific_hours:\s*\"?(.*?)\"?", line) if in_activities_block and current_activity_data else None
            
            details_parts = []
            if event_data.get("details_str"): details_parts.append(event_data["details_str"])
            if current_activity_data and current_activity_data.get("details_str"): details_parts = [current_activity_data["details_str"]]


            if match_activities_header:
                in_activities_block = True
                expected_indent +=2 # Activities properties are further indented
                idx += 1
                continue

            if in_activities_block:
                if match_activity_group_item:
                    if current_activity_data: activities_list.append(current_activity_data)
                    current_activity_data = {
                        "raw_date_str": event_data["raw_date_str"],
                        "raw_time_str": event_data["raw_time_str"], # Default to outer hour, override if specific_hours found
                        "attending_group_name": match_activity_group_item.group(1).strip()
                    }
                elif current_activity_data:
                    if match_activity_type: current_activity_data["activity_type_hint"] = match_activity_type.group(1).strip()
                    elif match_activity_details: current_activity_data["subject"] = match_activity_details.group(1).strip()
                    elif match_lecturer: current_activity_data["instructors_str"] = match_lecturer.group(1).strip() if match_lecturer.group(1).lower() != 'null' else None
                    elif match_location: current_activity_data["location"] = match_location.group(1).strip()
                    elif match_activity_specific_hours: current_activity_data["raw_time_str"] = match_activity_specific_hours.group(1).strip() # Override time
                    elif match_reading:
                        val = match_reading.group(1).strip()
                        if val.lower() != 'null': details_parts.append(f"Reading: {val}")
                    elif match_notes:
                        val = match_notes.group(1).strip()
                        if val.lower() != 'null': details_parts.append(f"Notes: {val}")
                    # Update details_str for the current_activity_data
                    if details_parts:
                         current_activity_data["details_str"] = "; ".join(details_parts)
                    details_parts = [] # reset for next property unless it continues current_activity_data["details_str"]
                    if current_activity_data.get("details_str"): details_parts.append(current_activity_data["details_str"])

            else: # Properties for the main event_data (non-activity block)
                if match_topic: event_data["subject"] = match_topic.group(1).strip()
                elif match_lecturer: event_data["instructors_str"] = match_lecturer.group(1).strip() if match_lecturer.group(1).lower() != 'null' else None
                elif match_location: event_data["location"] = match_location.group(1).strip()
                elif match_reading:
                    val = match_reading.group(1).strip()
                    if val.lower() != 'null': details_parts.append(f"Reading: {val}")
                elif match_notes:
                    val = match_notes.group(1).strip()
                    if val.lower() != 'null': details_parts.append(f"Notes: {val}")
                # Update details_str for event_data
                if details_parts:
                    event_data["details_str"] = "; ".join(details_parts)
                details_parts = [] # reset
                if event_data.get("details_str"): details_parts.append(event_data["details_str"])

            idx += 1
        
        if in_activities_block and current_activity_data: # Add last activity if any
            activities_list.append(current_activity_data)
        
        if activities_list: event_data["activities"] = activities_list # Store parsed activities back into event_data
        event_data["_next_idx"] = idx # Helper to advance outer loop
        return idx


# --- YAML Structure Builder ---
def build_yaml_structure(course_id, course_name, raw_events, student_group_names, academic_year):
    if not course_id and not course_name: return None
    final_course_id = course_id if course_id else course_name.lower().replace(' ', '-')
    final_course_name = course_name if course_name else course_id

    course_data = {
        "id": final_course_id,
        "name": final_course_name,
        "year": str(academic_year),
        "schedule": {"calendar_entries": []}
    }
    if student_group_names:
        course_data["student_groups"] = sorted([{"name": name} for name in student_group_names], key=lambda x: x["name"])

    events_by_date = defaultdict(list)
    for event in raw_events:
        formatted_date = format_source_date_to_yyyymmdd(event["raw_date_str"], academic_year)
        if formatted_date:
            events_by_date[formatted_date].append(event)
        else:
            print(f"Warning: Could not format date for event: {event.get('subject')}")

    for date_iso, date_events in sorted(events_by_date.items()):
        if not date_events: continue
        
        # Determine day of week from date_iso
        try:
            parsed_date_obj = datetime.datetime.strptime(date_iso, "%Y-%m-%d")
            day_heb = PYTHON_WEEKDAY_TO_HEB.get(parsed_date_obj.weekday())
            day_en = PYTHON_WEEKDAY_TO_ENG.get(parsed_date_obj.weekday())
        except ValueError:
            day_heb, day_en = None, None
            print(f"Warning: Could not parse date {date_iso} to determine day of week.")
        
        # If raw_day_heb was provided by parser, prefer it (e.g., Anatomy parser)
        # For Neuroanatomy, it's derived above.
        if date_events[0].get("raw_day_heb"):
            day_heb = date_events[0]["raw_day_heb"]
            day_en = HEB_DAY_TO_ENG_DAY.get(day_heb, day_en) # Update English if Hebrew exists
            
        calendar_entry = {"date": date_iso, "time_slots": []}
        if day_heb: calendar_entry["day_of_week_heb"] = day_heb
        if day_en: calendar_entry["day_of_week_en"] = day_en

        for event_detail in sorted(date_events, key=lambda x: (x.get("raw_time_str") or "")):
            start_time, end_time = parse_time_range_to_start_end(event_detail.get("raw_time_str"))
            instructors = parse_instructors_string(event_detail.get("instructors_str"))
            
            time_slot = {"subject": event_detail.get("subject", "N/A")}
            if start_time: time_slot["start_time"] = start_time
            if end_time: time_slot["end_time"] = end_time
            if event_detail.get("location"): time_slot["location"] = event_detail["location"]
            if instructors: time_slot["instructors"] = instructors
            
            activity_type = determine_activity_type(
                event_detail.get("subject"), 
                event_detail.get("location"), 
                event_detail.get("activity_type_hint")
            )
            if activity_type: time_slot["activity_type"] = activity_type

            attending_groups = [event_detail["attending_group_name"]] if event_detail.get("attending_group_name") else ["All"]
            time_slot["attending_groups"] = attending_groups
            
            if event_detail.get("details_str"): time_slot["details"] = event_detail["details_str"]
            
            calendar_entry["time_slots"].append(time_slot)
        
        if calendar_entry["time_slots"]:
            course_data["schedule"]["calendar_entries"].append(calendar_entry)
    
    return {"courses": [course_data]} if course_data["schedule"]["calendar_entries"] else None

# --- Main Execution Logic ---
def get_course_blocks(lines):
    blocks = []
    current_block = []
    for line in lines:
        if line.strip().startswith("course:") and current_block:
            blocks.append(current_block)
            current_block = []
        current_block.append(line)
    if current_block: # Add the last block
        blocks.append(current_block)
    return blocks

def choose_parser(course_block_lines):
    if not course_block_lines: return None
    first_line = course_block_lines[0].strip()
    # Simple chooser based on keywords in the first line of the block
    if "anatomy-first-part" in first_line or (first_line.startswith("course:") and ("יום שני" in "".join(course_block_lines[:15]))): # Anatomy has days
        print("Using AnatomyDataParser")
        return AnatomyDataParser()
    elif "נוירואנטומיה" in first_line or (first_line.startswith("course:") and ("activities:" in "".join(course_block_lines[:25]))): # Neuro has activities
        print("Using NeuroanatomyDataParser")
        return NeuroanatomyDataParser()
    print(f"Warning: Could not determine parser for course starting with: {first_line}")
    return None # Or a default parser

def main():
    # Configuration for which file to parse and what the output should be
    # This can be made dynamic (e.g. CLI arguments)
    # SOURCE_FILE = "docs/data.txt" # Original file with potentially multiple courses
    SOURCE_FILE = "docs/neuro_data.txt" # Specifically for neuro data as per current task
    # OUTPUT_BASE_NAME = "docs/parsed_course_data" # Base for output, ID will be appended

    if not os.path.exists(SOURCE_FILE):
        print(f"Error: Source data file not found at {SOURCE_FILE}")
        return

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()

    course_blocks = get_course_blocks(all_lines)
    
    parsed_count = 0
    for i, block in enumerate(course_blocks):
        print(f"\nProcessing course block {i+1}/{len(course_blocks)}...")
        parser = choose_parser(block)
        if not parser:
            print("Skipping block, no suitable parser found.")
            continue

        course_id, course_name, raw_events, student_groups = parser.parse_course_data(block)

        if not course_id and not course_name:
            print(f"Could not parse course identifier from block. Skipping.")
            continue
        if not raw_events:
            print(f"No schedule events parsed for {course_name or course_id}. Skipping.")
            continue

        print(f"Parsed: {course_name or course_id} (ID: {course_id})")
        print(f"Found {len(raw_events)} raw event entries.")
        if student_groups:
            print(f"Identified student groups: {sorted(list(student_groups))}")

        final_yaml_data = build_yaml_structure(course_id, course_name, raw_events, student_groups, ACADEMIC_YEAR)

        if final_yaml_data:
            output_filename = f"docs/{final_yaml_data['courses'][0]['id']}_course_data.yaml"
            try:
                output_dir = os.path.dirname(output_filename)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                with open(output_filename, 'w', encoding='utf-8') as f:
                    yaml.dump(final_yaml_data, f, allow_unicode=True, sort_keys=False, indent=2, Dumper=yaml.SafeDumper)
                print(f"Data successfully synced to {output_filename}")
                parsed_count += 1
            except Exception as e:
                print(f"Error writing YAML to {output_filename}: {e}")
        else:
            print(f"Failed to generate YAML structure for {course_name or course_id}.")
            
    if parsed_count == 0 and course_blocks:
        print("\nNo courses were successfully parsed or generated into YAML.")
    elif parsed_count > 0:
        print(f"\nSuccessfully parsed and generated YAML for {parsed_count} course(s).")
    else:
        print("\nNo course data found in the source file.")

if __name__ == "__main__":
    main() 