# Complete Simulation Guide

## How to Run a Full Simulation

### Step 1: Start All Services

**Terminal 1: Port Forwarding**
```bash
cd /home/niveditha/lastmile-main
./scripts/port_forward_services.sh
```

**Terminal 2: Backend**
```bash
cd /home/niveditha/lastmile-main/backend
python3 app.py
```

**Terminal 3: Frontend**
```bash
cd /home/niveditha/lastmile-main/frontend
npm run dev
```

### Step 2: Run Demo Simulation

**Terminal 4: Demo**
```bash
cd /home/niveditha/lastmile-main
python3 scripts/demo_simulation.py
```

### Step 3: Watch the Frontend

Open http://localhost:3000 in your browser

**What You'll See**:

1. **Notifications** (Top-right)
   - 🎉 Green notification when match is created
   - ✅ Blue notification when trip completes
   - Auto-dismisses after 8 seconds

2. **Map**
   - 🟦 **Blue markers**: Stations (ST101, ST102, ST103)
   - 🚗 **Red car icons**: Active drivers
   - 🟠 **Orange dashed lines**: Scheduled trip routes
   - 🟢 **Green solid lines**: Active trip routes

3. **Active Trips Panel** (Left sidebar)
   - Shows all non-completed trips
   - Status badges: ⏳ Scheduled, 🚗 Active
   - Buttons: "Start Trip", "Complete Trip"

## Understanding the Map

### Red Car Icons (🚗) = Drivers
- **Red circle**: Driver has scheduled trip (waiting)
- **Green circle**: Driver has active trip (en route)
- **Click**: See trip details, riders, progress

### Colored Lines = Routes
- **Orange dashed**: Scheduled trip (not started)
- **Green solid**: Active trip (in progress)
- Shows path from origin station to destination

### Blue Markers = Stations
- Click to select
- Red circle appears when selected

## Trip Status Flow

1. **Match Created** → Trip status: `scheduled` (⏳ Yellow)
   - Notification appears
   - Orange dashed route shown
   - Red driver marker appears

2. **Click "Start Trip"** → Status: `active` (🚗 Green)
   - Route turns green solid
   - Driver marker turns green
   - Driver starts moving along route

3. **Click "Complete Trip"** → Status: `completed` (✅ Gray)
   - Trip disappears from active list
   - Driver seats reset
   - Notification appears

## Interactive Features

### Start a Trip
1. Find a scheduled trip in the sidebar
2. Click "▶️ Start Trip" button
3. Watch status change to "active"
4. See route turn green and driver start moving

### Complete a Trip
1. Find an active trip
2. Click "✅ Complete Trip" button
3. Confirm the action
4. Trip disappears, driver seats reset

### View Trip Details
- Click on a red/green car icon on the map
- See: Driver ID, Trip ID, Status, Riders, Route, Progress

## Tips for Best Simulation

1. **Run demo first**: `python3 scripts/demo_simulation.py`
2. **Watch notifications**: They appear when matches are created
3. **Start trips manually**: Click "Start Trip" to see active status
4. **Complete trips**: Click "Complete Trip" to reset driver seats
5. **Refresh**: Auto-refreshes every 5 seconds, or click "Refresh Trips"

## What Each Element Means

| Element | Meaning | Color/Icon |
|---------|---------|------------|
| Blue Marker | Station (pickup point) | Blue pin |
| Red Car Icon | Driver with scheduled trip | 🚗 in red circle |
| Green Car Icon | Driver with active trip | 🚗 in green circle |
| Orange Dashed Line | Scheduled trip route | Orange, dashed |
| Green Solid Line | Active trip route | Green, solid |
| Red Circle | Selected station | Red highlight |
| Yellow Badge | Scheduled trip | ⏳ Yellow |
| Green Badge | Active trip | 🚗 Green |

## Troubleshooting

### Notifications Not Showing
- Check browser console (F12) for errors
- Make sure backend is running
- Verify trips are being created

### All Trips Show "Scheduled"
- This is normal! Click "Start Trip" to change status
- Or trips will auto-start in a real system

### Routes Not Visible
- Routes only show for scheduled/active trips
- Completed trips hide routes
- Make sure trips have origin and destination

### Red Car Icons Not Moving
- They only move for "active" trips
- Start a trip first to see movement
- Updates every 2 seconds

## Summary

**Frontend is now fully functional with**:
- ✅ Working notifications
- ✅ Correct status display
- ✅ Proper route visualization
- ✅ Clear driver markers
- ✅ Trip management buttons
- ✅ Better UI overall

Enjoy your simulation! 🚗🎉

