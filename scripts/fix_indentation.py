import os
import allauth

# Encontrar o caminho do adapter.py
adapter_path = os.path.join(
    os.path.dirname(allauth.__file__), "socialaccount", "adapter.py"
)
print(f"Caminho do adapter.py: {adapter_path}")

# Ler conteúdo atual
with open(adapter_path, "r", encoding="utf-8") as f:
    content = f.readlines()

# Verificar se o backup existe, senão criar um
backup_path = adapter_path + ".bak2"
if not os.path.exists(backup_path):
    with open(backup_path, "w", encoding="utf-8") as f:
        f.writelines(content)
    print(f"Backup criado em {backup_path}")

# Encontrar e consertar a linha que lança MultipleObjectsReturned
found = False
for i, line in enumerate(content):
    if "# raise MultipleObjectsReturned" in line:
        # A próxima linha é o return que está com indentação incorreta
        if i + 1 < len(content) and "return visible_apps[0]" in content[i + 1]:
            # Verificar indentação da linha anterior (if len(visible_apps) > 1:)
            if_line = None
            for j in range(i - 1, max(0, i - 5), -1):
                if "if len(visible_apps) > 1:" in content[j]:
                    if_line = content[j]
                    break

            if if_line:
                # Pegar a indentação do if para aplicar ao return
                spaces = len(if_line) - len(if_line.lstrip())
                # Adicionar 4 espaços extras para indentação correta dentro do if
                proper_indent = " " * (spaces + 4)

                # Corrigir a indentação do return
                content[i + 1] = proper_indent + content[i + 1].lstrip()
                found = True
                print(f"Indentação corrigida na linha {i+2}")
                break

if not found:
    print(
        "Não foi possível encontrar a linha para corrigir. Usando abordagem alternativa..."
    )

    # Abordagem alternativa: restaurar do backup original e fazer novamente o patch
    original_backup = adapter_path + ".bak"
    if os.path.exists(original_backup):
        # Restaurar o arquivo original
        with open(original_backup, "r", encoding="utf-8") as f:
            original_content = f.readlines()

        # Fazer o patch com indentação correta
        for i, line in enumerate(original_content):
            if "raise MultipleObjectsReturned" in line:
                # Capturar a indentação correta
                indent = line[: len(line) - len(line.lstrip())]
                # Comentar a linha e adicionar o return com indentação correta
                original_content[i] = (
                    indent + "# " + line.lstrip() + "  # Comentado pelo patch\n"
                )
                original_content.insert(
                    i + 1,
                    indent
                    + "return visible_apps[0]  # Retornar o primeiro app (patch)\n",
                )
                found = True
                print(f"Patch reaplicado com indentação correta na linha {i+1}")
                break

        if found:
            content = original_content

# Escrever o arquivo corrigido
with open(adapter_path, "w", encoding="utf-8") as f:
    f.writelines(content)

if found:
    print("Correção aplicada com sucesso!")
    print("Reinicie o servidor Django para aplicar as alterações.")
else:
    print(
        "Não foi possível corrigir automaticamente. Restaure o arquivo do backup manualmente."
    )
