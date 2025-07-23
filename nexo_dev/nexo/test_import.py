#!/usr/bin/env python3
"""
Script de teste para verificar se a importação de planilhas está funcionando
"""

import os
import django
import dotenv

# Configurar Django
dotenv.load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Nexus.settings")
django.setup()

from core.models import UnidadeCargo
from core.utils import processa_planilhas, salvar_dados_no_banco
from django.core.files.uploadedfile import SimpleUploadedFile

def test_import():
    """Testa a importação de planilhas"""
    
    print("🧪 Testando importação de planilhas...")
    print(f"Registros atuais no banco: {UnidadeCargo.objects.count()}")
    
    # Verificar se existem arquivos de teste
    hierarquia_path = "test_hierarquia.xlsx"
    estrutura_path = "test_estrutura.xlsx"
    
    if not os.path.exists(hierarquia_path) or not os.path.exists(estrutura_path):
        print("❌ Arquivos de teste não encontrados!")
        print("Crie os arquivos test_hierarquia.xlsx e test_estrutura.xlsx para testar")
        return False
    
    try:
        # Simular upload de arquivos
        with open(hierarquia_path, 'rb') as f:
            file_hierarquia = SimpleUploadedFile(
                "test_hierarquia.xlsx",
                f.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with open(estrutura_path, 'rb') as f:
            file_estrutura = SimpleUploadedFile(
                "test_estrutura.xlsx",
                f.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Processar planilhas
        print("📊 Processando planilhas...")
        resultado = processa_planilhas(file_hierarquia, file_estrutura)
        print(f"✅ Planilhas processadas: {len(resultado)} registros")
        
        # Salvar no banco
        print("💾 Salvando no banco de dados...")
        registros_criados, erros = salvar_dados_no_banco(resultado)
        
        # Verificar resultado
        total_final = UnidadeCargo.objects.count()
        print(f"✅ Importação concluída!")
        print(f"   - Registros criados: {registros_criados}")
        print(f"   - Total no banco: {total_final}")
        print(f"   - Erros: {len(erros)}")
        
        if erros:
            print("⚠️ Erros encontrados:")
            for erro in erros[:3]:
                print(f"   - {erro}")
        
        return registros_criados > 0
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import()
    if success:
        print("🎉 Teste concluído com sucesso!")
    else:
        print("💥 Teste falhou!") 