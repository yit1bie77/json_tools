#!/usr/bin/env python3
"""
ASCII Path Converter Utility
This utility helps convert between regular strings and ASCII arrays for ISSP configuration files.
"""

import sys
import json

def string_to_ascii_array(text, target_length=256):
    """Convert a string to ASCII array with padding."""
    ascii_codes = [ord(char) for char in text]
    ascii_codes.extend([0] * (target_length - len(ascii_codes)))
    return ascii_codes[:target_length]

def ascii_array_to_string(ascii_array):
    """Convert ASCII array back to string."""
    end_index = ascii_array.index(0) if 0 in ascii_array else len(ascii_array)
    return ''.join(chr(code) for code in ascii_array[:end_index])

def main():
    if len(sys.argv) < 2:
        print("ASCII Path Converter Utility")
        print("Usage:")
        print("  python ascii_converter.py 'string_to_convert'")
        print("  python ascii_converter.py --from-ascii 47,104,111,109,101...")
        print("  python ascii_converter.py --help")
        sys.exit(1)
    
    if sys.argv[1] == "--help":
        print("ASCII Path Converter Utility")
        print("Convert between strings and ASCII arrays for ISSP configuration files.")
        print()
        print("Examples:")
        print("  Convert string to ASCII array:")
        print("    python ascii_converter.py '/home/issp/workspace/models/test.onnx'")
        print()
        print("  Convert ASCII array to string:")
        print("    python ascii_converter.py --from-ascii '47,104,111,109,101,47,105,115,115'")
        print()
        return
    
    if sys.argv[1] == "--from-ascii":
        if len(sys.argv) < 3:
            print("Error: Please provide ASCII codes separated by commas")
            sys.exit(1)
        
        try:
            ascii_codes = [int(x.strip()) for x in sys.argv[2].split(',')]
            result = ascii_array_to_string(ascii_codes)
            print(f"ASCII Array: {ascii_codes[:20]}{'...' if len(ascii_codes) > 20 else ''}")
            print(f"String: '{result}'")
        except ValueError as e:
            print(f"Error parsing ASCII codes: {e}")
            sys.exit(1)
    else:
        # Convert string to ASCII
        input_string = sys.argv[1]
        ascii_array = string_to_ascii_array(input_string)
        
        print(f"String: '{input_string}'")
        print(f"ASCII Array (first 20): {ascii_array[:20]}{'...' if len(ascii_array) > 20 else ''}")
        print(f"Full ASCII Array: {ascii_array}")
        print()
        print("JSON format for replacement file:")
        print(json.dumps(ascii_array, indent=2))

if __name__ == "__main__":
    main()
