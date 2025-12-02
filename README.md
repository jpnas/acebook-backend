# AceBook Backend

API em Django + Django REST Framework que alimenta o Acebook. Ela gerencia clubes, quadras, reservas, coaches e usuários, expondo endpoints documentados via Swagger e protegidos com JWT.

- **Stack**: Django 5.2, DRF, Simple JWT (login), drf-spectacular (Swagger), SQLite (dev) / Postgres (prod).
- **Deploy**: Railway – `https://acebook-backend-production-0278.up.railway.app`.
- **Swagger**: `https://acebook-backend-production-0278.up.railway.app/docs/`.
- **Autenticação**: JWT (`/api/auth/login/`) + roles (`admin`, `player`).
- **CRUDs**: quadras, reservas, jogadores e instrutores, respeitando as permissões de cada papel.

## Requisitos

- Python 3.11 ou superior.
- Virtualenv (`python -m venv`) ou equivalente.
- Banco SQLite local (padrão) ou Postgres via `DATABASE_URL`.
- Dependências listadas em `requirements.txt` (inclui `gunicorn`, `psycopg2-binary`, `dj-database-url`).

## Como rodar localmente

```bash
cd backend
python -m venv ../backend-venv
source ../backend-venv/bin/activate
pip install -r requirements.txt

# Variáveis locais (opcional)
export SECRET_KEY=dev-secret
export DEBUG=True
export DATABASE_URL=sqlite:///db.sqlite3

python manage.py migrate
python manage.py createsuperuser  # opcional
python manage.py runserver
# API em http://localhost:8000/api/
```

## Variáveis de ambiente

| Variável               | Descrição                                      | Exemplo                                                    |
| ---------------------- | ---------------------------------------------- | ---------------------------------------------------------- |
| `SECRET_KEY`           | Chave do Django                                | `django-insecure-...`                                      |
| `DEBUG`                | `True/False`                                   | `False`                                                    |
| `ALLOWED_HOSTS`        | Hosts permitidos (vírgulas)                    | `localhost,acebook-backend-production-0278.up.railway.app` |
| `DATABASE_URL`         | Conexão Postgres/SQLite                        | `postgresql://user:pass@host:port/db`                      |
| `CORS_ALLOWED_ORIGINS` | Domínios do frontend autorizados               | `https://acebook-frontend-xi.vercel.app`                   |
| `CSRF_TRUSTED_ORIGINS` | Mesmo domínio do frontend, com `https://`      | `https://acebook-frontend-xi.vercel.app`                   |
| `EMAIL_BACKEND`        | Backend de email                               | `django.core.mail.backends.smtp.EmailBackend`              |
| `EMAIL_HOST`           | Provedor SMTP                                  | `smtp.gmail.com`                                           |
| `EMAIL_PORT`           | Porta do SMTP                                  | `465`                                                      |
| `EMAIL_HOST_USER`      | Usuário/email do SMTP                          | `acebook.app@gmail.com`                                    |
| `EMAIL_HOST_PASSWORD`  | Senha/apppassword                              | `xxxxxxxxxxxxxxxx`                                         |
| `EMAIL_USE_TLS`        | `True/False`                                   | `True`                                                     |
| `EMAIL_USE_SSL`        | `True/False`                                   | `False`                                                    |
| `DEFAULT_FROM_EMAIL`   | Remetente padrão                               | `acebook.app@gmail.com`                                    |
| `FRONTEND_RESET_URL`   | URL do formulário de reset (`/reset-password`) | `https://acebook-frontend-xi.vercel.app/reset-password`    |

## Deploy (Railway)

1. Crie o serviço Postgres e copie o `DATABASE_URL`.
2. Crie o Web Service apontando para este repositório. Build command:  
   `pip install -r requirements.txt && python manage.py collectstatic --noinput`
3. Start command: `gunicorn backend.wsgi`.
4. Defina todas as variáveis da tabela acima (mais `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=...`).
5. Rode `python manage.py migrate` e `python manage.py createsuperuser` via Shell do Railway.
6. API disponível em `https://<serviço>.up.railway.app/api/` e Swagger em `/api/schema/swagger/`.

## Endpoints principais

| Recurso         | Método | Endpoint                              | Observações                          |
| --------------- | ------ | ------------------------------------- | ------------------------------------ |
| Auth            | POST   | `/api/auth/login/`                    | Retorna `{access, refresh, user}`    |
| Registro        | POST   | `/api/auth/register/`                 | Admin cria clube; player entra em um |
| Esqueci senha   | POST   | `/api/auth/password/forgot/`          | Gera token + envia email             |
| Reset senha     | POST   | `/api/auth/password/reset/`           | Valida token e aplica nova senha     |
| Perfil          | GET    | `/api/auth/me/`                       | Dados do usuário logado (JWT)        |
| Quadras         | CRUD   | `/api/courts/`                        | Admins criam/editam; players leem    |
| Coaches         | CRUD   | `/api/coaches/`                       | Admin gerencia; players consultam    |
| Reservas        | CRUD   | `/api/reservations/`                  | Players criam/cancelam; admins total |
| Disponibilidade | GET    | `/api/reservations/availability/`     | Slots ocupados por quadra/data       |
| Usuários clube  | GET    | `/api/club-users/`                    | Admin lista/edita/deleta jogadores   |
| Slug de clube   | GET    | `/api/club-slug/available/?slug=xxxx` | Verifica disponibilidade do código   |
| Swagger         | GET    | `/api/schema/swagger/`                | Interface interativa                 |

Todas as rotas mutáveis exigem `Authorization: Bearer <token>`. Players só acessam dados do próprio clube; admins administram o clube inteiro.

### Como testar o Swagger

1. Abra `https://acebook-backend-production-0278.up.railway.app/docs`.
2. Clique em **Authorize** (canto superior direito).
3. Em `Value`, informe `Bearer <token>`.
   - Obtenha o token pelo próprio Swagger em `/api/auth/login/` (ou via `curl/Postman`) usando um email/senha válido.
   - Copie o campo `access` retornado e cole após `Bearer`.
4. Clique em **Authorize** e depois \*\*Close`. As chamadas autenticadas passarão a usar o token automaticamente.
5. Quando o token expirar, repita o passo 3.

## Relato / Resultados

- **Funcionou**:
  - CRUD completo de quadras, reservas, jogadores e coaches.
  - Login com JWT, registro de admin/player e visões distintas (players só veem os próprios recursos).
  - Endpoint `/reservations/availability/` respeitando horário local e manutenção de quadra.
  - Documentação Swagger e deploy estável no Railway.
- **Não funcionou**:
  - Envio de e-mail via Gmail em produção para recuperação de senha não funcionou.

João Pedro Bonato – 2210028
