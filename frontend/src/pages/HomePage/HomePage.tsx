import { HealthStatus } from '../../components/HealthStatus/HealthStatus'
import { useAuth } from '../../hooks/useAuth'
import { useHealthCheck } from '../../hooks/useHealthCheck'
import styles from './HomePage.module.css'

/** Visão geral. O painel com indicadores de estudo chega na Etapa 3. */
export function HomePage() {
  const { user } = useAuth()
  const { state, retry } = useHealthCheck()

  return (
    <>
      <h1 className={styles.title}>Olá, {user?.display_name}</h1>
      <p className={styles.lead}>
        Bem-vindo ao StudyFlow AI. Em breve, aqui ficarão suas horas de estudo, trilhas em andamento e
        recomendações do tutor.
      </p>
      <HealthStatus state={state} onRetry={retry} />
    </>
  )
}
