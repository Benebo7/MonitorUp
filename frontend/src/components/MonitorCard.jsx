import './MonitorCard.css'

function MonitorCard({ monitor, onDelete }) {
  const isUp = monitor.status_code >= 200 && monitor.status_code < 400
  const statusText = monitor.status_code === 0 ? 'Pending' : isUp ? 'Up' : 'Down'
  const statusClass = monitor.status_code === 0 ? 'pending' : isUp ? 'up' : 'down'

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Never'
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  return (
    <div className={`monitor-card ${statusClass}`}>
      <div className="monitor-info">
        <div className="monitor-header">
          <span className={`status-dot ${statusClass}`}></span>
          <h3>{monitor.name}</h3>
          <span className={`status-badge ${statusClass}`}>{statusText}</span>
        </div>
        <p className="monitor-url">{monitor.url}</p>
        <p className="monitor-meta">
          Status: {monitor.status_code || '—'} | Last checked: {formatTime(monitor.last_checked)}
        </p>
      </div>
      <button className="btn-delete" onClick={onDelete}>Delete</button>
    </div>
  )
}

export default MonitorCard
