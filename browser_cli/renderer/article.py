import re
from bs4 import Tag
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from browser_cli.renderer.code import render_code_block
from browser_cli.renderer.inline import format_inline
from browser_cli.renderer.lists import render_list
from browser_cli.renderer.tables import render_table


def render_article_content(body: Tag, console: Console, base_url: str = "", page_title: str = "") -> None:
    """
    Renderiza o conteúdo do artigo com hierarquia tipográfica de modo leitura,
    percorrendo blocos top-down e impedindo duplicações de nós aninhados.
    """
    block_tags = {
        "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "pre", "ul", "ol", "dl", "blockquote",
        "table", "hr", "div", "section"
    }

    all_blocks = body.find_all(lambda tag: tag.name in block_tags)
    processed_blocks: set[Tag] = set()

    clean_page_title = re.sub(r"\s+", " ", page_title).strip().lower()

    for el in all_blocks:
        # Se algum ancestral de bloco já foi processado, pula para evitar duplicação!
        if any(parent in processed_blocks for parent in el.parents):
            continue

        name = el.name

        # Suporte a <div> ou <section> que atuam como parágrafos diretos (sem outros blocos filhos)
        if name in ["div", "section"]:
            child_blocks = el.find_all(lambda t: t.name in (block_tags - {"div", "section"}))
            if not child_blocks:
                processed_blocks.add(el)
                p_text = format_inline(el, base_url)
                if p_text.plain.strip() and len(p_text.plain.strip()) > 15:
                    console.print(p_text)
                    console.print()
            continue

        processed_blocks.add(el)

        if name == "hr":
            console.print(Rule(style="dim cyan"))
            console.print()

        elif name == "h1":
            title = re.sub(r"\s+", " ", el.get_text(strip=True))
            # Evita duplicar se o título for idêntico ao já impresso no painel do topo
            if title and (not clean_page_title or title.lower() not in clean_page_title):
                console.print(Rule(f" {title} ", style="bold bright_cyan"))
                console.print()

        elif name == "h2":
            h2_text = re.sub(r"\s+", " ", el.get_text(strip=True).replace("[edit]", ""))
            if h2_text and len(h2_text) < 120:
                console.print(Rule(f" {h2_text} ", style="bold cyan", align="left"))
                console.print()

        elif name == "h3":
            h3_text = re.sub(r"\s+", " ", el.get_text(strip=True).replace("[edit]", ""))
            if h3_text and len(h3_text) < 120:
                console.print(Text(f"◆  {h3_text}", style="bold yellow"))
                console.print()

        elif name in ["h4", "h5", "h6"]:
            h_text = re.sub(r"\s+", " ", el.get_text(strip=True).replace("[edit]", ""))
            if h_text:
                console.print(Text(f"▸  {h_text}", style="bold bright_white"))
                console.print()

        elif name == "p":
            p_text = format_inline(el, base_url)
            if p_text.plain.strip():
                console.print(p_text)
                console.print()

        elif name == "pre":
            render_code_block(el, console)

        elif name in ["ul", "ol"]:
            render_list(el, console, base_url, level=0)

        elif name == "dl":
            for child in el.children:
                if isinstance(child, Tag):
                    if child.name == "dt":
                        dt_text = format_inline(child, base_url)
                        if dt_text.plain.strip():
                            console.print(Text("  ▸ ", style="bold cyan") + dt_text)
                    elif child.name == "dd":
                        dd_text = format_inline(child, base_url)
                        if dd_text.plain.strip():
                            console.print(Text("    ") + dd_text)
                            console.print()

        elif name == "blockquote":
            quote_text = format_inline(el, base_url)
            if quote_text.plain.strip():
                console.print(
                    Panel(
                        quote_text,
                        border_style="dim cyan",
                        box=box.ROUNDED,
                        padding=(0, 2),
                    )
                )
                console.print()

        elif name == "table":
            render_table(el, console)
