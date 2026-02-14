from typing import Protocol, runtime_checkable
from argparse import _SubParsersAction
from aide.core.context import Context

@runtime_checkable
class Plugin(Protocol):
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        ...
