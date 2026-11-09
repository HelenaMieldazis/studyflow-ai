import { api } from './api'
import type {
  ChangePasswordInput,
  LoginInput,
  RegisterInput,
  SessionResponse,
  UpdateProfileInput,
  User,
} from '../types/auth'

export async function register(input: RegisterInput): Promise<SessionResponse> {
  const { data } = await api.post<SessionResponse>('/auth/register', input)
  return data
}

export async function login(input: LoginInput): Promise<SessionResponse> {
  const { data } = await api.post<SessionResponse>('/auth/login', input)
  return data
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}

/** Sessão atual. Lança erro 401 se não houver sessão válida. */
export async function fetchCurrentSession(): Promise<SessionResponse> {
  const { data } = await api.get<SessionResponse>('/auth/me')
  return data
}

export async function updateProfile(input: UpdateProfileInput): Promise<User> {
  const { data } = await api.patch<{ user: User }>('/users/me', input)
  return data.user
}

export async function changePassword(input: ChangePasswordInput): Promise<SessionResponse> {
  const { data } = await api.put<SessionResponse>('/users/me/password', input)
  return data
}

export async function deleteAccount(password: string): Promise<void> {
  await api.delete('/users/me', { data: { password } })
}
