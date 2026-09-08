from bs4 import Tag
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text


def extract_language_from_pre(pre_tag: Tag) -> str:
    """Tenta detectar a linguagem de programação de um bloco <pre> ou <code>."""
    classes = list(pre_tag.get("class", []))
    code_tag = pre_tag.find("code")
    if code_tag and code_tag.get("class"):
        classes.extend(code_tag.get("class", []))

    for cls in classes:
        cls_lower = cls.lower()
        if cls_lower.startswith("language-"):
            return cls_lower.replace("language-", "")
        if cls_lower.startswith("highlight-"):
            return cls_lower.replace("highlight-", "")
        if cls_lower in [
            "python", "py", "javascript", "js", "html", "css", "bash", "sh",
            "json", "sql", "rust", "go", "c", "cpp"
        ]:
            return cls_lower
    return ""


def render_code_block(pre_tag: Tag, console: Console) -> None:
    """Renderiza um bloco de código <pre> com Syntax highlighting e painel estilizado."""
    code = pre_tag.get_text().rstrip()
    if not code:
        return

    lang = extract_language_from_pre(pre_tag)
    if lang:
        try:
            renderable = Syntax(code, lang, theme="monokai", line_numbers=False, word_wrap=True)
        except Exception:
            renderable = Text(code, style="bright_white")
    else:
        renderable = Text(code, style="bright_white")

    title_badge = f"[bold cyan] {lang.upper()} [/bold cyan]" if lang else "[dim cyan] Código [/dim cyan]"
    console.print(
        Panel(
            renderable,
            box=box.ROUNDED,
            border_style="dim cyan",
            title=title_badge,
        )
    )
    console.print()
