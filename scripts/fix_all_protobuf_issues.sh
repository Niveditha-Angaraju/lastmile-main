#!/bin/bash
# Fix all protobuf compatibility issues
# This script fixes all known protobuf/gRPC compatibility problems

echo "Fixing all protobuf and gRPC compatibility issues..."
echo ""

# Fix nested try/except blocks first (most critical)
echo "1. Fixing nested try/except blocks..."
for file in services/common_lib/protos_generated/*_pb2.py; do
    if [ -f "$file" ]; then
        # Fix the nested try structure
        sed -i '/^try:$/{N;N;N;N;N;N;N;N;/try:\n    try:/{s/try:\n    try:/try:/; s/\n    from google.protobuf import runtime_version as _runtime_version/\n    from google.protobuf import runtime_version as _runtime_version/; s/\nexcept ImportError:\n    _runtime_version = None\nexcept ImportError:\n    _runtime_version = None/\nexcept ImportError:\n    _runtime_version = None/}}' "$file"
    fi
done

# Fix any remaining nested try blocks manually
python3 << 'EOF'
import os
import re

PROTOS_DIR = "services/common_lib/protos_generated"

for filename in os.listdir(PROTOS_DIR):
    if filename.endswith('_pb2.py'):
        filepath = os.path.join(PROTOS_DIR, filename)
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Fix nested try blocks
        old_pattern = r'try:\s+try:\s+from google\.protobuf import runtime_version'
        new_pattern = 'try:\n    from google.protobuf import runtime_version'
        content = re.sub(old_pattern, new_pattern, content)
        
        # Fix duplicate except blocks
        content = re.sub(
            r'except ImportError:\s+_runtime_version = None\s+except ImportError:\s+_runtime_version = None',
            'except ImportError:\n    _runtime_version = None',
            content
        )
        
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath}")
EOF

echo ""
echo "2. Running other fix scripts..."
python3 scripts/fix_protobuf_imports.py
python3 scripts/fix_grpc_final.py
python3 scripts/fix_grpc_registered_method.py

echo ""
echo "✅ All fixes applied!"
echo "You can now run your scripts."

