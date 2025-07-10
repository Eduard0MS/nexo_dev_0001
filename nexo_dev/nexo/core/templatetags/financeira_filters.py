from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def divisao(value, arg):
    """Divide o valor pelo argumento e retorna o resultado em percentual."""
    try:
        if arg == 0:
            return 0
        return (float(value) / float(arg)) * 100
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


@register.filter
def porcentagem(value):
    """Formata o valor como percentual."""
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "0,0%"


@register.filter
def moeda(value):
    """Formata o valor como moeda (R$)."""
    try:
        if value is None:
            return "R$ 0,00"

        # Converter para float para garantir
        valor_float = float(value)

        # Formatar com separador de milhares e duas casas decimais
        valor_formatado = f"R$ {valor_float:,.2f}"

        # Adaptar para o formato brasileiro (substituir . por , e , por .)
        valor_formatado = (
            valor_formatado.replace(",", "X").replace(".", ",").replace("X", ".")
        )

        return valor_formatado
    except (TypeError, ValueError, AttributeError):
        return "R$ 0,00"


@register.filter
def percentual_execucao(executado, orcado):
    """Calcula o percentual de execução orçamentária."""
    try:
        if float(orcado) == 0:
            return 0
        return (float(executado) / float(orcado)) * 100
    except (TypeError, ValueError, ZeroDivisionError):
        return 0
