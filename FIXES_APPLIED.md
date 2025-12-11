# Protobuf and gRPC Compatibility Fixes Applied

## Issues
1. **Protobuf**: The generated protobuf files were created with protoc 6.31.1, but protobuf 6.x is not available via pip for Python 3.8. This caused import errors.
2. **gRPC**: The generated gRPC files require grpcio>=1.76.0, but only up to 1.70.0 is available for Python 3.8.

## Solutions
1. **Protobuf fix** (`scripts/fix_protobuf_imports.py`): 
   - Made `runtime_version` import optional (with try/except)
   - Commented out the strict version validation

2. **gRPC fix** (`scripts/fix_grpc_final.py`):
   - Commented out the version check that raises RuntimeError
   - Allows using grpcio 1.60.0+ instead of requiring 1.76.0+

3. **gRPC _registered_method fix** (`scripts/fix_grpc_registered_method.py`):
   - Removed `_registered_method=True` parameter from all `unary_unary()` and `unary_stream()` calls
   - This parameter is not supported in grpcio 1.60.0 (was added in newer versions)

## Changes Made

1. **Updated `backend/requirements.txt`**:
   - Changed protobuf requirement to `>=5.26.0` (compatible with Python 3.8)

2. **Fixed all protobuf generated files** (8 files):
   - `driver_pb2.py`, `rider_pb2.py`, `trip_pb2.py`, `station_pb2.py`
   - `location_pb2.py`, `matching_pb2.py`, `notification_pb2.py`, `user_pb2.py`

3. **Fixed all gRPC generated files** (8 files):
   - `driver_pb2_grpc.py`, `rider_pb2_grpc.py`, `trip_pb2_grpc.py`, `station_pb2_grpc.py`
   - `location_pb2_grpc.py`, `matching_pb2_grpc.py`, `notification_pb2_grpc.py`, `user_pb2_grpc.py`
   - Removed version checks and `_registered_method` parameters

4. **Created helper scripts**:
   - `scripts/fix_protobuf_imports.py` - Can be re-run if needed
   - `scripts/fix_grpc_final.py` - Can be re-run if needed
   - `scripts/fix_grpc_registered_method.py` - Can be re-run if needed

## Usage

All scripts should now work with `python3`:

```bash
# Test imports
python3 -c "from services.common_lib.protos_generated import driver_pb2; print('OK')"

# Run demo
python3 scripts/demo_simulation.py

# Run tests
python3 tests/e2e_test_k8s.py

# Run simulations
python3 scripts/simulate_driver_k8s.py --driver-id drv-1 --station-id ST101
python3 scripts/simulate_rider_k8s.py --rider-id rider-1 --station-id ST101
```

## Notes

1. **If you regenerate the protobuf files**, you may need to run the fix scripts again:
   ```bash
   python3 scripts/fix_protobuf_imports.py
   python3 scripts/fix_grpc_imports.py
   ```

2. **To avoid these issues in the future**, when regenerating protobuf files:
   - Use protoc 5.x to match the Python protobuf library version
   - Use grpcio-tools 1.60.0 or lower to match available grpcio versions

3. **All scripts now use `python3`** instead of `python`:
   ```bash
   python3 scripts/demo_simulation.py
   python3 tests/e2e_test_k8s.py
   ```

