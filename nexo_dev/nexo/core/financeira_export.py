"""
Funções de backup para exportação de arquivos financeiros.
Este módulo contém implementações alternativas para o caso
de falha nas funções principais de exportação.
"""

import csv
import io
from django.http import HttpResponse
from django.utils import timezone


def dados_financeiros_backup():
    """Retorna dados financeiros de backup para quando a API falhar"""
    return {
        "orcamento_total": 1500000,
        "executado_total": 900000,
        "variacao_periodo": 5.2,
        "titulo": "Relatório Financeiro (Backup)",
        "periodo": "Mês Atual",
        "_info": "Dados de backup - os valores podem estar desatualizados",
        "unidades": [
            {
                "codigo": "ADM001",
                "nome": "Secretaria de Administração",
                "orcamento": 400000,
                "executado": 280000,
                "percentual": 70.0,
                "status": "Adequado",
            },
            {
                "codigo": "EDU001",
                "nome": "Secretaria de Educação",
                "orcamento": 650000,
                "executado": 420000,
                "percentual": 64.6,
                "status": "Adequado",
            },
            {
                "codigo": "SAU001",
                "nome": "Secretaria de Saúde",
                "orcamento": 450000,
                "executado": 200000,
                "percentual": 44.4,
                "status": "Atenção",
            },
        ],
        "execucao_mensal": [
            {"mes": "Jan", "orcado": 150000, "executado": 140000},
            {"mes": "Fev", "orcado": 150000, "executado": 145000},
            {"mes": "Mar", "orcado": 150000, "executado": 140000},
            {"mes": "Abr", "orcado": 150000, "executado": 135000},
            {"mes": "Mai", "orcado": 150000, "executado": 170000},
            {"mes": "Jun", "orcado": 150000, "executado": 170000},
        ],
    }


def exportar_csv_simples(dados, componente="completo"):
    """
    Função simplificada para exportar CSV quando a função principal falhar.
    Usa a biblioteca padrão csv para maior confiabilidade.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="financeiro_{componente}_backup.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(["RELATÓRIO FINANCEIRO (BACKUP)"])
    writer.writerow(["Período", dados.get("periodo", "Período atual")])
    writer.writerow(["Data Geração", timezone.now().strftime("%d/%m/%Y %H:%M")])
    writer.writerow([])

    # Resumo
    writer.writerow(["RESUMO FINANCEIRO"])
    writer.writerow(
        [
            "Orçamento Total",
            f'R$ {dados.get("orcamento_total", 0):.2f}'.replace(".", ","),
        ]
    )
    writer.writerow(
        [
            "Executado Total",
            f'R$ {dados.get("executado_total", 0):.2f}'.replace(".", ","),
        ]
    )
    writer.writerow(["Variação Período", f'{dados.get("variacao_periodo", 0):.1f}%'])
    writer.writerow([])

    # Distribuição por Unidade
    writer.writerow(["DISTRIBUIÇÃO POR UNIDADE"])
    writer.writerow(["Unidade", "Orçamento", "Executado", "Percentual", "Status"])

    for unidade in dados.get("unidades", []):
        writer.writerow(
            [
                unidade.get("nome", ""),
                f'R$ {unidade.get("orcamento", 0):.2f}'.replace(".", ","),
                f'R$ {unidade.get("executado", 0):.2f}'.replace(".", ","),
                f'{unidade.get("percentual", 0):.1f}%',
                unidade.get("status", ""),
            ]
        )

    writer.writerow([])

    # Execução Orçamentária
    writer.writerow(["EXECUÇÃO ORÇAMENTÁRIA"])
    writer.writerow(["Mês", "Orçado", "Executado", "% Executado"])

    for execucao in dados.get("execucao_mensal", []):
        orcado = execucao.get("orcado", 0)
        executado = execucao.get("executado", 0)
        percentual = (executado / orcado * 100) if orcado > 0 else 0

        writer.writerow(
            [
                execucao.get("mes", ""),
                f"R$ {orcado:.2f}".replace(".", ","),
                f"R$ {executado:.2f}".replace(".", ","),
                f"{percentual:.1f}%",
            ]
        )

    return response


def exportar_html_simples(dados, componente="completo"):
    """
    Função simplificada para exportar HTML quando a função principal falhar.
    Gera HTML básico sem depender de templates do Django.
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório Financeiro (Backup)</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #2c5282; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .info {{ background-color: #e3f2fd; padding: 10px; border-radius: 4px; margin: 10px 0; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <h1>Relatório Financeiro (Backup)</h1>
        <p>Período: {dados.get("periodo", "Atual")}</p>
        <p>Gerado em: {timezone.now().strftime('%d/%m/%Y %H:%M')}</p>
        
        <div class="info">
            <strong>Nota:</strong> Este é um relatório de backup gerado quando o sistema não conseguiu processar 
            o relatório original. Os dados podem estar desatualizados.
        </div>
        
        <h2>Resumo Financeiro</h2>
        <table>
            <tr>
                <th>Métrica</th>
                <th>Valor</th>
            </tr>
            <tr>
                <td>Orçamento Total</td>
                <td>R$ {dados.get("orcamento_total", 0):.2f}</td>
            </tr>
            <tr>
                <td>Executado Total</td>
                <td>R$ {dados.get("executado_total", 0):.2f}</td>
            </tr>
            <tr>
                <td>Variação Período</td>
                <td>{dados.get("variacao_periodo", 0):.1f}%</td>
            </tr>
        </table>
        
        <h2>Distribuição por Unidade</h2>
        <table>
            <tr>
                <th>Unidade</th>
                <th>Orçamento</th>
                <th>Executado</th>
                <th>Percentual</th>
                <th>Status</th>
            </tr>
    """

    # Adicionar dados das unidades
    for unidade in dados.get("unidades", []):
        html += f"""
            <tr>
                <td>{unidade.get("nome", "")}</td>
                <td>R$ {unidade.get("orcamento", 0):.2f}</td>
                <td>R$ {unidade.get("executado", 0):.2f}</td>
                <td>{unidade.get("percentual", 0):.1f}%</td>
                <td>{unidade.get("status", "")}</td>
            </tr>
        """

    html += """
        </table>
        
        <h2>Execução Orçamentária</h2>
        <table>
            <tr>
                <th>Mês</th>
                <th>Orçado</th>
                <th>Executado</th>
                <th>% Executado</th>
            </tr>
    """

    # Adicionar dados de execução mensal
    for execucao in dados.get("execucao_mensal", []):
        orcado = execucao.get("orcado", 0)
        executado = execucao.get("executado", 0)
        percentual = (executado / orcado * 100) if orcado > 0 else 0

        html += f"""
            <tr>
                <td>{execucao.get("mes", "")}</td>
                <td>R$ {orcado:.2f}</td>
                <td>R$ {executado:.2f}</td>
                <td>{percentual:.1f}%</td>
            </tr>
        """

    # Finalizar HTML
    html += """
        </table>
        
        <div class="footer">
            <p>© 2023-2024 Nexo - Sistema de Gestão - Todos os direitos reservados</p>
        </div>
    </body>
    </html>
    """

    response = HttpResponse(html, content_type="text/html")
    response["Content-Disposition"] = (
        f'inline; filename="financeiro_{componente}_backup.html"'
    )
    return response
