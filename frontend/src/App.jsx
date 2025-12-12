import React, { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet'
import L from 'leaflet'
import axios from 'axios'
import { TripVisualization } from './components/TripVisualization'
import { MatchNotifications } from './components/MatchNotifications'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8081'

function App() {
  const [stations, setStations] = useState([])
  const [drivers, setDrivers] = useState([])
  const [riders, setRiders] = useState([])
  const [trips, setTrips] = useState([])
  const [matches, setMatches] = useState([])
  const [selectedStation, setSelectedStation] = useState(null)
  const [selectedDriver, setSelectedDriver] = useState(null)
  const [mapCenter, setMapCenter] = useState([12.9716, 77.5946]) // Bangalore default
  const [autoRefresh, setAutoRefresh] = useState(true)
  const wsRef = useRef(null)

  // Load initial data
  useEffect(() => {
    loadStations()
    loadTrips()
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadStations()
        loadTrips()
      }, 5000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    // Connect to WebSocket for real-time match events
    // Note: You'll need to implement a WebSocket server that publishes match.found events
    // For now, we'll use polling

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const loadStations = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/stations`)
      if (response.data && response.data.stations) {
        setStations(response.data.stations)
        if (response.data.stations.length > 0) {
          const first = response.data.stations[0]
          setMapCenter([first.lat, first.lng])
        }
      }
    } catch (error) {
      console.error('Error loading stations:', error)
    }
  }

  const loadTrips = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/trips`)
      if (response.data && response.data.trips) {
        // Filter out completed trips and only show recent/active ones
        const now = Date.now()
        const oneHourAgo = now - 3600000 // 1 hour in ms
        
        const filteredTrips = response.data.trips
          .filter(t => {
            // Show if not completed
            if (t.status !== 'completed') return true
            // Or if completed but recent (within last hour)
            if (t.end_time && t.end_time > oneHourAgo) return true
            return false
          })
          .sort((a, b) => (b.start_time || 0) - (a.start_time || 0)) // Newest first
        
        setTrips(filteredTrips)
      }
    } catch (error) {
      console.error('Error loading trips:', error)
    }
  }

  const requestPickup = async (riderId, stationId, destination) => {
    try {
      const response = await axios.post(`${API_BASE}/api/riders/request-pickup`, {
        rider_id: riderId,
        station_id: stationId,
        destination: destination
      })
      alert(`Pickup requested: ${response.data.request_id}`)
      loadTrips()
    } catch (error) {
      console.error('Error requesting pickup:', error)
      alert('Failed to request pickup')
    }
  }

  const registerRider = async (name, phone) => {
    try {
      const riderId = `rider-${Date.now()}`
      const response = await axios.post(`${API_BASE}/api/riders/register`, {
        rider_id: riderId,
        name: name,
        phone: phone
      })
      alert(`Rider registered: ${riderId}`)
      return riderId
    } catch (error) {
      console.error('Error registering rider:', error)
      alert('Failed to register rider')
      return null
    }
  }

  const registerDriver = async (name, phone, vehicleNo) => {
    try {
      const driverId = `drv-${Date.now()}`
      const response = await axios.post(`${API_BASE}/api/drivers/register`, {
        driver_id: driverId,
        name: name,
        phone: phone,
        vehicle_no: vehicleNo
      })
      alert(`Driver registered: ${driverId}`)
      return driverId
    } catch (error) {
      console.error('Error registering driver:', error)
      alert('Failed to register driver')
      return null
    }
  }

  const handleNewMatch = (trip) => {
    // Center map on trip origin station
    const station = stations.find(s => s.station_id === trip.origin_station)
    if (station) {
      setMapCenter([station.lat, station.lng])
    }
  }

  return (
    <div className="app">
      <MatchNotifications trips={trips} onNewMatch={handleNewMatch} />
      <header className="app-header">
        <h1>🚗 LastMile - Ride Matching System</h1>
        <div className="controls">
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh (5s)
          </label>
          <button onClick={loadStations}>Refresh Stations</button>
          <button onClick={loadTrips}>Refresh Trips</button>
        </div>
      </header>

      <div className="app-content">
        <div className="sidebar">
          <div className="panel">
            <h2>📍 Stations ({stations.length})</h2>
            <div className="station-list">
              {stations.map((station) => (
                <div
                  key={station.station_id}
                  className={`station-item ${selectedStation?.station_id === station.station_id ? 'selected' : ''}`}
                  onClick={() => setSelectedStation(station)}
                >
                  <strong>{station.station_id}</strong>
                  <div>{station.name}</div>
                  <div className="coords">{station.lat.toFixed(4)}, {station.lng.toFixed(4)}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <h2>🚕 Active Trips ({trips.filter(t => {
              if (!t.status || t.status === 'completed') return false
              const now = Date.now()
              const twoHoursAgo = now - 7200000
              if (t.start_time && t.start_time < twoHoursAgo) return false
              return true
            }).length})</h2>
            <div className="trip-list">
              {trips.length === 0 ? (
                <div className="trip-item" style={{fontStyle: 'italic', color: '#6c757d'}}>
                  No trips yet. Run a simulation to see matches!
                </div>
              ) : (
                trips
                  .filter(t => {
                    // Only show scheduled or active trips
                    if (!t.status || t.status === 'completed') return false
                    // Limit to recent trips (within last 2 hours)
                    const now = Date.now()
                    const twoHoursAgo = now - 7200000
                    if (t.start_time && t.start_time < twoHoursAgo) return false
                    return true
                  })
                  .sort((a, b) => (b.start_time || 0) - (a.start_time || 0)) // Newest first
                  .slice(0, 20) // Limit to 20 most recent
                  .map((trip) => {
                    const statusIcon = {
                      'scheduled': '⏳',
                      'active': '🚗',
                      'completed': '✅'
                    }[trip.status] || '❓'
                    
                    return (
                      <div key={trip.trip_id} className="trip-item">
                        <div className="trip-header">
                          <strong>{statusIcon} Trip: {trip.trip_id.substring(0, 12)}...</strong>
                          <span className={`status-badge status-${trip.status}`}>{trip.status}</span>
                        </div>
                        <div className="trip-details">
                          <div><strong>Driver:</strong> {trip.driver_id}</div>
                          <div><strong>Riders:</strong> {trip.rider_ids?.length || 0} ({trip.rider_ids?.join(', ') || 'None'})</div>
                          <div><strong>Route:</strong> {trip.origin_station} → {trip.destination}</div>
                          {trip.start_time && (
                            <div className="trip-time">
                              <strong>Started:</strong> {new Date(trip.start_time).toLocaleTimeString()}
                            </div>
                          )}
                          {trip.seats_reserved && (
                            <div><strong>Seats:</strong> {trip.seats_reserved}</div>
                          )}
                        </div>
                        {trip.status === 'scheduled' && (
                          <button 
                            className="trip-action-btn"
                            onClick={async () => {
                              try {
                                const response = await axios.post(`${API_BASE}/api/trips/${trip.trip_id}/start`)
                                if (response.data.ok) {
                                  setTimeout(() => loadTrips(), 500)
                                }
                              } catch (e) {
                                console.error('Error starting trip:', e)
                                alert('Failed to start trip: ' + (e.response?.data?.error || e.message))
                              }
                            }}
                          >
                            ▶️ Start Trip
                          </button>
                        )}
                        {trip.status === 'active' && (
                          <button 
                            className="trip-action-btn complete-btn"
                            onClick={async () => {
                              if (!confirm(`Complete trip ${trip.trip_id.substring(0, 12)}...?`)) return
                              try {
                                const response = await axios.post(`${API_BASE}/api/trips/${trip.trip_id}/complete`)
                                if (response.data.ok) {
                                  setTimeout(() => loadTrips(), 500)
                                }
                              } catch (e) {
                                console.error('Error completing trip:', e)
                                alert('Failed to complete trip: ' + (e.response?.data?.error || e.message))
                              }
                            }}
                          >
                            ✅ Complete Trip
                          </button>
                        )}
                      </div>
                    )
                  })
              )}
            </div>
          </div>

          <div className="panel">
            <h2>🎮 Quick Actions</h2>
            <div className="action-buttons">
              <button onClick={() => {
                const name = prompt('Rider name:')
                const phone = prompt('Phone:') || '0000000000'
                if (name) registerRider(name, phone)
              }}>
                Register Rider
              </button>
              <button onClick={() => {
                const name = prompt('Driver name:')
                const phone = prompt('Phone:') || '0000000000'
                const vehicle = prompt('Vehicle No:') || 'TEST-001'
                if (name) registerDriver(name, phone, vehicle)
              }}>
                Register Driver
              </button>
              {selectedStation && (
                <button onClick={() => {
                  const riderId = prompt('Rider ID:')
                  const destination = prompt('Destination:') || 'Downtown'
                  if (riderId) requestPickup(riderId, selectedStation.station_id, destination)
                }}>
                  Request Pickup at {selectedStation.station_id}
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="map-container">
          <MapContainer
            center={mapCenter}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            {/* Station markers */}
            {stations.map((station) => (
              <Marker
                key={station.station_id}
                position={[station.lat, station.lng]}
                eventHandlers={{
                  click: () => setSelectedStation(station)
                }}
              >
                <Popup>
                  <div>
                    <strong>{station.station_id}</strong><br />
                    {station.name}<br />
                    {station.lat.toFixed(4)}, {station.lng.toFixed(4)}
                  </div>
                </Popup>
                <Circle
                  center={[station.lat, station.lng]}
                  radius={200}
                  pathOptions={{ color: 'blue', fillColor: 'blue', fillOpacity: 0.1 }}
                />
              </Marker>
            ))}

            {/* Selected station highlight */}
            {selectedStation && (
              <Circle
                center={[selectedStation.lat, selectedStation.lng]}
                radius={200}
                pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.2, weight: 3 }}
              />
            )}

            {/* Trip visualization - drivers, routes, matches */}
            <TripVisualization trips={trips} stations={stations} />
          </MapContainer>
        </div>
      </div>
    </div>
  )
}

export default App

