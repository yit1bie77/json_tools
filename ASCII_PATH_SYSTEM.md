# Enhanced ASCII Path Replacement System

## 🚀 **Problem Solved**

Your ISSP dataset files contain ASCII arrays representing file paths. The enhanced system now automatically:

1. **Detects ASCII path arrays** in JSON files
2. **Converts them to readable strings** 
3. **Applies path replacements**
4. **Converts back to ASCII arrays** with proper padding

## 📋 **New Configuration Format**

### `issp_dataset_replacements_new.json`:
```json
{
    "version": "2.0",
    "path_mappings": {
        "old_base_path": "/home/iss",
        "new_base_path": "/home/issp/workspace"
    },
    "replacements": [
        {
            "description": "Enable CAN usage",
            "from": "\"use_can\": 0",
            "to": "\"use_can\": 1"
        }
    ],
    "ascii_path_replacements": {
        "automatic_replacements": [
            {
                "old_path": "/home/iss/issp_oms_models",
                "new_path": "/home/issp/workspace/issp_oms_models"
            }
        ]
    }
}
```

## 🛠️ **How It Works**

### 1. **Automatic ASCII Detection**
The script automatically finds fields ending with `_path` that contain ASCII arrays:
```python
if key.endswith('_path') and isinstance(value, list):
    # This is an ASCII path array
```

### 2. **Smart Path Replacement**
```python
def replace_path_in_ascii_arrays(data, old_path, new_path):
    # Converts ASCII to string
    current_path = ascii_array_to_string(value)
    
    # Applies replacement
    if old_path in current_path:
        new_full_path = current_path.replace(old_path, new_path)
        
    # Converts back to ASCII array
    result[key] = string_to_ascii_array(new_full_path, len(value))
```

## 🎯 **Benefits**

### ✅ **User-Friendly Configuration**
- No more manually editing ASCII arrays
- Define paths as readable strings
- Automatic conversion handles the complexity

### ✅ **Flexible Path Mapping**
```python
# Easy to configure in JSON:
"path_mappings": {
    "old_base_path": "/home/iss",
    "new_base_path": "/home/issp/workspace"
}
```

### ✅ **Automatic Detection**
- Finds all `*_path` fields automatically
- Works with nested JSON structures
- Preserves array lengths and padding

## 🔧 **Utility Tools**

### `ascii_converter.py` - Helper Script
```bash
# Convert string to ASCII array
python ascii_converter.py '/home/issp/workspace/models/test.onnx'

# Convert ASCII array to string
python ascii_converter.py --from-ascii '47,104,111,109,101,47,105,115,115'

# Get help
python ascii_converter.py --help
```

## 📊 **Example Transformation**

### Before (ASCII Array):
```json
"model_path": [47, 104, 111, 109, 101, 47, 105, 115, 115, 47, 105, 115, 115, 112, 95, 111, 109, 115, 95, 109, 111, 100, 101, 108, 115, 47, 115, 101, 97, 116, 98, 101, 108, 116, 95, 109, 111, 100, 101, 108, 46, 111, 110, 110, 120, 0, 0, 0, ...]
```

### After Processing:
```json
"model_path": [47, 104, 111, 109, 101, 47, 105, 115, 115, 112, 47, 119, 111, 114, 107, 115, 112, 97, 99, 101, 47, 105, 115, 115, 112, 95, 111, 109, 115, 95, 109, 111, 100, 101, 108, 115, 47, 115, 101, 97, 116, 98, 101, 108, 116, 95, 109, 111, 100, 101, 108, 46, 111, 110, 110, 120, 0, 0, 0, ...]
```

### Translation:
- **Before**: `/home/iss/issp_oms_models/seatbelt_model.onnx`
- **After**: `/home/issp/workspace/issp_oms_models/seatbelt_model.onnx`

## 🚀 **Usage**

1. **Edit the configuration**: Update `issp_dataset_replacements_new.json` with your desired paths
2. **Run the script**: `python set_settings.py /path/to/project`
3. **Automatic processing**: Script handles ASCII conversion automatically

## 💡 **Advanced Features**

### Variable Path Mapping
You can easily change the base paths by editing the configuration:
```json
"path_mappings": {
    "old_base_path": "/old/path",
    "new_base_path": "/new/path"
}
```

### Multiple Path Types
The system automatically handles all path fields:
- `model_path`
- `misuse_model_path`  
- `config_path`
- Any field ending with `_path`

This solution is **much more maintainable** than manually editing ASCII arrays! 🎉
