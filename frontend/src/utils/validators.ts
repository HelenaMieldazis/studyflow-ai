/**
 * Validação no navegador — só para dar retorno rápido ao usuário.
 * O backend repete todas as validações e é ele quem decide.
 */
export const PASSWORD_MIN_LENGTH = 12
export const PASSWORD_MAX_LENGTH = 128
export const DISPLAY_NAME_MAX_LENGTH = 80

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateEmail(value: string): string | undefined {
  if (!value.trim()) return 'Informe seu e-mail.'
  if (!EMAIL_PATTERN.test(value.trim())) return 'Informe um e-mail válido.'
  return undefined
}

export function validateNewPassword(value: string): string | undefined {
  if (!value) return 'Informe uma senha.'
  if (value.length < PASSWORD_MIN_LENGTH) return `Use pelo menos ${PASSWORD_MIN_LENGTH} caracteres.`
  if (value.length > PASSWORD_MAX_LENGTH) return `Use no máximo ${PASSWORD_MAX_LENGTH} caracteres.`
  if (!value.trim()) return 'A senha não pode ser composta apenas por espaços.'
  return undefined
}

export function validateDisplayName(value: string): string | undefined {
  if (!value.trim()) return 'Informe seu nome.'
  if (value.trim().length > DISPLAY_NAME_MAX_LENGTH) return `Use no máximo ${DISPLAY_NAME_MAX_LENGTH} caracteres.`
  return undefined
}

export function hasErrors(errors: Record<string, string | undefined>): boolean {
  return Object.values(errors).some(Boolean)
}
