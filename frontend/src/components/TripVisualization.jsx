import React, { useEffect, useState, useRef } from 'react'
import { Marker, Popup, Polyline } from 'react-leaflet'
import L from 'leaflet'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8081'

// Create custom driver icon
const createDriverIcon = (status) => {
  const color = status === 'active' ? 'green' : status === 'completed' ? 'gray' : 'red'
  return L.divIcon({
    className: 'custom-driver-icon',
    html: `<div style="
      background-color: ${color};
      width: 24px;
      height: 24px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: bold;
      font-size: 12px;
    ">🚗</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  })
}

export function TripVisualization({ trips, stations }) {
  const [driverLocations, setDriverLocations] = useState({})
  const [tripRoutes, setTripRoutes] = useState({})
  const tripProgressRef = React.useRef({}) // Use ref to avoid dependency issues

  // Fetch driver locations for active trips
  useEffect(() => {
    const fetchDriverLocations = () => {
      // In a real system, this would come from location service
      // For now, we'll simulate based on trip data and progress
      const activeTrips = trips.filter(t => t.status === 'scheduled' || t.status === 'active')
      
      const locations = {}
      activeTrips.forEach(trip => {
        const originStation = stations.find(s => s.station_id === trip.origin_station)
        if (originStation) {
          // Get or initialize progress for this trip
          const tripKey = `${trip.trip_id}-${trip.driver_id}`
          if (!tripProgressRef.current[tripKey]) {
            tripProgressRef.current[tripKey] = trip.status === 'scheduled' ? 0 : 0
          }
          
          let progress = tripProgressRef.current[tripKey]
          
          // For multi-station routes, find next stations in sequence
          // Try to find a route pattern: if origin is ST101, next might be ST102, ST103, etc.
          const originIndex = stations.findIndex(s => s.station_id === trip.origin_station)
          let nextStation = null
          let destOffset = { lat: 0.005, lng: 0.005 } // Default
          
          // Try to find next station in sequence (for multi-station routes)
          if (originIndex >= 0 && originIndex < stations.length - 1) {
            nextStation = stations[originIndex + 1]
            destOffset = {
              lat: nextStation.lat - originStation.lat,
              lng: nextStation.lng - originStation.lng
            }
          } else {
            // Fallback: use destination name-based offset
            destOffset = {
              'Downtown': { lat: 0.008, lng: 0.008 },
              'Airport': { lat: -0.01, lng: 0.015 },
              'Mall': { lat: 0.006, lng: -0.006 },
            }[trip.destination] || { lat: 0.005, lng: 0.005 }
          }
          
          // Reset progress if trip just became scheduled
          if (trip.status === 'scheduled') {
            progress = 0
            tripProgressRef.current[tripKey] = 0
          }
          
          // Increment progress for active trips only
          if (trip.status === 'active' && progress < 1) {
            progress = Math.min(1, progress + 0.05) // Faster movement (5% per update)
            tripProgressRef.current[tripKey] = progress
          }
          
          // Simulate driver moving along route based on progress
          const currentLat = originStation.lat + (destOffset.lat * progress)
          const currentLng = originStation.lng + (destOffset.lng * progress)
          
          locations[trip.driver_id] = {
            lat: currentLat,
            lng: currentLng,
            trip_id: trip.trip_id,
            status: trip.status,
            progress: progress,
            nextStation: nextStation?.station_id || null
          }
        }
      })
      setDriverLocations(locations)
    }

    if (trips.length > 0 && stations.length > 0) {
      fetchDriverLocations()
      const interval = setInterval(fetchDriverLocations, 1000) // Update every 1 second for smoother movement
      return () => clearInterval(interval)
    }
  }, [trips, stations])

  // Generate routes for trips from origin to destination
  useEffect(() => {
    const routes = {}
    const activeTrips = trips.filter(t => t.status === 'scheduled' || t.status === 'active')
    
    activeTrips.forEach(trip => {
      const originStation = stations.find(s => s.station_id === trip.origin_station)
      if (originStation && trip.destination) {
        // Try to find next stations in sequence for multi-station routes
        const originIndex = stations.findIndex(s => s.station_id === trip.origin_station)
        let routePoints = []
        
        if (originIndex >= 0 && originIndex < stations.length - 1) {
          // Multi-station route: connect to next 2-3 stations
          const nextStations = stations.slice(originIndex + 1, Math.min(originIndex + 4, stations.length))
          routePoints = [
            [originStation.lat, originStation.lng],
            ...nextStations.map(s => [s.lat, s.lng])
          ]
        } else {
          // Single station route: use destination-based offset
          const destOffset = {
            'Downtown': { lat: 0.008, lng: 0.008 },
            'Airport': { lat: -0.01, lng: 0.015 },
            'Mall': { lat: 0.006, lng: -0.006 },
          }[trip.destination] || { lat: 0.005, lng: 0.005 }
          
          const destLat = originStation.lat + destOffset.lat
          const destLng = originStation.lng + destOffset.lng
          
          routePoints = [
            [originStation.lat, originStation.lng],
            [originStation.lat + destOffset.lat * 0.2, originStation.lng + destOffset.lng * 0.2],
            [originStation.lat + destOffset.lat * 0.4, originStation.lng + destOffset.lng * 0.4],
            [originStation.lat + destOffset.lat * 0.6, originStation.lng + destOffset.lng * 0.6],
            [originStation.lat + destOffset.lat * 0.8, originStation.lng + destOffset.lng * 0.8],
            [destLat, destLng],
          ]
        }
        
        if (routePoints.length >= 2) {
          routes[trip.trip_id] = routePoints
        }
      }
    })
    setTripRoutes(routes)
  }, [trips, stations])

  return (
    <>
      {/* Driver location markers (RED markers = active drivers) */}
      {Object.entries(driverLocations).map(([driverId, location]) => {
        const trip = trips.find(t => t.driver_id === driverId && (t.status === 'scheduled' || t.status === 'active'))
        if (!trip) return null
        
        return (
          <Marker
            key={`driver-${driverId}`}
            position={[location.lat, location.lng]}
            icon={createDriverIcon(location.status)}
          >
            <Popup>
              <div className="driver-popup">
                <strong>🚗 Driver: {driverId}</strong><br />
                <div><strong>Trip:</strong> {location.trip_id.substring(0, 15)}...</div>
                <div><strong>Status:</strong> <span className={`status-${location.status}`}>{location.status}</span></div>
                <div><strong>Riders:</strong> {trip.rider_ids?.join(', ') || 'None'}</div>
                <div><strong>From:</strong> {trip.origin_station}</div>
                <div><strong>To:</strong> {trip.destination}</div>
                {location.progress !== undefined && (
                  <div><strong>Progress:</strong> {Math.round(location.progress * 100)}%</div>
                )}
              </div>
            </Popup>
          </Marker>
        )
      })}

      {/* Trip routes - colored lines showing path from origin to destination */}
      {Object.entries(tripRoutes).map(([tripId, route]) => {
        const trip = trips.find(t => t.trip_id === tripId)
        if (!trip || trip.status === 'completed' || !route || route.length < 2) return null
        
        // Color based on status
        const routeColor = trip.status === 'active' ? '#28a745' : trip.status === 'scheduled' ? '#ffc107' : '#6c757d'
        const routeWeight = trip.status === 'active' ? 6 : 5
        
        return (
          <Polyline
            key={`route-${tripId}`}
            positions={route}
            color={routeColor}
            weight={routeWeight}
            opacity={0.8}
            dashArray={trip.status === 'scheduled' ? '10, 5' : undefined}
          />
        )
      })}
    </>
  )
}

