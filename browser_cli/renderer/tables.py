import re
from bs4 import Tag
from rich import box
from rich.console import Console
from rich.table import Table


def render_table(table_tag: Tag, console: Console) -> None:
    """Converte um elemento <table> em uma Rich Table bem formatada."""
    rows = table_tag.find_all("tr")
    if not rows:
        return

    ths = table_tag.find_all("th")
    rtable = Table(box=box.ROUNDED, border_style="dim cyan", show_header=bool(ths))

    if ths:
        for th in ths:
            col_text = re.sub(r"\s+", " ", th.get_text(strip=True))
            rtable.add_column(col_text or "-", style="bold cyan")
        for tr in rows:
            tds = tr.find_all("td")
            if len(tds) == len(ths):
                rtable.add_row(*[re.sub(r"\s+", " ", td.get_text(" ", strip=True)) for td in tds])
        console.print(rtable)
        console.print()
        return

    # Tabelas sem <th> (ex: pares chave/valor)
    cols_count = max(len(tr.find_all(["td", "th"])) for tr in rows)
    if 2 <= cols_count <= 6:
        for i in range(cols_count):
            rtable.add_column(f"Col {i+1}", style="white")
        for tr in rows:
            tds = tr.find_all(["td", "th"])
            vals = [re.sub(r"\s+", " ", td.get_text(" ", strip=True)) for td in tds]
            while len(vals) < cols_count:
                vals.append("")
            if any(vals):
                rtable.add_row(*vals)
        console.print(rtable)
        console.print()
