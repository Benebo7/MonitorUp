import { useState } from 'react'
import AdminLogin from './AdminLogin'
import AdminDashboard from './AdminDashboard'

function AdminApp() {
  const [authed, setAuthed] = useState(false)

  if (!authed) {
    return <AdminLogin onVerified={() => setAuthed(true)} />
  }

  return <AdminDashboard onLogout={() => setAuthed(false)} />
}

export default AdminApp
