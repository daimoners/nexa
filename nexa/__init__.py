# nexa/__init__.py
from .executor import UnifiedExecutor

# Entry point per la CLI di visualizzazione
def nexa_viz():
    from .viz.cli import main
    main()
