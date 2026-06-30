# Memora

Memora é uma aplicação de IA/RAG para preservar e reaproveitar a memória corporativa de projetos. A visão do produto é conectar fontes como o Confluence, indexar documentação histórica e ajudar equipes a encontrar soluções técnicas semelhantes a partir de novas anotações.

Nesta primeira versão, o projeto apenas valida a integração com o Confluence Cloud: lista espaços, localiza páginas por CQL, obtém seu conteúdo e converte o HTML para texto simples. Ainda não há LLM, embeddings, banco vetorial ou interface web.

## Requisitos

- Python 3.11 ou superior
- Uma conta do Confluence Cloud e um API token da Atlassian

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
```


## Execução

Na raiz do projeto, execute:

```powershell
python -m app.main
```

O terminal mostrará os espaços disponíveis e uma prévia limpa de todas as páginas encontradas no espaço configurado. A busca percorre automaticamente todas as páginas de resultados da API. Falhas de configuração, conexão e HTTP são apresentadas com mensagens claras; o token nunca é exibido.

## Testes

```powershell
pytest
```

## Estrutura

```text
app/          configuração e entrada CLI
connectors/   integrações com serviços externos
extractors/   limpeza e transformação de conteúdo
models/       modelos de domínio normalizados
tests/        testes automatizados
```

## Próximos passos planejados

- Extrair anexos do Confluence
- Dividir documentos em chunks
- Gerar embeddings
- Persistir vetores no ChromaDB
- Criar uma interface com Streamlit
- Integrar OpenAI, Gemini ou Ollama
