import { useState, type FormEvent } from 'react'
import { Alert } from '../../components/forms/Alert'
import { Button } from '../../components/forms/Button'
import { TextField } from '../../components/forms/TextField'
import formStyles from '../../components/forms/forms.module.css'
import { useAuth } from '../../hooks/useAuth'
import { getApiError } from '../../services/apiError'
import { deleteAccount } from '../../services/authService'
import styles from './SettingsPage.module.css'

export function DeleteAccountSection() {
  const { clearSession } = useAuth()
  const [password, setPassword] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    if (!confirmed || !password) {
      setError('Confirme que entende a exclusão e informe sua senha.')
      return
    }

    setSubmitting(true)
    try {
      await deleteAccount(password)
      // Sem sessão, o ProtectedRoute leva ao login, que exibe a confirmação.
      clearSession('account_deleted')
    } catch (err) {
      setError(getApiError(err).message)
      setPassword('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className={`${styles.card} ${styles.danger}`} aria-labelledby="delete-title">
      <h2 id="delete-title" className={styles.cardTitle}>
        Excluir conta
      </h2>
      <p className={styles.text}>
        A exclusão é <strong>permanente</strong>: sua conta e todos os dados associados são apagados e não podem ser
        recuperados.
      </p>
      {error && <Alert tone="error">{error}</Alert>}
      <form onSubmit={handleSubmit} noValidate>
        <label className={formStyles.checkbox}>
          <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
          <span>Entendo que esta ação é permanente.</span>
        </label>
        <TextField
          label="Senha"
          type="password"
          name="delete_password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          maxLength={128}
        />
        <Button type="submit" variant="danger" loading={submitting} disabled={!confirmed}>
          Excluir minha conta
        </Button>
      </form>
    </section>
  )
}
