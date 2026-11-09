import { Link } from 'react-router-dom'
import styles from './PrivacyPage.module.css'

/** Aviso de privacidade (LGPD): o que é coletado, para quê, e como excluir. */
export function PrivacyPage() {
  return (
    <main className={styles.page}>
      <article className={styles.article}>
        <h1>Como usamos seus dados</h1>
        <p className={styles.updated}>Versão aplicável à fase atual do StudyFlow AI.</p>

        <h2>O que coletamos</h2>
        <ul>
          <li>
            <strong>Nome e e-mail</strong>: para identificar sua conta e permitir o login.
          </li>
          <li>
            <strong>Senha</strong>: guardada apenas como um hash Argon2id. Nem a equipe consegue ver sua senha.
          </li>
          <li>
            <strong>Sessões de login</strong>: data de criação e do último uso, para manter você conectado com
            segurança. Não registramos seu endereço IP nem seu navegador nas sessões.
          </li>
        </ul>

        <h2>Para que usamos</h2>
        <p>
          Somente para operar a sua conta. Seus dados não são vendidos, não são compartilhados com outros usuários e
          não são usados para treinar modelos de inteligência artificial sem o seu consentimento explícito.
        </p>

        <h2>Cookies</h2>
        <p>
          Usamos um único cookie essencial, que mantém sua sessão de login. Ele não pode ser lido por scripts da página
          e não é usado para rastreamento ou publicidade.
        </p>

        <h2>Seus direitos</h2>
        <p>
          Você pode corrigir seu nome e e-mail e <strong>excluir sua conta</strong> a qualquer momento em
          Configurações. A exclusão apaga a conta e os dados associados de forma permanente.
        </p>

        <p className={styles.back}>
          <Link to="/">Voltar</Link>
        </p>
      </article>
    </main>
  )
}
