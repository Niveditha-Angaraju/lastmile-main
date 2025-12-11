"""
Fix protobuf imports in generated files to work with protobuf 5.x
This patches the generated files to remove strict version checking.
"""
import os
import re
import sys

PROTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          "services/common_lib/protos_generated")

def fix_protobuf_file(filepath):
    """Remove or comment out runtime_version validation."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove the ValidateProtobufRuntimeVersion call
    # This is a multi-line pattern
    pattern1 = r'_runtime_version\.ValidateProtobufRuntimeVersion\([^)]+\)'
    content = re.sub(pattern1, '# Version check disabled for compatibility', content, flags=re.MULTILINE)
    
    # Also try to make runtime_version import optional
    if 'from google.protobuf import runtime_version' in content:
        # Replace with try/except
        old_import = 'from google.protobuf import runtime_version as _runtime_version'
        new_import = '''try:
    from google.protobuf import runtime_version as _runtime_version
except ImportError:
    _runtime_version = None'''
        
        content = content.replace(old_import, new_import)
        
        # Wrap the validation call
        if '_runtime_version.ValidateProtobufRuntimeVersion' in content:
            # Find and comment out the validation
            lines = content.split('\n')
            new_lines = []
            skip_next = False
            for i, line in enumerate(lines):
                if '_runtime_version.ValidateProtobufRuntimeVersion' in line:
                    # Comment out this line and the next few lines until closing paren
                    new_lines.append('# ' + line)
                    # Count open and close parens
                    open_count = line.count('(') - line.count(')')
                    skip_next = open_count > 0
                elif skip_next:
                    new_lines.append('# ' + line)
                    open_count = line.count('(') - line.count(')')
                    if open_count <= 0 and ')' in line:
                        skip_next = False
                else:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath}")
        return True
    else:
        print(f"⚠️  No changes needed: {filepath}")
        return False

def main():
    if not os.path.exists(PROTOS_DIR):
        print(f"❌ Directory not found: {PROTOS_DIR}")
        return 1
    
    pb2_files = [f for f in os.listdir(PROTOS_DIR) if f.endswith('_pb2.py')]
    
    if not pb2_files:
        print(f"❌ No _pb2.py files found in {PROTOS_DIR}")
        return 1
    
    print(f"Found {len(pb2_files)} protobuf files to fix...")
    print()
    
    fixed_count = 0
    for filename in pb2_files:
        filepath = os.path.join(PROTOS_DIR, filename)
        if fix_protobuf_file(filepath):
            fixed_count += 1
    
    print()
    print(f"✅ Fixed {fixed_count} out of {len(pb2_files)} files")
    print()
    print("Now try running your scripts again!")
    return 0

if __name__ == '__main__':
    sys.exit(main())

