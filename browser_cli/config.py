import os
import sys
from rich.console import Console

# Configuração de UTF-8 no Windows para compatibilidade adequada com consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def clear_screen(*args, **kwargs) -> None:
    """Limpa completamente a tela e o histórico de rolagem do terminal de forma robusta e cross-platform."""
    try:
        # Comando nativo do SO: 'cls' no Windows, 'clear' no Linux/macOS
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass

    try:
        # Sequências ANSI para garantir cursor no topo e scrollback limpo (xterm/Windows Terminal/VS Code)
        # \033[H: cursor para (1, 1)
        # \033[2J: limpa a tela visível
        # \033[3J: limpa o buffer de histórico de rolagem
        sys.stdout.write("\033[H\033[2J\033[3J")
        sys.stdout.flush()
    except Exception:
        pass


console = Console()
# Vincula console.clear à limpeza completa do sistema e do buffer de rolagem
console.clear = clear_screen  # type: ignore[assignment]

