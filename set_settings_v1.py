import os
import shutil
import sys
import json
import re
from validate_json_files import validate_json_file as detailed_validate_json_file, find_json_files

##########################################
# Configuration Variables
##########################################

# Define path mapping for easy maintenance
PATH_MAPPINGS = {
    "OLD_BASE_PATH": "/home/iss",
    "NEW_BASE_PATH": "/home/issp/workspace",
    "MODEL_SUBPATH": "/issp_oms_models",
    "LIBRARY_SUBPATH": "/issp_oms_so"
}

##########################################
# Helper Functions
##########################################

def string_to_ascii_array(text, target_length=256):
    """
    Convert a string to ASCII array with padding.
    
    Args:
        text (str): The string to convert
        target_length (int): Target array length (default 256 for compatibility)
        
    Returns:
        list: ASCII codes padded with zeros
    """
    ascii_codes = [ord(char) for char in text]
    # Pad with zeros to reach target length
    ascii_codes.extend([0] * (target_length - len(ascii_codes)))
    return ascii_codes[:target_length]  # Ensure we don't exceed target length

def ascii_array_to_string(ascii_array):
    """
    Convert ASCII array back to string, stopping at first null (0).
    
    Args:
        ascii_array (list): List of ASCII codes
        
    Returns:
        str: Converted string
    """
    # Stop at first null terminator
    end_index = ascii_array.index(0) if 0 in ascii_array else len(ascii_array)
    return ''.join(chr(code) for code in ascii_array[:end_index])

def replace_path_in_ascii_arrays(data, old_path, new_path, report_prefix=""):
    """
    Recursively find and replace ASCII path arrays in JSON data.
    
    Args:
        data: JSON data structure (dict, list, or primitive)
        old_path (str): Path to replace
        new_path (str): New path
        report_prefix (str): Prefix for error reporting
        
    Returns:
        Modified data structure
    """
    replacements_made = 0
    failed_replacements = []
    
    def _replace_recursive(data, prefix=""):
        nonlocal replacements_made, failed_replacements
        
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                current_prefix = f"{prefix}.{key}" if prefix else key
                
                if key.endswith('_path') and isinstance(value, list):
                    # This looks like an ASCII path array
                    current_path = ascii_array_to_string(value)
                    
                    # If path is already the target path, skip replacement
                    if current_path == new_path:
                        result[key] = value
                    # Check if this is the exact path we want to replace
                    elif current_path == old_path:
                        result[key] = string_to_ascii_array(new_path, len(value))
                        replacements_made += 1
                    elif old_path in current_path:
                        # Partial match - replace within the path
                        new_full_path = current_path.replace(old_path, new_path)
                        result[key] = string_to_ascii_array(new_full_path, len(value))
                        replacements_made += 1
                    else:
                        # Path is different and doesn't match our target - keep as is
                        result[key] = value
                else:
                    result[key] = _replace_recursive(value, current_prefix)
            return result
        elif isinstance(data, list):
            return [_replace_recursive(item, f"{prefix}[{i}]") for i, item in enumerate(data)]
        else:
            return data
    
    result = _replace_recursive(data)
    
    # Report results
    if failed_replacements:
        for field_name, expected, found in failed_replacements:
            print(f"❌ Replacement failed for '{field_name}': Expected '{expected}' but found '{found}'")
    
    if replacements_made > 0:
        print(f"✅ Successfully updated {replacements_made} path(s) from '{old_path}' to '{new_path}'")
    elif not failed_replacements:
        print(f"ℹ️  No instances of '{old_path}' found to replace")
    
    return result

##########################################
# Set parameters in the esme file
##########################################

if len(sys.argv) < 2:
    print("Usage: python set_settings.py <prj_folder_path>")
    sys.exit(1)

prj_folder = sys.argv[1]

found_esme = False
found_dataset = False
dataset_path = None
esme_path = None
for root, dirs, files in os.walk(prj_folder):
    if "esme_manifest_issp_roudi.json" in files and not found_esme:
        esme_path = os.path.join(root, "esme_manifest_issp_roudi.json")
        print(f"esme json found, path is {esme_path}")
        found_esme = True
    if "issp_dataset.json" in files and not found_dataset:
        dataset_path = os.path.join(root, "issp_dataset.json")
        print(f"dataset json found, path is {dataset_path}")
        found_dataset = True
    if found_esme and found_dataset:
        break
if not found_esme and not found_dataset:
    print("Neither esme_manifest_issp_roudi.json nor issp_dataset.json found in project folder.")
elif not found_esme:
    print("esme_manifest_issp_roudi.json not found in project folder.")
elif not found_dataset:
    print("issp_dataset.json not found in project folder.")

if esme_path is not None and os.path.exists(esme_path) and not os.path.exists(esme_path + ".bak"):
    shutil.copyfile(esme_path, esme_path + ".bak")
    print(f"Created backup: {esme_path}.bak")
    
if dataset_path is not None and os.path.exists(dataset_path) and not os.path.exists(dataset_path + ".bak"):
    shutil.copyfile(dataset_path, dataset_path + ".bak")
    print(f"Created backup: {dataset_path}.bak")
    
##########################################
# Load replacements from a JSON file
##########################################

replacements_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "esme_replacements.json")
if not os.path.exists(replacements_json_path):
    print(f"Replacement file not found: {replacements_json_path}")
    sys.exit(1)

with open(replacements_json_path, "r") as f:
    replacements_data = json.load(f)

if "replacements" not in replacements_data:
    print("Error: 'replacements' key not found in JSON file")
    sys.exit(1)

replacements = replacements_data["replacements"]
print(f"Loaded {len(replacements)} replacement rules from {replacements_json_path}")

# replacements should be a list of {"from": ..., "to": ...}
if esme_path is None:
    print("esme_path is not set. Cannot proceed.")
    sys.exit(1)

try:
    with open(esme_path, "r") as fh:
        esme_data = fh.read()
except IOError as e:
    print(f"Error reading ESME file {esme_path}: {e}")
    sys.exit(1)

# Note: Using str.replace in a loop can cause cascading replacements if the "to" value of one replacement matches the "from" value of another.
# To avoid this, we use regular expressions to perform all replacements in a single pass.

def multiple_replace(text, replacements):
    """
    Perform multiple string replacements in a single pass to avoid cascading replacements.
    
    Args:
        text (str): The input text to perform replacements on
        replacements (list): List of replacement dictionaries with 'from' and 'to' keys
        
    Returns:
        str: Text with all replacements applied
    """
    # Build a regex pattern with all "from" values escaped
    rep_dict = {rep["from"]: rep["to"] for rep in replacements}
    pattern = re.compile("|".join(re.escape(k) for k in rep_dict.keys()))
    
    def replace_func(match):
        return rep_dict[match.group(0)]
    
    return pattern.sub(replace_func, text)

print(f"Applying {len(replacements)} replacements to ESME file...")
esme_data = multiple_replace(esme_data, replacements)

print(f"Successfully applied replacements to {esme_path}")

try:
    with open(esme_path, "w") as fh:
        fh.write(esme_data)
    print(f"ESME file updated successfully: {esme_path}")
except IOError as e:
    print(f"Error writing to ESME file {esme_path}: {e}")
    sys.exit(1)



##########################################
# Set parameters in the dataset file
##########################################

if dataset_path is not None and os.path.exists(dataset_path) and not os.path.exists(dataset_path + ".bak"):
    shutil.copyfile(dataset_path, dataset_path + ".bak")
    print(f"Created backup: {dataset_path}.bak")

replacements_dataset_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "issp_dataset_replacements.json")
if not os.path.exists(replacements_dataset_json_path):
    print(f"Replacement file not found: {replacements_dataset_json_path}")
    sys.exit(1)

with open(replacements_dataset_json_path, "r") as f:
    replacements_dataset_data = json.load(f)

if "replacements" not in replacements_dataset_data:
    print("Error: 'replacements' key not found in issp_dataset_replacements.json")
    sys.exit(1)

replacements_dataset = replacements_dataset_data["replacements"]
print(f"Loaded {len(replacements_dataset)} replacement rules from {replacements_dataset_json_path}")

# Load path mappings if available
path_mappings = replacements_dataset_data.get("path_mappings", {})
old_base_path = path_mappings.get("old_base_path", PATH_MAPPINGS["OLD_BASE_PATH"])
new_base_path = path_mappings.get("new_base_path", PATH_MAPPINGS["NEW_BASE_PATH"])

if dataset_path is None:
    print("dataset_path is not set. Cannot proceed.")
    sys.exit(1)

# Read dataset file, apply replacements, and write back
try:
    with open(dataset_path, "r") as fh:
        dataset_data = fh.read()
except IOError as e:
    print(f"Error reading dataset file {dataset_path}: {e}")
    sys.exit(1)

# Apply text-based replacements first
print(f"Applying {len(replacements_dataset)} text replacements to dataset file...")
dataset_data = multiple_replace(dataset_data, replacements_dataset)

def show_mirror_default_paths(data, title="Mirror Default Paths"):
    """
    Show current status of path fields only for configurations containing 'mirror' and 'default'.
    """
    print(f"\n📋 {title}")
    print("=" * 50)
    
    def scan_paths(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_prefix = f"{prefix}.{key}" if prefix else key
                # Only show if the path contains both 'mirror' and 'default'
                if ('mirror' in current_prefix.lower() and 'default' in current_prefix.lower()) or prefix and ('mirror' in prefix.lower() and 'default' in prefix.lower()):
                    if key.endswith('_path') and isinstance(value, list):
                        current_path = ascii_array_to_string(value)
                        print(f"  {current_prefix}: {current_path}")
                scan_paths(value, current_prefix)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                scan_paths(item, f"{prefix}[{i}]")
    
    scan_paths(data)
    print("=" * 50)

# Parse JSON for ASCII path replacements
try:
    dataset_json = json.loads(dataset_data)
    
    # Show initial status for mirror default only
    show_mirror_default_paths(dataset_json, "BEFORE Replacements - Mirror Default Only")
    
    print("Applying ASCII path replacements...")
    
    # Apply general path mappings first
    if old_base_path and new_base_path:
        dataset_json = replace_path_in_ascii_arrays(
            dataset_json, 
            old_base_path, 
            new_base_path
        )
    
    # Apply specific path replacements from configuration
    ascii_replacements = replacements_dataset_data.get("ascii_path_replacements", {})
    specific_replacements = ascii_replacements.get("automatic_replacements", [])
    
    for i, replacement in enumerate(specific_replacements, 1):
        old_specific_path = replacement.get("old_path")
        new_specific_path = replacement.get("new_path")
        if old_specific_path and new_specific_path:
            dataset_json = replace_path_in_ascii_arrays(
                dataset_json, 
                old_specific_path, 
                new_specific_path
            )
    
    # Show final status for mirror default only
    show_mirror_default_paths(dataset_json, "AFTER Replacements - Mirror Default Only")
    
    # Convert back to string
    dataset_data = json.dumps(dataset_json, indent=2)
    
except json.JSONDecodeError as e:
    print(f"Warning: Could not parse dataset as JSON for ASCII replacements: {e}")
    print("Continuing with text-only replacements...")

print(f"Successfully applied replacements to {dataset_path}")

try:
    with open(dataset_path, "w") as fh:
        fh.write(dataset_data)
    print(f"Dataset file updated successfully: {dataset_path}")
except IOError as e:
    print(f"Error writing to dataset file {dataset_path}: {e}")
    sys.exit(1)

##########################################
# JSON Validation Functions
##########################################

def validate_json_file_detailed(file_path, file_type="JSON"):
    """
    Validate if a JSON file is properly formatted with detailed error reporting.
    
    Args:
        file_path (str): Path to the JSON file
        file_type (str): Type description for reporting
        
    Returns:
        bool: True if valid, False if invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # First, try to parse the JSON to get the first error
        try:
            json.loads(content)
            print(f"✅ {file_type} file is valid: {os.path.basename(file_path)}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ {file_type} file has JSON syntax error: {os.path.basename(file_path)}")
            print(f"   Error at Line {e.lineno}, Column {e.colno}: {e.msg}")
            
            # Try to find additional errors
            lines = content.splitlines()
            print(f"   Context around error:")
            start_line = max(1, e.lineno - 2)
            end_line = min(len(lines), e.lineno + 2)
            
            for i in range(start_line - 1, end_line):
                line_content = lines[i].rstrip()
                marker = ">>> " if i == e.lineno - 1 else "    "
                print(f"   {marker}Line {i+1:3d}: {line_content}")
            
            return False
            
    except FileNotFoundError:
        print(f"❌ {file_type} file not found: {file_path}")
        return False
    except Exception as e:
        print(f"❌ {file_type} file validation failed: {file_path}")
        print(f"   Error: {str(e)}")
        return False

def validate_json_file(file_path, file_type="JSON"):
    """
    Validate if a JSON file is properly formatted.
    
    Args:
        file_path (str): Path to the JSON file
        file_type (str): Type description for reporting
        
    Returns:
        bool: True if valid, False if invalid
    """
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        print(f"✅ {file_type} file is valid: {file_path}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ {file_type} file has JSON syntax error: {file_path}")
        print(f"   Error: {str(e)}")
        return False
    except FileNotFoundError:
        print(f"❌ {file_type} file not found: {file_path}")
        return False
    except Exception as e:
        print(f"❌ {file_type} file validation failed: {file_path}")
        print(f"   Error: {str(e)}")
        return False

##########################################
# Final Validation Step
##########################################

print("\n" + "="*60)
print("🔍 FINAL JSON VALIDATION")
print("="*60)

validation_results = []

# Find JSON files in the project folder if prj_folder is available
if 'prj_folder' in locals() and prj_folder:
    print(f"Searching for JSON files in: {prj_folder}")
    found_esme_path, found_dataset_path = find_json_files(prj_folder)
    
    # Update paths if files are found
    if found_esme_path:
        esme_path = found_esme_path
    if found_dataset_path:
        dataset_path = found_dataset_path

# Validate ESME JSON file
if esme_path and os.path.exists(esme_path):
    print(f"\nValidating ESME file: {esme_path}")
    is_valid = validate_json_file_detailed(esme_path, "ESME JSON")
    validation_results.append(("ESME", esme_path, is_valid))
else:
    print("ℹ️  ESME file not found or not processed")

# Validate Dataset JSON file  
if dataset_path and os.path.exists(dataset_path):
    print(f"\nValidating Dataset file: {dataset_path}")
    is_valid = validate_json_file_detailed(dataset_path, "Dataset JSON")
    validation_results.append(("Dataset", dataset_path, is_valid))
else:
    print("ℹ️  Dataset file not found or not processed")

# Summary
print("\n" + "="*60)
print("📊 VALIDATION SUMMARY")
print("="*60)

all_valid = True
for file_type, path, is_valid in validation_results:
    status = "✅ VALID" if is_valid else "❌ INVALID"
    print(f"{file_type:10} {status:10} {os.path.basename(path)}")
    if not is_valid:
        all_valid = False

if validation_results:
    if all_valid:
        print(f"\n🎉 SUCCESS: All {len(validation_results)} JSON file(s) are valid and ready for use!")
        print("="*60)
        print("\n🎉 All operations completed successfully!")
        print("   - File replacements applied")
        print("   - JSON validation passed")
        print("   - Configuration is ready for use")
    else:
        invalid_count = sum(1 for _, _, valid in validation_results if not valid)
        print(f"\n⚠️  ERROR: {invalid_count} file(s) have validation errors!")
        print("   Please check the error messages above and fix any JSON syntax issues.")
        print("="*60)
        print("\n❌ Configuration completed with ERRORS!")
        print("   - File replacements applied")
        print("   - JSON validation FAILED")
        print("   - Please fix JSON syntax errors before proceeding")
        sys.exit(1)
else:
    print("\nℹ️  No JSON files were processed for validation.")
    print("="*60)
    print("\n🎉 Operations completed!")
    print("   - File replacements applied")
    print("   - No JSON files found for validation")

