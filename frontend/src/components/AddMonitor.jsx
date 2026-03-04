import { useState } from 'react'
import './AddMonitor.css'

function AddMonitor({ onAdd, onCancel }) {
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (name && url) {
      onAdd(name, url)
    }
  }

  return (
    <div className="add-monitor-overlay" onClick={onCancel}>
      <div className="add-monitor-modal" onClick={e => e.stopPropagation()}>
        <h2>Add Monitor</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Name (e.g. My Website)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            type="url"
            placeholder="URL (e.g. https://example.com)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <div className="modal-actions">
            <button type="button" className="btn-cancel" onClick={onCancel}>Cancel</button>
            <button type="submit" className="btn-submit">Add</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default AddMonitor
