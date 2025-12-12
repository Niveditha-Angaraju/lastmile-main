import React, { useEffect, useState, useRef } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8081'

export function MatchNotifications({ trips, onNewMatch }) {
  const [notifications, setNotifications] = useState([])
  const [lastTripIds, setLastTripIds] = useState(new Set())
  const notificationIdRef = useRef(0)

  useEffect(() => {
    // Detect new trips (matches) by comparing trip IDs
    const currentTripIds = new Set(trips.map(t => t.trip_id))
    const newTrips = trips.filter(trip => !lastTripIds.has(trip.trip_id))
    
    newTrips.forEach(trip => {
      if (trip.status === 'scheduled' || trip.status === 'active') {
        notificationIdRef.current += 1
        const notification = {
          id: notificationIdRef.current,
          timestamp: Date.now(),
          type: 'match',
          trip: trip,
          message: `🎉 Match Found! Driver ${trip.driver_id} will pick up ${trip.rider_ids?.length || 0} rider(s) at ${trip.origin_station}`,
          details: `Trip ${trip.trip_id.substring(0, 12)}... → ${trip.destination}`
        }
        setNotifications(prev => [notification, ...prev.slice(0, 4)])
        if (onNewMatch) onNewMatch(trip)
      }
    })

    // Also detect status changes
    trips.forEach(trip => {
      if (trip.status === 'completed' && lastTripIds.has(trip.trip_id)) {
        const oldTrip = Array.from(lastTripIds).find(id => id === trip.trip_id)
        if (oldTrip && trips.find(t => t.trip_id === oldTrip)?.status !== 'completed') {
          notificationIdRef.current += 1
          const notification = {
            id: notificationIdRef.current,
            timestamp: Date.now(),
            type: 'completed',
            trip: trip,
            message: `✅ Trip Completed! Driver ${trip.driver_id} finished trip to ${trip.destination}`,
            details: `Trip ${trip.trip_id.substring(0, 12)}... completed`
          }
          setNotifications(prev => [notification, ...prev.slice(0, 4)])
        }
      }
    })

    setLastTripIds(currentTripIds)
  }, [trips, lastTripIds, onNewMatch])

  // Auto-dismiss notifications after 8 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now()
      setNotifications(prev => prev.filter(n => now - n.timestamp < 8000))
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  if (notifications.length === 0) return null

  return (
    <div className="notifications-container">
      {notifications.map(notif => (
        <div 
          key={notif.id} 
          className={`notification ${notif.type === 'match' ? 'match-notification' : 'completed-notification'}`}
        >
          <div className="notification-content">
            <div className="notification-message">{notif.message}</div>
            <div className="notification-details">{notif.details}</div>
          </div>
          <button 
            className="notification-close"
            onClick={() => dismissNotification(notif.id)}
            aria-label="Close"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}

