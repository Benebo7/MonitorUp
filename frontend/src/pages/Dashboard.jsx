import { useState, useEffect, useRef } from 'react'
import MonitorCard from '../components/MonitorCard'
import AddMonitor from '../components/AddMonitor'
import './Dashboard.css'

function Dashboard({ token, onLogout }) {
  const [monitors, setMonitors] = useState([])
  const [showAdd, setShowAdd] = useState(false)
  const [loading, setLoading] = useState(true)
  const ws = useRef(null)

  const fetchMonitors = async () => {
    try {
      const res = await fetch('/monitor/read', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (res.status === 401) {
        onLogout()
        return
      }
      const data = await res.json()
      setMonitors(data)
    } catch (err) {
      console.error('Failed to fetch monitors:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMonitors()

    // WebSocket connection for live updates
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${protocol}://${window.location.host}/ws/${token}`
    ws.current = new WebSocket(wsUrl)

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setMonitors(prev =>
        prev.map(m =>
          m.id === data.monitor_id
            ? { ...m, status_code: data.status_code, last_checked: data.last_checked }
            : m
        )
      )
    }

    ws.current.onclose = () => {
      console.log('WebSocket disconnected')
    }

    return () => {
      if (ws.current) ws.current.close()
    }
  }, [token])

  const handleDelete = async (monitorId) => {
    try {
      const res = await fetch(`/monitor/delete/${monitorId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (res.ok) {
        setMonitors(prev => prev.filter(m => m.id !== monitorId))
      }
    } catch (err) {
      console.error('Failed to delete monitor:', err)
    }
  }

  const handleAdd = async (name, url) => {
    try {
      const res = await fetch('/monitor/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ name, url }),
      })
      if (res.ok) {
        setShowAdd(false)
        fetchMonitors()
      }
    } catch (err) {
      console.error('Failed to add monitor:', err)
    }
  }

  const getStatusSummary = () => {
    const up = monitors.filter(m => m.status_code >= 200 && m.status_code < 400).length
    const down = monitors.filter(m => !m.status_code || m.status_code >= 400).length
    return { up, down, total: monitors.length }
  }

  const summary = getStatusSummary()

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>MonitorUp</h1>
          <p className="header-subtitle">{summary.total} monitors - {summary.up} up, {summary.down} down</p>
        </div>
        <div className="header-actions">
          <button className="btn-add" onClick={() => setShowAdd(true)}>+ Add Monitor</button>
          <button className="btn-logout" onClick={onLogout}>Logout</button>
        </div>
      </header>

      {showAdd && (
        <AddMonitor onAdd={handleAdd} onCancel={() => setShowAdd(false)} />
      )}

      <div className="monitors-grid">
        {loading ? (
          <p className="loading">Loading monitors...</p>
        ) : monitors.length === 0 ? (
          <p className="empty">No monitors yet. Add one to get started.</p>
        ) : (
          monitors.map(monitor => (
            <MonitorCard
              key={monitor.id}
              monitor={monitor}
              onDelete={() => handleDelete(monitor.id)}
            />
          ))
        )}
      </div>
    </div>
  )
}

export default Dashboard
