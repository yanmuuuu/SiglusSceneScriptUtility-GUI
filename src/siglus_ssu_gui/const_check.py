from __future__ import annotations


def const_available() -> bool:
    try:
        from siglus_ssu._const_manager import _read_validated_const

        _read_validated_const()
        return True
    except (FileNotFoundError, RuntimeError, ImportError):
        return False
