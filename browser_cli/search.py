import urllib.request
import urllib.parse
from dataclasses import dataclass
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class SearchResult:
    index: int
    title: str
    url: str
    snippet: str


@dataclass
class SearchResponse:
    results: list[SearchResult]
    has_next: bool = False
    next_payload: dict[str, str] | None = None
    engine: str = "html"

    def __iter__(self):
        return iter(self.results)

    def __len__(self):
        return len(self.results)

    def __getitem__(self, item):
        return self.results[item]


def clean_ddg_url(raw_url: str) -> str:
    """Extrai a URL de destino real caso o link seja um redirecionador uddg do DuckDuckGo."""
    if not raw_url:
        return ""
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url

    parsed = urllib.parse.urlparse(raw_url)
    qs = urllib.parse.parse_qs(parsed.query)
    if "uddg" in qs and qs["uddg"]:
        return qs["uddg"][0]
    return raw_url


def _extract_next_payload(soup: BeautifulSoup) -> dict[str, str] | None:
    """Extrai campos ocultos e de controle do formulário 'Next' do DuckDuckGo."""
    for f in soup.find_all("form"):
        inputs = {
            inp.get("name"): inp.get("value", "")
            for inp in f.find_all("input")
            if inp.get("name")
        }
        if "s" in inputs or "nextParams" in inputs:
            return inputs
    return None


def search_duckduckgo_html(
    query: str,
    max_results: int = 15,
    next_payload: dict[str, str] | None = None,
    start_index: int = 1,
) -> SearchResponse:
    """
    Realiza busca no DuckDuckGo HTML (sem bloqueio de bots, sem javascript, gratuito).
    Suporta paginação passando next_payload retornado da requisição anterior.
    """
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    if next_payload:
        data = urllib.parse.urlencode(next_payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
    else:
        encoded_query = urllib.parse.quote_plus(query)
        req = urllib.request.Request(f"{url}?q={encoded_query}", headers=headers)

    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    soup = BeautifulSoup(html, "html.parser")
    results: list[SearchResult] = []

    items = soup.select(".result")
    count = start_index

    for item in items:
        if "result--ad" in item.get("class", []):
            continue

        title_tag = item.select_one(".result__title a")
        snippet_tag = item.select_one(".result__snippet")

        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        raw_href = title_tag.get("href", "")
        dest_url = clean_ddg_url(raw_href)

        if not dest_url or dest_url.startswith("/"):
            continue

        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

        results.append(
            SearchResult(
                index=count,
                title=title,
                url=dest_url,
                snippet=snippet,
            )
        )
        count += 1
        if len(results) >= max_results:
            break

    next_form = _extract_next_payload(soup)

    return SearchResponse(
        results=results,
        has_next=bool(next_form),
        next_payload=next_form,
        engine="html",
    )


def search_duckduckgo_lite(
    query: str,
    max_results: int = 15,
    next_payload: dict[str, str] | None = None,
    start_index: int = 1,
) -> SearchResponse:
    """
    Fallback usando DuckDuckGo Lite se a versão HTML retornar vazia.
    Suporta paginação passando next_payload.
    """
    url = "https://lite.duckduckgo.com/lite/"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    if next_payload:
        data = urllib.parse.urlencode(next_payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
    else:
        encoded_query = urllib.parse.quote_plus(query)
        req = urllib.request.Request(f"{url}?q={encoded_query}", headers=headers)

    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    soup = BeautifulSoup(html, "html.parser")
    results: list[SearchResult] = []

    link_tags = soup.select(".result-link")
    snippet_tags = soup.select(".result-snippet")
    count = start_index

    for i, link_tag in enumerate(link_tags):
        raw_href = link_tag.get("href", "")
        dest_url = clean_ddg_url(raw_href)
        if not dest_url or dest_url.startswith("/"):
            continue

        title = link_tag.get_text(strip=True)
        snippet = snippet_tags[i].get_text(strip=True) if i < len(snippet_tags) else ""

        results.append(
            SearchResult(
                index=count,
                title=title,
                url=dest_url,
                snippet=snippet,
            )
        )
        count += 1
        if len(results) >= max_results:
            break

    next_form = _extract_next_payload(soup)

    return SearchResponse(
        results=results,
        has_next=bool(next_form),
        next_payload=next_form,
        engine="lite",
    )


def search(
    query: str,
    max_results: int = 10,
    next_payload: dict[str, str] | None = None,
    engine: str = "html",
    start_index: int = 1,
) -> SearchResponse:
    """
    Busca principal que tenta DuckDuckGo HTML e usa Lite como fallback.
    Suporta paginação mantendo a sequência de índices e payload da próxima tela.
    """
    if engine != "lite":
        try:
            resp = search_duckduckgo_html(
                query,
                max_results=max_results,
                next_payload=next_payload,
                start_index=start_index,
            )
            if resp.results:
                return resp
        except Exception:
            pass

    try:
        return search_duckduckgo_lite(
            query,
            max_results=max_results,
            next_payload=next_payload,
            start_index=start_index,
        )
    except Exception:
        return SearchResponse(results=[], has_next=False, next_payload=None, engine=engine)

