from typing import List, Dict, Any
from deepdiff import DeepDiff

from app.models.syllabus import FieldChange

def detect_changes(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[FieldChange]:
    """
    Detect changes between two versions of syllabus data.
    
    Args:
        old_data: The previous version data
        new_data: The new version data
        
    Returns:
        List of FieldChange objects describing the differences
    """
    changes = []
    
    # Use DeepDiff to find differences
    diff = DeepDiff(old_data, new_data, ignore_order=True, verbose_level=2)
    
    # Process value changes
    if 'values_changed' in diff:
        for path, change in diff['values_changed'].items():
            field_path = path.replace("root", "").replace("[", ".").replace("]", "").replace("'", "")
            if field_path.startswith("."):
                field_path = field_path[1:]
                
            changes.append(FieldChange(
                field_path=field_path,
                old_value=change['old_value'],
                new_value=change['new_value'],
                change_type="update"
            ))
    
    # Process added items
    if 'dictionary_item_added' in diff:
        for path in diff['dictionary_item_added']:
            field_path = path.replace("root", "").replace("[", ".").replace("]", "").replace("'", "")
            if field_path.startswith("."):
                field_path = field_path[1:]
                
            # Get the new value from the path
            value = new_data
            for part in field_path.split('.'):
                if part:
                    value = value.get(part, None) if isinstance(value, dict) else None
                    
            changes.append(FieldChange(
                field_path=field_path,
                old_value=None,
                new_value=value,
                change_type="add"
            ))
    
    # Process removed items
    if 'dictionary_item_removed' in diff:
        for path in diff['dictionary_item_removed']:
            field_path = path.replace("root", "").replace("[", ".").replace("]", "").replace("'", "")
            if field_path.startswith("."):
                field_path = field_path[1:]
                
            # Get the old value from the path
            value = old_data
            for part in field_path.split('.'):
                if part:
                    value = value.get(part, None) if isinstance(value, dict) else None
                    
            changes.append(FieldChange(
                field_path=field_path,
                old_value=value,
                new_value=None,
                change_type="delete"
            ))
    
    # Process items added to lists
    if 'iterable_item_added' in diff:
        for path, value in diff['iterable_item_added'].items():
            field_path = path.replace("root", "").replace("[", ".").replace("]", "").replace("'", "")
            if field_path.startswith("."):
                field_path = field_path[1:]
                
            changes.append(FieldChange(
                field_path=field_path,
                old_value=None,
                new_value=value,
                change_type="add"
            ))
    
    # Process items removed from lists
    if 'iterable_item_removed' in diff:
        for path, value in diff['iterable_item_removed'].items():
            field_path = path.replace("root", "").replace("[", ".").replace("]", "").replace("'", "")
            if field_path.startswith("."):
                field_path = field_path[1:]
                
            changes.append(FieldChange(
                field_path=field_path,
                old_value=value,
                new_value=None,
                change_type="delete"
            ))
    
    return changes 