import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from '../../components/forms/Alert'
import { Button } from '../../components/forms/Button'
import { TextField } from '../../components/forms/TextField'
import { useAuth } from '../../hooks/useAuth'
import { getApiError } from '../../services/apiError'
import {
  DISPLAY_NAME_MAX_LENGTH,
  PASSWORD_MAX_LENGTH,
  PASSWORD_MIN_LENGTH,
  hasErrors,
  validateDisplayName,
  validateEmail,
  validateNewPassword,
} from '../../utils/validators'
import styles from '../authForms.module.css'

type Fields = { display_name: string; email: string; password: string; confirm: string }
type Errors = Partial<Record<keyof Fields, string>>

export function RegisterPage() {
  const { register } = useAuth()
  const [values, setValues] = useState<Fields>({ display_name: '', email: '', password: '', confirm: '' })
  const [errors, setErrors] = useState<Errors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (field: keyof Fields) => (e: ChangeEvent<HTMLInputElement>) =>
    setValues((v) => ({ ...v, [field]: e.target.value }))

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors: Errors = {
      display_name: validateDisplayName(values.display_name),
      email: validateEmail(values.email),
      password: validateNewPassword(values.password),
      confirm: values.confirm === values.password ? undefined : 'As senhas não conferem.',
    }
    setErrors(nextErrors)
    setFormError(null)
    if (hasErrors(nextErrors)) return

    setSubmitting(true)
    try {
      await register({
        display_name: values.display_name.trim(),
        email: values.email.trim(),
        password: values.password,
      })
      // Com a sessão ativa, o PublicOnlyRoute leva ao painel.
    } catch (error) {
      const info = getApiError(error)
      setErrors({
        display_name: info.fields.display_name,
        email: info.fields.email ?? (info.code === 'email_unavailable' ? info.message : undefined),
        password: info.fields.password,
      })
      setFormError(info.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1>Criar conta</h1>
      <p className={styles.subtitle}>Organize seus estudos com apoio de um tutor de IA.</p>

      {formError && <Alert tone="error">{formError}</Alert>}

      <form onSubmit={handleSubmit} noValidate>
        <TextField
          label="Nome"
          name="display_name"
          autoComplete="name"
          value={values.display_name}
          onChange={update('display_name')}
          error={errors.display_name}
          maxLength={DISPLAY_NAME_MAX_LENGTH}
          required
        />
        <TextField
          label="E-mail"
          type="email"
          name="email"
          autoComplete="email"
          value={values.email}
          onChange={update('email')}
          error={errors.email}
          maxLength={254}
          required
        />
        <TextField
          label="Senha"
          type="password"
          name="password"
          autoComplete="new-password"
          value={values.password}
          onChange={update('password')}
          error={errors.password}
          hint={`Mínimo de ${PASSWORD_MIN_LENGTH} caracteres. Uma frase com espaços é uma ótima opção.`}
          maxLength={PASSWORD_MAX_LENGTH}
          required
        />
        <TextField
          label="Confirmar senha"
          type="password"
          name="confirm"
          autoComplete="new-password"
          value={values.confirm}
          onChange={update('confirm')}
          error={errors.confirm}
          maxLength={PASSWORD_MAX_LENGTH}
          required
        />

        <p className={styles.privacy}>
          Ao criar a conta, você concorda com o uso dos seus dados descrito em{' '}
          <Link to="/privacidade">Como usamos seus dados</Link>.
        </p>

        <Button type="submit" loading={submitting} className={styles.submit}>
          Criar conta
        </Button>
      </form>

      <p className={styles.footer}>
        Já tem conta? <Link to="/entrar">Entrar</Link>
      </p>
    </>
  )
}
