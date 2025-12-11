#!/bin/bash
# Quick fix for nested try/except in protobuf files
# Run this if you see "IndentationError: expected an indented block"

echo "Fixing nested try/except blocks in protobuf files..."

for file in services/common_lib/protos_generated/*_pb2.py; do
    if [ -f "$file" ]; then
        # Fix the nested try structure - replace nested try with single try
        python3 << EOF
import re

with open("$file", 'r') as f:
    content = f.read()

# Fix nested try blocks
content = re.sub(
    r'try:\s+try:\s+from google\.protobuf import runtime_version as _runtime_version\s+except ImportError:\s+_runtime_version = None\s+except ImportError:\s+_runtime_version = None',
    'try:\n    from google.protobuf import runtime_version as _runtime_version\nexcept ImportError:\n    _runtime_version = None',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Also fix if the structure is slightly different
content = re.sub(
    r'try:\n    try:\n    from google\.protobuf import runtime_version',
    'try:\n    from google.protobuf import runtime_version',
    content
)

# Remove duplicate except blocks
content = re.sub(
    r'except ImportError:\s+_runtime_version = None\s+except ImportError:\s+_runtime_version = None',
    'except ImportError:\n    _runtime_version = None',
    content,
    flags=re.MULTILINE
)

with open("$file", 'w') as f:
    f.write(content)
EOF
        echo "✅ Fixed: $file"
    fi
done

echo ""
echo "✅ All files fixed!"
echo "You can now run: cd backend && python3 app.py"

