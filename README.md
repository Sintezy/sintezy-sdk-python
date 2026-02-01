# Sintezy SDK Python

SDK oficial para integração com a plataforma Sintezy.

## Instalação

```bash
pip install sintezy
```

## Uso Rápido

```python
from sintezy import SintezySDK

# 1. Inicializar a SDK
sdk = SintezySDK(
    client_id='seu-client-id',
    client_secret='seu-client-secret'
)

# 2. Criar uma consulta (autenticação é automática)
appointment = sdk.create_appointment(
    user_email='medico@clinica.com',
    user_name='Dr. João Silva',
    layout={
        'fields': [
            {'name': 'Queixa Principal', 'content': 'inserir aqui a queixa principal', 'position': 0},
            {'name': 'História da Doença Atual', 'content': 'inserir aqui a história', 'position': 1},
            {'name': 'Exame Físico', 'content': 'inserir aqui os exames', 'position': 2},
            {'name': 'Diagnóstico', 'content': 'inserir aqui o diagnóstico', 'position': 3},
            {'name': 'Conduta', 'content': 'inserir aqui a conduta', 'position': 4},
        ]
    }
)

# 3. Abrir portal para gravação
print(f"Portal URL: {appointment.portal_url}")
# O médico grava a consulta no portal

# 4. Após finalizar, buscar o documento principal
documento = sdk.get_document(appointment.secure_id, 'document')

# 5. Gerar outros documentos
receita = sdk.generate_document(appointment.secure_id, 'prescription')
atestado = sdk.generate_document(appointment.secure_id, 'certificate')
```

## Métodos Disponíveis

### Autenticação

| Método | Descrição |
|--------|-----------|
| `authenticate()` | Autentica usando Client Credentials (OAuth 2.0). Chamado automaticamente. |
| `is_authenticated()` | Verifica se há um token válido |

### Consultas (Appointments)

| Método | Descrição |
|--------|-----------|
| `create_appointment(...)` | Cria uma nova consulta e retorna a URL do portal |
| `get_appointment(secure_id)` | Busca uma consulta pelo ID |
| `delete_appointment(secure_id)` | Exclui uma consulta (soft delete) |

### Documentos

| Método | Descrição |
|--------|-----------|
| `generate_document(secure_id, type)` | Gera um documento a partir de uma consulta finalizada |
| `get_document(secure_id, type)` | Busca um documento específico |
| `list_documents(secure_id)` | Lista todos os documentos disponíveis |

## Tipos de Documento

| Tipo | Descrição |
|------|-----------|
| `document` | Prontuário/Documento principal (gerado automaticamente ao finalizar) |
| `anamnese_summary` | Resumo de anamnese |
| `clinic_summary` | Resumo clínico |
| `referral` | Encaminhamento |
| `exames_call` | Solicitação de exames |
| `prescription` | Receita médica |
| `certificate` | Atestado médico |
| `inss_report` | Laudo INSS |

## Licença

MIT
