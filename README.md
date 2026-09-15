# Browser CLI (Terminal Reader Mode)

Uma ferramenta em Python que utiliza **Playwright**, **BeautifulSoup** e **Rich** para carregar páginas web via Chromium e renderizá-las no terminal em um verdadeiro **Modo Leitura de Terminal (Terminal Reader Mode)**: tipografia elegante, abas horizontais de navegação, syntax highlighting de código, tabelas estruturadas e remoção completa de ruídos — **100% em modo texto e sem nenhuma imagem**.

## Recursos

- 🔍 **Pesquisa Integrada no Terminal (Livre de Bloqueios & Gratuita)**: Pesquise qualquer assunto diretamente no terminal sem chaves de API e sem CAPTCHAs ou bloqueios de bots através do motor DuckDuckGo HTML/Lite.
- 🔄 **Navegação Interativa com Histórico em Memória**: Navegue pelos resultados numerados (`[1-N]`), abra o artigo desejado e volte instantaneamente (`v`) para a lista anterior sem precisar pesquisar novamente.
- 📖 **Modo Leitura com Tipografia Rica**: Limpeza inteligente de ruídos (banners de cookies, modais, anúncios, sidebars e rodapés de dezenas de categorias) focando no conteúdo central com largura de leitura ergonômica (~95 colunas).
- 📑 **Abas e Navegação Fiel ao CSS**: Elementos de navegação primários (`<nav>`, `<header>`, `.navbar`, `.tabs`, etc.) são apresentados como **painéis de abas horizontais** no topo da página.
- 💻 **Syntax Highlighting em Código**: Blocos de código (`<pre><code>`) contam com detecção de linguagem e realce de sintaxe nativo via `rich.syntax.Syntax`.
- 🚫 **Totalmente Livre de Imagens**: Todas as imagens (`<img>`, `<svg>`, `<picture>`, `<canvas>`, etc.) são bloqueadas no nível de rede e descartadas no processamento, garantindo velocidade máxima e zero ruído.
- 📊 **Tabelas e Listas Estruturadas**: Respeita colunas, tabelas de dados formatadas com bordas arredondadas e listas com marcadores hierárquicos multi-nível (`•`, `⁃`, `◦`).
- 🔗 **Links Clicáveis no Terminal**: Utiliza hiperlinks ANSI compatíveis com terminais modernos (Windows Terminal, VS Code, iTerm, etc.) com resolução automática de URLs relativas para absolutas.
- 📰 **Layout Especializado para Feeds**: Agregadores como Hacker News são renderizados como listas numeradas organizadas com rank, título, domínio e métricas.
- 📄 **Modo Pager (`--pager` / `-p`)**: Permite navegar por artigos longos com scroll interativo via setas/espaço (estilo `less`).

## Estrutura Modular do Projeto

```
browser-cli/
├── browser_cli/
│   ├── __init__.py      # Metadados do pacote e configuração UTF-8
│   ├── browser.py       # Automação Playwright e download do HTML sem imagens
│   ├── config.py        # Configuração do console Rich e UTF-8 para Windows
│   ├── search.py        # Mecanismo de busca HTML/Lite bot-free (DuckDuckGo)
│   ├── interactive.py   # Sessão interativa de pesquisa e navegação com histórico
│   ├── tabs.py          # Identificação e estilização de abas de navegação primárias
│   ├── renderer/        # Motor modular do Modo Leitura de Terminal
│   │   ├── __init__.py  # Orquestrador (render_reader_layout) e exportador da API pública
│   │   ├── article.py   # Hierarquia tipográfica e processamento de blocos
│   │   ├── cleaner.py   # Limpeza de ruídos (scripts, banners, cookies) e extração do corpo
│   │   ├── code.py      # Detecção de linguagem e syntax highlighting
│   │   ├── feed.py      # Layout especializado para agregadores e feeds (ex: Hacker News)
│   │   ├── header.py    # Painel de cabeçalho da página estilizado
│   │   ├── inline.py    # Formatação recursiva de texto inline e hiperlinks
│   │   ├── lists.py     # Renderização de listas ordenadas/não-ordenadas aninhadas
│   │   └── tables.py    # Conversão de tabelas HTML em tabelas Rich formatadas
│   └── cli.py           # Parser de argumentos e orquestração da CLI
├── main.py              # Ponto de entrada leve da aplicação
├── requirements.txt     # Dependências do projeto (Playwright, BeautifulSoup, Rich)
└── README.md            # Documentação e guia de uso
```

## Instalação

1. Clone ou acesse o repositório:
```powershell
cd c:\repos\browser-cli
```

2. Crie e ative o ambiente virtual:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instale as dependências:
```powershell
pip install -r requirements.txt
playwright install chromium
```

## Como Usar

### 1. Modo de Pesquisa Interativo (Sem parâmetros)
Execute sem argumentos para abrir o buscador interativo no terminal:
```powershell
python main.py
```
> **Atalhos do Modo Interativo:**
> - Digite um número `[1-N]` para abrir a página correspondente no modo leitor (com tela limpa).
> - `m` ou `prox`: busca a **próxima tela de resultados (+10)**, limpando a tela anterior.
> - `ant`: volta para a **tela anterior de resultados**.
> - `v`: volta para a lista de resultados da pesquisa atual.
> - `cls` ou `clear`: limpa completamente a tela e o buffer do terminal.
> - `n`: inicia uma nova pesquisa.
> - `u <url>`: acessa diretamente um link ou domínio.
> - `q`: encerra a sessão.

### 2. Pesquisa Direta via Linha de Comando
```powershell
python main.py "python tutorial"
# ou
python main.py -s "noticias tecnologia"
```

### 3. Acesso Direto a uma URL
```powershell
python main.py https://news.ycombinator.com
```

### 4. Leitura de Artigos com Paginação (Pager / Less)
```powershell
python main.py "https://en.wikipedia.org/wiki/Python_(programming_language)" --pager
```

## Opções de Linha de Comando

| Argumento | Descrição |
|-----------|-----------|
| `target` | URL direta ou termo de pesquisa inicial. Se omitido, abre a busca interativa. |
| `-s`, `--search <termo>` | Executa uma busca diretamente pelo termo especificado. |
| `-i`, `--interactive` | Força a inicialização no modo interativo. |
| `-p`, `--pager` | Habilita paginação interativa no terminal (estilo 'less'). |
| `--raw-html` | Exibe o HTML completo retornado pelo Playwright. |
| `--headful` | Abre o navegador de forma visível em vez de headless. |
| `--timeout <ms>` | Timeout de carregamento em milissegundos (padrão: 30000). |
| `--wait-until <cond>` | Condição de espera do carregamento (`domcontentloaded`, `load`, `networkidle`). |
