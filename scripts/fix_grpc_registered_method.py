"""
Fix gRPC generated files to remove _registered_method parameter
which is not supported in grpcio 1.60.0
"""
import os
import re
import sys

PROTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          "services/common_lib/protos_generated")

def fix_grpc_file(filepath):
    """Remove _registered_method=True parameter from unary_unary/unary_stream calls."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match _registered_method=True parameter
    # This can appear in different positions, so we need to handle it carefully
    
    # Remove _registered_method=True from method calls
    # Pattern 1: , _registered_method=True) at end
    content = re.sub(r',\s*_registered_method=True\)', ')', content)
    
    # Pattern 2: _registered_method=True, in middle
    content = re.sub(r',\s*_registered_method=True\s*,', ',', content)
    
    # Pattern 3: _registered_method=True at start of parameters
    content = re.sub(r'\(\s*_registered_method=True\s*,', '(', content)
    
    # Pattern 4: _registered_method=True as only parameter
    content = re.sub(r'\(\s*_registered_method=True\s*\)', '()', content)
    
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
    
    grpc_files = [f for f in os.listdir(PROTOS_DIR) if f.endswith('_pb2_grpc.py')]
    
    if not grpc_files:
        print(f"❌ No _pb2_grpc.py files found in {PROTOS_DIR}")
        return 1
    
    print(f"Found {len(grpc_files)} grpc files to fix...")
    print()
    
    fixed_count = 0
    for filename in grpc_files:
        filepath = os.path.join(PROTOS_DIR, filename)
        if fix_grpc_file(filepath):
            fixed_count += 1
    
    print()
    print(f"✅ Fixed {fixed_count} out of {len(grpc_files)} files")
    print()
    print("Now try running your scripts again!")
    return 0

if __name__ == '__main__':
    sys.exit(main())

