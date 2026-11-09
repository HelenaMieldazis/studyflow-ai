import axios from 'axios'

export type ApiErrorInfo = {
  status: number | null
  code: string
  message: string
  /** Mensagens por campo (ex.: { email: "Informe um e-mail válido." }). */
  fields: Record<string, string>
}

type ErrorBody = {
  error?: {
    code?: unknown
    message?: unknown
    fields?: unknown
  }
}

/** Converte qualquer erro de requisição numa estrutura segura para exibir na interface. */
export function getApiError(error: unknown): ApiErrorInfo {
  if (!axios.isAxiosError(error)) {
    return { status: null, code: 'unknown', message: 'Ocorreu um erro inesperado.', fields: {} }
  }
  if (!error.response) {
    return {
      status: null,
      code: 'network_error',
      message: 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.',
      fields: {},
    }
  }

  const body = (error.response.data ?? {}) as ErrorBody
  const fields: Record<string, string> = {}
  if (Array.isArray(body.error?.fields)) {
    for (const item of body.error.fields) {
      if (item && typeof item.field === 'string' && typeof item.message === 'string' && !(item.field in fields)) {
        fields[item.field] = item.message
      }
    }
  }

  return {
    status: error.response.status,
    code: typeof body.error?.code === 'string' ? body.error.code : 'error',
    message: typeof body.error?.message === 'string' ? body.error.message : 'Não foi possível concluir a operação.',
    fields,
  }
}
