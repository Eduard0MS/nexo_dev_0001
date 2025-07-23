#!/usr/bin/env python3
"""
Script para limpar completamente o banco de dados e cache do sistema
"""

import os
import django
import dotenv
import shutil
from pathlib import Path

# Configurar Django
dotenv.load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

from core.models import (
    UnidadeCargo, 
    CargoSIORG, 
    PlanilhaImportada,
    RelatorioGratificacoes,
    RelatorioEfetivo,
    RelatorioGratificacoesPlan1,
    SimulacaoSalva,
    SolicitacaoRealocacao,
    SolicitacaoPermuta,
    ConfiguracaoRelatorio,
    TipoUsuario,
    SolicitacaoSimulacao,
    NotificacaoSimulacao,
    Decreto
)

def limpar_banco_completo():
    """Limpa todos os dados do banco de dados"""
    print("🗑️ Iniciando limpeza completa do banco de dados...")
    
    # Contadores
    total_removidos = 0
    
    # 1. Limpar UnidadeCargo
    count = UnidadeCargo.objects.count()
    UnidadeCargo.objects.all().delete()
    print(f"   ✅ UnidadeCargo: {count} registros removidos")
    total_removidos += count
    
    # 2. Limpar CargoSIORG
    count = CargoSIORG.objects.count()
    CargoSIORG.objects.all().delete()
    print(f"   ✅ CargoSIORG: {count} registros removidos")
    total_removidos += count
    
    # 3. Limpar PlanilhaImportada
    count = PlanilhaImportada.objects.count()
    PlanilhaImportada.objects.all().delete()
    print(f"   ✅ PlanilhaImportada: {count} registros removidos")
    total_removidos += count
    
    # 4. Limpar Relatórios
    count = RelatorioGratificacoes.objects.count()
    RelatorioGratificacoes.objects.all().delete()
    print(f"   ✅ RelatorioGratificacoes: {count} registros removidos")
    total_removidos += count
    
    count = RelatorioEfetivo.objects.count()
    RelatorioEfetivo.objects.all().delete()
    print(f"   ✅ RelatorioEfetivo: {count} registros removidos")
    total_removidos += count
    
    count = RelatorioGratificacoesPlan1.objects.count()
    RelatorioGratificacoesPlan1.objects.all().delete()
    print(f"   ✅ RelatorioGratificacoesPlan1: {count} registros removidos")
    total_removidos += count
    
    # 5. Limpar Simulações
    count = SimulacaoSalva.objects.count()
    SimulacaoSalva.objects.all().delete()
    print(f"   ✅ SimulacaoSalva: {count} registros removidos")
    total_removidos += count
    
    # 6. Limpar Solicitações
    count = SolicitacaoRealocacao.objects.count()
    SolicitacaoRealocacao.objects.all().delete()
    print(f"   ✅ SolicitacaoRealocacao: {count} registros removidos")
    total_removidos += count
    
    count = SolicitacaoPermuta.objects.count()
    SolicitacaoPermuta.objects.all().delete()
    print(f"   ✅ SolicitacaoPermuta: {count} registros removidos")
    total_removidos += count
    
    # 7. Limpar Configurações
    count = ConfiguracaoRelatorio.objects.count()
    ConfiguracaoRelatorio.objects.all().delete()
    print(f"   ✅ ConfiguracaoRelatorio: {count} registros removidos")
    total_removidos += count
    
    # 8. Limpar Tipos de Usuário
    count = TipoUsuario.objects.count()
    TipoUsuario.objects.all().delete()
    print(f"   ✅ TipoUsuario: {count} registros removidos")
    total_removidos += count
    
    # 9. Limpar Solicitações de Simulação
    count = SolicitacaoSimulacao.objects.count()
    SolicitacaoSimulacao.objects.all().delete()
    print(f"   ✅ SolicitacaoSimulacao: {count} registros removidos")
    total_removidos += count
    
    # 10. Limpar Notificações
    count = NotificacaoSimulacao.objects.count()
    NotificacaoSimulacao.objects.all().delete()
    print(f"   ✅ NotificacaoSimulacao: {count} registros removidos")
    total_removidos += count
    
    # 11. Limpar Decretos
    count = Decreto.objects.count()
    Decreto.objects.all().delete()
    print(f"   ✅ Decreto: {count} registros removidos")
    total_removidos += count
    
    print(f"\n🎯 Total de registros removidos: {total_removidos}")
    return total_removidos

def limpar_cache_arquivos():
    """Limpa arquivos de cache e dados gerados"""
    print("\n🧹 Limpando cache e arquivos gerados...")
    
    # Diretórios para limpar
    diretorios_limpar = [
        "core/static/data/",
        "staticfiles/",
        "media/planilhas_importadas/",
        "__pycache__/",
        "core/__pycache__/",
        "Nexus/__pycache__/",
        ".pytest_cache/",
    ]
    
    arquivos_limpar = [
        "core/static/data/organograma.json",
        "core/static/data/dados.json",
        "dados.json",
        "organograma.json",
    ]
    
    total_removidos = 0
    
    # Limpar diretórios
    for dir_path in diretorios_limpar:
        if os.path.exists(dir_path):
            try:
                if os.path.isdir(dir_path):
                    shutil.rmtree(dir_path)
                    print(f"   ✅ Diretório removido: {dir_path}")
                else:
                    os.remove(dir_path)
                    print(f"   ✅ Arquivo removido: {dir_path}")
                total_removidos += 1
            except Exception as e:
                print(f"   ⚠️ Erro ao remover {dir_path}: {e}")
    
    # Limpar arquivos específicos
    for file_path in arquivos_limpar:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"   ✅ Arquivo removido: {file_path}")
                total_removidos += 1
            except Exception as e:
                print(f"   ⚠️ Erro ao remover {file_path}: {e}")
    
    # Recriar diretórios necessários
    diretorios_criar = [
        "core/static/data/",
        "staticfiles/",
        "media/planilhas_importadas/",
    ]
    
    for dir_path in diretorios_criar:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"   ✅ Diretório criado: {dir_path}")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar {dir_path}: {e}")
    
    print(f"\n🎯 Total de itens removidos: {total_removidos}")
    return total_removidos

def verificar_limpeza():
    """Verifica se a limpeza foi bem-sucedida"""
    print("\n🔍 Verificando limpeza...")
    
    # Verificar banco
    total_banco = (
        UnidadeCargo.objects.count() +
        CargoSIORG.objects.count() +
        PlanilhaImportada.objects.count() +
        RelatorioGratificacoes.objects.count() +
        RelatorioEfetivo.objects.count() +
        RelatorioGratificacoesPlan1.objects.count() +
        SimulacaoSalva.objects.count() +
        SolicitacaoRealocacao.objects.count() +
        SolicitacaoPermuta.objects.count() +
        ConfiguracaoRelatorio.objects.count() +
        TipoUsuario.objects.count() +
        SolicitacaoSimulacao.objects.count() +
        NotificacaoSimulacao.objects.count() +
        Decreto.objects.count()
    )
    
    print(f"   📊 Total de registros no banco: {total_banco}")
    
    # Verificar arquivos
    arquivos_verificar = [
        "core/static/data/organograma.json",
        "core/static/data/dados.json",
        "dados.json",
        "organograma.json",
    ]
    
    arquivos_existentes = 0
    for file_path in arquivos_verificar:
        if os.path.exists(file_path):
            arquivos_existentes += 1
            print(f"   ⚠️ Arquivo ainda existe: {file_path}")
    
    print(f"   📁 Arquivos de dados existentes: {arquivos_existentes}")
    
    if total_banco == 0 and arquivos_existentes == 0:
        print("   ✅ Limpeza completa bem-sucedida!")
        return True
    else:
        print("   ⚠️ Alguns dados ainda persistem")
        return False

def main():
    """Função principal"""
    print("🚀 SISTEMA DE LIMPEZA COMPLETA")
    print("=" * 50)
    
    # Confirmar ação
    resposta = input("\n⚠️ ATENÇÃO: Esta ação irá remover TODOS os dados do sistema!\n"
                    "Isso inclui:\n"
                    "  - Todos os registros do banco de dados\n"
                    "  - Todos os arquivos de cache\n"
                    "  - Todos os arquivos gerados\n"
                    "  - Todas as planilhas importadas\n\n"
                    "Digite 'LIMPAR' para confirmar: ")
    
    if resposta != "LIMPAR":
        print("❌ Operação cancelada pelo usuário")
        return
    
    try:
        # 1. Limpar banco
        registros_removidos = limpar_banco_completo()
        
        # 2. Limpar cache
        arquivos_removidos = limpar_cache_arquivos()
        
        # 3. Verificar limpeza
        sucesso = verificar_limpeza()
        
        print("\n" + "=" * 50)
        if sucesso:
            print("🎉 LIMPEZA COMPLETA REALIZADA COM SUCESSO!")
            print("\n📋 Próximos passos:")
            print("1. Importe as novas planilhas através do admin Django")
            print("2. Execute: python manage.py collectstatic")
            print("3. Reinicie o servidor Django")
        else:
            print("⚠️ Limpeza realizada, mas alguns dados podem persistir")
            
        print(f"\n📊 Resumo:")
        print(f"   - Registros removidos: {registros_removidos}")
        print(f"   - Arquivos removidos: {arquivos_removidos}")
        
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 