import { Routes, Route, Navigate } from 'react-router-dom'
import Login     from './pages/Login'
import Dashboard from './pages/Dashboard'
import NewScan   from './pages/NewScan'
import Patients  from './pages/Patients'
import Reports   from './pages/Reports'
import Billing   from './pages/Billing'

function PrivateRoute({ children }) {
  return localStorage.getItem('token') ? children : <Navigate to="/login" />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login"   element={<Login />} />
      <Route path="/"        element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/scan"    element={<PrivateRoute><NewScan /></PrivateRoute>} />
      <Route path="/patients"element={<PrivateRoute><Patients /></PrivateRoute>} />
      <Route path="/reports" element={<PrivateRoute><Reports /></PrivateRoute>} />
      <Route path="/billing" element={<PrivateRoute><Billing /></PrivateRoute>} />
      <Route path="*"        element={<Navigate to="/" />} />
    </Routes>
  )
}