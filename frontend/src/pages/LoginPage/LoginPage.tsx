import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from '../../components/forms/Alert'
import { Button } from '../../components/forms/Button'
import { TextField } from '../../components/forms/TextField'
import { useAuth } from '../../hooks/useAuth'
import { getApiError } from '../../services/apiError'
import { hasErrors, validateEmail } from '../../utils/validators'
import styles from '../authForms.module.css'

type Errors = { email?: string; password?: string }

export function LoginPage() {
  const { login, notice } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<Errors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors: Errors = {
      email: validateEmail(email),
      password: password ? undefined : 'Informe sua senha.',
    }
    setErrors(nextErrors)
    setFormError(null)
    if (hasErrors(nextErrors)) return

    setSubmitting(true)
    try {
      // Com a sessão ativa, o PublicOnlyRoute leva à página de destino.
      await login({ email: email.trim(), password })
    } catch (error) {
      const info = getApiError(error)
      setErrors({ email: info.fields.email, password: info.fields.password })
      setFormError(info.message)
      setPassword('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1>Entrar</h1>
      <p className={styles.subtitle}>Acesse sua conta para continuar seus estudos.</p>

      {notice === 'logged_out' && !formError && <Alert tone="info">Você saiu da sua conta.</Alert>}
      {notice === 'account_deleted' && !formError && <Alert tone="success">Sua conta foi excluída.</Alert>}
      {notice === 'session_expired' && !formError && (
        <Alert tone="info">Sua sessão expirou. Entre novamente.</Alert>
      )}
      {formError && <Alert tone="error">{formError}</Alert>}

      <form onSubmit={handleSubmit} noValidate>
        <TextField
          label="E-mail"
          type="email"
          name="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
          maxLength={254}
          required
        />
        <TextField
          label="Senha"
          type="password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          maxLength={128}
          required
        />
        <Button type="submit" loading={submitting} className={styles.submit}>
          Entrar
        </Button>
      </form>

      <p className={styles.footer}>
        Ainda não tem conta? <Link to="/cadastro">Criar conta</Link>
      </p>
    </>
  )
}
