"""
Final fix for grpc version checks - properly comments out the entire block.
"""
import os
import sys

PROTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          "services/common_lib/protos_generated")

def fix_grpc_file(filepath):
    """Properly comment out the version check block."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is the version check block
        if 'if _version_not_supported:' in line:
            # Comment out the if statement
            new_lines.append('# Version check disabled for compatibility\n')
            new_lines.append('# ' + line)
            i += 1
            
            # Comment out everything until the closing paren
            paren_count = 0
            found_open = False
            while i < len(lines):
                next_line = lines[i]
                # Count parentheses
                paren_count += next_line.count('(') - next_line.count(')')
                if '(' in next_line:
                    found_open = True
                
                # Comment out this line
                new_lines.append('# ' + next_line)
                i += 1
                
                # Stop when we've closed all parentheses
                if found_open and paren_count <= 0 and ')' in next_line:
                    break
            
            # Add a pass statement to make it valid Python
            new_lines.append('if False:  # Disabled version check\n')
            new_lines.append('    pass\n')
            continue
        else:
            new_lines.append(line)
        
        i += 1
    
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    print(f"✅ Fixed: {filepath}")

def main():
    grpc_files = [f for f in os.listdir(PROTOS_DIR) if f.endswith('_pb2_grpc.py')]
    
    for filename in grpc_files:
        filepath = os.path.join(PROTOS_DIR, filename)
        fix_grpc_file(filepath)
    
    print(f"\n✅ Fixed {len(grpc_files)} files")

if __name__ == '__main__':
    main()

