"""
Final fix for nested try/except blocks in all protobuf files.
This ensures all files have the correct structure.
"""
import os
import sys

PROTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          "services/common_lib/protos_generated")

def fix_file(filepath):
    """Fix nested try/except structure."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    fixed = False
    
    while i < len(lines):
        line = lines[i]
        
        # Check for the problematic pattern: try: followed by try: on next line
        if line.strip() == 'try:' and i + 1 < len(lines):
            next_line = lines[i + 1]
            if next_line.strip() == 'try:':
                # Found nested try - fix it
                fixed = True
                new_lines.append('try:\n')
                i += 2  # Skip both try lines
                
                # Now find the import line and fix its indentation
                if i < len(lines) and 'from google.protobuf import runtime_version' in lines[i]:
                    # Ensure proper indentation (4 spaces)
                    import_line = lines[i].lstrip()
                    new_lines.append('    ' + import_line)
                    i += 1
                    
                    # Handle the except blocks
                    except_count = 0
                    while i < len(lines) and except_count < 2:
                        current_line = lines[i]
                        if 'except ImportError:' in current_line:
                            new_lines.append(current_line)
                            i += 1
                            except_count += 1
                            # Get the _runtime_version = None line
                            if i < len(lines) and '_runtime_version = None' in lines[i]:
                                new_lines.append('    ' + lines[i].lstrip())
                                i += 1
                        else:
                            break
                    
                    # Skip any duplicate except blocks
                    if i < len(lines) and 'except ImportError:' in lines[i]:
                        i += 1
                    if i < len(lines) and '_runtime_version = None' in lines[i]:
                        i += 1
                    
                    continue
        
        new_lines.append(line)
        i += 1
    
    if fixed:
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        print(f"✅ Fixed: {filepath}")
        return True
    else:
        # Double check - maybe the structure is different
        content = ''.join(lines)
        if 'try:\n    try:' in content:
            # Use regex replacement
            import re
            content = re.sub(
                r'try:\s+try:\s+from google\.protobuf import runtime_version as _runtime_version\s+except ImportError:\s+_runtime_version = None\s+except ImportError:\s+_runtime_version = None',
                'try:\n    from google.protobuf import runtime_version as _runtime_version\nexcept ImportError:\n    _runtime_version = None',
                content
            )
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Fixed (regex): {filepath}")
            return True
        
        print(f"⚠️  No changes needed: {filepath}")
        return False

def main():
    if not os.path.exists(PROTOS_DIR):
        print(f"❌ Directory not found: {PROTOS_DIR}")
        return 1
    
    pb2_files = [f for f in os.listdir(PROTOS_DIR) if f.endswith('_pb2.py')]
    
    print(f"Fixing {len(pb2_files)} protobuf files...")
    print()
    
    fixed_count = 0
    for filename in pb2_files:
        filepath = os.path.join(PROTOS_DIR, filename)
        if fix_file(filepath):
            fixed_count += 1
    
    print()
    print(f"✅ Fixed {fixed_count} out of {len(pb2_files)} files")
    return 0

if __name__ == '__main__':
    sys.exit(main())

