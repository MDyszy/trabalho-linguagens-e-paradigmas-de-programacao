# Sistema de Estoque — Paradigma Orientado a Dados

API REST para controle de estoque de produtos, construída com **FastAPI** e
**PostgreSQL**. O projeto é o trabalho final da disciplina **LPP** e tem como
objetivo demonstrar o **paradigma de programação orientado a dados**: o estado
do sistema não é mutado diretamente — ele é **derivado** de um histórico de
eventos imutáveis, e a lógica de negócio vive em **funções puras** que apenas
recebem dados e devolvem dados.

> **Ideia central:** a quantidade em estoque de um produto **não é um campo no
> banco**. Ela é calculada (`saldo = entradas − saídas`) a partir da tabela de
> movimentações, que é *append-only*. O sistema só **cria** produtos e
> **registra** movimentações — não existe `UPDATE` nem `DELETE`.

---

## Índice

- [Escopo do projeto](#escopo-do-projeto)
- [Tecnologias](#tecnologias)
- [Paradigma orientado a dados](#paradigma-orientado-a-dados)
- [Arquitetura](#arquitetura)
- [Modelo de dados](#modelo-de-dados)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como executar](#como-executar)
- [Acessos](#acessos)
- [Referência da API](#referência-da-api)
- [Exemplo de uso completo](#exemplo-de-uso-completo)
- [Regras de negócio](#regras-de-negócio)
- [Notas de desenvolvimento](#notas-de-desenvolvimento)

---

## Escopo do projeto

Projeto acadêmico (trabalho final da disciplina **LPP**) cujo objetivo é
**demonstrar o paradigma de programação orientado a dados** aplicado a um caso
concreto: o controle de estoque de produtos. O foco está na **modelagem**
(eventos imutáveis + estado derivado por funções puras), e não em entregar um
sistema de produção completo.

**Funcionalidades (em escopo):**

- Cadastro de produtos, com a categoria criada automaticamente pelo nome
- Consulta de produtos (lista e por ID) e de categorias
- Registro de movimentações de estoque (entrada/saída) como **eventos imutáveis**
- Saldo de estoque **derivado** do histórico de movimentações (nunca armazenado)
- Alerta de produtos com saldo abaixo do estoque mínimo
- Histórico de movimentações por produto

---

## Tecnologias

- **Linguagem:** Python 3.11
- **Framework web:** FastAPI (ASGI, servido pelo Uvicorn)
- **ORM:** SQLAlchemy 2.0
- **Validação / serialização:** Pydantic 2
- **Banco de dados:** PostgreSQL 15
- **Infraestrutura:** Docker e Docker Compose
- **Visualização do banco:** pgAdmin 4

O schema do banco é criado automaticamente na inicialização da aplicação
(`Base.metadata.create_all`), a partir dos modelos SQLAlchemy.

---

## Paradigma orientado a dados

O projeto é organizado em torno dos **dados** e de **transformações** sobre
eles, e não em torno de objetos que guardam e mutam estado. Os princípios
aparecem assim no código:

| Princípio | Como é aplicado | Onde |
|-----------|-----------------|------|
| **Dados imutáveis** | A tabela `movimentacao` é *append-only*: cada entrada/saída é um evento que nunca é alterado nem apagado. | [`models/movimentacao.py`](backend/app/models/movimentacao.py) |
| **Estado derivado** | A `quantidade` do produto é um saldo calculado por um *fold* (`reduce`) sobre os eventos, não uma coluna. | [`domain/estoque.py`](backend/app/domain/estoque.py), [`models/produto.py`](backend/app/models/produto.py) |
| **Código separado dos dados** | As regras (saldo, alerta, validação de saída) são **funções puras**, sem banco e sem framework. | [`domain/estoque.py`](backend/app/domain/estoque.py) |
| **Sem mutação de estado** | Não há `PUT` nem `DELETE`. Para mudar o estoque, registra-se uma movimentação. | [`routers/produto_router.py`](backend/app/routers/produto_router.py) |

As funções puras de domínio:

```python
def saldo(movimentacoes) -> int:        # entradas somam, saídas subtraem (fold)
def em_alerta(saldo, estoque_minimo)    # saldo abaixo do mínimo?
def pode_retirar(saldo, quantidade)     # há saldo suficiente para a saída?
```

Como elas não dependem de banco nem de framework, são **determinísticas e
facilmente testáveis** — uma das principais vantagens do paradigma.

---

## Arquitetura

O backend segue uma arquitetura em camadas, com uma camada de **domínio**
(funções puras) separada da infraestrutura:

```
HTTP  ─►  router  ─►  service  ─►  repository  ─►  banco (SQLAlchemy/ORM)
                         │
                         └─►  domain (funções puras)  ◄─ usa os dados, sem I/O
```

- **router** — define os endpoints e os contratos HTTP (schemas Pydantic).
- **service** — orquestra as regras de negócio e chama o domínio.
- **repository** — único ponto que fala com o banco de dados.
- **domain** — funções puras de cálculo (saldo, alertas, validações).
- **schemas** — modelos Pydantic de entrada (`Create`) e saída (`Response`),
  separados dos modelos ORM (separação entre *schema* e *representação*).

---

## Modelo de dados

```
┌──────────────┐        ┌──────────────────────┐        ┌────────────────────────┐
│  categoria   │        │       produto        │        │      movimentacao      │
├──────────────┤        ├──────────────────────┤        ├────────────────────────┤
│ id           │1      N│ id                   │1      N│ id                     │
│ nome         │───────►│ nome                 │───────►│ produto_id  (FK)       │
└──────────────┘        │ categoria_id  (FK)   │        │ tipo  (entrada/saida)  │
                        │ estoque_minimo       │        │ quantidade             │
                        │ imagem_url           │        │ data                   │
                        │ quantidade  (derivada)│       └────────────────────────┘
                        └──────────────────────┘          (append-only / imutável)
```

- **`categoria`** — agrupa produtos. Criada automaticamente ao cadastrar um
  produto (pelo nome), se ainda não existir.
- **`produto`** — dados cadastrais + `estoque_minimo`. A **`quantidade` não é
  uma coluna**: é uma *property* derivada do histórico de movimentações.
- **`movimentacao`** — log de eventos imutáveis (`entrada` ou `saida`). Apagar
  um produto remove em cascata suas movimentações (não exposto via API).

---

## Estrutura do projeto

```
trabalho-final-lpp/
├── backend/
│   ├── app/
│   │   ├── domain/
│   │   │   └── estoque.py            # Funções puras: saldo (fold), alerta, validações
│   │   ├── models/                   # Modelos ORM (SQLAlchemy)
│   │   │   ├── categoria.py
│   │   │   ├── produto.py            # quantidade = property derivada (não é coluna)
│   │   │   └── movimentacao.py       # tabela append-only de eventos
│   │   ├── schemas/                  # Schemas Pydantic (validação/serialização)
│   │   │   ├── categoria.py
│   │   │   ├── produto.py
│   │   │   └── movimentacao.py
│   │   ├── repositories/             # Acesso ao banco de dados
│   │   │   ├── categoria_repository.py
│   │   │   ├── produto_repository.py
│   │   │   └── movimentacao_repository.py
│   │   ├── services/                 # Regras de negócio
│   │   │   ├── categoria_service.py
│   │   │   ├── produto_service.py
│   │   │   └── movimentacao_service.py
│   │   ├── routers/                  # Endpoints da API
│   │   │   ├── categoria_router.py
│   │   │   ├── produto_router.py
│   │   │   └── movimentacao_router.py
│   │   ├── database.py               # Engine, sessão, Base e get_db
│   │   └── main.py                   # Cria as tabelas e registra os routers
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml                # db (Postgres) + backend + pgAdmin
├── .env.example
└── README.md
```

---

## Como executar

Pré-requisito: **Docker** e **Docker Compose** instalados.

**1. Clone o repositório**
```bash
git clone https://github.com/MDyszy/trabalho-final-lpp.git
cd trabalho-final-lpp
```

**2. Configure as variáveis de ambiente**

Crie o arquivo `.env` a partir do exemplo e preencha os valores:
```bash
cp .env.example .env
```
```env
POSTGRES_USER=usuario
POSTGRES_PASSWORD=senha
POSTGRES_DB=estoque
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
```
> O `.env` está no `.gitignore` e **não** é versionado.

**3. Suba os containers**
```bash
docker compose up --build
```

A aplicação fica disponível em `http://localhost:8000`. As tabelas são criadas
automaticamente na primeira inicialização.

Para parar: `docker compose down` (ou `docker compose down -v` para apagar
também os dados do banco).

---

## Acessos

| Serviço | URL | Descrição |
|---------|-----|-----------|
| API     | http://localhost:8000      | API REST |
| Swagger | http://localhost:8000/docs | Documentação interativa (testar endpoints) |
| pgAdmin | http://localhost:5050      | Visualização do banco |

Para conectar ao banco no pgAdmin, registre um servidor com:
- **Host:** `db`
- **Port:** `5432`
- **User / Password / Database:** conforme o `.env`

---

## Referência da API

### Produtos

| Método | Rota                | Descrição                                   |
|--------|---------------------|---------------------------------------------|
| GET    | `/produtos/`        | Lista todos os produtos (com saldo derivado) |
| GET    | `/produtos/alertas` | Lista produtos com saldo abaixo do mínimo   |
| GET    | `/produtos/{id}`    | Busca um produto por ID (404 se não existir) |
| POST   | `/produtos/`        | Cria um produto                             |

**Corpo de criação (`POST /produtos/`):**

| Campo            | Tipo            | Obrigatório | Observação                              |
|------------------|-----------------|-------------|-----------------------------------------|
| `nome`           | string          | sim         | —                                       |
| `categoria_nome` | string          | sim         | Categoria criada automaticamente se nova |
| `quantidade`     | int             | não (0)     | Estoque inicial → vira uma entrada       |
| `estoque_minimo` | int             | sim         | Limite para disparar alerta             |
| `imagem_url`     | string \| null  | não         | —                                       |

**Resposta (produto):** `id`, `nome`, `categoria_id`, `quantidade` (derivada),
`estoque_minimo`, `imagem_url`.

### Categorias

| Método | Rota               | Descrição                  |
|--------|--------------------|----------------------------|
| GET    | `/categorias/`     | Lista todas as categorias  |
| GET    | `/categorias/{id}` | Busca uma categoria por ID |

> Categorias são criadas **implicitamente** ao cadastrar um produto; não há
> endpoint de criação direta.

### Movimentações de estoque

| Método | Rota                             | Descrição                            |
|--------|----------------------------------|--------------------------------------|
| POST   | `/produtos/{id}/movimentacoes`   | Registra uma entrada ou saída        |
| GET    | `/produtos/{id}/movimentacoes`   | Histórico de movimentações do produto |

**Corpo do registro (`POST /produtos/{id}/movimentacoes`):**

| Campo        | Tipo                       | Observação                          |
|--------------|----------------------------|-------------------------------------|
| `tipo`       | `"entrada"` \| `"saida"`   | —                                   |
| `quantidade` | int (> 0)                  | Saída não pode exceder o saldo atual |

**Resposta (movimentação):** `id`, `produto_id`, `tipo`, `quantidade`, `data`.

---

## Exemplo de uso completo

**1. Criar um produto com estoque inicial 5 e mínimo 10**
```http
POST /produtos/
{
  "nome": "Arroz",
  "categoria_nome": "Alimentos",
  "quantidade": 5,
  "estoque_minimo": 10
}
```
A categoria `Alimentos` é criada automaticamente, e o estoque inicial `5` vira a
primeira movimentação de **entrada**. Resposta:
```json
{ "id": 1, "nome": "Arroz", "categoria_id": 1, "quantidade": 5, "estoque_minimo": 10, "imagem_url": null }
```

**2. O produto aparece nos alertas (5 < 10)**
```http
GET /produtos/alertas
→ [ { "id": 1, "nome": "Arroz", "quantidade": 5, ... } ]
```

**3. Registrar uma entrada de 20 unidades**
```http
POST /produtos/1/movimentacoes
{ "tipo": "entrada", "quantidade": 20 }
```

**4. O saldo é recalculado para 25 (5 + 20) e sai dos alertas**
```http
GET /produtos/1
→ { "id": 1, "quantidade": 25, "estoque_minimo": 10, ... }

GET /produtos/alertas
→ []
```

**5. Tentar uma saída maior que o saldo é rejeitado**
```http
POST /produtos/1/movimentacoes
{ "tipo": "saida", "quantidade": 100 }
→ 400  { "detail": "Saída de 100 maior que o saldo atual (25)" }
```

**6. Consultar o histórico imutável**
```http
GET /produtos/1/movimentacoes
→ [
    { "id": 1, "tipo": "entrada", "quantidade": 5,  "data": "..." },
    { "id": 2, "tipo": "entrada", "quantidade": 20, "data": "..." }
  ]
```

Exemplo equivalente com `curl`:
```bash
curl -X POST http://localhost:8000/produtos/ \
  -H "Content-Type: application/json" \
  -d '{"nome":"Arroz","categoria_nome":"Alimentos","quantidade":5,"estoque_minimo":10}'
```

---

## Regras de negócio

- **Estoque é derivado:** `quantidade = soma(entradas) − soma(saídas)`, calculado
  em tempo de leitura a partir das movimentações.
- **Append-only:** produtos só são criados e movimentações só são registradas —
  não há alteração nem exclusão pela API.
- **Categoria automática:** ao criar um produto, a categoria é reutilizada (pelo
  nome) ou criada se não existir.
- **Estoque inicial:** o campo `quantidade` no cadastro vira a primeira
  movimentação de entrada (ou nenhuma, se for 0).
- **Alerta de estoque:** um produto está em alerta quando `saldo < estoque_minimo`.
- **Validação de saída:** a quantidade deve ser positiva, e uma saída não pode
  deixar o saldo negativo (HTTP 400 caso contrário).
- **Erros:** produto inexistente retorna **404**; dados inválidos, **422** (Pydantic);
  violação de regra de negócio, **400**.

---

## Notas de desenvolvimento

- O código do backend é **copiado** na imagem (`COPY . .`) na hora do build.
  Por isso, após alterar o código, é preciso reconstruir a imagem:
  ```bash
  docker compose up --build -d backend
  ```
- Para **recarga automática** durante o desenvolvimento (o `--reload` do Uvicorn
  já está no `Dockerfile`), monte o código como volume no serviço `backend` do
  `docker-compose.yml`:
  ```yaml
  backend:
    build: ./backend
    volumes:
      - ./backend:/app
  ```
- Alterações no **modelo de dados** (colunas/tabelas) exigem recriar o banco,
  pois o `create_all` não altera tabelas existentes:
  ```bash
  docker compose down -v && docker compose up --build
  ```
