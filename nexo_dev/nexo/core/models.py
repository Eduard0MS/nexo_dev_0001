# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount

class UnidadeCargo(models.Model):
    nivel_hierarquico = models.IntegerField(verbose_name="Nível Hierárquico")
    tipo_unidade = models.CharField(max_length=100, verbose_name="Tipo Unidade")
    denominacao_unidade = models.CharField(max_length=255, verbose_name="Denominação Unidade")
    codigo_unidade = models.CharField(max_length=50, verbose_name="Código Unidade")
    sigla_unidade = models.CharField(max_length=50, verbose_name="Sigla Unidade")
    categoria_unidade = models.CharField(max_length=100, verbose_name="Categoria Unidade")
    orgao_entidade = models.CharField(max_length=255, verbose_name="Órgão/Entidade")
    tipo_cargo = models.CharField(max_length=100, verbose_name="Tipo do Cargo")
    denominacao = models.CharField(max_length=255, verbose_name="Denominação")
    complemento_denominacao = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Complemento Denominação"
    )
    categoria = models.IntegerField(verbose_name="Categoria")
    nivel = models.IntegerField(verbose_name="Nível")
    quantidade = models.IntegerField(verbose_name="Quantidade")
    grafo = models.CharField(max_length=100, verbose_name="Grafo")
    sigla = models.CharField(max_length=100, verbose_name="Sigla")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Total")
    pontos_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Pontos Total")

    def __str__(self):
        tipo_cargo = self.tipo_cargo if self.tipo_cargo else ""
        denominacao = self.denominacao if self.denominacao else ""
        denominacao_unidade = self.denominacao_unidade if self.denominacao_unidade else ""
        return str(denominacao_unidade + " - " + tipo_cargo + " - " + denominacao).strip()
    
    def save(self, *args, **kwargs):
        # Garantir que registros com grafo vazio não sejam salvos
        if not self.grafo or self.grafo.strip() == "":
            return  # Não salvar registros sem grafo
        
        # Continuar com o comportamento normal de save para registros válidos
        super().save(*args, **kwargs)


class Perfil(models.Model):
    """
    Modelo para armazenar informações adicionais do usuário.
    """
    usuario = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(upload_to='perfil_fotos/', blank=True, null=True, verbose_name="Foto de Perfil")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo")
    departamento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Departamento")
    bio = models.TextField(blank=True, null=True, verbose_name="Biografia")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    def get_foto_url(self):
        """
        Retorna a URL da foto do perfil, priorizando:
        1. Foto do Google (se disponível)
        2. Foto enviada pelo usuário
        3. None (se nenhuma foto estiver disponível)
        """
        try:
            # Primeiro tenta obter a foto do Google
            social_account = SocialAccount.objects.get(user=self.usuario, provider='google')
            if 'picture' in social_account.extra_data:
                return social_account.extra_data['picture']
        except SocialAccount.DoesNotExist:
            pass
        
        # Se não houver foto do Google, usa a foto enviada pelo usuário
        if self.foto:
            return self.foto.url
            
        return None

    def __str__(self):
        try:
            if hasattr(self, 'usuario') and self.usuario:
                # Tentar obter username
                username = self.usuario.username if hasattr(self.usuario, 'username') else ""
                # Lidar com casos onde username está vazio ou é um caractere especial
                if username == "-" or not username:
                    username = str(self.usuario.id) if hasattr(self.usuario, 'id') else "Usuário"
                return str("Perfil de " + username)
            else:
                return str("Perfil sem usuário")
        except:
            # Em último caso, retornar um valor simples e seguro
            return str("Perfil")

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria automaticamente um perfil para novos usuários.
    """
    if created:
        Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Salva o perfil do usuário sempre que o usuário for salvo.
    """
    try:
        instance.perfil.save()
    except Perfil.DoesNotExist:
        Perfil.objects.create(usuario=instance)

class CargoSIORG(models.Model):
    cargo = models.CharField(max_length=255, verbose_name="Cargo")
    nivel = models.CharField(max_length=50, verbose_name="Nível")
    quantidade = models.IntegerField(verbose_name="Quantidade")
    valor = models.CharField(max_length=50, verbose_name="Valor")
    unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Unitário", default=0.00)
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Cargo SIORG"
        verbose_name_plural = "Cargos SIORG"
        ordering = ['cargo']

    def __str__(self):
        cargo_str = str(self.cargo) if self.cargo else ""
        nivel_str = str(self.nivel) if self.nivel else ""
        return str(cargo_str + " - " + nivel_str).strip()
