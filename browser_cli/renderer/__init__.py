"""
Motor de Renderização do Modo Leitura de Terminal (Terminal Reader Mode).
Subdividido em submódulos especializados e coesos.
"""

import browser_cli.config  # noqa: F401
from bs4 import BeautifulSoup
from rich.console import Console

from browser_cli.tabs import extract_navigation_tabs
from browser_cli.renderer.cleaner import strip_noise, extract_reader_body
from browser_cli.renderer.header import create_header
from browser_cli.renderer.inline import format_inline
from browser_cli.renderer.lists import render_list
from browser_cli.renderer.tables import render_table
from browser_cli.renderer.code import extract_language_from_pre, render_code_block
from browser_cli.renderer.feed import render_feed_items
from browser_cli.renderer.article import render_article_content


def render_reader_layout(html_content: str, console: Console, base_url: str = "", page_title: str = "") -> None:
    """
    Modo Leitura de Terminal (Terminal Reader Mode):
    1. Ajusta largura de coluna para leitura confortável e ergonômica (~95 colunas).
    2. Exibe abas horizontais de navegação no topo (se existirem e forem relevantes).
    3. Exibe o conteúdo principal com tipografia limpa, regras divisórias e cores.
    4. 100% texto e totalmente livre de imagens e scripts.
    """
    reader_width = min(console.width or 95, 95)
    reader_console = Console(width=reader_width)

    soup = BeautifulSoup(html_content, "html.parser")
    strip_noise(soup)

    # 1. Extrair e exibir abas / barras de navegação primárias no topo
    tab_panels = extract_navigation_tabs(soup, base_url=base_url)
    for tp in tab_panels:
        reader_console.print(tp)
        reader_console.print()

    # 2. Se for uma lista de links / feeds (ex: Hacker News), renderiza layout especializado
    if render_feed_items(soup, reader_console, base_url=base_url):
        return

    # 3. Extrair corpo principal do artigo e renderizar
    body = extract_reader_body(soup)
    render_article_content(body, reader_console, base_url=base_url, page_title=page_title)


__all__ = [
    "create_header",
    "render_reader_layout",
    "format_inline",
    "strip_noise",
    "extract_reader_body",
    "render_article_content",
    "render_table",
    "render_list",
    "render_code_block",
    "extract_language_from_pre",
    "render_feed_items",
]
