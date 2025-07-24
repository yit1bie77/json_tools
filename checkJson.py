import json
import sys
import re

def check_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # First, try to parse the JSON to get the first error
        first_error = None
        try:
            json.loads(content)
            print("✅ JSON is valid.")
            return
        except json.JSONDecodeError as e:
            first_error = e
        
        print("❌ JSON is invalid!")
        print("=" * 50)
        
        # Find ALL errors using comprehensive analysis
        all_errors = find_all_json_errors(content)
        
        if all_errors:
            print(f"Found {len(all_errors)} syntax error(s) at these lines:")
            for error in all_errors:
                print(f"Line {error['line']}: {error['type']}")
        else:
            # Fallback to original error if comprehensive analysis fails
            print(f"Syntax error at Line {first_error.lineno}, Column {first_error.colno}: {first_error.msg}")
    
    except FileNotFoundError:
        print(f"❌ Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"❌ Error reading file: {e}")

def find_all_json_errors(content):
    """Find all JSON syntax errors in the content"""
    errors = []
    lines = content.splitlines()
    
    # Check each line for common JSON syntax errors
    for line_num, line in enumerate(lines, 1):
        line_errors = analyze_line_for_errors(line, line_num, lines)
        errors.extend(line_errors)
    
    # Check for structural issues
    structural_errors = check_json_structure(lines)
    errors.extend(structural_errors)
    
    # Sort errors by line number
    errors.sort(key=lambda x: (x['line'], x['column']))
    
    return errors

def analyze_line_for_errors(line, line_num, all_lines):
    """Analyze a single line for JSON syntax errors"""
    errors = []
    stripped_line = line.strip()
    
    if not stripped_line or stripped_line.startswith('//'):
        return errors
    
    # Check for invalid characters at the beginning of property lines
    invalid_start_pattern = r'^(\s*)([a-zA-Z+\-*/@#$%^&()=<>!]+)\s*"'
    match = re.match(invalid_start_pattern, line)
    if match:
        invalid_char = match.group(2)
        if not invalid_char.startswith('"'):
            errors.append({
                'line': line_num,
                'column': len(match.group(1)) + 1,
                'message': f'Invalid character "{invalid_char}" before property name',
                'line_content': line.rstrip(),
                'suggestion': f'Remove "{invalid_char}" - property names should start with quotes'
            })
    
    # Check for standalone invalid characters at line start
    standalone_invalid = re.match(r'^(\s*)([+\-*/@#$%^&()=<>!]+)\s', line)
    if standalone_invalid:
        invalid_char = standalone_invalid.group(2)
        errors.append({
            'line': line_num,
            'column': len(standalone_invalid.group(1)) + 1,
            'message': f'Invalid character "{invalid_char}" in JSON',
            'line_content': line.rstrip(),
            'suggestion': f'Remove "{invalid_char}" - not valid in JSON syntax'
        })
    
    # Check for unquoted property names
    unquoted_prop = re.match(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
    if unquoted_prop and not line.strip().startswith('"'):
        prop_name = unquoted_prop.group(2)
        errors.append({
            'line': line_num,
            'column': len(unquoted_prop.group(1)) + 1,
            'message': f'Property name "{prop_name}" is not quoted',
            'line_content': line.rstrip(),
            'suggestion': f'Change {prop_name} to "{prop_name}"'
        })
    
    # Check for single quotes
    if "'" in line and not line.strip().startswith('//'):
        single_quote_pos = line.find("'")
        errors.append({
            'line': line_num,
            'column': single_quote_pos + 1,
            'message': 'Single quotes are not allowed in JSON',
            'line_content': line.rstrip(),
            'suggestion': 'Use double quotes (") instead of single quotes (\')' 
        })
    
    # Check for trailing commas
    if re.search(r',\s*[}\]]', line):
        comma_pos = line.rfind(',')
        errors.append({
            'line': line_num,
            'column': comma_pos + 1,
            'message': 'Trailing comma before closing bracket/brace',
            'line_content': line.rstrip(),
            'suggestion': 'Remove the trailing comma'
        })
    
    # Check for missing commas (compare with next line)
    if line_num < len(all_lines):
        current_ends_with_value = (
            stripped_line.endswith('}') or stripped_line.endswith(']') or 
            stripped_line.endswith('"') or stripped_line.endswith('true') or
            stripped_line.endswith('false') or stripped_line.endswith('null') or
            re.search(r'\d$', stripped_line)
        )
        
        next_line = all_lines[line_num].strip() if line_num < len(all_lines) else ""
        next_starts_with_property = (
            next_line.startswith('"') or 
            re.match(r'^[a-zA-Z_]', next_line)
        )
        
        if (current_ends_with_value and next_starts_with_property and 
            not stripped_line.endswith(',') and 
            not next_line.startswith('}') and not next_line.startswith(']')):
            errors.append({
                'line': line_num,
                'column': len(line.rstrip()),
                'message': 'Missing comma after value',
                'line_content': line.rstrip(),
                'suggestion': 'Add a comma at the end of this line'
            })
    
    # Check for comments
    if '//' in line or '/*' in line:
        comment_pos = max(line.find('//'), line.find('/*'))
        if comment_pos >= 0:
            errors.append({
                'line': line_num,
                'column': comment_pos + 1,
                'message': 'Comments are not allowed in JSON',
                'line_content': line.rstrip(),
                'suggestion': 'Remove the comment'
            })
    
    return errors

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python checkJson.py <json_file_path>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    check_json_file(json_file)
    """Print detailed error information"""
    print("=" * 80)
    print("🔍 DETAILED ERROR ANALYSIS")
    print("=" * 80)
    
    for i, error in enumerate(errors, 1):
        print(f"\n📍 Error #{i:02d} Details:")
        print(f"   ├─ Location: Line {error['line']}, Column {error['column']}")
        print(f"   ├─ Type: {classify_error_type(error['message'])}")
        print(f"   ├─ Issue: {error['message']}")
        print(f"   ├─ Content: {error['line_content']}")
        
        # Show error position with pointer
        if error['column'] > 0 and len(error['line_content']) >= error['column']:
            pointer = ' ' * (len("   ├─ Content: ") + error['column'] - 1) + '↑'
            print(f"   ├─ Position:{pointer}")
        
        if error.get('suggestion'):
            print(f"   └─ 💡 Fix: {error['suggestion']}")
        else:
            print(f"   └─ (No automatic fix available)")

def classify_error_type(message):
    """Classify error into categories for the table"""
    message_lower = message.lower()
    
    if 'invalid character' in message_lower:
        return "INVALID_CHAR"
    elif 'not quoted' in message_lower or 'property name' in message_lower:
        return "UNQUOTED_PROPERTY"
    elif 'single quotes' in message_lower:
        return "QUOTE_TYPE"
    elif 'trailing comma' in message_lower:
        return "TRAILING_COMMA"
    elif 'missing comma' in message_lower:
        return "MISSING_COMMA"
    elif 'comment' in message_lower:
        return "COMMENT"
    elif 'bracket' in message_lower or 'brace' in message_lower:
        return "BRACKET_MISMATCH"
    elif 'unclosed' in message_lower:
        return "UNCLOSED_BRACKET"
    else:
        return "OTHER"

def get_error_severity(message):
    """Determine error severity"""
    message_lower = message.lower()
    
    # Critical errors that completely break JSON parsing
    critical_keywords = ['invalid character', 'unmatched', 'unclosed', 'mismatched']
    if any(keyword in message_lower for keyword in critical_keywords):
        return "CRITICAL"
    
    # Warning-level errors that are bad practice but might not always break parsing
    warning_keywords = ['trailing comma', 'comment']
    if any(keyword in message_lower for keyword in warning_keywords):
        return "WARNING"
    
    # High priority errors that should be fixed
    return "HIGH"

def truncate_text(text, max_length):
    """Truncate text to fit in table column"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def check_json_structure(lines):
    """Check for structural issues like unmatched brackets"""
    errors = []
    bracket_stack = []
    
    for line_num, line in enumerate(lines, 1):
        for col_num, char in enumerate(line, 1):
            if char in '{[':
                bracket_stack.append((char, line_num, col_num))
            elif char in '}]':
                if not bracket_stack:
                    errors.append({
                        'line': line_num,
                        'column': col_num,
                        'message': f'Unmatched closing bracket "{char}"',
                        'line_content': line.rstrip(),
                        'suggestion': f'Remove this "{char}" or add matching opening bracket'
                    })
                else:
                    opening_char, opening_line, opening_col = bracket_stack.pop()
                    if (char == '}' and opening_char != '{') or (char == ']' and opening_char != '['):
                        errors.append({
                            'line': line_num,
                            'column': col_num,
                            'message': f'Mismatched bracket: "{opening_char}" at line {opening_line} vs "{char}" at line {line_num}',
                            'line_content': line.rstrip(),
                            'suggestion': f'Change "{char}" to match "{opening_char}" or fix the opening bracket'
                        })
    
    # Check for unclosed brackets
    for opening_char, line_num, col_num in bracket_stack:
        closing_char = '}' if opening_char == '{' else ']'
        errors.append({
            'line': line_num,
            'column': col_num,
            'message': f'Unclosed bracket "{opening_char}"',
            'line_content': lines[line_num - 1].rstrip() if line_num <= len(lines) else '',
            'suggestion': f'Add closing "{closing_char}" bracket'
        })
    
    return errors
    """Check for structural issues like unmatched brackets"""
    errors = []
    bracket_stack = []
    
    for line_num, line in enumerate(lines, 1):
        for col_num, char in enumerate(line, 1):
            if char in '{[':
                bracket_stack.append((char, line_num, col_num))
            elif char in '}]':
                if not bracket_stack:
                    errors.append({
                        'line': line_num,
                        'column': col_num,
                        'message': f'Unmatched closing bracket "{char}"',
                        'line_content': line.rstrip(),
                        'suggestion': f'Remove this "{char}" or add matching opening bracket'
                    })
                else:
                    opening_char, opening_line, opening_col = bracket_stack.pop()
                    if (char == '}' and opening_char != '{') or (char == ']' and opening_char != '['):
                        errors.append({
                            'line': line_num,
                            'column': col_num,
                            'message': f'Mismatched bracket: "{opening_char}" at line {opening_line} vs "{char}" at line {line_num}',
                            'line_content': line.rstrip(),
                            'suggestion': f'Change "{char}" to match "{opening_char}" or fix the opening bracket'
                        })
    
    # Check for unclosed brackets
    for opening_char, line_num, col_num in bracket_stack:
        closing_char = '}' if opening_char == '{' else ']'
        errors.append({
            'line': line_num,
            'column': col_num,
            'message': f'Unclosed bracket "{opening_char}"',
            'line_content': lines[line_num - 1].rstrip() if line_num <= len(lines) else '',
            'suggestion': f'Add closing "{closing_char}" bracket'
        })
    
    return errors

def validate_json_with_fixes(filepath):
    """Show what the file would look like with suggested fixes"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        errors = find_all_json_errors(content)
        if not errors:
            return
        
        print("\n" + "=" * 50)
        print("🔧 SUGGESTED CORRECTIONS:")
        print("=" * 50)
        
        lines = content.splitlines()
        fixed_lines = lines.copy()
        
        # Apply fixes (in reverse order to maintain line numbers)
        for error in reversed(errors):
            line_idx = error['line'] - 1
            if line_idx < len(fixed_lines):
                line = fixed_lines[line_idx]
                
                # Apply specific fixes based on error type
                if 'Invalid character' in error['message'] and 'before property name' in error['message']:
                    # Remove invalid characters before property names
                    fixed_line = re.sub(r'^(\s*)[a-zA-Z+\-*/@#$%^&()=<>!]+\s*(")', r'\1\2', line)
                    fixed_lines[line_idx] = fixed_line
                    
                elif 'Invalid character' in error['message'] and 'in JSON' in error['message']:
                    # Remove standalone invalid characters
                    fixed_line = re.sub(r'^(\s*)[+\-*/@#$%^&()=<>!]+\s*', r'\1', line)
                    fixed_lines[line_idx] = fixed_line
        
        # Show the corrected version
        print("Here's what your JSON should look like:")
        print("-" * 30)
        for i, line in enumerate(fixed_lines, 1):
            print(f"{i:2}: {line}")
        
        # Try to validate the corrected version
        try:
            corrected_content = '\n'.join(fixed_lines)
            json.loads(corrected_content)
            print("\n✅ The corrected version is valid JSON!")
        except json.JSONDecodeError as e:
            print(f"\n⚠️  The corrected version still has issues: {e.msg}")
            
    except Exception as e:
        print(f"Error generating corrections: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python checkJson.py <json_file>")
        print("Example: python checkJson.py test.json")
    else:
        filepath = sys.argv[1]
        print(f"🔍 Checking JSON file: {filepath}")
        print("=" * 40)
        
        check_json_file(filepath)
        validate_json_with_fixes(filepath)