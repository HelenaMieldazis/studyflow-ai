/** Usuário público (espelha app/schemas/serializers.py). */
export type User = {
  id: string
  email: string
  display_name: string
  created_at: string
}

/** Resposta de login, cadastro, /auth/me e troca de senha. */
export type SessionResponse = {
  user: User
  csrf_token: string
}

export type RegisterInput = {
  email: string
  password: string
  display_name: string
}

export type LoginInput = {
  email: string
  password: string
}

export type UpdateProfileInput = {
  display_name?: string
  email?: string
  current_password?: string
}

export type ChangePasswordInput = {
  current_password: string
  new_password: string
}
