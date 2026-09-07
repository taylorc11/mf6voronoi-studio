"""
mf6voronoi_bootstrap.py
=======================
Make ``import mf6Voronoi`` cheap and dependency-light by stubbing pyvista/VTK
when they are not installed.  Import this module **before** importing
``mf6Voronoi``.
"""
import sys
import types


def _install_pyvista_stub() -> bool:
    try:
        import pyvista  # noqa: F401
        return False
    except Exception:
        pass

    pv = types.ModuleType("pyvista")
    pv.__version__ = "0-stub"
    examples = types.ModuleType("pyvista.examples")
    pv.examples = examples

    def _unavailable(*_args, **_kwargs):
        raise RuntimeError(
            "The 3-D pyvista/VTK features of mf6Voronoi are not bundled in this "
            "build. Reinstall pyvista to use them.")

    pv.__getattr__ = lambda name: _unavailable  # type: ignore[attr-defined]
    sys.modules["pyvista"] = pv
    sys.modules["pyvista.examples"] = examples
    return True


STUBBED = _install_pyvista_stub()
