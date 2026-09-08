from urllib.parse import urljoin
from bs4 import BeautifulSoup
from rich import box
from rich.panel import Panel


def extract_navigation_tabs(soup: BeautifulSoup, base_url: str = "") -> list[Panel]:
    """
    Identifica a barra de navegação principal (header, navbars, abas) e
    constrói um painel horizontal estilizado para o topo do terminal.
    Limita a abas primárias (2 a 10 links) para evitar poluição com índices ou rodapés.
    """
    seen_texts = set()

    # Procura candidatos de navegação principal no topo do documento
    nav_candidates = soup.find_all(
        lambda tag: tag.name in ["nav", "header"]
        or tag.get("role") in ["navigation", "tablist"]
        or (
            tag.get("class")
            and any(
                k in " ".join(tag.get("class", [])).lower()
                for k in ["navbar", "nav-tabs", "tabs", "pagetop", "top-nav", "main-nav"]
            )
        )
    )

    primary_panel = None

    for nav in nav_candidates:
        links = nav.find_all("a")
        # Filtra apenas links visíveis e significativos
        valid_links = []
        for a in links:
            text = a.get_text(strip=True)
            # Ignora ícones vazios ou links de pular para conteúdo
            if not text or len(text) > 35 or text.lower().startswith("skip"):
                continue
            if text not in seen_texts:
                seen_texts.add(text)
                valid_links.append((text, a.get("href", "")))

        # Só é considerado uma barra de abas se tiver entre 2 e 10 itens
        if 2 <= len(valid_links) <= 10 and primary_panel is None:
            tab_items = []
            for text, href in valid_links:
                abs_href = urljoin(base_url, href) if base_url and href else href
                if abs_href:
                    tab_items.append(
                        f"[bold white on #005f87] [link={abs_href}]{text}[/link] [/]"
                    )
                else:
                    tab_items.append(f"[bold white on #333333] {text} [/]")

            tab_bar = "  ".join(tab_items)
            primary_panel = Panel(
                tab_bar,
                title="[bold cyan]Navegação / Abas[/bold cyan]",
                box=box.ROUNDED,
                border_style="cyan",
            )

        # Decompõe para não duplicar no corpo do texto
        nav.decompose()

    # Remove quaisquer outras tags <nav> residuais para evitar poluição
    for leftover_nav in soup.find_all("nav"):
        leftover_nav.decompose()

    return [primary_panel] if primary_panel else []
