import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Bell, LogOut, BarChart2, Home } from 'lucide-react'

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Bell size={24} />
        <span className="navbar-title">HawkEar</span>
      </div>
      <div className="navbar-links">
        <Link to="/" className="navbar-link">
          <Home size={16} />
          Dashboard
        </Link>
        <Link to="/training" className="navbar-link">
          <BarChart2 size={16} />
          Training
        </Link>
      </div>
      <div className="navbar-user">
        {user && <span className="navbar-username">{user.username}</span>}
        <button className="btn btn-ghost" onClick={handleLogout}>
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </nav>
  )
}
