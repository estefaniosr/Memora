from extractors.html_cleaner import clean_confluence_html


def test_clean_confluence_html_removes_tags_and_keeps_text() -> None:
    html = """
    <html>
      <head><style>.hidden { display: none; }</style></head>
      <body>
        <h1>Projeto Aurora</h1>
        <p>Decisão técnica <strong>importante</strong>.</p>
        <script>alert('não incluir')</script>
      </body>
    </html>
    """

    result = clean_confluence_html(html)

    assert "Projeto Aurora" in result
    assert "Decisão técnica" in result
    assert "importante" in result
    assert "<h1>" not in result
    assert "display: none" not in result
    assert "não incluir" not in result


def test_clean_confluence_html_handles_empty_input() -> None:
    assert clean_confluence_html("") == ""
