import { useState, type FormEvent } from 'react'
import { Alert } from '../../components/forms/Alert'
import { Button } from '../../components/forms/Button'
import { TextField } from '../../components/forms/TextField'
import { useAuth } from '../../hooks/useAuth'
import { getApiError } from '../../services/apiError'
import { changePassword } from '../../services/authService'
import { PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH, hasErrors, validateNewPassword } from '../../utils/validators'
import styles from './SettingsPage.module.css'

type Errors = { current_password?: string; new_password?: string; confirm?: string }

export function PasswordSection() {
  const { applySession } = useAuth()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [errors, setErrors] = useState<Errors>({})
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors: Errors = {
      current_password: current ? undefined : 'Informe sua senha atual.',
      new_password: validateNewPassword(next) ?? (next === current ? 'A nova senha deve ser diferente da atual.' : undefined),
      confirm: confirm === next ? undefined : 'As senhas não conferem.',
    }
    setErrors(nextErrors)
    setFeedback(null)
    if (hasErrors(nextErrors)) return

    setSubmitting(true)
    try {
      // O backend encerra as outras sessões e devolve uma sessão nova (novo token CSRF).
      applySession(await changePassword({ current_password: current, new_password: next }))
      setCurrent('')
      setNext('')
      setConfirm('')
      setFeedback({ tone: 'success', text: 'Senha alterada. Suas sessões em outros dispositivos foram encerradas.' })
    } catch (error) {
      const info = getApiError(error)
      setErrors({
        current_password: info.code === 'invalid_password' ? info.message : info.fields.current_password,
        new_password: info.fields.new_password,
      })
      setFeedback({ tone: 'error', text: info.message })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className={styles.card} aria-labelledby="password-title">
      <h2 id="password-title" className={styles.cardTitle}>
        Alterar senha
      </h2>
      {feedback && <Alert tone={feedback.tone}>{feedback.text}</Alert>}
      <form onSubmit={handleSubmit} noValidate>
        <TextField
          label="Senha atual"
          type="password"
          name="current_password"
          autoComplete="current-password"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
          error={errors.current_password}
          maxLength={PASSWORD_MAX_LENGTH}
        />
        <TextField
          label="Nova senha"
          type="password"
          name="new_password"
          autoComplete="new-password"
          value={next}
          onChange={(e) => setNext(e.target.value)}
          error={errors.new_password}
          hint={`Mínimo de ${PASSWORD_MIN_LENGTH} caracteres.`}
          maxLength={PASSWORD_MAX_LENGTH}
        />
        <TextField
          label="Confirmar nova senha"
          type="password"
          name="confirm"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={errors.confirm}
          maxLength={PASSWORD_MAX_LENGTH}
        />
        <Button type="submit" loading={submitting}>
          Alterar senha
        </Button>
      </form>
    </section>
  )
}
