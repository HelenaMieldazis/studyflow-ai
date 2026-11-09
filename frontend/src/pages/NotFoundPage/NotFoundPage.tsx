import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <>
      <h1>Página não encontrada</h1>
      <p>O endereço acessado não existe.</p>
      <Link to="/">Voltar para o início</Link>
    </>
  )
}
