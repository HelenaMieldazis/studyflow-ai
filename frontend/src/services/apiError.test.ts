import { AxiosError } from 'axios'
import { describe, expect, it } from 'vitest'
import { apiError } from '../test/utils'
import { getApiError } from './apiError'

describe('getApiError', () => {
  it('extrai código, mensagem e erros por campo da resposta da API', () => {
    const info = getApiError(
      apiError(422, {
        code: 'unprocessable_entity',
        message: 'Verifique os dados informados.',
        fields: [
          { field: 'email', message: 'Informe um e-mail válido.' },
          { field: 'password', message: 'Use pelo menos 12 caracteres.' },
        ],
      }),
    )

    expect(info).toEqual({
      status: 422,
      code: 'unprocessable_entity',
      message: 'Verifique os dados informados.',
      fields: { email: 'Informe um e-mail válido.', password: 'Use pelo menos 12 caracteres.' },
    })
  })

  it('traduz falha de rede numa mensagem compreensível', () => {
    const info = getApiError(new AxiosError('Network Error', 'ERR_NETWORK'))
    expect(info.code).toBe('network_error')
    expect(info.message).toMatch(/Não foi possível conectar/)
  })

  it('ignora respostas fora do formato esperado', () => {
    const info = getApiError(apiError(502, { code: 1 as unknown as string, message: {} as unknown as string }))
    expect(info.code).toBe('error')
    expect(info.message).toBe('Não foi possível concluir a operação.')
  })

  it('trata erros que não vêm do Axios', () => {
    expect(getApiError(new Error('x')).code).toBe('unknown')
  })
})
