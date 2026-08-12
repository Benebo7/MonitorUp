import { useState } from 'react'
import AdminUsersTable from './AdminUsersTable'
import AdminMonitorsTable from './AdminMonitorsTable'
import './AdminDashboard.css'

function AdminDashboard({ onLogout }) {
  const [tab, setTab] = useState('users')

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <h1>MonitorUp <span className="admin-tag">Admin</span></h1>

        <div className="admin-header-actions">
          <div className="admin-tabs">
            <button className={tab === 'users' ? 'active' : ''} onClick={() => setTab('users')}>
              Users
            </button>
            <button className={tab === 'monitors' ? 'active' : ''} onClick={() => setTab('monitors')}>
              Monitors
            </button>
          </div>
          <button className="btn-logout" onClick={onLogout}>Logout</button>
        </div>
      </header>

      {tab === 'users' ? (
        <AdminUsersTable onUnauthorized={onLogout} />
      ) : (
        <AdminMonitorsTable onUnauthorized={onLogout} />
      )}
    </div>
  )
}

export default AdminDashboard
