"""
Fix indentation errors in protobuf files caused by the previous fix.
"""
import os
import sys

PROTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          "services/common_lib/protos_generated")

def fix_protobuf_file(filepath):
    """Fix the malformed try/except structure."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for the malformed try/except structure
        if line.strip() == 'try:' and i + 1 < len(lines):
            next_line = lines[i + 1]
            # Check if next line is also 'try:' (malformed)
            if next_line.strip() == 'try:':
                # This is the malformed structure, fix it
                new_lines.append('try:\n')
                i += 1  # Skip the duplicate try
                # Now find the import line and fix its indentation
                while i < len(lines):
                    current_line = lines[i]
                    if 'from google.protobuf import runtime_version' in current_line:
                        # Fix indentation - should be indented under try
                        new_lines.append('    ' + current_line.lstrip())
                    elif current_line.strip().startswith('except ImportError:'):
                        new_lines.append(current_line)
                    elif '_runtime_version = None' in current_line and not current_line.strip().startswith('#'):
                        # Make sure it's properly indented
                        if 'except' in lines[i-1] if i > 0 else False:
                            new_lines.append('    ' + current_line.lstrip())
                        else:
                            new_lines.append(current_line)
                    else:
                        new_lines.append(current_line)
                    i += 1
                    # Stop when we've processed the except block
                    if i < len(lines) and 'from google.protobuf import symbol_database' in lines[i]:
                        break
                continue
        
        new_lines.append(line)
        i += 1
    
    # Write the fixed content
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    print(f"✅ Fixed: {filepath}")

def main():
    pb2_files = [f for f in os.listdir(PROTOS_DIR) if f.endswith('_pb2.py')]
    
    print(f"Fixing {len(pb2_files)} protobuf files...")
    print()
    
    for filename in pb2_files:
        filepath = os.path.join(PROTOS_DIR, filename)
        fix_protobuf_file(filepath)
    
    print(f"\n✅ Fixed {len(pb2_files)} files")

if __name__ == '__main__':
    main()

