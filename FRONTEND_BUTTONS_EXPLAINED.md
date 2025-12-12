# Frontend Buttons Explained

## Start Trip Button (▶️ Start Trip)

**What it does:**
- Changes trip status from `scheduled` → `active`
- Triggers car movement animation
- Updates route color from orange (dashed) to green (solid)
- Starts progress tracking for the trip

**When to use:**
- After a match is created (trip is `scheduled`)
- When you want to simulate the driver starting the trip
- Before the car will start moving on the map

**What happens:**
1. Backend updates trip status to `active`
2. Frontend detects status change
3. Car icon changes from red to green
4. Route line changes from orange dashed to green solid
5. Car starts moving along the route (progress increments)

## Complete Trip Button (✅ Complete Trip)

**What it does:**
- Changes trip status from `active` → `completed`
- Removes trip from active trips list
- Resets driver's available seats (in matching service)
- Allows driver to pick up new riders

**When to use:**
- When trip is `active` and you want to finish it
- To simulate driver dropping off riders
- To free up driver seats for new matches

**What happens:**
1. Backend updates trip status to `completed`
2. Matching service receives `trip.updated` event
3. Driver seats reset to default (5 seats)
4. Trip disappears from active trips panel
5. Car icon and route disappear from map

## Why Cars Don't Move Until You Click "Start Trip"

**Current Behavior:**
- Trips are created with status `scheduled` (waiting to start)
- Cars stay at origin station (progress = 0)
- Routes show as orange dashed lines

**To See Movement:**
1. Find a `scheduled` trip in the sidebar
2. Click "▶️ Start Trip" button
3. Watch the car move along the green route

**This is by design:**
- In real system, trips start when driver picks up riders
- Frontend simulates this with manual start button
- Allows you to control when trips begin

## How Concurrent Riders Are Handled

**Multiple Riders at Same Station:**
1. All riders publish requests to `rider.requests` queue
2. Matching service stores them in `station_waiting_riders[station_id]`
3. When driver arrives, matching service:
   - Checks available seats
   - Matches up to `seats` riders from waiting list
   - Creates one trip with all matched riders
   - Removes matched riders from waiting list

**Example:**
- 5 riders request at Station A
- Driver arrives with 5 seats
- All 5 riders matched in single trip
- Trip shows: `rider_ids: [rider1, rider2, rider3, rider4, rider5]`

**If More Riders Than Seats:**
- Driver has 3 seats
- 5 riders request
- Only first 3 riders matched
- Remaining 2 stay in waiting list
- Next driver can pick them up

## Troubleshooting

### Cars Not Moving
- **Check:** Is trip status `active`? (Should be green badge)
- **Fix:** Click "▶️ Start Trip" button
- **Verify:** Car icon should be green, route should be green solid line

### Routes Not Showing
- **Check:** Do trips have `origin_station` and `destination`?
- **Check:** Are trips `scheduled` or `active`? (completed trips hide routes)
- **Fix:** Refresh trips or check browser console for errors

### Buttons Not Working
- **Check:** Is backend running on port 8081?
- **Check:** Browser console (F12) for errors
- **Fix:** Restart backend if needed

### Too Many Trips Showing
- **Fixed:** Now only shows trips from last 2 hours
- **Fixed:** Limited to 20 most recent trips
- **Fixed:** Completed trips filtered out

