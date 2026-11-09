/**
 * Valida o destino pós-login. Só aceita caminhos internos ("/algo"), evitando
 * open redirect para outro site (ex.: "//site-malicioso.com" ou "https://...").
 */
export function safeRedirectPath(value: unknown, fallback = '/'): string {
  if (typeof value !== 'string') return fallback
  if (!value.startsWith('/') || value.startsWith('//') || value.startsWith('/\\')) return fallback
  return value
}
