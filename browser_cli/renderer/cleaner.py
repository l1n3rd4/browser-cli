from bs4 import BeautifulSoup, Tag


def strip_noise(soup: BeautifulSoup) -> None:
    """
    Remove ruídos visuais, códigos de rastreamento, mídias e elementos secundários
    para deixar o DOM pronto para o Modo Leitura.
    """
    # 1. Tags de mídia e scripts
    media_and_scripts = [
        "img",
        "svg",
        "picture",
        "video",
        "canvas",
        "iframe",
        "audio",
        "source",
        "noscript",
        "script",
        "style",
        "template",
        "footer",
        "aside",
        "form",
    ]
    for tag in soup(media_and_scripts):
        tag.decompose()

    # 2. Banners de cookies, anúncios, modais e elementos ocultos
    def is_noise(tag: Tag) -> bool:
        if not isinstance(tag, Tag):
            return False

        # Elementos explicitamente ocultos
        if tag.get("hidden") is not None or tag.get("aria-hidden") == "true":
            return True
        style = tag.get("style", "").lower()
        if "display: none" in style or "visibility: hidden" in style:
            return True

        role = tag.get("role", "").lower()
        if role in ["dialog", "alertdialog", "complementary", "contentinfo"]:
            return True

        tag_classes = tag.get("class", [])
        classes_str = " ".join(tag_classes).lower()
        tag_id = tag.get("id", "").lower()
        combined = f"{classes_str} {tag_id}"

        # Wikipédia: remover números de citação [1], links de edição [edit], navboxes e categorias
        if tag.name == "sup" and any("reference" in c for c in tag_classes):
            return True
        if any(cls in classes_str for cls in [
            "mw-editsection", "reflist", "navbox", "vertical-navbox", "catlinks", "printfooter", "mw-jump-link"
        ]):
            return True
        if tag_id in ["toc", "mw-navigation"]:
            return True
        if tag.name == "table" and "infobox" in classes_str:
            return True

        # Documentação Sphinx / Python: remover âncoras ¶ e sidebar
        if "headerlink" in classes_str or "sphinxsidebar" in classes_str:
            return True

        # Padrões comuns de anúncios, banners de cookies, popups e newsletters
        noise_patterns = [
            "cookie",
            "consent",
            "gdpr",
            "ad-container",
            "advertisement",
            "google-ad",
            "newsletter-signup",
            "subscribe-form",
            "social-share",
            "share-buttons",
            "popup-modal",
            "modal-backdrop",
        ]
        return any(pat in combined for pat in noise_patterns)

    for noisy in soup.find_all(is_noise):
        noisy.decompose()


def extract_reader_body(soup: BeautifulSoup) -> Tag:
    """
    Identifica o container principal do artigo (Readability pattern),
    descartando barras laterais e cabeçalhos genéricos.
    """
    # 1. Artigo semântico explícito
    article = soup.find("article")
    if article and len(article.get_text(strip=True)) > 150:
        return article

    # 2. Main semântico
    main = soup.find("main") or soup.find(attrs={"role": "main"})
    if main and len(main.get_text(strip=True)) > 150:
        return main

    # 3. Classes ou IDs comuns de conteúdo
    content_candidates = soup.find_all(
        lambda tag: tag.name in ["div", "section"]
        and (
            tag.get("id")
            and any(k in tag.get("id", "").lower() for k in [
                "content", "main-content", "article-body", "mw-parser-output"
            ])
            or tag.get("class")
            and any(k in " ".join(tag.get("class", [])).lower() for k in [
                "post-content", "article-content", "entry-content", "markdown-body", "mw-parser-output"
            ])
        )
    )
    for candidate in content_candidates:
        if len(candidate.get_text(strip=True)) > 150:
            return candidate

    return soup.body or soup
