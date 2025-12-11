"""
Fix nested try/except blocks in protobuf files.
"""
import os
import sys

PROTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          "services/common_lib/protos_generated")

def fix_file(filepath):
    """Fix the nested try/except structure."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to find and fix the nested try/except
    # Look for: try:\n    try:\n    from google.protobuf...
    import_pattern = r'try:\s+try:\s+from google\.protobuf import runtime_version as _runtime_version\s+except ImportError:\s+_runtime_version = None\s+except ImportError:\s+_runtime_version = None'
    
    # Replace with correct structure
    replacement = '''try:
    from google.protobuf import runtime_version as _runtime_version
except ImportError:
    _runtime_version = None'''
    
    # Use a more direct approach - find the problematic block
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if we're at the start of the problematic block
        if line.strip() == 'try:' and i + 1 < len(lines):
            next_line = lines[i + 1]
            if next_line.strip() == 'try:':
                # Found nested try - fix it
                new_lines.append('try:')
                i += 2  # Skip both try lines
                # Now find and fix the import line
                if i < len(lines) and 'from google.protobuf import runtime_version' in lines[i]:
                    # Fix indentation
                    new_lines.append('    ' + lines[i].lstrip())
                    i += 1
                    # Handle except blocks
                    while i < len(lines):
                        if 'except ImportError:' in lines[i]:
                            new_lines.append(lines[i])
                            i += 1
                            if i < len(lines) and '_runtime_version = None' in lines[i]:
                                new_lines.append('    ' + lines[i].lstrip())
                                i += 1
                                # Skip duplicate except block
                                if i < len(lines) and 'except ImportError:' in lines[i]:
                                    i += 1
                                if i < len(lines) and '_runtime_version = None' in lines[i]:
                                    i += 1
                                break
                        else:
                            break
                continue
        
        new_lines.append(line)
        i += 1
    
    fixed_content = '\n'.join(new_lines)
    
    if fixed_content != content:
        with open(filepath, 'w') as f:
            f.write(fixed_content)
        print(f"✅ Fixed: {filepath}")
        return True
    else:
        print(f"⚠️  No changes: {filepath}")
        return False

def main():
    pb2_files = [f for f in os.listdir(PROTOS_DIR) if f.endswith('_pb2.py')]
    
    for filename in pb2_files:
        filepath = os.path.join(PROTOS_DIR, filename)
        fix_file(filepath)
    
    print(f"\n✅ Processed {len(pb2_files)} files")

if __name__ == '__main__':
    main()

