# Map Legend - Understanding the Frontend

## Map Elements

### 🟦 Blue Markers with Circles
**What**: Stations (Pickup Points)
- **Icon**: Standard blue marker
- **Circle**: 200m radius (pickup zone)
- **Click**: Selects station, shows details
- **Example**: ST101 (MG Road), ST102 (Cubbon Park)

### 🚗 Red Car Icons
**What**: Active Drivers with Trips
- **Icon**: Custom car emoji in colored circle
- **Color Meanings**:
  - 🔴 **Red**: Driver has scheduled trip (waiting to start)
  - 🟢 **Green**: Driver has active trip (en route)
  - ⚪ **Gray**: Driver finished trip (completed)
- **Click**: Shows trip details, riders, route, progress
- **Movement**: Updates every 2 seconds for active trips

### 🟠 Orange Dashed Lines
**What**: Scheduled Trip Routes
- **Style**: Dashed orange line
- **Meaning**: Trip is matched but not started yet
- **Shows**: Path from origin station to destination
- **Action**: Click "Start Trip" button to activate

### 🟢 Green Solid Lines
**What**: Active Trip Routes
- **Style**: Thick green solid line
- **Meaning**: Trip is in progress
- **Shows**: Current route from origin to destination
- **Animation**: Driver marker moves along this route

### 🔴 Red Circle (Large)
**What**: Selected Station Highlight
- **Appears**: When you click a station
- **Purpose**: Highlights the selected station
- **Radius**: 200m (same as station pickup zone)

## Sidebar Panels

### 📍 Stations Panel
- Lists all available stations
- Click station to select it
- Selected station highlighted in green
- Shows station ID, name, coordinates

### 🚕 Active Trips Panel
- Shows all non-completed trips
- **Status Badges**:
  - ⏳ **Scheduled** (Yellow): Matched, waiting to start
  - 🚗 **Active** (Green): Trip in progress
  - ✅ **Completed** (Gray): Trip finished (hidden from active list)
- **Actions**:
  - "Start Trip" button for scheduled trips
  - "Complete Trip" button for active trips

### 🎮 Quick Actions Panel
- Register new riders/drivers
- Request pickups at selected station
- Refresh data manually

## Notifications

### 🎉 Green Notifications
**When**: New match created
**Shows**: Driver ID, number of riders, station
**Duration**: 8 seconds (auto-dismiss)
**Action**: Click × to dismiss early

### ✅ Blue Notifications
**When**: Trip completed
**Shows**: Driver ID, destination
**Duration**: 8 seconds (auto-dismiss)

## Trip Status Flow

1. **Scheduled** (⏳ Yellow)
   - Match created
   - Driver and riders matched
   - Waiting to start
   - **Action**: Click "Start Trip"

2. **Active** (🚗 Green)
   - Trip started
   - Driver en route
   - Shows progress
   - **Action**: Click "Complete Trip"

3. **Completed** (✅ Gray)
   - Trip finished
   - Driver seats reset
   - Hidden from active list

## Tips for Simulation

1. **Run Demo**: `python3 scripts/demo_simulation.py`
2. **Watch Notifications**: Top-right corner for match events
3. **Check Map**: See drivers (red cars) and routes (colored lines)
4. **Manage Trips**: Use buttons to start/complete trips
5. **Refresh**: Auto-refreshes every 5 seconds, or click "Refresh Trips"

## Common Questions

**Q: Why are all trips "scheduled"?**
A: They need to be manually started. Click "Start Trip" button to change status to "active".

**Q: What are the red car icons?**
A: They're drivers who have active trips. Red = scheduled, Green = active.

**Q: Why don't I see routes?**
A: Routes only show for scheduled/active trips. Completed trips hide routes.

**Q: How do I see trip progress?**
A: Click on a red car icon (driver marker) to see progress percentage.

**Q: Notifications not showing?**
A: Make sure backend is running and trips are being created. Check browser console (F12).

