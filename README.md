# Memora

Memora é uma aplicação de IA/RAG para preservar e reaproveitar a memória corporativa de projetos. A visão do produto é conectar fontes como o Confluence, indexar documentação histórica e ajudar equipes a encontrar soluções técnicas semelhantes a partir de novas anotações.

Nesta versão, o projeto extrai páginas do Confluence Cloud, converte o HTML para texto, cria embeddings multilíngues e persiste uma base vetorial no ChromaDB. No terminal, é possível fazer busca semântica ou gerar uma análise RAG de reaproveitamento técnico com Ollama, OpenAI ou Gemini. Ainda não há interface web.

## Requisitos

- Python 3.11 ou superior
- Uma conta do Confluence Cloud e um API token da Atlassian
- Ollama local ou uma API key da OpenAI/Gemini para análises generativas

## Configuração

Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copie o exemplo de configuração:

```powershell
Copy-Item .env.example .env
```

Preencha o `.env` com a URL do seu Confluence, e-mail, API token e chave do espaço desejado:

```dotenv
CONFLUENCE_BASE_URL=https://seu-site.atlassian.net/wiki
CONFLUENCE_EMAIL=seu-email@exemplo.com
CONFLUENCE_API_TOKEN=seu-token-aqui
CONFLUENCE_SPACE_KEY=PROJECT-KB
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=memora_projects

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
RAG_TOP_K=8
RAG_MAX_CONTEXT_CHARS=12000
```

> Nunca envie o arquivo `.env` ao GitHub. Ele contém credenciais e já está listado no `.gitignore`.

## Execução

Na raiz do projeto, execute:

```powershell
python -m app.main
```

O terminal mostrará os espaços disponíveis e uma prévia limpa de todas as páginas encontradas no espaço configurado. A busca percorre automaticamente todas as páginas de resultados da API. Falhas de configuração, conexão e HTTP são apresentadas com mensagens claras; o token nunca é exibido.

## Indexação vetorial

Baixe as páginas e gere a base vetorial local:

```powershell
python -m app.index_confluence
```

Na primeira execução, o modelo de embeddings será baixado. Os vetores serão persistidos no diretório configurado por `CHROMA_DB_PATH`.

Depois, faça uma busca semântica:

```powershell
python -m app.search "portal web com login dashboard cadastro de clientes e permissões"
```

Outros exemplos:

```powershell
python -m app.search "sistema para acompanhar chamados SLA status e histórico de solicitações"
python -m app.search "integração com API de pagamentos webhooks conciliação e logs"
```

## Análise RAG generativa

Com a base já indexada, envie as anotações de uma reunião:

```powershell
python -m app.analyze "cliente precisa de um portal web com login, dashboard, cadastro de clientes, permissões por perfil e integração com API externa"
python -m app.analyze "precisamos de um sistema para acompanhar chamados, SLA, status de atendimento e histórico de solicitações"
python -m app.analyze "novo projeto precisa integrar com API de pagamentos, conciliação, webhooks e logs de auditoria"
```

### Ollama

Instale o modelo antes da primeira análise (`ollama pull llama3.1:8b`) e use:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### OpenAI

O modelo é intencionalmente configurável e não possui valor fixo no projeto:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=sua-chave-aqui
OPENAI_MODEL=seu-modelo-aqui
```

### Gemini

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=sua-chave-aqui
GEMINI_MODEL=seu-modelo-aqui
```

Somente as credenciais do provider selecionado são obrigatórias. Nunca publique o `.env`.

## Testes

```powershell
pytest
```

## Estrutura

```text
app/          configuração e entrada CLI
connectors/   integrações com serviços externos
extractors/   limpeza e transformação de conteúdo
indexing/     chunks, embeddings e persistência vetorial
llm/          adapters e factory dos providers generativos
models/       modelos de domínio normalizados
rag/          recuperação, prompt e geração de respostas
tests/        testes automatizados
```

## Próximos passos planejados

- Extrair anexos do Confluence
- Criar uma interface com Streamlit
- Adicionar avaliações automatizadas da qualidade do RAG
