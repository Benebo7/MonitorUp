import { useState, useEffect } from 'react'
import Pagination from './Pagination'

const STATUS_OPTIONS = [
  { value: '', label: 'All status codes' },
  { value: '2', label: '2xx' },
  { value: '3', label: '3xx' },
  { value: '4', label: '4xx' },
  { value: '5', label: '5xx' },
]

function AdminMonitorsTable({ onUnauthorized }) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [statusCode, setStatusCode] = useState('')
  const [lastChecked, setLastChecked] = useState('')
  const [lcMode, setLcMode] = useState('after')
  const [data, setData] = useState({ monitors: [], total_monitors: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadMonitors() {
      setLoading(true)
      setError('')

      const params = new URLSearchParams({ page, page_size: pageSize })
      if (statusCode !== '') params.set('statuscode', statusCode)
      if (lastChecked !== '') {
        params.set('last_checked', lastChecked)
        params.set('lc_mode', lcMode)
      }

      try {
        const res = await fetch(`/admin/monitors?${params}`, { credentials: 'include' })
        if (res.status === 401 || res.status === 403) {
          onUnauthorized()
          return
        }
        if (!res.ok) throw new Error('Failed to load monitors')
        setData(await res.json())
      } catch {
        setError('Could not load monitors.')
      } finally {
        setLoading(false)
      }
    }

    loadMonitors()
  }, [page, pageSize, statusCode, lastChecked, lcMode, onUnauthorized])

  const updateFilter = (setter) => (value) => {
    setter(value)
    setPage(1)
  }

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Never'
    return new Date(timestamp).toLocaleString()
  }

  return (
    <div className="admin-panel">
      <div className="admin-filters">
        <select value={statusCode} onChange={(e) => updateFilter(setStatusCode)(e.target.value)}>
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <select value={lcMode} onChange={(e) => updateFilter(setLcMode)(e.target.value)}>
          <option value="before">Checked before</option>
          <option value="after">Checked after</option>
          <option value="on">Checked on</option>
        </select>
        <input
          type="date"
          value={lastChecked}
          onChange={(e) => updateFilter(setLastChecked)(e.target.value)}
        />
      </div>

      {error && <p className="admin-error">{error}</p>}

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>URL</th>
              <th>Status</th>
              <th>Last checked</th>
              <th>Owner</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="admin-empty">Loading...</td></tr>
            ) : data.monitors.length === 0 ? (
              <tr><td colSpan={5} className="admin-empty">No monitors found.</td></tr>
            ) : (
              data.monitors.map((m, i) => (
                <tr key={i}>
                  <td>{m.name}</td>
                  <td className="admin-url">{m.url}</td>
                  <td>{m.status_code || '—'}</td>
                  <td>{formatTime(m.last_checked)}</td>
                  <td>
                    {m.user?.user}{' '}
                    <span className="admin-owner-email">({m.user?.email})</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Pagination
        page={page}
        pageSize={pageSize}
        total={data.total_monitors}
        onPageChange={setPage}
        onPageSizeChange={(v) => { setPageSize(v); setPage(1) }}
      />
    </div>
  )
}

export default AdminMonitorsTable
