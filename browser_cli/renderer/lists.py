from bs4 import Tag
from rich.console import Console
from rich.text import Text

from browser_cli.renderer.inline import format_inline


def render_list(list_tag: Tag, console: Console, base_url: str = "", level: int = 0) -> None:
    """
    Renderiza listas ordenadas (<ol>) ou não ordenadas (<ul>) com suporte a
    múltiplos níveis de aninhamento e marcadores hierárquicos.
    """
    is_ordered = list_tag.name == "ol"
    bullets = ["• ", "⁃ ", "◦ "]
    bullet_marker = bullets[min(level, len(bullets) - 1)]

    for idx, li in enumerate(list_tag.find_all("li", recursive=False), 1):
        indent = "  " * (level + 1)
        prefix = f"{indent}{idx}. " if is_ordered else f"{indent}{bullet_marker}"

        sublists = li.find_all(["ul", "ol"], recursive=False)

        # Formata nós diretos do li (format_inline ignora sublistas ul/ol)
        li_inline = format_inline(li, base_url)
        li_plain = li_inline.plain.strip()

        if li_plain:
            item_text = Text(prefix, style="bold cyan")
            item_text.append(li_inline)
            console.print(item_text)

        # Renderiza sublistas recursivamente com nível aumentado
        for sub in sublists:
            render_list(sub, console, base_url, level=level + 1)

    if level == 0:
        console.print()
