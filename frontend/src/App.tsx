import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import NavBar from './components/NavBar'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import TouchDetailPage from './pages/TouchDetailPage'
import AnalysisPage from './pages/AnalysisPage'
import TrainingPage from './pages/TrainingPage'

function AppLayout() {
  return (
    <>
      <NavBar />
      <main className="main-content">
        <Outlet />
      </main>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/touches/:id" element={<TouchDetailPage />} />
              <Route path="/touches/:id/analysis" element={<AnalysisPage />} />
              <Route path="/training" element={<TrainingPage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
