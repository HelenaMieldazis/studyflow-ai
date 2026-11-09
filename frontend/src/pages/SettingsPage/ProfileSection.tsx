import { useState, type FormEvent } from 'react'
import { Alert } from '../../components/forms/Alert'
import { Button } from '../../components/forms/Button'
import { TextField } from '../../components/forms/TextField'
import { useAuth } from '../../hooks/useAuth'
import { getApiError } from '../../services/apiError'
import { updateProfile } from '../../services/authService'
import type { UpdateProfileInput } from '../../types/auth'
import { DISPLAY_NAME_MAX_LENGTH, hasErrors, validateDisplayName, validateEmail } from '../../utils/validators'
import styles from './SettingsPage.module.css'

type Errors = { display_name?: string; email?: string; current_password?: string }

export function ProfileSection() {
  const { user, setUser } = useAuth()
  const [displayName, setDisplayName] = useState(user?.display_name ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [errors, setErrors] = useState<Errors>({})
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!user) return null
  const emailChanged = email.trim().toLowerCase() !== user.email

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors: Errors = {
      display_name: validateDisplayName(displayName),
      email: validateEmail(email),
      current_password: emailChanged && !currentPassword ? 'Informe sua senha atual para alterar o e-mail.' : undefined,
    }
    setErrors(nextErrors)
    setFeedback(null)
    if (hasErrors(nextErrors)) return

    const input: UpdateProfileInput = { display_name: displayName.trim() }
    if (emailChanged) {
      input.email = email.trim()
      input.current_password = currentPassword
    }

    setSubmitting(true)
    try {
      const updated = await updateProfile(input)
      setUser(updated)
      setEmail(updated.email)
      setCurrentPassword('')
      setFeedback({ tone: 'success', text: 'Perfil atualizado.' })
    } catch (error) {
      const info = getApiError(error)
      setErrors({
        display_name: info.fields.display_name,
        email: info.fields.email ?? (info.code === 'email_unavailable' ? info.message : undefined),
        current_password: info.code === 'invalid_password' ? info.message : info.fields.current_password,
      })
      setFeedback({ tone: 'error', text: info.message })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className={styles.card} aria-labelledby="profile-title">
      <h2 id="profile-title" className={styles.cardTitle}>
        Perfil
      </h2>
      {feedback && <Alert tone={feedback.tone}>{feedback.text}</Alert>}
      <form onSubmit={handleSubmit} noValidate>
        <TextField
          label="Nome"
          name="display_name"
          autoComplete="name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          error={errors.display_name}
          maxLength={DISPLAY_NAME_MAX_LENGTH}
        />
        <TextField
          label="E-mail"
          type="email"
          name="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
          maxLength={254}
        />
        {emailChanged && (
          <TextField
            label="Senha atual"
            type="password"
            name="current_password"
            autoComplete="current-password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            error={errors.current_password}
            hint="Por segurança, confirme sua senha para alterar o e-mail."
            maxLength={128}
          />
        )}
        <Button type="submit" loading={submitting}>
          Salvar perfil
        </Button>
      </form>
    </section>
  )
}
