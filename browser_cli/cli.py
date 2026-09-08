import argparse
import asyncio
from contextlib import nullcontext
from rich import box
from rich.panel import Panel

from browser_cli.browser import fetch_page
from browser_cli.config import console
from browser_cli.renderer import create_header, render_reader_layout


async def browse_and_render(
    url: str,
    use_pager: bool = False,
    raw_html: bool = False,
    headless: bool = True,
    timeout: int = 30000,
    wait_until: str = "domcontentloaded",
) -> None:
    """Orquestra o download da página via Playwright e a renderização estrutural no terminal."""
    status_ctx = (
        console.status(f"[bold cyan]Acessando {url}...[/bold cyan]", spinner="dots")
        if console.is_terminal
        else nullcontext()
    )

    try:
        with status_ctx:
            title, html = await fetch_page(
                url=url,
                headless=headless,
                timeout=timeout,
                wait_until=wait_until,
            )
    except Exception as e:
        console.print(
            Panel(
                f"[bold red]Erro ao navegar na página:[/bold red]\n{e}",
                title="Erro de Conexão",
                border_style="red",
                box=box.ROUNDED,
            )
        )
        return

    # Se o usuário solicitou apenas o HTML bruto retornado pelo Playwright
    if raw_html:
        console.print(html)
        return

    header = create_header(title, url)

    # Renderização no Modo Leitura de Terminal
    if use_pager:
        with console.pager(styles=True):
            console.print(header)
            console.print()
            render_reader_layout(html, console, base_url=url, page_title=title)
    else:
        console.print(header)
        console.print()
        render_reader_layout(html, console, base_url=url, page_title=title)


def parse_args() -> argparse.Namespace:
    """Configura e analisa os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Browser CLI - Modo Leitura de Terminal de alta fidelidade para navegação em websites (100% texto, sem imagens, tipografia rica e abas)."
    )
    parser.add_argument(
        "url",
        help="URL do site a ser acessado (ex: example.com ou https://news.ycombinator.com)",
    )
    parser.add_argument(
        "--pager",
        "-p",
        action="store_true",
        help="Habilita paginação interativa (estilo 'less') para navegar em páginas longas.",
    )
    parser.add_argument(
        "--raw-html",
        action="store_true",
        help="Exibe o HTML bruto retornado pelo Playwright.",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Abre o navegador de forma visível em vez de rodar headless.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Timeout de carregamento em milissegundos (padrão: 30000).",
    )
    parser.add_argument(
        "--wait-until",
        default="domcontentloaded",
        choices=["domcontentloaded", "load", "networkidle"],
        help="Condição de espera do carregamento (padrão: domcontentloaded).",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(
        browse_and_render(
            url=args.url,
            use_pager=args.pager,
            raw_html=args.raw_html,
            headless=not args.headful,
            timeout=args.timeout,
            wait_until=args.wait_until,
        )
    )
