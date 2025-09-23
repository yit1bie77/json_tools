#!/bin/bash

# ISSP JSON Tools Test Script
# This script demonstrates how to use the set_settings.py tool

# Configuration - Update these paths as needed
PRJ_Folder="/home/yit1bie/Documents/issp_dataset"
JSON_Tools_Folder="/home/yit1bie/workspace/python/json_tools"

# Configuration JSON files path - Set to specific subfolder or leave empty for default
# Examples:
#   CONFIG_Path=""           # Use default (JSON files in main folder)
#   CONFIG_Path="./etron"    # Use files from etron subfolder
#   CONFIG_Path="./zotac"    # Use files from zotac subfolder
CONFIG_Path="./zotac"  # Set to your desired configuration path

# Control flag - set to false to skip settings modification
if_setsettings=true

# Validate paths exist
if [ ! -d "$PRJ_Folder" ]; then
    echo "Error: Project folder not found: $PRJ_Folder"
    exit 1
fi

if [ ! -d "$JSON_Tools_Folder" ]; then
    echo "Error: JSON Tools folder not found: $JSON_Tools_Folder"
    exit 1
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --esme-only      Only apply ESME replacements"
    echo "  --dataset-only   Only apply dataset replacements"
    echo "  --steering-only  Only apply steering wheel replacements"
    echo "  --config-path    Specify path to configuration JSON files (overrides CONFIG_Path variable)"
    echo "  --all           Run esme-only, dataset-only, and steering-only sequentially"
    echo "  --help           Show this help message"
    echo ""
    echo "Configuration:"
    echo "  Edit the CONFIG_Path variable at the top of this script to set default configuration folder"
    echo "  Current CONFIG_Path: ${CONFIG_Path:-\"(default - main folder)\"}"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run all operations using CONFIG_Path setting"
    echo "  $0 --esme-only               # Only ESME replacements using CONFIG_Path setting"
    echo "  $0 --dataset-only            # Only dataset replacements using CONFIG_Path setting"
    echo "  $0 --config-path ./etron     # Override CONFIG_Path and use ./etron folder"
}

# Check for help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_usage
    exit 0
fi

# Handle --all option (or no option)
if [[ "$1" == "--all" || $# -eq 0 ]]; then
    echo "\n🚀 Running all modes: esme-only, dataset-only, steering-only"
    for mode in --esme-only --dataset-only --steering-only; do
        echo "\n=================================================="
        echo "Running: $0 $mode ${@:2}"
        "$0" $mode "${@:2}"
        status=$?
        if [ $status -ne 0 ]; then
            echo "❌ $mode failed with exit code $status"
            exit $status
        fi
    done
    echo "\n✅ All modes completed successfully!"
    exit 0
fi

if [ "$if_setsettings" = true ]; then
    echo "🚀 Starting ISSP JSON Tools..."
    echo "=================================================="
    echo "=== ISSP Configuration Tool ==="
    echo "Project folder: $PRJ_Folder"
    echo "Tools folder: $JSON_Tools_Folder"
    echo
    
    cd "$JSON_Tools_Folder" || exit 1
    echo "Setting settings for project folder: $PRJ_Folder"
    
    # Check if Python script exists
    if [ ! -f "set_settings.py" ]; then
        echo "Error: set_settings.py not found in $JSON_Tools_Folder"
        exit 1
    fi
    
    # Run the Python configuration tool with all command line arguments
    if [ -n "$CONFIG_Path" ] && [ "$CONFIG_Path" != "" ]; then
        echo "Running: python set_settings.py \"$PRJ_Folder\" --config-path \"$CONFIG_Path\" $@"
        echo "📁 Using configuration files from: $CONFIG_Path"
    else
        echo "Running: python set_settings.py \"$PRJ_Folder\" $@"
        echo "📁 Using default configuration files"
    fi
    echo "=================================================="
    
    if [ -n "$CONFIG_Path" ] && [ "$CONFIG_Path" != "" ]; then
        python3 set_settings.py "$PRJ_Folder" --config-path "$CONFIG_Path" "$@"
    else
        python3 set_settings.py "$PRJ_Folder" "$@"
    fi
    exit_code=$?
    
    echo "=================================================="
    if [ $exit_code -eq 0 ]; then
        echo "✅ Configuration completed successfully!"
        echo "📂 Project location: $PRJ_Folder"
    else
        echo "❌ Configuration failed with exit code: $exit_code"
        exit $exit_code
    fi
else
    echo "⏭️  Skipping settings configuration for project folder: $PRJ_Folder"
fi

echo ""
echo "🎉 ISSP JSON Tools completed!"
echo "=================================================="


