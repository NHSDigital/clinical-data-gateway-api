"""Pytest configuration for the stubs package.

``stubs/__init__.py`` imports from two modules that cannot be loaded in a bare
Python 3 environment:

* ``stubs.provider.stub`` – contains Python 2-only multi-exception syntax
  (``except A, B, C:``), which is a ``SyntaxError`` in Python 3.
* ``stubs.sds.stub`` – depends on ``gateway_api``, which is not on the path
  when running the stubs package in isolation.

This conftest lives *outside* the ``stubs`` Python package (this directory has
no ``__init__.py``), so pytest loads it as a plain script before it attempts to
import any ``stubs.*`` module.  Pre-populating ``sys.modules`` with minimal
stand-ins for the two problematic modules allows the package-level import to
complete without touching the broken files.
"""

import sys
from pathlib import Path
from types import ModuleType

# Make the ``stubs`` package importable from any pytest working directory.
_stubs_root = Path(__file__).parent  # …/gateway-api/stubs
sys.path.insert(0, str(_stubs_root))


def _register(name: str) -> ModuleType:
    if name not in sys.modules:
        sys.modules[name] = ModuleType(name)
    return sys.modules[name]


# Stub out gateway_api (required by stubs.sds.stub).
_register("gateway_api")
_register("gateway_api.get_structured_record")

# Stub out stubs.provider (Python 2 syntax in its stub.py).
_register("stubs.provider")
_provider_stub = _register("stubs.provider.stub")
if not hasattr(_provider_stub, "GpProviderStub"):
    _provider_stub.GpProviderStub = type("GpProviderStub", (), {})  # type: ignore[attr-defined]

# Stub out stubs.sds (depends on gateway_api which is not installed here).
_register("stubs.sds")
_sds_stub = _register("stubs.sds.stub")
if not hasattr(_sds_stub, "SdsFhirApiStub"):
    _sds_stub.SdsFhirApiStub = type("SdsFhirApiStub", (), {})  # type: ignore[attr-defined]
