# core/forms.py
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordChangeForm,
)
from django.contrib.auth.models import User
import re
from .models import Perfil


class CustomLoginForm(AuthenticationForm):
    """
    Formulário customizado de login, herdando de AuthenticationForm.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Usuário", "id": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Senha", "id": "password"}
        )


class CustomRegisterForm(UserCreationForm):
    """
    Formulário customizado de registro, herdando de UserCreationForm.
    """

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Usuário", "id": "username"}
        )
        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "E-mail", "id": "email"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Senha", "id": "password1"}
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Confirme a senha",
                "id": "password2",
            }
        )

        # Traduzir mensagens de ajuda
        self.fields["username"].help_text = (
            "Obrigatório. 150 caracteres ou menos. Letras, números e @/./+/-/_ apenas."
        )
        self.fields["password1"].help_text = (
            '<div class="password-requirements">'
            '<h6 style="margin-top: 10px; font-weight: 600;">Requisitos de segurança:</h6>'
            '<ul style="margin-top: 5px; padding-left: 20px;">'
            '<li><span style="color: #0066cc;">&#10003;</span> Mínimo de 8 caracteres</li>'
            '<li><span style="color: #0066cc;">&#10003;</span> Pelo menos uma letra maiúscula (A-Z)</li>'
            '<li><span style="color: #0066cc;">&#10003;</span> Pelo menos uma letra minúscula (a-z)</li>'
            '<li><span style="color: #0066cc;">&#10003;</span> Pelo menos um número (0-9)</li>'
            '<li><span style="color: #0066cc;">&#10003;</span> Pelo menos um caractere especial (!@#$%^&*)</li>'
            "</ul>"
            '<p style="margin-top: 8px; color: #666; font-size: 0.9em;">Além disso, sua senha não deve:</p>'
            '<ul style="margin-top: 5px; padding-left: 20px; color: #666; font-size: 0.9em;">'
            "<li>Ser semelhante ao seu nome de usuário ou e-mail</li>"
            "<li>Ser uma senha comum ou facilmente adivinhável</li>"
            "<li>Conter apenas números</li>"
            "</ul>"
            "</div>"
        )
        self.fields["password2"].help_text = (
            "Digite a mesma senha novamente, para verificação."
        )

    def clean_password1(self):
        password = self.cleaned_data.get("password1")

        # Verificar comprimento mínimo
        if len(password) < 8:
            raise forms.ValidationError("A senha deve ter pelo menos 8 caracteres.")

        # Verificar letras maiúsculas
        if not any(char.isupper() for char in password):
            raise forms.ValidationError(
                "A senha deve conter pelo menos uma letra maiúscula."
            )

        # Verificar letras minúsculas
        if not any(char.islower() for char in password):
            raise forms.ValidationError(
                "A senha deve conter pelo menos uma letra minúscula."
            )

        # Verificar números
        if not any(char.isdigit() for char in password):
            raise forms.ValidationError("A senha deve conter pelo menos um número.")

        # Verificar caracteres especiais
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError(
                "A senha deve conter pelo menos um caractere especial."
            )

        # Lista de senhas comuns
        common_passwords = [
            "password",
            "123456",
            "12345678",
            "qwerty",
            "abc123",
            "admin123",
            "welcome",
            "senha123",
            "admin",
            "123mudar",
            "1234",
            "12345",
            "123456789",
            "test123",
            "usuario",
            "q1w2e3r4",
            "qwerty123",
            "1q2w3e",
            "abcd1234",
        ]

        # Verificar se a senha é comum
        if password.lower() in common_passwords:
            raise forms.ValidationError(
                "Esta senha é muito comum. Por favor, escolha uma senha mais segura."
            )

        return password

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este endereço de e-mail já está em uso.")
        return email


class FileUploadForm(forms.Form):
    file = forms.FileField(
        label="Selecione um arquivo CSV ou Excel",
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )

    def clean_file(self):
        file = self.cleaned_data["file"]
        if not file.name.endswith((".csv", ".xlsx")):
            raise forms.ValidationError("O arquivo deve ser um arquivo CSV ou Excel.")
        return file


class DualFileUploadForm(forms.Form):
    file_estrutura_viva = forms.FileField(
        label="Planilha de Estrutura Viva",
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )

    def clean_file_hierarquia(self):
        file = self.cleaned_data["file_hierarquia"]
        if not file.name.endswith((".csv", ".xlsx")):
            raise forms.ValidationError(
                "O arquivo de hierarquia deve ser CSV ou Excel."
            )
        return file

    def clean_file_estrutura_viva(self):
        file = self.cleaned_data["file_estrutura_viva"]
        if not file.name.endswith((".csv", ".xlsx")):
            raise forms.ValidationError(
                "O arquivo de estrutura viva deve ser CSV ou Excel."
            )
        return file


class UserUpdateForm(forms.ModelForm):
    """
    Formulário para atualização dos dados do usuário.
    """

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Usuário", "id": "username"}
        )
        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "E-mail", "id": "email"}
        )
        self.fields["first_name"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Nome", "id": "first_name"}
        )
        self.fields["last_name"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Sobrenome", "id": "last_name"}
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        username = self.cleaned_data.get("username")

        # Verificar se o email já existe para outro usuário
        if User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError("Este email já está em uso por outro usuário.")

        return email


class PerfilUpdateForm(forms.ModelForm):
    """
    Formulário para atualização dos dados do perfil do usuário.
    """

    class Meta:
        model = Perfil
        fields = ["foto", "telefone", "cargo", "departamento", "bio"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["foto"].widget.attrs.update(
            {
                "class": "form-control",
                "accept": "image/jpeg,image/png",
                "style": "cursor: pointer;",
            }
        )
        self.fields["telefone"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Telefone", "id": "telefone"}
        )
        self.fields["cargo"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Cargo", "id": "cargo"}
        )
        self.fields["departamento"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Departamento",
                "id": "departamento",
            }
        )
        self.fields["bio"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Biografia",
                "id": "bio",
                "rows": "3",
            }
        )


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulário customizado para alteração de senha.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Senha atual",
                "id": "old_password",
            }
        )
        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Nova senha",
                "id": "new_password1",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Confirme a nova senha",
                "id": "new_password2",
            }
        )

        # Traduzir mensagens de ajuda
        self.fields["new_password1"].help_text = (
            "A senha deve conter pelo menos 8 caracteres, incluindo letras e números."
        )
