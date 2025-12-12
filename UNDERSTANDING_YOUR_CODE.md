# Understanding Your Code Change

## What You Changed

You modified the `RegisterRider` method in `services/rider_service/app.py` to use PostgreSQL's `ON CONFLICT DO UPDATE` clause.

## The Code (Fixed Version)

```python
def RegisterRider(self, request, context):
    profile = request.profile
    rid = profile.rider_id or f"rider-{int(time.time()*1000)}"

    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO riders (rider_id, user_id, name, phone)
                VALUES (:rid, :uid, :name, :phone)
                ON CONFLICT (rider_id) DO UPDATE
                SET user_id = EXCLUDED.user_id,
                    name = EXCLUDED.name,
                    phone = EXCLUDED.phone
            """), {
                "rid": rid,
                "uid": profile.user_id,
                "name": profile.name,
                "phone": profile.phone,
            })
        logger.info("Registered rider: %s", rid)
        return rider_pb2.RegisterRiderResponse(rider_id=rid, ok=True)
    except Exception as e:
        logger.exception("RegisterRider error: %s", e)
        return rider_pb2.RegisterRiderResponse(ok=False)
```

## What `ON CONFLICT DO UPDATE` Does

### Before (Original Code)
```sql
INSERT INTO riders(rider_id, user_id, name, phone)
VALUES(:rid, :uid, :name, :phone)
```
- **Problem**: If `rider_id` already exists, PostgreSQL throws an error
- **Result**: Registration fails with duplicate key error

### After (Your Change)
```sql
INSERT INTO riders (rider_id, user_id, name, phone)
VALUES (:rid, :uid, :name, :phone)
ON CONFLICT (rider_id) DO UPDATE
SET user_id = EXCLUDED.user_id,
    name = EXCLUDED.name,
    phone = EXCLUDED.phone
```
- **If rider_id is NEW**: Creates a new record
- **If rider_id EXISTS**: Updates the existing record instead of erroring
- **Result**: Registration always succeeds (creates or updates)

## Why This Is Useful

1. **Idempotent Operations**: Can call RegisterRider multiple times safely
2. **Update Rider Info**: If rider re-registers, their info gets updated
3. **No Errors**: Prevents duplicate key constraint violations
4. **Better UX**: Users can re-register without issues

## What Was Wrong Before

Your original change had syntax errors:
- Missing `self` parameter
- Wrong method signature (not a proper gRPC method)
- Incorrect indentation
- Missing proper error handling

The fixed version maintains the gRPC interface while adding your UPSERT logic.

