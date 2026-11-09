import type { ConnectionState } from '../../types/health'
import styles from './HealthStatus.module.css'

type Props = {
  state: ConnectionState
  onRetry: () => void
}

const CONTENT: Record<ConnectionState['kind'], { title: string; description: string; tone: string }> = {
  loading: {
    title: 'Verificando conexão…',
    description: 'Consultando o servidor do StudyFlow AI.',
    tone: styles.toneNeutral,
  },
  online: {
    title: 'Sistema operacional',
    description: 'A API e o banco de dados estão respondendo normalmente.',
    tone: styles.toneSuccess,
  },
  degraded: {
    title: 'Banco de dados indisponível',
    description: 'A API está no ar, mas não conseguiu acessar o banco de dados.',
    tone: styles.toneWarning,
  },
  offline: {
    title: 'Servidor inacessível',
    description: 'Não foi possível conectar à API. Verifique se o backend está em execução.',
    tone: styles.toneDanger,
  },
}

/** Cartão que mostra o resultado de GET /api/health. */
export function HealthStatus({ state, onRetry }: Props) {
  const content = CONTENT[state.kind]
  const isLoading = state.kind === 'loading'

  return (
    <section className={styles.card} aria-labelledby="health-title">
      <div className={styles.header}>
        <span className={`${styles.dot} ${content.tone}`} aria-hidden="true" />
        <h2 id="health-title" className={styles.title}>
          Status do sistema
        </h2>
      </div>

      {/* role="status" anuncia mudanças a leitores de tela sem roubar o foco. */}
      <div role="status" aria-live="polite" aria-busy={isLoading}>
        <p className={styles.state}>{content.title}</p>
        <p className={styles.description}>{content.description}</p>
      </div>

      {(state.kind === 'online' || state.kind === 'degraded') && (
        <dl className={styles.checks}>
          <div className={styles.checkRow}>
            <dt>API</dt>
            <dd>no ar</dd>
          </div>
          <div className={styles.checkRow}>
            <dt>Banco de dados</dt>
            <dd>{state.data.checks.database === 'ok' ? 'conectado' : 'indisponível'}</dd>
          </div>
        </dl>
      )}

      <button type="button" className={styles.button} onClick={onRetry} disabled={isLoading}>
        Verificar novamente
      </button>
    </section>
  )
}
