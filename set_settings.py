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
                            
                            # If old_values is specified, check for exact match
                            if old_values:
                                if current_values == old_values:
                                    value[field_name] = new_values
                                    success_count += 1
                                    print(f"✅ Updated {field_name} in '{current_path}': {old_values} → {new_values}")
                                else:
                                    print(f"ℹ️  {field_name} in '{current_path}' has different values: {current_values}")
                                    print(f"    Expected: {old_values}")
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

def apply_steering_wheel_replacements(dataset_path):
    """
    Apply steering wheel replacements to the dataset file based on configuration.

    Args:
        dataset_path (str): Path to the dataset JSON file to modify.
    """
    try:
        # Load steering wheel replacement configuration
        steering_wheel_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steering_wheel_replacements.json")
        
        if not os.path.exists(steering_wheel_config_path):
            print(f"ℹ️  No steering wheel replacements configuration found")
            print(f"📁 Expected: {steering_wheel_config_path}")
            return True
        
        with open(steering_wheel_config_path, 'r') as f:
            config_data = json.load(f)
        
        replacements = config_data.get('replacements', [])
        if not replacements:
            print("ℹ️  No steering wheel replacement rules found in configuration")
            return True
            
        print(f"📋 Loaded {len(replacements)} steering wheel replacement rules")
        
        # Load dataset JSON
        with open(dataset_path, 'r') as f:
            dataset_data = json.load(f)
        
        # Add diagnostic search
        print("\n🔍 DIAGNOSTIC: Searching for current steering wheel values...")
        found_values = find_steering_wheel_values(dataset_data, "MIRRORSE_CHN1CAMDEFAULT")
        
        if found_values:
            print(f"📋 Found {len(found_values)} steering wheel configuration(s)")
            for i, found in enumerate(found_values, 1):
                print(f"   {i}. Path: {found['path']}")
                print(f"      Current values: {found['values']}")
        else:
            print("⚠️  No MIRRORSE_CHN1CAMDEFAULT steering wheel configurations found")
            return True
        
        # Create backup if not exists
        backup_path = dataset_path + '.steering_wheel.bak'
        if not os.path.exists(backup_path):
            with open(backup_path, 'w') as f:
                json.dump(dataset_data, f, indent=2)
            print(f"\n📁 Created backup: {os.path.basename(backup_path)}")
        else:
            print(f"\n📁 Backup already exists: {os.path.basename(backup_path)}")
        
        # Apply steering wheel replacements
        print("\n🔄 Applying steering wheel replacements...")
        dataset_data, success_count = replace_steering_wheel_values(dataset_data, replacements)
        
        # Save modified dataset
        with open(dataset_path, 'w') as f:
            json.dump(dataset_data, f, indent=2)
        
        # Report results
        print(f"\n📊 STEERING WHEEL REPLACEMENT RESULTS:")
        print(f"   Successful updates: {success_count}")
        print(f"   Configuration rules: {len(replacements)}")
        
        if success_count > 0:
            print(f"✅ Successfully updated {success_count} steering_wheel configuration(s)")
            print(f"💾 Modified dataset saved to: {dataset_path}")
        else:
            print(f"ℹ️  No matching steering_wheel configurations found to update")
            
        return True
        
    except Exception as e:
        print(f"❌ Error applying steering wheel replacements: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python set_settings.py <project_path> [options]")
        print("Options:")
        print("  --steering-only  Only apply steering wheel replacements")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    # Fix: Look for dataset file in the correct subdirectory
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
    
    if "--steering-only" in sys.argv:
        print("🔄 STEERING WHEEL REPLACEMENTS ONLY")
        print("="*50)
        apply_steering_wheel_replacements(dataset_path)
    else:
        print("ℹ️  Add --steering-only to run steering wheel replacements")
