"""Funções de formatação em pt-BR usadas pela interface."""
from __future__ import annotations

import math


def brl(valor: float, compacto: bool = False) -> str:
    """Formata um valor em reais.

    >>> brl(1234567)
    'R$ 1.234.567'
    >>> brl(1234567, compacto=True)
    'R$ 1,2 mi'
    >>> brl(48500, compacto=True)
    'R$ 49 mil'
    """
    if compacto:
        absoluto = abs(valor)
        if absoluto >= 1e6:
            texto = f"{valor / 1e6:.1f}".replace(".", ",") + " mi"
        elif absoluto >= 1e3:
            texto = f"{math.floor(valor / 1e3 + 0.5):.0f} mil"  # arredonda metade para cima
        else:
            texto = f"{valor:.0f}"
        return f"R$ {texto}"
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def inteiro(valor: float) -> str:
    """Inteiro com separador de milhar brasileiro."""
    return f"{valor:,.0f}".replace(",", ".")
