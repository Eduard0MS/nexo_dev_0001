import os
import allauth
import shutil

# Encontrar o caminho do arquivo adapter.py
adapter_path = os.path.join(
    os.path.dirname(allauth.__file__), "socialaccount", "adapter.py"
)
print(f"Caminho do adapter.py: {adapter_path}")

# Criar backup
backup_path = adapter_path + ".bak"
shutil.copy2(adapter_path, backup_path)
print(f"Backup criado em {backup_path}")

# Ler o conteúdo original
with open(adapter_path, "r", encoding="utf-8") as f:
    content = f.readlines()

# Encontrar e modificar a linha que lança MultipleObjectsReturned
for i, line in enumerate(content):
    if "raise MultipleObjectsReturned" in line:
        # Comentar a linha que lança a exceção e adicionar código para retornar o primeiro item
        content[i] = f"            # {line.strip()}  # Comentado pelo patch\n"
        content.insert(
            i + 1,
            "            return visible_apps[0]  # Retornar o primeiro aplicativo (adicionado pelo patch)\n",
        )
        print(f"Patch aplicado na linha {i+1}")
        break
else:
    print("A linha 'raise MultipleObjectsReturned' não foi encontrada")
    exit(1)

# Escrever o arquivo modificado
with open(adapter_path, "w", encoding="utf-8") as f:
    f.writelines(content)

print("Patch aplicado com sucesso!")
print("Reinicie o servidor Django para aplicar as alterações.")
print("Para reverter, substitua o arquivo pelo backup criado.")
