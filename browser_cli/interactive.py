import asyncio
from contextlib import nullcontext
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from browser_cli.browser import fetch_page
from browser_cli.config import clear_screen, console
from browser_cli.renderer import create_header, render_reader_layout
from browser_cli.search import SearchResult, search, SearchResponse


def print_search_banner() -> None:
    """Exibe o cabeçalho de boas-vindas do modo interativo."""
    console.print(
        Panel.fit(
            "[bold cyan]🌐 BROWSER CLI[/bold cyan] [bold white]— Navegador & Motor de Busca no Terminal[/bold white]\n"
            "[dim]Modo Leitor sem anúncios, sem rastreadores, 100% texto e livre de bloqueios de bots.[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )


def display_results_table(
    query: str,
    results: list[SearchResult],
    page: int = 1,
    has_next: bool = False,
    has_prev: bool = False,
    total_loaded: int = 0,
) -> None:
    """Renderiza a lista de resultados da tela atual limpando a tela anterior."""
    clear_screen()
    print_search_banner()
    console.print()

    start_idx = results[0].index if results else 1
    end_idx = results[-1].index if results else len(results)
    page_info = f" • Página {page} [dim](Resultados {start_idx}–{end_idx})[/dim]" if results else ""

    console.print(
        Panel(
            f"🔍 Resultados da busca para: [bold green]\"{query}\"[/bold green]{page_info}",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )

    for r in results:
        content = Text()
        content.append(f"[{r.index}] ", style="bold cyan")
        content.append(f"{r.title}\n", style="bold white")
        content.append(f"    {r.url}\n", style="dim blue underline")
        if r.snippet:
            content.append(f"    {r.snippet}", style="dim")
        console.print(content)
        console.print()

    actions = ["[bold white]Ações:[/bold white] [bold cyan]1-N[/bold cyan] (abrir página)"]
    if has_next:
        actions.append("[bold cyan]m[/bold cyan] ou [bold cyan]prox[/bold cyan] (próxima tela +10)")
    if has_prev:
        actions.append("[bold cyan]ant[/bold cyan] (página anterior)")
    actions.append("[bold cyan]n[/bold cyan] (nova busca)")
    actions.append("[bold cyan]u <url>[/bold cyan] (abrir link)")
    actions.append("[bold cyan]q[/bold cyan] (sair)")

    console.print(
        Panel(
            " │ ".join(actions),
            border_style="dim",
            box=box.ROUNDED,
        )
    )


async def open_and_display_page(
    url: str,
    use_pager: bool = False,
    headless: bool = True,
    timeout: int = 30000,
) -> None:
    """Acessa a página especificada e a renderiza no modo leitor de terminal, limpando a tela anterior."""
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
                wait_until="domcontentloaded",
            )
    except Exception as e:
        clear_screen()
        console.print(
            Panel(
                f"[bold red]Erro ao carregar a página:[/bold red]\n{e}",
                title="Erro de Conexão",
                border_style="red",
                box=box.ROUNDED,
            )
        )
        return

    # Limpa a tela do terminal para a nova página/aba ser exibida com destaque
    clear_screen()
    header = create_header(title, url)

    if use_pager:
        with console.pager(styles=True):
            console.print(header)
            console.print()
            render_reader_layout(html, console, base_url=url, page_title=title)
    else:
        console.print(header)
        console.print()
        render_reader_layout(html, console, base_url=url, page_title=title)


async def run_interactive_session(
    initial_query: str | None = None,
    use_pager: bool = False,
    headless: bool = True,
    timeout: int = 30000,
) -> None:
    """Loop interativo principal do terminal com suporte a paginação e telas limpas."""
    clear_screen()
    print_search_banner()

    current_query: str = initial_query or ""
    current_page: int = 1
    pages: dict[int, list[SearchResult]] = {}
    all_results_by_index: dict[int, SearchResult] = {}
    next_payload: dict[str, str] | None = None
    has_next: bool = False
    current_engine: str = "html"

    def execute_new_search(query_text: str) -> None:
        nonlocal current_query, current_page, pages, all_results_by_index, next_payload, has_next, current_engine
        current_query = query_text
        current_page = 1
        pages = {}
        all_results_by_index = {}
        with console.status(f"[bold cyan]Buscando por '{current_query}'...[/bold cyan]"):
            resp = search(current_query, max_results=10)
        if resp.results:
            pages[1] = resp.results
            for r in resp.results:
                all_results_by_index[r.index] = r
            next_payload = resp.next_payload
            has_next = resp.has_next
            current_engine = resp.engine
            display_results_table(
                current_query,
                pages[1],
                page=1,
                has_next=has_next,
                has_prev=False,
                total_loaded=len(all_results_by_index),
            )
        else:
            clear_screen()
            print_search_banner()
            console.print(f"[yellow]Nenhum resultado encontrado para '{current_query}'.[/yellow]")

    # Se já foi passado um termo inicial
    if current_query:
        execute_new_search(current_query)

    while True:
        try:
            current_results = pages.get(current_page, [])

            # Se ainda não temos resultados, pedimos a pesquisa inicial
            if not current_results:
                prompt_text = "[bold green]🔍 Digite sua pesquisa[/bold green] (ou 'u <url>' para ir direto, 'q' para sair): "
                user_input = console.input(prompt_text).strip()
            else:
                max_idx = max(all_results_by_index.keys()) if all_results_by_index else len(current_results)
                prompt_text = (
                    "[bold green]Escolha uma opção[/bold green] "
                    f"([1-{max_idx}], 'm' mais, 'ant' anterior, 'v' voltar, 'n' nova busca, 'q' sair): "
                )
                user_input = console.input(prompt_text).strip()

            if not user_input:
                continue

            # Sair
            if user_input.lower() in ("q", "quit", "exit", "sair"):
                console.print("[cyan]Encerrando Browser CLI. Até logo![/cyan]")
                break

            # Limpar a tela (cls / clear / limpar)
            if user_input.lower() in ("cls", "clear", "limpar"):
                clear_screen()
                if current_results:
                    display_results_table(
                        current_query,
                        pages[current_page],
                        page=current_page,
                        has_next=has_next or ((current_page + 1) in pages),
                        has_prev=(current_page > 1),
                        total_loaded=len(all_results_by_index),
                    )
                else:
                    print_search_banner()
                continue

            # Próxima tela de resultados (+10 resultados)
            if user_input.lower() in ("m", "mais", "prox", "proxima", "próxima", "next", "+"):
                next_page_num = current_page + 1
                if next_page_num in pages:
                    current_page = next_page_num
                    display_results_table(
                        current_query,
                        pages[current_page],
                        page=current_page,
                        has_next=has_next or ((current_page + 1) in pages),
                        has_prev=True,
                        total_loaded=len(all_results_by_index),
                    )
                    continue

                if has_next and next_payload:
                    start_idx = len(all_results_by_index) + 1
                    with console.status(f"[bold cyan]Buscando próxima tela (+10 resultados)...[/bold cyan]"):
                        resp = search(
                            current_query,
                            max_results=10,
                            next_payload=next_payload,
                            engine=current_engine,
                            start_index=start_idx,
                        )
                    if resp.results:
                        current_page = next_page_num
                        pages[current_page] = resp.results
                        for r in resp.results:
                            all_results_by_index[r.index] = r
                        next_payload = resp.next_payload
                        has_next = resp.has_next
                        current_engine = resp.engine
                        display_results_table(
                            current_query,
                            pages[current_page],
                            page=current_page,
                            has_next=has_next,
                            has_prev=True,
                            total_loaded=len(all_results_by_index),
                        )
                    else:
                        has_next = False
                        console.print("[yellow]Não há mais resultados adicionais para esta pesquisa.[/yellow]")
                else:
                    console.print("[yellow]Fim dos resultados. Não há próxima tela disponível.[/yellow]")
                continue

            # Tela anterior de resultados
            if user_input.lower() in ("ant", "anterior", "prev", "-"):
                if current_page > 1:
                    current_page -= 1
                    display_results_table(
                        current_query,
                        pages[current_page],
                        page=current_page,
                        has_next=has_next or ((current_page + 1) in pages),
                        has_prev=(current_page > 1),
                        total_loaded=len(all_results_by_index),
                    )
                else:
                    console.print("[yellow]Você já está na primeira tela de resultados.[/yellow]")
                continue

            # Voltar à lista de resultados anteriores
            if user_input.lower() in ("v", "voltar", "back"):
                if current_page in pages:
                    display_results_table(
                        current_query,
                        pages[current_page],
                        page=current_page,
                        has_next=has_next or ((current_page + 1) in pages),
                        has_prev=(current_page > 1),
                        total_loaded=len(all_results_by_index),
                    )
                else:
                    console.print("[yellow]Nenhuma lista de resultados anterior disponível.[/yellow]")
                continue

            # Nova pesquisa pelo comando n / nova / busca / search
            if user_input.lower() in ("n", "nova", "search", "busca"):
                new_q = console.input("[bold green]🔍 Nova pesquisa:[/bold green] ").strip()
                if not new_q:
                    continue
                execute_new_search(new_q)
                continue

            # Nova busca direta com prefixo: n <termo> ou busca <termo>
            if user_input.lower().startswith(("n ", "nova ", "busca ", "buscar ")):
                new_q = user_input.split(" ", 1)[1].strip()
                if new_q:
                    execute_new_search(new_q)
                continue

            # Abrir URL direta com prefixo: u <url>
            if user_input.lower().startswith(("u ", "url ", "goto ", "open ")):
                target_url = user_input.split(" ", 1)[1].strip()
                if target_url:
                    await open_and_display_page(target_url, use_pager=use_pager, headless=headless, timeout=timeout)
                    console.rule("[bold cyan]Fim da Leitura[/bold cyan]", style="dim cyan")
                    console.print(
                        "[dim]Comandos: Digite um número ([1-N]), [bold cyan]'v'[/bold cyan] (voltar aos resultados), [bold cyan]'n'[/bold cyan] (nova busca), ou [bold cyan]'q'[/bold cyan] (sair):[/dim]\n"
                    )
                continue

            # Se o usuário digitou uma URL diretamente (ex: https://... ou http://...)
            if user_input.startswith(("http://", "https://", "www.")):
                await open_and_display_page(user_input, use_pager=use_pager, headless=headless, timeout=timeout)
                console.rule("[bold cyan]Fim da Leitura[/bold cyan]", style="dim cyan")
                console.print(
                    "[dim]Comandos: Digite um número ([1-N]), [bold cyan]'v'[/bold cyan] (voltar aos resultados), [bold cyan]'n'[/bold cyan] (nova busca), ou [bold cyan]'q'[/bold cyan] (sair):[/dim]\n"
                )
                continue

            # Se for um número selecionando um resultado
            if user_input.isdigit():
                idx = int(user_input)
                if idx in all_results_by_index:
                    selected = all_results_by_index[idx]
                    console.print(f"\n[bold cyan]Abrindo [{selected.index}] {selected.title}...[/bold cyan]")
                    console.print(f"[dim]{selected.url}[/dim]\n")
                    await open_and_display_page(
                        selected.url,
                        use_pager=use_pager,
                        headless=headless,
                        timeout=timeout,
                    )
                    console.rule("[bold cyan]Fim da Leitura[/bold cyan]", style="dim cyan")
                    console.print(
                        "[dim]Comandos: Digite outro número ([1-N]), [bold cyan]'v'[/bold cyan] (voltar aos resultados), [bold cyan]'m'[/bold cyan] (mais resultados), [bold cyan]'n'[/bold cyan] (nova busca), ou [bold cyan]'q'[/bold cyan] (sair):[/dim]\n"
                    )
                    continue
                else:
                    max_available = max(all_results_by_index.keys()) if all_results_by_index else 0
                    console.print(f"[yellow]Opção inválida. Escolha um número entre 1 e {max_available}.[/yellow]")
                    continue

            # Se não tínhamos resultados ou se o usuário digitou uma frase qualquer, trate como nova busca!
            execute_new_search(user_input)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[cyan]Sessão encerrada.[/cyan]")
            break
        except Exception as e:
            console.print(f"[red]Ocorreu um erro:[/red] {e}")

