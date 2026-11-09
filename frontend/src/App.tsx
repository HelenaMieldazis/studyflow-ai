import { Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/AppLayout/AppLayout'
import { AuthLayout } from './components/AuthLayout/AuthLayout'
import { ProtectedRoute, PublicOnlyRoute } from './components/RouteGuards/RouteGuards'
import { HomePage } from './pages/HomePage/HomePage'
import { LoginPage } from './pages/LoginPage/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage/NotFoundPage'
import { PrivacyPage } from './pages/PrivacyPage/PrivacyPage'
import { RegisterPage } from './pages/RegisterPage/RegisterPage'
import { SettingsPage } from './pages/SettingsPage/SettingsPage'

/** Definição das rotas. BrowserRouter e AuthProvider ficam em main.tsx (facilita os testes). */
export default function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route element={<AuthLayout />}>
          <Route path="/entrar" element={<LoginPage />} />
          <Route path="/cadastro" element={<RegisterPage />} />
        </Route>
      </Route>

      <Route path="/privacidade" element={<PrivacyPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<HomePage />} />
          <Route path="/configuracoes" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  )
}
