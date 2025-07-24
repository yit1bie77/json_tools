#!/bin/bash

# ISSP JSON Tools Test Script
# This script demonstrates how to use the set_settings.py tool

# Configuration - Update these paths as needed
PRJ_Folder="/home/tie/workspace/AOS/issp_aos_dply_prj_ref_4_1_0"
JSON_Tools_Folder="/home/tie/workspace/ISSP/Json_Tools"

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
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all operations (ESME + Dataset + Steering)"
    echo "  $0 --esme-only        # Only ESME replacements"
    echo "  $0 --dataset-only     # Only dataset replacements"
    echo "  $0 --steering-only    # Only steering wheel replacements"
}

# Check for help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_usage
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
    echo "Running: python set_settings.py \"$PRJ_Folder\" $@"
    echo "=================================================="
    
    python set_settings.py "$PRJ_Folder" "$@"
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


