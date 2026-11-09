# Segurança

Registro das medidas implementadas, pendentes e limitações conhecidas. Atualizado a cada etapa.

## Autenticação e sessões (Etapa 2)

| Ameaça | Medida | Teste automatizado |
|---|---|---|
| Vazamento do banco expõe senhas | Argon2id (argon2-cffi, perfil RFC 9106), salt por senha, rehash automático se os parâmetros mudarem | `test_password_is_stored_as_argon2id_hash` |
| Vazamento do banco expõe sessões | Banco guarda só SHA-256 do token | `test_session_token_is_stored_only_as_hash` |
| Roubo de sessão via XSS | Cookie `HttpOnly`; token CSRF só em memória; nada em `localStorage` | `test_register_creates_user_session_and_secure_cookie`, e2e e `api.test.ts` |
| Interceptação em rede | Cookie `Secure` + prefixo `__Host-` em produção; app não inicia sem isso | `test_production_config_refuses_insecure_settings` |
| Logout que não desloga | Sessão apagada no servidor | `test_logout_invalidates_session_on_server` |
| Sessão eterna | Expiração por inatividade (2 h) e absoluta (7 dias); limpeza via CLI | `test_session_expires_*`, `test_cleanup_command_*` |
| Fixação de sessão | Login sempre gera token novo e revoga o anterior | `test_login_replaces_previous_session_of_same_browser` |
| Senha trocada, invasor continua logado | Troca de senha encerra todas as sessões | `test_change_password_revokes_all_other_sessions` |
| CSRF | Token HMAC vinculado à sessão no header `X-CSRF-Token` + `SameSite=Lax` + verificação de `Origin` + JSON obrigatório | `test_state_changing_request_without_csrf_token_is_rejected`, `test_csrf_token_from_another_session_is_rejected`, `test_requests_from_untrusted_origin_are_blocked` |
| Enumeração de contas no login | Mesma resposta e tempo equivalente (hash fictício) para e-mail inexistente e senha errada | `test_wrong_password_and_unknown_email_get_identical_responses` |
| Força bruta | 5 tentativas/15 min e 20/dia **por conta**; 10/min e 50/h **por IP** | `test_login_is_rate_limited_per_account` |
| Credential stuffing | Limite por IP em todas as contas | `test_login_is_rate_limited_per_ip_across_many_accounts` |
| Criação em massa de contas | 5 cadastros/h por IP | `test_registration_is_rate_limited_per_ip` |
| Operações sensíveis sem confirmação | Alterar e-mail, trocar senha e excluir conta exigem a senha atual | `test_changing_email_requires_current_password`, `test_delete_account_requires_password` |
| IDOR / Broken Access Control | Nenhuma rota recebe id de usuário; o usuário vem sempre da sessão | `test_user_cannot_modify_another_account_by_id`, `test_each_user_only_sees_own_account` |
| Mass assignment | Pydantic com `extra="forbid"`: campos inesperados geram 422 | `test_mass_assignment_is_rejected`, `test_register_validates_input` |
| SQL Injection | ORM com consultas parametrizadas; e-mail validado | `test_sql_injection_*` |
| XSS armazenado | API só devolve JSON com `nosniff` e CSP `default-src 'none'`; React escapa o conteúdo; sem `dangerouslySetInnerHTML` | `test_xss_payload_is_returned_as_json_data_never_as_html`, `App.test.tsx` (XSS) e e2e |
| Spoofing de texto | Nomes com caracteres de controle ou de direção (bidi) são rejeitados | `test_control_and_bidi_characters_are_rejected` |
| Open redirect pós-login | Destino aceito só se for caminho interno | `redirect.test.ts`, `LoginPage.test.tsx` |
| Payloads gigantes | Limite global de 1 MiB; senha máx. 128 caracteres (evita DoS no hash) | `test_oversized_registration_payload_is_rejected` |
| Cache de dados pessoais | `Cache-Control: no-store` em toda a API | `test_register_creates_user_session_and_secure_cookie` |

### Validação de entrada

- E-mail: formato validado por `email-validator`, normalizado (minúsculas), máx. 254 caracteres.
- Nome: 1 a 80 caracteres, normalização Unicode NFC, sem caracteres de controle nem bidi.
- Senha nova: 12 a 128 caracteres, não pode ser só espaços nem igual ao e-mail. Sem regras de composição obrigatória (seguindo NIST SP 800-63B): frases-senha são incentivadas.
- Corpo da requisição: precisa ser `application/json` e um objeto; campos extras são rejeitados.

### Logs

Registram apenas eventos (`auth.login_failed`, `auth.login_succeeded user_id=…`, `account.deleted user_id=…`). Nunca e-mail, senha, token ou corpo de requisição. O limitador de requisições usa o **hash** do e-mail como chave. Verificado no teste ponta a ponta: nenhum e-mail ou senha aparece no log do servidor.

## Base (Etapa 1)

- Segredos apenas em variáveis de ambiente; `.env` no `.gitignore`.
- Ambiente padrão `production` (falha fechada). Em produção a aplicação não inicia com `SECRET_KEY` fraca, sem `DATABASE_URL`, com CORS `*` ou HTTP, ou com cookie não-`Secure`.
- Erros centralizados em JSON, sem stack trace; `/api/health` não revela detalhes do banco.
- CORS com lista explícita de origens.
- Headers: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, CSP restritiva, `Cross-Origin-Resource-Policy`, `Permissions-Policy`, HSTS fora de dev/teste.
- PostgreSQL publicado só em `127.0.0.1`, `scram-sha-256`, limites de CPU/memória.

## Pendente

| Etapa | Medida |
|---|---|
| 2.1 | Recuperação de senha por e-mail: token de uso único (PyJWT + registro no banco), expiração curta, resposta idêntica para e-mail existente ou não, Mailpit em desenvolvimento. |
| 3+ | Toda consulta filtrada pelo usuário autenticado; paginação obrigatória. |
| 4 | Camada de IA isolada; separação de instruções e dados (prompt injection); limites e timeout. |
| 7 | Proteção contra SSRF ao processar links. |
| 8 | Gunicorn com usuário não-root; proxy reverso com HTTPS; `ProxyFix` (IP real para o rate limit); Redis para o rate limit com vários workers; CSP do frontend; agendamento de `cleanup-sessions`; varredura de dependências na CI. |

## Limitações conhecidas

- **Enumeração no cadastro:** tentar cadastrar um e-mail existente retorna 409, revelando que a conta existe. Sem confirmação por e-mail não há como evitar isso sem prejudicar a experiência. Mitigação: limite de 5 cadastros/h por IP. Será revisto junto com a verificação de e-mail.
- **Rate limit em memória:** vale por processo e é zerado ao reiniciar. Em produção com vários workers, é necessário Redis (`RATELIMIT_STORAGE_URI`).
- **Bloqueio por conta pode ser abusado:** um atacante pode esgotar as tentativas de uma vítima (bloqueio temporário de 15 min). É o custo de proteger contra força bruta distribuída; o limite é temporário.
- **IP atrás de proxy:** sem `ProxyFix` (Etapa 8), todos os clientes atrás de um proxy compartilham o mesmo limite por IP.
- **Sem MFA:** autenticação de dois fatores não faz parte do MVP.
- O servidor de desenvolvimento do Flask não deve ser usado em produção.
- Testes passando não significam que o sistema é seguro; uma revisão de segurança dedicada será feita antes da publicação.
