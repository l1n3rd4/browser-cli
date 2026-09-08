import html
import re
from urllib.parse import urljoin
import bs4
from bs4 import Tag
from rich.text import Text


def format_inline(element: Tag, base_url: str = "") -> Text:
    """
    Formata recursivamente nós de texto inline:
    - Normaliza espaços em branco (colapsa quebras de linha e tabulações do HTML)
    - Negrito (strong, b)
    - Itálico (em, i)
    - Código inline (code, kbd, samp)
    - Links clicáveis (a) com resolução de URLs absolutas
    - Realces e tachados (mark, s, del, strike)
    - Sublinhado (u)
    """
    result = Text()

    def walk(node: bs4.PageElement, current_style: str = "", current_link: str = "") -> None:
        if isinstance(node, bs4.NavigableString):
            raw = html.unescape(str(node))
            clean_str = re.sub(r"<ref[^>]*>.*?</ref>", "", raw, flags=re.DOTALL)
            clean_str = re.sub(r"<ref[^>]*>", "", clean_str)
            clean_str = re.sub(r"\{\{[^}]*\}\}", "", clean_str)
            clean_str = re.sub(r"\s+", " ", clean_str)
            if clean_str:
                # Se o texto atual já termina com espaço e clean_str começa com espaço, colapsa
                if result.plain.endswith(" ") and clean_str.startswith(" "):
                    clean_str = clean_str[1:]
                if clean_str:
                    style_to_apply = f"{current_style} link {current_link}".strip() if current_link else current_style
                    result.append(clean_str, style=style_to_apply or None)
            return

        if not isinstance(node, Tag):
            return

        # Ignorar tags estruturais de bloco dentro de nós inline (exceto o próprio nó raiz)
        if node != element and node.name in ["ul", "ol", "li", "pre", "table"]:
            return

        next_style = current_style
        next_link = current_link

        tag_name = node.name
        if tag_name in ["strong", "b"]:
            next_style = (next_style + " bold").strip()
        elif tag_name in ["em", "i"]:
            next_style = (next_style + " italic").strip()
        elif tag_name in ["code", "kbd", "samp"]:
            next_style = (next_style + " bold bright_cyan on #1a1a2e").strip()
        elif tag_name == "mark":
            next_style = (next_style + " bold black on bright_yellow").strip()
        elif tag_name in ["s", "del", "strike"]:
            next_style = (next_style + " strike dim").strip()
        elif tag_name == "u":
            next_style = (next_style + " underline").strip()
        elif tag_name == "a":
            href = node.get("href", "")
            if href:
                abs_href = urljoin(base_url, href) if base_url else href
                next_link = abs_href
                next_style = (next_style + " bold cyan underline").strip()
            else:
                next_style = (next_style + " cyan underline").strip()

        for child in node.children:
            walk(child, next_style, next_link)

    walk(element)

    # Remover espaços em branco nas pontas
    result.rstrip()
    start = 0
    while start < len(result.plain) and result.plain[start] == " ":
        start += 1
    if start > 0:
        result = result[start:]

    return result
