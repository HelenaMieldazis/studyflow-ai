import type { ReactNode } from 'react'
import styles from './forms.module.css'

type Props = {
  tone: 'error' | 'success' | 'info'
  children: ReactNode
}

/** Mensagem de retorno. Erros usam role="alert" (anunciados imediatamente por leitores de tela). */
export function Alert({ tone, children }: Props) {
  return (
    <div className={`${styles.alert} ${styles[`alert_${tone}`]}`} role={tone === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}
