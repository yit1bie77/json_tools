#!/usr/bin/env python3
"""
ISSP JSON Tools - Configuration Settings Manager
"""

import json
import sys
import os

def replace_steering_wheel_values(data, replacements):
    """
    Replace steering_wheel values based on configuration rules.
    
    Args:
        data (dict): JSON data to modify
        replacements (list): List of replacement rules from configuration
        
    Returns:
        tuple: (modified_data, success_count)
    """
    success_count = 0
    
    def values_match(current, expected, tolerance=1e-6):
        """Check if two lists of values match within tolerance"""
        if len(current) != len(expected):
            return False
        return all(abs(c - e) < tolerance for c, e in zip(current, expected))
    
    def find_and_replace_steering_wheel(obj, path=""):
        nonlocal success_count
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check each replacement rule
                for replacement in replacements:
                    target_camera = replacement.get("target_camera")
                    field_name = replacement.get("field_name", "steering_wheel")
                    old_values = replacement.get("old_values")  # Use old_values for matching
                    new_values = replacement.get("new_values")
                    
                    if not target_camera or not new_values:
                        continue
                    
                    # Check if we found the target camera
                    if key == target_camera and isinstance(value, dict):
                        # Look for the field in this camera configuration
                        if field_name in value and isinstance(value[field_name], list):
                            current_values = value[field_name]
                            
                            # If old_values is specified, check for match (with tolerance for floating point)
                            if old_values:
                                if values_match(current_values, old_values):
                                    value[field_name] = new_values
                                    success_count += 1
                                    print(f"✅ Updated {field_name} in '{current_path}': {old_values} → {new_values}")
                                elif values_match(current_values, new_values):
                                    print(f"ℹ️  {field_name} in '{current_path}' already has target values: {current_values}")
                                else:
                                    print(f"ℹ️  {field_name} in '{current_path}' has different values: {current_values}")
                                    print(f"    Expected: {old_values}")
                                    print(f"    Target: {new_values}")
                                    # Offer to update anyway if values are close to target
                                    if values_match(current_values, new_values, tolerance=1e-4):
                                        value[field_name] = new_values
                                        success_count += 1
                                        print(f"✅ Updated {field_name} (values were close to target): {current_values} → {new_values}")
                            else:
                                # If no old_values specified, replace regardless
                                value[field_name] = new_values
                                success_count += 1
                                print(f"✅ Updated {field_name} in '{current_path}': {current_values} → {new_values}")
                        else:
                            print(f"ℹ️  No {field_name} found in '{current_path}'")
                
                # Continue searching recursively
                if isinstance(value, (dict, list)):
                    find_and_replace_steering_wheel(value, current_path)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    find_and_replace_steering_wheel(item, f"{path}[{i}]")
    
    find_and_replace_steering_wheel(data)
    return data, success_count

def find_steering_wheel_values(data, target_camera="MIRRORSE_CHN1CAMDEFAULT"):
    """
    Find and display steering wheel values for diagnostic purposes.
    
    Args:
        data (dict): JSON data to search
        target_camera (str): Target camera name to search for
    """
    found_values = []
    
    def search_steering_wheel(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if we found the target camera
                if key == target_camera and isinstance(value, dict):
                    if "steering_wheel" in value and isinstance(value["steering_wheel"], list):
                        found_values.append({
                            "path": current_path,
                            "values": value["steering_wheel"]
                        })
                        print(f"🔍 Found steering_wheel in '{current_path}': {value['steering_wheel']}")
                
                # Continue searching recursively
                if isinstance(value, (dict, list)):
                    search_steering_wheel(value, current_path)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    search_steering_wheel(item, f"{path}[{i}]")
    
    search_steering_wheel(data)
    return found_values

def apply_esme_replacements(esme_manifest_path):
    """
    Apply ESME replacements to the ESME manifest file based on configuration.

    Args:
        esme_manifest_path (str): Path to the ESME manifest JSON file to modify.
    """
    try:
        # Load ESME replacement configuration
        esme_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "esme_replacements.json")
        
        if not os.path.exists(esme_config_path):
            print(f"ℹ️  No ESME replacements configuration found")
            print(f"📁 Expected: {esme_config_path}")
            return True
        
        with open(esme_config_path, 'r') as f:
            config_data = json.load(f)
        
        replacements = config_data.get('replacements', [])
        if not replacements:
            print("ℹ️  No ESME replacement rules found in configuration")
            return True
            
        print(f"📋 Loaded {len(replacements)} ESME replacement rules")
        
        # Read the ESME manifest as text (since we're doing string replacements)
        with open(esme_manifest_path, 'r') as f:
            esme_content = f.read()
        
        # Create backup if not exists
        backup_path = esme_manifest_path + '.esme.bak'
        if not os.path.exists(backup_path):
            with open(backup_path, 'w') as f:
                f.write(esme_content)
            print(f"\n📁 Created backup: {os.path.basename(backup_path)}")
        else:
            print(f"\n📁 Backup already exists: {os.path.basename(backup_path)}")
        
        # Apply ESME replacements
        print("\n🔄 Applying ESME replacements...")
        success_count = 0
        original_content = esme_content
        
        for replacement in replacements:
            from_text = replacement.get('from')
            to_text = replacement.get('to')
            description = replacement.get('description', 'No description')
            
            if not from_text or not to_text:
                print(f"⚠️  Skipping invalid replacement rule: {description}")
                continue
            
            if from_text in esme_content:
                esme_content = esme_content.replace(from_text, to_text)
                success_count += 1
                print(f"✅ Applied: {description}")
                print(f"   From: {from_text[:60]}{'...' if len(from_text) > 60 else ''}")
                print(f"   To:   {to_text[:60]}{'...' if len(to_text) > 60 else ''}")
            else:
                print(f"ℹ️  Not found: {description}")
                print(f"   Searched for: {from_text[:60]}{'...' if len(from_text) > 60 else ''}")
        
        # Save modified ESME manifest only if changes were made
        if esme_content != original_content:
            with open(esme_manifest_path, 'w') as f:
                f.write(esme_content)
            print(f"\n✅ Successfully applied {success_count} ESME replacement(s)")
            print(f"💾 Modified ESME manifest saved to: {esme_manifest_path}")
        else:
            print(f"\nℹ️  No changes applied to ESME manifest")
        
        # Report results
        print(f"\n📊 ESME REPLACEMENT RESULTS:")
        print(f"   Successful updates: {success_count}")
        print(f"   Configuration rules: {len(replacements)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error applying ESME replacements: {str(e)}")
        return False

def apply_steering_wheel_replacements(dataset_path):
    """
    Apply steering wheel replacements to the dataset file based on configuration.

    Args:
        dataset_path (str): Path to the dataset JSON file to modify.
    """
    try:
        # Load dataset replacement configuration (comprehensive file)
        dataset_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "issp_dataset_replacements.json")
        
        # Fallback to old steering wheel config if new one doesn't exist
        if not os.path.exists(dataset_config_path):
            dataset_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steering_wheel_replacements.json")
        
        if not os.path.exists(dataset_config_path):
            print(f"ℹ️  No dataset replacements configuration found")
            print(f"📁 Expected: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'issp_dataset_replacements.json')}")
            return True
        
        with open(dataset_config_path, 'r') as f:
            config_data = json.load(f)
        
        print(f"📋 Loaded configuration from: {os.path.basename(dataset_config_path)}")
        
        # Load dataset JSON
        with open(dataset_path, 'r') as f:
            dataset_content = f.read()
        
        # Create backup if not exists
        backup_path = dataset_path + '.dataset.bak'
        if not os.path.exists(backup_path):
            with open(backup_path, 'w') as f:
                f.write(dataset_content)
            print(f"📁 Created backup: {os.path.basename(backup_path)}")
        else:
            print(f"📁 Backup already exists: {os.path.basename(backup_path)}")
        
        total_changes = 0
        
        # 1. Apply regular string replacements
        regular_replacements = config_data.get('replacements', [])
        if regular_replacements:
            print(f"\n� Applying {len(regular_replacements)} regular string replacements...")
            original_content = dataset_content
            
            for replacement in regular_replacements:
                from_values = replacement.get('from')
                to_value = replacement.get('to')
                description = replacement.get('description', 'No description')
                
                if not from_values or not to_value:
                    continue
                
                # Handle multiple "from" values
                if isinstance(from_values, list):
                    for from_val in from_values:
                        if from_val in dataset_content:
                            dataset_content = dataset_content.replace(from_val, to_value)
                            total_changes += 1
                            print(f"✅ Applied: {description}")
                            print(f"   From: {from_val}")
                            print(f"   To:   {to_value}")
                else:
                    if from_values in dataset_content:
                        dataset_content = dataset_content.replace(from_values, to_value)
                        total_changes += 1
                        print(f"✅ Applied: {description}")
                        print(f"   From: {from_values}")
                        print(f"   To:   {to_value}")
                    else:
                        print(f"ℹ️  Not found: {description}")
        
        # 2. Apply ASCII path replacements - targeted approach for specific camera configurations
        ascii_replacements = config_data.get('ascii_path_replacements', {}).get('automatic_replacements', [])
        if ascii_replacements:
            print(f"\n🔄 Applying {len(ascii_replacements)} ASCII path replacements...")
            
            for replacement in ascii_replacements:
                old_path = replacement.get('old_path')
                new_path = replacement.get('new_path')
                description = replacement.get('description', 'No description')
                
                if not old_path or not new_path:
                    continue
                
                # Convert paths to ASCII arrays (without padding zeros for pattern matching)
                old_ascii_list = [ord(c) for c in old_path]
                new_ascii_list = [ord(c) for c in new_path]
                
                replacement_made = False
                
                # Search for the specific camera configuration pattern
                camera_pattern = '"MIRRORSE_CHN1CAMDEFAULT":'
                if camera_pattern in dataset_content:
                    print(f"🔍 Found MIRRORSE_CHN1CAMDEFAULT camera configuration")
                    
                    # Find all model_path and misuse_model_path fields within this camera config
                    camera_start = dataset_content.find(camera_pattern)
                    
                    # Find the end of this camera configuration (next camera or closing brace)
                    camera_section_start = camera_start
                    brace_count = 0
                    found_opening = False
                    camera_end = len(dataset_content)
                    
                    for i in range(camera_start, len(dataset_content)):
                        if dataset_content[i] == '{':
                            if not found_opening:
                                found_opening = True
                            brace_count += 1
                        elif dataset_content[i] == '}':
                            brace_count -= 1
                            if found_opening and brace_count == 0:
                                camera_end = i + 1
                                break
                    
                    camera_section = dataset_content[camera_section_start:camera_end]
                    
                    # Look for model_path and misuse_model_path with ASCII arrays
                    for field_name in ['model_path', 'misuse_model_path']:
                        field_pattern = f'"{field_name}": ['
                        if field_pattern in camera_section:
                            print(f"   🔍 Found {field_name} field in camera configuration")
                            
                            # Find the ASCII array for this field
                            field_start = camera_section.find(field_pattern)
                            if field_start != -1:
                                # Find the start and end of the array
                                array_start = camera_section.find('[', field_start)
                                array_end = camera_section.find(']', array_start) + 1
                                
                                if array_start != -1 and array_end != -1:
                                    current_array = camera_section[array_start:array_end]
                                    
                                    # Check if this array contains our target path
                                    # Convert current array to list for comparison
                                    try:
                                        import ast
                                        current_ascii_list = ast.literal_eval(current_array)
                                        
                                        # Extract the meaningful part (remove trailing zeros)
                                        meaningful_ascii = []
                                        for val in current_ascii_list:
                                            if val == 0:
                                                break
                                            meaningful_ascii.append(val)
                                        
                                        # Convert back to string for comparison
                                        if meaningful_ascii == old_ascii_list:
                                            # Found a match! Replace it
                                            # Preserve the same array length by padding with zeros
                                            new_ascii_padded = new_ascii_list + [0] * (len(current_ascii_list) - len(new_ascii_list))
                                            new_array = str(new_ascii_padded)
                                            
                                            # Replace in the main content
                                            dataset_content = dataset_content.replace(current_array, new_array)
                                            total_changes += 1
                                            replacement_made = True
                                            
                                            current_path = ''.join(chr(c) for c in meaningful_ascii)
                                            print(f"   ✅ Replaced {field_name} ASCII array: {description}")
                                            print(f"      From path: {current_path}")
                                            print(f"      To path:   {new_path}")
                                            print(f"      Array length: {len(current_ascii_list)} (padded with zeros)")
                                        else:
                                            current_path = ''.join(chr(c) for c in meaningful_ascii) if meaningful_ascii else "(empty/invalid)"
                                            print(f"   ℹ️  {field_name} contains different path: {current_path}")
                                    
                                    except (ValueError, SyntaxError) as e:
                                        print(f"   ⚠️  Could not parse {field_name} array: {e}")
                
                if not replacement_made:
                    print(f"ℹ️  No matching ASCII path found: {description}")
                    print(f"   Target path: {old_path}")
                    
                    # Additional diagnostic
                    if camera_pattern not in dataset_content:
                        print(f"   ℹ️  MIRRORSE_CHN1CAMDEFAULT camera not found in dataset")
        
        # 3. Skip steering wheel replacements (removed as requested)
        steering_replacements = []
        # Note: Steering wheel replacements have been removed to focus on ASCII path replacements
        
        if steering_replacements:
            print(f"\n🔄 Applying {len(steering_replacements)} steering wheel replacements...")
            
            # Parse JSON for steering wheel updates
            dataset_data = json.loads(dataset_content)
            
            # Add diagnostic search
            print("\n� DIAGNOSTIC: Searching for current steering wheel values...")
            found_values = find_steering_wheel_values(dataset_data, "MIRRORSE_CHN1CAMDEFAULT")
            
            if found_values:
                print(f"📋 Found {len(found_values)} steering wheel configuration(s)")
                for i, found in enumerate(found_values, 1):
                    print(f"   {i}. Path: {found['path']}")
                    print(f"      Current values: {found['values']}")
                
                # Apply steering wheel replacements
                dataset_data, steering_success_count = replace_steering_wheel_values(dataset_data, steering_replacements)
                
                # Convert back to string
                dataset_content = json.dumps(dataset_data, indent=2)
                total_changes += steering_success_count
            else:
                print("⚠️  No MIRRORSE_CHN1CAMDEFAULT steering wheel configurations found")
        
        # Save modified dataset
        if total_changes > 0:
            with open(dataset_path, 'w') as f:
                f.write(dataset_content)
            print(f"\n✅ Successfully applied {total_changes} replacement(s)")
            print(f"💾 Modified dataset saved to: {dataset_path}")
        else:
            print(f"\nℹ️  No changes applied to dataset")
        
        # Report results
        print(f"\n📊 DATASET REPLACEMENT RESULTS:")
        print(f"   Total successful updates: {total_changes}")
        print(f"   Regular replacements: {len(regular_replacements)}")
        print(f"   ASCII path replacements: {len(ascii_replacements)}")
        print(f"   Steering wheel replacements: {len(steering_replacements)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error applying dataset replacements: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python set_settings.py <project_path> [options]")
        print("Options:")
        print("  --esme-only      Only apply ESME replacements")
        print("  --steering-only  Only apply steering wheel replacements")
        print("  --dataset-only   Only apply dataset replacements")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    # Handle ESME replacements
    if "--esme-only" in sys.argv:
        print("🔄 ESME REPLACEMENTS ONLY")
        print("="*50)
        
        # Find ESME manifest file - first check project root
        esme_manifest_path = os.path.join(project_path, "esme_manifest_issp_roudi.json")
        
        # If not found in root, try the original subdirectory structure
        if not os.path.exists(esme_manifest_path):
            esme_manifest_path = os.path.join(project_path, "aos", "yaaac_codegen", "deploy", "carma_0_22", "issp_roudi", "esme", "esme_manifest_issp_roudi.json")
        
        if not os.path.exists(esme_manifest_path):
            print(f"❌ Error: ESME manifest file not found at:")
            print(f"   {os.path.join(project_path, 'esme_manifest_issp_roudi.json')}")
            print(f"   {os.path.join(project_path, 'aos', 'yaaac_codegen', 'deploy', 'carma_0_22', 'issp_roudi', 'esme', 'esme_manifest_issp_roudi.json')}")
            sys.exit(1)
        
        print(f"📁 Found ESME manifest file: {esme_manifest_path}")
        apply_esme_replacements(esme_manifest_path)
        sys.exit(0)
    
    # Handle steering wheel replacements
    if "--steering-only" in sys.argv:
        print("🔄 STEERING WHEEL REPLACEMENTS ONLY")
        print("="*50)
        
        # Look for dataset file in the correct subdirectory
        dataset_path = os.path.join(project_path, "aos", "dataset", "issp_dataset.json")
        
        # Also check alternative locations
        if not os.path.exists(dataset_path):
            # Try the root directory as fallback
            dataset_path = os.path.join(project_path, "issp_dataset.json")
        
        if not os.path.exists(dataset_path):
            print(f"❌ Error: Dataset file not found at:")
            print(f"   {os.path.join(project_path, 'aos', 'dataset', 'issp_dataset.json')}")
            print(f"   {os.path.join(project_path, 'issp_dataset.json')}")
            sys.exit(1)
        
        print(f"📁 Found dataset file: {dataset_path}")
        apply_steering_wheel_replacements(dataset_path)
        sys.exit(0)
    
    # Handle dataset-only (alias for steering-only)
    if "--dataset-only" in sys.argv:
        print("🔄 DATASET REPLACEMENTS ONLY")
        print("="*50)
        
        # Look for dataset file in the correct subdirectory
        dataset_path = os.path.join(project_path, "aos", "dataset", "issp_dataset.json")
        
        # Also check alternative locations
        if not os.path.exists(dataset_path):
            # Try the root directory as fallback
            dataset_path = os.path.join(project_path, "issp_dataset.json")
        
        if not os.path.exists(dataset_path):
            print(f"❌ Error: Dataset file not found at:")
            print(f"   {os.path.join(project_path, 'aos', 'dataset', 'issp_dataset.json')}")
            print(f"   {os.path.join(project_path, 'issp_dataset.json')}")
            sys.exit(1)
        
        print(f"📁 Found dataset file: {dataset_path}")
        apply_steering_wheel_replacements(dataset_path)
        sys.exit(0)
    
    # Default behavior - show available options
    print("ℹ️  Available options:")
    print("  --esme-only      Only apply ESME replacements") 
    print("  --steering-only  Only apply steering wheel replacements")
    print("  --dataset-only   Only apply dataset replacements")
