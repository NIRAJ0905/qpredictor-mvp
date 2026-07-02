import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './store/authStore'
import Landing      from './pages/Landing'
import { LoginPage, SignupPage } from './pages/Auth'
import Dashboard    from './pages/Dashboard'
import UploadPage   from './pages/Upload'
import AnalysisPage from './pages/Analysis'
import PredictionsPage from './pages/Predictions'
import ChatPage     from './pages/Chat'

function Protected({ children }) {
  const { token } = useAuthStore()
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"           element={<Landing />} />
        <Route path="/login"      element={<LoginPage />} />
        <Route path="/signup"     element={<SignupPage />} />
        <Route path="/dashboard"  element={<Protected><Dashboard /></Protected>} />
        <Route path="/upload"     element={<Protected><UploadPage /></Protected>} />
        <Route path="/analysis"   element={<Protected><AnalysisPage /></Protected>} />
        <Route path="/predictions"element={<Protected><PredictionsPage /></Protected>} />
        <Route path="/chat"       element={<Protected><ChatPage /></Protected>} />
        <Route path="*"           element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
