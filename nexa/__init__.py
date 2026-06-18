# nexa/__init__.py
from .executor import UnifiedExecutor
from .backends.base import WorkflowResult, ModuleResult


def nexa_viz():
    from .viz.cli import main
    main()
