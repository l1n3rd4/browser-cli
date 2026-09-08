import re
from rich import box
from rich.panel import Panel


def create_header(title: str, url: str) -> Panel:
    """Cria um painel de cabeçalho estilizado com título e URL."""
    clean_title = re.sub(r"\s+", " ", title).strip() if title else "Sem Título"
    return Panel(
        f"[bold bright_green]{clean_title}[/bold bright_green]\n[dim cyan]{url}[/dim cyan]",
        border_style="cyan",
        box=box.ROUNDED,
    )
