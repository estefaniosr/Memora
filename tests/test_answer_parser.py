from rag.answer_parser import parse_answer_sections


def test_parser_splits_markdown_headings_into_sections() -> None:
    answer = """### 1. Resumo da nova demanda
Criar um sistema de ponto.

### 2. Projetos antigos mais semelhantes
Foram encontrados os projetos **PM-001** e **PM-002**.

### 3. Evidências encontradas nos documentos
- Registro de entrada e saída
- Auditoria de alterações
"""

    sections = parse_answer_sections(answer)

    assert [section["number"] for section in sections] == [1, 2, 3]
    assert sections[0]["paragraphs"] == ["Criar um sistema de ponto."]
    assert sections[1]["paragraphs"] == [
        "Foram encontrados os projetos PM-001 e PM-002."
    ]
    assert sections[2]["items"] == [
        "Registro de entrada e saída",
        "Auditoria de alterações",
    ]


def test_parser_handles_headings_returned_on_one_line() -> None:
    answer = (
        "### 1. Resumo da nova demanda Registro de ponto dos funcionários. "
        "### 2. Projetos antigos mais semelhantes O **PM-002** possui controles. "
        "### 3. Evidências encontradas nos documentos Há registro e auditoria. "
        "### 4. O que pode ser reaproveitado - Estrutura de dados - Autenticação"
    )

    sections = parse_answer_sections(answer)

    assert len(sections) == 4
    assert sections[0]["paragraphs"] == ["Registro de ponto dos funcionários."]
    assert sections[3]["items"] == ["Estrutura de dados", "Autenticação"]


def test_parser_falls_back_to_safe_plain_content() -> None:
    sections = parse_answer_sections("Resposta com **ênfase** e `código`.")

    assert sections == [
        {
            "number": 1,
            "title": "Análise gerada",
            "paragraphs": ["Resposta com ênfase e código."],
            "items": [],
        }
    ]


def test_parser_recognizes_section_titles_formatted_as_bullets() -> None:
    answer = """- Resumo da nova demanda
Sistema para operações de jogos.
- Projetos antigos mais semelhantes
- PM-011 — Automação de Onboarding
- PM-005 — Plataforma de Agendamento
- Evidências encontradas
- O PM-011 descreve práticas de automação.
- O que pode ser reaproveitado
- Componentes de automação e gerenciamento de usuários.
- Possível estrutura inicial
- Módulo de operações
- Interface administrativa
"""

    sections = parse_answer_sections(answer)

    assert [section["number"] for section in sections] == [1, 2, 3, 4, 5]
    assert sections[1]["items"] == [
        "PM-011 — Automação de Onboarding",
        "PM-005 — Plataforma de Agendamento",
    ]
    assert sections[3]["items"] == [
        "Componentes de automação e gerenciamento de usuários."
    ]
    assert sections[4]["items"] == [
        "Módulo de operações",
        "Interface administrativa",
    ]
