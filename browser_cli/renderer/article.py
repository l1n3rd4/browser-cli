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


LEAF_BLOCK_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "pre", "ul", "ol", "dl", "blockquote",
    "table", "hr",
}

CONTAINER_TAGS = {
    "div", "section", "article", "main", "aside",
    "details", "summary", "header", "figure", "fieldset",
}


def render_article_content(body: Tag, console: Console, base_url: str = "", page_title: str = "") -> None:
    """
    Renderiza o conteúdo do artigo com hierarquia tipográfica de modo leitura,
    percorrendo a árvore DOM de forma linear O(N) e modular.
    """
    clean_page_title = re.sub(r"\s+", " ", page_title).strip().lower()

    def render_leaf(el: Tag, name: str) -> None:
        if name == "hr":
            console.print(Rule(style="dim cyan"))
            console.print()

        elif name == "h1":
            title = re.sub(r"\s+", " ", el.get_text(strip=True))
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

    def walk(node: Tag) -> None:
        for child in node.children:
            if not isinstance(child, Tag):
                continue

            name = child.name

            # Se for um bloco atômico/folha conhecido, renderiza e não entra nos filhos
            if name in LEAF_BLOCK_TAGS:
                render_leaf(child, name)
                continue

            # Se for contêiner ou elemento estrutural
            has_leaf = child.find(lambda t: t.name in LEAF_BLOCK_TAGS)
            if not has_leaf:
                # Sem blocos folha: verifica se há subcontêineres
                has_subcontainer = child.find(lambda t: t.name in CONTAINER_TAGS)
                if has_subcontainer:
                    walk(child)
                else:
                    # Contêiner folha (ex: div que atua como parágrafo de texto)
                    p_text = format_inline(child, base_url)
                    text_str = p_text.plain.strip()
                    if text_str and len(text_str) > 15:
                        console.print(p_text)
                        console.print()
            else:
                walk(child)

    walk(body)
