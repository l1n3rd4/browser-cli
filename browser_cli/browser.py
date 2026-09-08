from playwright.async_api import async_playwright


async def fetch_page(
    url: str,
    headless: bool = True,
    timeout: int = 30000,
    wait_until: str = "domcontentloaded",
) -> tuple[str, str]:
    """
    Navega até uma URL usando Playwright Chromium com bloqueio total de imagens no nível de rede.
    Retorna uma tupla: (titulo_da_pagina, conteudo_html).
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        # Bloqueio total de imagens e mídias para carregamento rápido e sem ruído
        await page.route(
            "**/*.{png,jpg,jpeg,webp,gif,svg,ico,bmp,tiff}",
            lambda route: route.abort(),
        )

        await page.goto(url, wait_until=wait_until, timeout=timeout)

        title = await page.title()
        html = await page.content()

        await browser.close()

    return title, html
