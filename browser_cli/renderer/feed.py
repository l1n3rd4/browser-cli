import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from rich.console import Console
from rich.text import Text


def render_feed_items(soup: BeautifulSoup, console: Console, base_url: str = "") -> bool:
    """
    Detecta e renderiza feeds e agregadores de links (ex: Hacker News, Reddit)
    com formatação limpa, colorida e legível para terminal.
    """
    hn_items = soup.find_all("tr", class_="athing")
    if not hn_items:
        return False

    for tr in hn_items:
        rank = tr.find(class_="rank")
        rank_str = rank.get_text(strip=True) if rank else ""
        titleline = tr.find(class_="titleline")
        title_a = titleline.find("a") if titleline else None
        title_text = title_a.get_text(strip=True) if title_a else ""
        raw_href = title_a.get("href", "") if title_a else ""
        abs_href = urljoin(base_url, raw_href) if base_url and raw_href else raw_href

        sitestr = titleline.find(class_="sitestr") if titleline else None
        domain = f"({sitestr.get_text(strip=True)})" if sitestr else ""

        sub = tr.find_next_sibling("tr")
        subtext = sub.find(class_="subtext") if sub else None
        sub_str = subtext.get_text(" ", strip=True) if subtext else ""
        sub_str = re.sub(r"\s+", " ", sub_str)

        line = Text()
        line.append(f"{rank_str:>4}  ", style="bold cyan")
        if abs_href:
            line.append(title_text, style=f"bold white link {abs_href}")
        else:
            line.append(title_text, style="bold white")

        if domain:
            line.append(f"  {domain}", style="dim cyan")
        if sub_str:
            line.append(f"\n      {sub_str}", style="dim white")

        console.print(line)
        console.print()

    return True
