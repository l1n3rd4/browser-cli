import argparse
import asyncio
from contextlib import nullcontext
from rich import box
from rich.panel import Panel

from browser_cli.browser import fetch_page
from browser_cli.config import clear_screen, console
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

    clear_screen()
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


from browser_cli.interactive import run_interactive_session


def parse_args() -> argparse.Namespace:
    """Configura e analisa os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Browser CLI - Modo Leitura de Terminal de alta fidelidade para navegação e pesquisa na web (100% texto, livre de anúncios e bloqueios)."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="URL do site (ex: example.com) ou termo de busca inicial. Se omitido, abre a busca interativa.",
    )
    parser.add_argument(
        "--search",
        "-s",
        type=str,
        default=None,
        help="Inicia diretamente uma pesquisa pelo termo especificado.",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Inicia o modo interativo de pesquisa e navegação no terminal.",
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


def is_url(text: str) -> bool:
    """Verifica de forma simples se a string parece ser uma URL ou um termo de busca."""
    if not text:
        return False
    t = text.strip()
    if t.startswith(("http://", "https://", "localhost")):
        return True
    # Se contém espaços, é termo de busca
    if " " in t:
        return False
    # Se tem ponto e sem espaços (ex: github.com, news.ycombinator.com)
    if "." in t and not t.endswith("."):
        return True
    return False


def main() -> None:
    args = parse_args()

    # Determina se deve rodar no modo direto de URL ou no modo interativo
    target = args.target

    # Se especificou busca via flag -s/--search
    if args.search:
        asyncio.run(
            run_interactive_session(
                initial_query=args.search,
                use_pager=args.pager,
                headless=not args.headful,
                timeout=args.timeout,
            )
        )
        return

    # Se nenhum alvo foi fornecido, ou se foi pedida a flag interativa
    if not target or args.interactive:
        asyncio.run(
            run_interactive_session(
                initial_query=None,
                use_pager=args.pager,
                headless=not args.headful,
                timeout=args.timeout,
            )
        )
        return

    # Se foi fornecido um texto mas não parece URL (ex: 'python tutorial' ou 'teste')
    if not is_url(target) and not args.raw_html:
        asyncio.run(
            run_interactive_session(
                initial_query=target,
                use_pager=args.pager,
                headless=not args.headful,
                timeout=args.timeout,
            )
        )
        return

    # Caso contrário, navega diretamente na URL
    asyncio.run(
        browse_and_render(
            url=target,
            use_pager=args.pager,
            raw_html=args.raw_html,
            headless=not args.headful,
            timeout=args.timeout,
            wait_until=args.wait_until,
        )
    )

