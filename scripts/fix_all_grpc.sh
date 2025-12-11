#!/bin/bash
# Fix all gRPC compatibility issues
# Run this if you regenerate protobuf files or encounter gRPC errors

echo "Fixing gRPC compatibility issues..."
echo ""

# First fix nested try/except blocks in protobuf files
echo "1. Fixing protobuf nested try/except blocks..."
for file in services/common_lib/protos_generated/*_pb2.py; do
    if [ -f "$file" ]; then
        # Replace nested try structure
        sed -i '9,15s/^    try:$/try:/' "$file" 2>/dev/null
        sed -i '10,15s/^    from google.protobuf import runtime_version/    from google.protobuf import runtime_version/' "$file" 2>/dev/null
        sed -i '/^    try:$/,/^    except ImportError:$/{/^    try:$/d; /^    except ImportError:$/{N; s/^    except ImportError:\n    _runtime_version = None\n    except ImportError:\n    _runtime_version = None/    except ImportError:\n    _runtime_version = None/}}' "$file" 2>/dev/null
    fi
done

python3 scripts/fix_protobuf_imports.py
python3 scripts/fix_grpc_final.py
python3 scripts/fix_grpc_registered_method.py

echo ""
echo "✅ All fixes applied!"
echo "You can now run your scripts."

