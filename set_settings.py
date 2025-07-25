# === ASCII path replacement helpers from set_settings_v1.py ===
def string_to_ascii_array(text, target_length=256):
    ascii_codes = [ord(char) for char in text]
    ascii_codes.extend([0] * (target_length - len(ascii_codes)))
    return ascii_codes[:target_length]

def ascii_array_to_string(ascii_array):
    end_index = ascii_array.index(0) if 0 in ascii_array else len(ascii_array)
    return ''.join(chr(code) for code in ascii_array[:end_index])

def replace_path_in_ascii_arrays(data, old_path, new_path):
    replacements_made = 0
    def _replace_recursive(data):
        nonlocal replacements_made
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key.endswith('_path') and isinstance(value, list):
                    current_path = ascii_array_to_string(value)
                    if current_path == new_path:
                        result[key] = value
                    elif current_path == old_path:
                        result[key] = string_to_ascii_array(new_path, len(value))
                        replacements_made += 1
                    elif old_path in current_path:
                        new_full_path = current_path.replace(old_path, new_path)
                        result[key] = string_to_ascii_array(new_full_path, len(value))
                        replacements_made += 1
                    else:
                        result[key] = value
                else:
                    result[key] = _replace_recursive(value)
            return result
        elif isinstance(data, list):
            return [_replace_recursive(item) for item in data]
        else:
            return data
    result = _replace_recursive(data)
    if replacements_made > 0:
        print(f"✅ Successfully updated {replacements_made} ASCII path(s) from '{old_path}' to '{new_path}'")
    else:
        print(f"ℹ️  No instances of '{old_path}' found to replace as ASCII path")
    return result
def apply_dataset_replacements(dataset_path, config_path=None):
    """
    Apply generic replacements (from 'replacements' and 'ascii_path_replacements') to the dataset file based on configuration.
    Args:
        dataset_path (str): Path to the dataset JSON file to modify.
        config_path (str, optional): Path to directory containing configuration files.
    """
    try:
        # Load dataset replacement configuration
        if config_path:
            dataset_config_path = os.path.join(config_path, "issp_dataset_replacements.json")
        else:
            dataset_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "issp_dataset_replacements.json")

        if not os.path.exists(dataset_config_path):
            print(f"ℹ️  No dataset replacements configuration found")
            if config_path:
                print(f"📁 Expected: {os.path.join(config_path, 'issp_dataset_replacements.json')}")
            else:
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

        original_content = dataset_content
        total_changes = 0

        # Apply string/regex replacements
        replacements = config_data.get('replacements', [])
        if replacements:
            print(f"\n🔄 Applying {len(replacements)} generic replacements...")
            for replacement in replacements:
                from_patterns = replacement.get('from')
                to_pattern = replacement.get('to')
                description = replacement.get('description', 'No description')
                if not from_patterns or not to_pattern:
                    print(f"⚠️  Skipping invalid replacement rule: {description}")
                    continue
                if isinstance(from_patterns, list):
                    for from_pattern in from_patterns:
                        if from_pattern in dataset_content:
                            dataset_content = dataset_content.replace(from_pattern, to_pattern)
                            total_changes += 1
                            print(f"✅ Applied: {description} (pattern: {from_pattern})")
                        else:
                            print(f"ℹ️  Not found: {description} (pattern: {from_pattern})")
                else:
                    if from_patterns in dataset_content:
                        dataset_content = dataset_content.replace(from_patterns, to_pattern)
                        total_changes += 1
                        print(f"✅ Applied: {description}")
                    else:
                        print(f"ℹ️  Not found: {description}")


        # Apply ASCII path replacements (robust, using parsed JSON)
        ascii_paths = config_data.get('ascii_path_replacements', {}).get('automatic_replacements', [])
        if ascii_paths:
            try:
                dataset_json = json.loads(dataset_content)
                print(f"\n🔄 Applying {len(ascii_paths)} ASCII path replacements (robust)...")
                for path_rule in ascii_paths:
                    old_path = path_rule.get('old_path')
                    new_path = path_rule.get('new_path')
                    description = path_rule.get('description', 'No description')
                    if not old_path or not new_path:
                        print(f"⚠️  Skipping invalid ASCII path rule: {description}")
                        continue
                    dataset_json = replace_path_in_ascii_arrays(dataset_json, old_path, new_path)
                dataset_content = json.dumps(dataset_json, indent=2)
            except Exception as e:
                print(f"❌ Error during robust ASCII path replacement: {e}")

        # Save modified dataset
        if dataset_content != original_content:
            with open(dataset_path, 'w') as f:
                f.write(dataset_content)
            print(f"\n✅ Successfully applied {total_changes} replacement(s)")
            print(f"💾 Modified dataset saved to: {dataset_path}")
        else:
            print(f"\nℹ️  No changes applied to dataset")

        # Report results
        print(f"\n📊 DATASET REPLACEMENT RESULTS:")
        print(f"   Total successful updates: {total_changes}")
        print(f"   Generic replacements: {len(replacements)}")
        print(f"   ASCII path replacements: {len(ascii_paths)}")
        return True
    except Exception as e:
        print(f"❌ Error applying dataset replacements: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
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
    
    def values_match(current, expected, tolerance=1e-4):
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

def apply_esme_replacements(esme_manifest_path, config_path=None):
    """
    Apply ESME replacements to the ESME manifest file based on configuration.

    Args:
        esme_manifest_path (str): Path to the ESME manifest JSON file to modify.
        config_path (str, optional): Path to directory containing configuration files.
    """
    try:
        # Load ESME replacement configuration
        if config_path:
            esme_config_path = os.path.join(config_path, "esme_replacements.json")
        else:
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

def apply_steering_wheel_replacements(dataset_path, config_path=None):
    """
    Apply steering wheel replacements to the dataset file based on configuration.

    Args:
        dataset_path (str): Path to the dataset JSON file to modify.
        config_path (str, optional): Path to directory containing configuration files.
    """
    try:
        # Load dataset replacement configuration (comprehensive file)
        if config_path:
            dataset_config_path = os.path.join(config_path, "issp_dataset_replacements.json")
            # Fallback to old steering wheel config if new one doesn't exist
            if not os.path.exists(dataset_config_path):
                dataset_config_path = os.path.join(config_path, "steering_wheel_replacements.json")
        else:
            dataset_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "issp_dataset_replacements.json")
            # Fallback to old steering wheel config if new one doesn't exist
            if not os.path.exists(dataset_config_path):
                dataset_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steering_wheel_replacements.json")
        
        if not os.path.exists(dataset_config_path):
            print(f"ℹ️  No dataset replacements configuration found")
            if config_path:
                print(f"📁 Expected: {os.path.join(config_path, 'issp_dataset_replacements.json')}")
                print(f"📁 Or: {os.path.join(config_path, 'steering_wheel_replacements.json')}")
            else:
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
        
        # Only apply steering wheel replacements in steering-only mode
        steering_replacements = config_data.get('steering_wheel_replacements', {}).get('replacements', [])
        if steering_replacements:
            print(f"\n🔄 Applying {len(steering_replacements)} steering wheel replacements...")
            dataset_data = json.loads(dataset_content)
            print("\n� DIAGNOSTIC: Searching for current steering wheel values...")
            found_values = find_steering_wheel_values(dataset_data, "MIRRORSE_CHN1CAMDEFAULT")
            if found_values:
                print(f"📋 Found {len(found_values)} steering wheel configuration(s)")
                for i, found in enumerate(found_values, 1):
                    print(f"   {i}. Path: {found['path']}")
                    print(f"      Current values: {found['values']}")
                dataset_data, steering_success_count = replace_steering_wheel_values(dataset_data, steering_replacements)
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
        print("  --all           Apply ESME, dataset, and steering wheel replacements in sequence")
        print("  --esme-only      Only apply ESME replacements")
        print("  --steering-only  Only apply steering wheel replacements")
        print("  --dataset-only   Only apply dataset replacements")
        print("  --config-path    Path to directory containing configuration JSON files")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    # Parse config path argument
    config_path = None
    if "--config-path" in sys.argv:
        try:
            config_index = sys.argv.index("--config-path")
            if config_index + 1 < len(sys.argv):
                config_path = sys.argv[config_index + 1]
                if not os.path.isdir(config_path):
                    print(f"❌ Error: Configuration path is not a directory: {config_path}")
                    sys.exit(1)
                config_path = os.path.abspath(config_path)
                print(f"📁 Using configuration files from: {config_path}")
            else:
                print("❌ Error: --config-path requires a directory path")
                sys.exit(1)
        except ValueError:
            pass
    
    # Handle --all option first, so it takes precedence
    if "--all" in sys.argv:
        print("🔄 RUNNING ALL REPLACEMENTS (ESME, DATASET, STEERING WHEEL)")
        print("="*50)

        # ESME
        esme_manifest_path = os.path.join(project_path, "esme_manifest_issp_roudi.json")
        if not os.path.exists(esme_manifest_path):
            esme_manifest_path = os.path.join(project_path, "aos", "yaaac_codegen", "deploy", "carma_0_22", "issp_roudi", "esme", "esme_manifest_issp_roudi.json")
        if os.path.exists(esme_manifest_path):
            print(f"\n📁 Found ESME manifest file: {esme_manifest_path}")
            apply_esme_replacements(esme_manifest_path, config_path)
        else:
            print(f"❌ Error: ESME manifest file not found at:")
            print(f"   {os.path.join(project_path, 'esme_manifest_issp_roudi.json')}")
            print(f"   {os.path.join(project_path, 'aos', 'yaaac_codegen', 'deploy', 'carma_0_22', 'issp_roudi', 'esme', 'esme_manifest_issp_roudi.json')}")

        # DATASET/STEERING
        dataset_path = os.path.join(project_path, "aos", "dataset", "issp_dataset.json")
        if not os.path.exists(dataset_path):
            dataset_path = os.path.join(project_path, "issp_dataset.json")
        if os.path.exists(dataset_path):
            print(f"\n📁 Found dataset file: {dataset_path}")
            apply_steering_wheel_replacements(dataset_path, config_path)
        else:
            print(f"❌ Error: Dataset file not found at:")
            print(f"   {os.path.join(project_path, 'aos', 'dataset', 'issp_dataset.json')}")
            print(f"   {os.path.join(project_path, 'issp_dataset.json')}")

        sys.exit(0)

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
        apply_esme_replacements(esme_manifest_path, config_path)
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
        apply_steering_wheel_replacements(dataset_path, config_path)
        sys.exit(0)

    # Handle dataset-only (generic replacements only)
    if "--dataset-only" in sys.argv:
        print("🔄 DATASET REPLACEMENTS ONLY (GENERIC)")
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
        apply_dataset_replacements(dataset_path, config_path)
        sys.exit(0)

    # Default behavior - show available options
    print("ℹ️  Available options:")
    print("  --all           Apply ESME, dataset, and steering wheel replacements in sequence")
    print("  --esme-only      Only apply ESME replacements")
    print("  --steering-only  Only apply steering wheel replacements")
    print("  --dataset-only   Only apply dataset replacements")
    print("  --config-path    Path to directory containing configuration JSON files")
