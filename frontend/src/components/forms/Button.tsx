import type { ButtonHTMLAttributes } from 'react'
import styles from './forms.module.css'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger'
  loading?: boolean
}

export function Button({ variant = 'primary', loading = false, disabled, children, className, ...rest }: Props) {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${className ?? ''}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? 'Aguarde…' : children}
    </button>
  )
}
