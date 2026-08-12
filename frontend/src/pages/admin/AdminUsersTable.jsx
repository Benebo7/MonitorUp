import { useState, useEffect, Fragment } from 'react'
import Pagination from './Pagination'

function AdminUsersTable({ onUnauthorized }) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [isVerified, setIsVerified] = useState('')
  const [monitorsQtt, setMonitorsQtt] = useState('')
  const [data, setData] = useState({ users: [], total_users: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    async function loadUsers() {
      setLoading(true)
      setError('')

      const params = new URLSearchParams({ page, page_size: pageSize })
      if (isVerified !== '') params.set('is_verified', isVerified)
      if (monitorsQtt !== '') params.set('monitors_qtt', monitorsQtt)

      try {
        const res = await fetch(`/admin/users?${params}`, { credentials: 'include' })
        if (res.status === 401 || res.status === 403) {
          onUnauthorized()
          return
        }
        if (!res.ok) throw new Error('Failed to load users')
        setData(await res.json())
      } catch {
        setError('Could not load users.')
      } finally {
        setLoading(false)
      }
    }

    loadUsers()
  }, [page, pageSize, isVerified, monitorsQtt, onUnauthorized])

  const updateFilter = (setter) => (value) => {
    setter(value)
    setPage(1)
  }

  return (
    <div className="admin-panel">
      <div className="admin-filters">
        <select value={isVerified} onChange={(e) => updateFilter(setIsVerified)(e.target.value)}>
          <option value="">All statuses</option>
          <option value="true">Verified</option>
          <option value="false">Not verified</option>
        </select>
        <input
          type="number"
          min="0"
          placeholder="Min. monitors"
          value={monitorsQtt}
          onChange={(e) => updateFilter(setMonitorsQtt)(e.target.value)}
        />
      </div>

      {error && <p className="admin-error">{error}</p>}

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th></th>
              <th>User</th>
              <th>Email</th>
              <th>Verified</th>
              <th>Monitors</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="admin-empty">Loading...</td></tr>
            ) : data.users.length === 0 ? (
              <tr><td colSpan={5} className="admin-empty">No users found.</td></tr>
            ) : (
              data.users.map((u, i) => (
                <Fragment key={i}>
                  <tr className="admin-row" onClick={() => setExpanded(expanded === i ? null : i)}>
                    <td className="admin-expand">{expanded === i ? '▾' : '▸'}</td>
                    <td>{u.user}</td>
                    <td>{u.email}</td>
                    <td>
                      <span className={`admin-badge ${u.is_verified ? 'yes' : 'no'}`}>
                        {u.is_verified ? 'Verified' : 'Unverified'}
                      </span>
                    </td>
                    <td>{u.monitors.length}</td>
                  </tr>
                  {expanded === i && (
                    <tr className="admin-subrow">
                      <td colSpan={5}>
                        {u.monitors.length === 0 ? (
                          <span className="admin-empty-inline">No monitors.</span>
                        ) : (
                          <ul className="admin-sublist">
                            {u.monitors.map((m, j) => (
                              <li key={j}>
                                <strong>{m.name}</strong> — {m.url} ({m.status_code || '—'})
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Pagination
        page={page}
        pageSize={pageSize}
        total={data.total_users}
        onPageChange={setPage}
        onPageSizeChange={(v) => { setPageSize(v); setPage(1) }}
      />
    </div>
  )
}

export default AdminUsersTable
