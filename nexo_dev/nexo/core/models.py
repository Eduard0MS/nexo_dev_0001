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

class PlanilhaImportada(models.Model):
    """
    Modelo para armazenar planilhas importadas.
    """
    nome = models.CharField(max_length=255, verbose_name="Nome")
    arquivo = models.FileField(upload_to='planilhas_importadas/', verbose_name="Arquivo da Planilha")
    data_importacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Importação")
    ativo = models.BooleanField(default=False, verbose_name="Planilha Ativa")

    class Meta:
        verbose_name = "Planilha Importada"
        verbose_name_plural = "Planilhas Importadas"
        ordering = ['-data_importacao']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Se esta planilha está sendo marcada como ativa, desativa todas as outras
        if self.ativo:
            PlanilhaImportada.objects.filter(ativo=True).update(ativo=False)
        super().save(*args, **kwargs)

class SimulacaoSalva(models.Model):
    """
    Modelo para armazenar simulações salvas pelos usuários.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    nome = models.CharField(max_length=255, verbose_name="Nome da Simulação")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    dados_estrutura = models.JSONField(verbose_name="Dados da Estrutura")
    unidade_base = models.CharField(max_length=100, blank=True, null=True, verbose_name="Unidade Base")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Simulação Salva"
        verbose_name_plural = "Simulações Salvas"
        ordering = ['-criado_em']
        unique_together = ['usuario', 'nome']  # Um usuário não pode ter duas simulações com o mesmo nome

    def __str__(self):
        return f"{self.nome} - {self.usuario.username}"

    def save(self, *args, **kwargs):
        # Validar que o usuário não tenha mais de 5 simulações
        if not self.pk:  # Se é uma nova simulação (não uma atualização)
            count = SimulacaoSalva.objects.filter(usuario=self.usuario).count()
            if count >= 5:
                from django.core.exceptions import ValidationError
                raise ValidationError("Cada usuário pode ter no máximo 5 simulações salvas.")
        super().save(*args, **kwargs)


# === NOVOS MODELOS PARA SISTEMA DE RELATÓRIOS ===


class RelatorioGratificacoes(models.Model):
    """
    Modelo para armazenar dados de gratificações e lotações dos funcionários.
    """
    data_importacao = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação")
    nome_servidor = models.CharField(max_length=255, verbose_name="Nome do Servidor")
    matricula_siape = models.CharField(max_length=50, verbose_name="Matrícula SIAPE")
    situacao_funcional = models.CharField(max_length=100, blank=True, verbose_name="Situação Funcional")
    cargo = models.CharField(max_length=255, blank=True, verbose_name="Cargo")
    nivel = models.CharField(max_length=50, blank=True, verbose_name="Nível")
    gsiste = models.CharField(max_length=100, blank=True, verbose_name="Gsiste")
    gsiste_nivel = models.CharField(max_length=50, blank=True, verbose_name="Gsiste Nível")
    funcao = models.CharField(max_length=255, blank=True, verbose_name="Função")
    nivel_funcao = models.CharField(max_length=50, blank=True, verbose_name="Nível da Função")
    atividade_funcao = models.CharField(max_length=255, blank=True, verbose_name="Atividade da Função")
    jornada_trabalho = models.CharField(max_length=50, blank=True, verbose_name="Jornada de Trabalho")
    unidade_lotacao = models.CharField(max_length=255, blank=True, verbose_name="Unidade de Lotação")
    secretaria_lotacao = models.CharField(max_length=255, blank=True, verbose_name="Secretaria da Lotação")
    uf = models.CharField(max_length=2, blank=True, verbose_name="UF")
    uorg_exercicio = models.CharField(max_length=100, blank=True, verbose_name="UORG de Exercício")
    unidade_exercicio = models.CharField(max_length=255, blank=True, verbose_name="Unidade de Exercício")
    coordenacao = models.CharField(max_length=255, blank=True, verbose_name="Coordenação")
    diretoria = models.CharField(max_length=255, blank=True, verbose_name="Diretoria")
    secretaria = models.CharField(max_length=255, blank=True, verbose_name="Secretaria")
    orgao_origem = models.CharField(max_length=255, blank=True, verbose_name="Órgão Origem")
    email_institucional = models.EmailField(blank=True, verbose_name="e-Mail Institucional")
    siape_titular_chefe = models.CharField(max_length=50, blank=True, verbose_name="Siape do Titular Chefe")
    siape_substituto = models.CharField(max_length=50, blank=True, verbose_name="Siape do Substituto")
    
    class Meta:
        verbose_name = "Dados de Gratificações"
        verbose_name_plural = "Dados de Gratificações"
        ordering = ['nome_servidor']
    
    def __str__(self):
        return f"{self.nome_servidor} - {self.cargo}"


class RelatorioOrgaosCentrais(models.Model):
    """
    Modelo para armazenar dados de órgãos centrais e setoriais.
    """
    data_importacao = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação")
    tipo_orgao = models.CharField(max_length=20, choices=[('central', 'Central'), ('setorial', 'Setorial')], verbose_name="Tipo de Órgão")
    nivel_cargo = models.CharField(max_length=50, verbose_name="Nível do Cargo")
    valor_maximo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Máximo da GSISTE")
    efeitos_financeiros_data = models.CharField(max_length=100, blank=True, verbose_name="Efeitos Financeiros a partir de")
    
    class Meta:
        verbose_name = "Dados de Órgãos"
        verbose_name_plural = "Dados de Órgãos"
        ordering = ['tipo_orgao', 'nivel_cargo']
    
    def __str__(self):
        return f"{self.get_tipo_orgao_display()} - {self.nivel_cargo} - R$ {self.valor_maximo}"


class RelatorioGratificacoesPlan1(models.Model):
    """
    Modelo para dados da aba Plan1 - Gratificações e Valores por Órgão
    """
    data_importacao = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação")
    tipo_orgao = models.CharField(max_length=20, choices=[('central', 'Órgãos Centrais'), ('setorial', 'Órgãos Setoriais'), ('limites', 'Limites GSISTE')], verbose_name="Tipo de Órgão")
    nivel_cargo = models.CharField(max_length=50, verbose_name="Nível do Cargo")
    valor_maximo_gsiste = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Máximo da GSISTE")
    efeitos_financeiros_data = models.CharField(max_length=100, blank=True, verbose_name="Efeitos Financeiros a partir de")
    
    class Meta:
        verbose_name = "Gratificação por Órgão (Plan1)"
        verbose_name_plural = "Gratificações por Órgão (Plan1)"
        ordering = ['tipo_orgao', 'nivel_cargo']
    
    def __str__(self):
        return f"{self.get_tipo_orgao_display()} - {self.nivel_cargo} - R$ {self.valor_maximo_gsiste}"


class RelatorioEfetivo(models.Model):
    """
    Modelo para armazenar dados de efetivo de funcionários.
    """
    data_importacao = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação")
    ordem_planilha = models.IntegerField(verbose_name="Ordem na Planilha", help_text="Posição original na planilha", default=0)
    qt = models.IntegerField(verbose_name="QT")
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    funcao = models.CharField(max_length=255, verbose_name="Função")
    unidade_macro = models.CharField(max_length=100, blank=True, verbose_name="Unidade Macro")
    horario = models.CharField(max_length=100, blank=True, verbose_name="Horário")
    bloco_andar = models.CharField(max_length=100, blank=True, verbose_name="Bloco/Andar")
    
    class Meta:
        verbose_name = "Dados de Efetivo"
        verbose_name_plural = "Dados de Efetivo"
        ordering = ['ordem_planilha']  # Ordenar pela ordem original da planilha
    
    def __str__(self):
        return f"{self.qt} - {self.nome_completo} - {self.funcao}"
