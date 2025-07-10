# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from django.core.exceptions import ValidationError
import json


class UnidadeCargo(models.Model):
    nivel_hierarquico = models.IntegerField(verbose_name="Nível Hierárquico")
    tipo_unidade = models.CharField(max_length=100, verbose_name="Tipo Unidade")
    denominacao_unidade = models.CharField(
        max_length=255, verbose_name="Denominação Unidade"
    )
    codigo_unidade = models.CharField(max_length=50, verbose_name="Código Unidade")
    sigla_unidade = models.CharField(max_length=50, verbose_name="Sigla Unidade")
    categoria_unidade = models.CharField(
        max_length=100, verbose_name="Categoria Unidade"
    )
    orgao_entidade = models.CharField(max_length=255, verbose_name="Órgão/Entidade")
    tipo_cargo = models.CharField(max_length=100, verbose_name="Tipo do Cargo")
    denominacao = models.CharField(max_length=255, verbose_name="Denominação")
    complemento_denominacao = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Complemento Denominação"
    )
    categoria = models.IntegerField(verbose_name="Categoria")
    nivel = models.IntegerField(verbose_name="Nível")
    quantidade = models.IntegerField(verbose_name="Quantidade")
    grafo = models.CharField(max_length=100, verbose_name="Grafo")
    sigla = models.CharField(max_length=100, verbose_name="Sigla")
    valor_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Valor Total"
    )
    pontos_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Pontos Total"
    )

    # Campo para associar cargo ao usuário (cargos manuais)
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Usuário Criador",
        help_text="Deixe em branco para cargos padrão do sistema",
    )

    def __str__(self):
        tipo_cargo = self.tipo_cargo if self.tipo_cargo else ""
        denominacao = self.denominacao if self.denominacao else ""
        denominacao_unidade = (
            self.denominacao_unidade if self.denominacao_unidade else ""
        )
        return str(
            denominacao_unidade + " - " + tipo_cargo + " - " + denominacao
        ).strip()

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

    usuario = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, related_name="perfil"
    )
    foto = models.ImageField(
        upload_to="perfil_fotos/", blank=True, null=True, verbose_name="Foto de Perfil"
    )
    telefone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Telefone"
    )
    cargo = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Cargo"
    )
    departamento = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Departamento"
    )
    bio = models.TextField(blank=True, null=True, verbose_name="Biografia")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Data de Atualização"
    )

    def get_foto_url(self):
        """
        Retorna a URL da foto do perfil, priorizando:
        1. Foto do Google (se disponível)
        2. Foto enviada pelo usuário
        3. None (se nenhuma foto estiver disponível)
        """
        try:
            # Primeiro tenta obter a foto do Google
            social_account = SocialAccount.objects.get(
                user=self.usuario, provider="google"
            )
            if "picture" in social_account.extra_data:
                return social_account.extra_data["picture"]
        except SocialAccount.DoesNotExist:
            pass

        # Se não houver foto do Google, usa a foto enviada pelo usuário
        if self.foto:
            return self.foto.url

        return None

    def __str__(self):
        try:
            if hasattr(self, "usuario") and self.usuario:
                # Tentar obter username
                username = (
                    self.usuario.username if hasattr(self.usuario, "username") else ""
                )
                # Lidar com casos onde username está vazio ou é um caractere especial
                if username == "-" or not username:
                    username = (
                        str(self.usuario.id)
                        if hasattr(self.usuario, "id")
                        else "Usuário"
                    )
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


@receiver(post_save, sender=User)
def create_or_update_tipo_usuario(sender, instance, created, **kwargs):
    """
    Sinal para criar ou atualizar o TipoUsuario baseado nos grupos do usuário
    """
    # Usar a função helper para garantir que o TipoUsuario existe
    obter_tipo_usuario(instance)


@receiver(post_save, sender="core.TipoUsuario")
def atualizar_simulacoes_usuario(sender, instance, **kwargs):
    """
    Atualiza as simulações do usuário quando seu tipo muda
    """
    # Atualizar todas as simulações do usuário para refletir o novo tipo
    SimulacaoSalva.objects.filter(usuario=instance.usuario).update(
        tipo_usuario=instance.tipo
    )


class CargoSIORG(models.Model):
    cargo = models.CharField(max_length=255, verbose_name="Cargo")
    nivel = models.CharField(max_length=50, verbose_name="Nível")
    quantidade = models.IntegerField(verbose_name="Quantidade")
    valor = models.CharField(max_length=50, verbose_name="Valor")
    unitario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Unitário", default=0.00
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Data de Atualização"
    )

    class Meta:
        verbose_name = "Cargo SIORG"
        verbose_name_plural = "Cargos SIORG"
        ordering = ["cargo"]

    def __str__(self):
        cargo_str = str(self.cargo) if self.cargo else ""
        nivel_str = str(self.nivel) if self.nivel else ""
        return str(cargo_str + " - " + nivel_str).strip()


class PlanilhaImportada(models.Model):
    """
    Modelo para armazenar planilhas importadas.
    """

    nome = models.CharField(max_length=255, verbose_name="Nome")
    arquivo = models.FileField(
        upload_to="planilhas_importadas/", verbose_name="Arquivo da Planilha"
    )
    data_importacao = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Importação"
    )
    ativo = models.BooleanField(default=False, verbose_name="Planilha Ativa")

    class Meta:
        verbose_name = "Planilha Importada"
        verbose_name_plural = "Planilhas Importadas"
        ordering = ["-data_importacao"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Se esta planilha está sendo marcada como ativa, desativa todas as outras
        if self.ativo:
            PlanilhaImportada.objects.filter(ativo=True).update(ativo=False)
        super().save(*args, **kwargs)


def obter_tipo_usuario(usuario):
    """
    Função helper para obter o tipo de usuário baseado no modelo TipoUsuario.
    Se não existir, cria um baseado nos grupos do usuário.
    """
    try:
        tipo_usuario_obj = usuario.tipo_usuario_simulacao
        return tipo_usuario_obj.tipo
    except TipoUsuario.DoesNotExist:
        # Se não existe o TipoUsuario, criar baseado nos grupos
        if usuario.groups.filter(name="user_gerente").exists():
            tipo = "gerente"
        elif (
            usuario.groups.filter(name="Administradores").exists()
            or usuario.groups.filter(name="Gerentes").exists()
            or usuario.is_superuser
        ):
            tipo = "interno"
        else:
            tipo = "externo"

        # Criar o registro TipoUsuario
        TipoUsuario.objects.create(
            usuario=usuario,
            tipo=tipo,
            pode_solicitar=(tipo == "gerente"),
            pode_ver_todas=(tipo in ["gerente", "interno"]),
        )
        return tipo


class SimulacaoSalva(models.Model):
    """
    Modelo para armazenar simulações salvas pelos usuários.
    """

    STATUS_CHOICES = [
        ("rascunho", "Rascunho"),
        ("enviada_analise", "Enviada para Análise"),
        ("aprovada", "Aprovada"),
        ("rejeitada", "Rejeitada"),
        ("rejeitada_editada", "Rejeitada (Editada)"),
    ]

    TIPO_USUARIO_CHOICES = [
        ("externo", "Usuário Externo"),
        ("interno", "Usuário Interno"),
        ("gerente", "Usuário Gerente"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    nome = models.CharField(max_length=255, verbose_name="Nome da Simulação")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    dados_estrutura = models.JSONField(verbose_name="Dados da Estrutura")
    unidade_base = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Unidade Base"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="rascunho", verbose_name="Status"
    )
    tipo_usuario = models.CharField(
        max_length=10,
        choices=TIPO_USUARIO_CHOICES,
        default="externo",
        verbose_name="Tipo de Usuário",
    )
    visivel_para_gerentes = models.BooleanField(
        default=False, verbose_name="Visível para Gerentes"
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Simulação Salva"
        verbose_name_plural = "Simulações Salvas"
        ordering = ["-criado_em"]
        unique_together = [
            "usuario",
            "nome",
        ]  # Um usuário não pode ter duas simulações com o mesmo nome

    def __str__(self):
        return f"{self.nome} - {self.usuario.username}"

    @property
    def tipo_usuario_atual(self):
        """Retorna o tipo atual do usuário (sempre atualizado)"""
        return obter_tipo_usuario(self.usuario)

    def get_tipo_usuario_display_atual(self):
        """Retorna o display do tipo atual do usuário"""
        tipo_map = {
            "externo": "Usuário Externo",
            "interno": "Usuário Interno",
            "gerente": "Usuário Gerente",
        }
        return tipo_map.get(self.tipo_usuario_atual, "Usuário Externo")

    def save(self, *args, **kwargs):
        # Validar que o usuário não tenha mais de 5 simulações (não se aplica a gerentes)
        if not self.pk:  # Se é uma nova simulação (não uma atualização)
            tipo_usuario_atual = obter_tipo_usuario(self.usuario)
            if tipo_usuario_atual != "gerente":
                count = SimulacaoSalva.objects.filter(usuario=self.usuario).count()
                if count >= 5:
                    from django.core.exceptions import ValidationError

                    raise ValidationError(
                        "Cada usuário pode ter no máximo 5 simulações salvas."
                    )

        # Definir tipo de usuário baseado no modelo TipoUsuario
        self.tipo_usuario = obter_tipo_usuario(self.usuario)

        # Se status é enviada_analise ou rejeitada e usuário é interno, tornar visível para gerentes
        if (
            self.status in ["enviada_analise", "rejeitada", "rejeitada_editada"]
            and self.tipo_usuario_atual == "interno"
        ):
            self.visivel_para_gerentes = True
        # Se aprovada, pode ser ocultada dos gerentes (opcional)
        elif self.status == "aprovada":
            self.visivel_para_gerentes = False

        super().save(*args, **kwargs)

    def pode_ser_vista_por(self, usuario):
        """Verifica se uma simulação pode ser vista por um usuário específico"""
        # Proprietário sempre pode ver
        if self.usuario == usuario:
            return True

        # Usar o tipo de usuário do modelo TipoUsuario
        tipo_visualizador = obter_tipo_usuario(usuario)

        # Gerentes podem ver simulações enviadas para análise ou rejeitadas por usuários internos
        if tipo_visualizador == "gerente":
            return self.visivel_para_gerentes and self.status in [
                "enviada_analise",
                "rejeitada",
                "rejeitada_editada",
            ]

        # Admins podem ver tudo
        if usuario.is_superuser:
            return True

        return False


class TipoUsuario(models.Model):
    """
    Modelo para definir tipos de usuários e suas permissões no sistema de simulações
    """

    TIPOS = [
        ("externo", "Usuário Externo"),
        ("interno", "Usuário Interno"),
        ("gerente", "Usuário Gerente"),
    ]

    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="tipo_usuario_simulacao"
    )
    tipo = models.CharField(
        max_length=10, choices=TIPOS, default="externo", verbose_name="Tipo de Usuário"
    )
    pode_solicitar = models.BooleanField(
        default=False, verbose_name="Pode Solicitar Simulações"
    )
    pode_ver_todas = models.BooleanField(
        default=False, verbose_name="Pode Ver Todas as Simulações"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Tipo de Usuário"
        verbose_name_plural = "Tipos de Usuários"

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()}"


class SolicitacaoSimulacao(models.Model):
    """
    Modelo para solicitações de simulações feitas por gerentes para usuários internos
    """

    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("em_andamento", "Em Andamento"),
        ("concluida", "Concluída"),
        ("cancelada", "Cancelada"),
    ]

    PRIORIDADE_CHOICES = [
        ("baixa", "Baixa"),
        ("normal", "Normal"),
        ("alta", "Alta"),
        ("urgente", "Urgente"),
    ]

    solicitante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="solicitacoes_feitas",
        verbose_name="Solicitante (Gerente)",
    )
    usuario_designado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="solicitacoes_recebidas",
        verbose_name="Usuário Designado",
    )
    titulo = models.CharField(max_length=255, verbose_name="Título da Solicitação")
    descricao = models.TextField(verbose_name="Descrição Detalhada")
    unidade_base_sugerida = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Unidade Base Sugerida"
    )
    prazo_estimado = models.DateField(
        blank=True, null=True, verbose_name="Prazo Estimado"
    )
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default="normal",
        verbose_name="Prioridade",
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default="pendente", verbose_name="Status"
    )

    # Resposta do usuário designado
    aceita_em = models.DateTimeField(blank=True, null=True, verbose_name="Aceita em")
    simulacao_criada = models.ForeignKey(
        SimulacaoSalva,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Simulação Criada",
    )
    observacoes_usuario = models.TextField(
        blank=True, null=True, verbose_name="Observações do Usuário"
    )

    criada_em = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    atualizada_em = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Solicitação de Simulação"
        verbose_name_plural = "Solicitações de Simulações"
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.titulo} - {self.solicitante.username} → {self.usuario_designado.username}"


class NotificacaoSimulacao(models.Model):
    """
    Modelo para notificações relacionadas a simulações
    """

    TIPOS = [
        ("nova_solicitacao", "Nova Solicitação"),
        ("simulacao_enviada", "Simulação Enviada para Análise"),
        ("solicitacao_aceita", "Solicitação Aceita"),
        ("simulacao_aprovada", "Simulação Aprovada"),
        ("simulacao_rejeitada", "Simulação Rejeitada"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    tipo = models.CharField(
        max_length=20, choices=TIPOS, verbose_name="Tipo de Notificação"
    )
    titulo = models.CharField(max_length=255, verbose_name="Título")
    mensagem = models.TextField(verbose_name="Mensagem")

    # Referências opcionais
    solicitacao = models.ForeignKey(
        SolicitacaoSimulacao,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Solicitação Relacionada",
    )
    simulacao = models.ForeignKey(
        SimulacaoSalva,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Simulação Relacionada",
    )

    lida = models.BooleanField(default=False, verbose_name="Lida")
    criada_em = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")

    class Meta:
        verbose_name = "Notificação de Simulação"
        verbose_name_plural = "Notificações de Simulações"
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"


# === NOVOS MODELOS PARA SISTEMA DE RELATÓRIOS ===


class RelatorioGratificacoes(models.Model):
    """
    Modelo para armazenar dados de gratificações e lotações dos funcionários.
    """

    data_importacao = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação"
    )
    nome_servidor = models.CharField(max_length=255, verbose_name="Nome do Servidor")
    matricula_siape = models.CharField(max_length=50, verbose_name="Matrícula SIAPE")
    situacao_funcional = models.CharField(
        max_length=100, blank=True, verbose_name="Situação Funcional"
    )
    cargo = models.CharField(max_length=255, blank=True, verbose_name="Cargo")
    nivel = models.CharField(max_length=50, blank=True, verbose_name="Nível")
    gsiste = models.CharField(max_length=100, blank=True, verbose_name="Gsiste")
    gsiste_nivel = models.CharField(
        max_length=50, blank=True, verbose_name="Gsiste Nível"
    )
    funcao = models.CharField(max_length=255, blank=True, verbose_name="Função")
    nivel_funcao = models.CharField(
        max_length=50, blank=True, verbose_name="Nível da Função"
    )
    atividade_funcao = models.CharField(
        max_length=255, blank=True, verbose_name="Atividade da Função"
    )
    jornada_trabalho = models.CharField(
        max_length=50, blank=True, verbose_name="Jornada de Trabalho"
    )
    unidade_lotacao = models.CharField(
        max_length=255, blank=True, verbose_name="Unidade de Lotação"
    )
    secretaria_lotacao = models.CharField(
        max_length=255, blank=True, verbose_name="Secretaria da Lotação"
    )
    uf = models.CharField(max_length=2, blank=True, verbose_name="UF")
    uorg_exercicio = models.CharField(
        max_length=100, blank=True, verbose_name="UORG de Exercício"
    )
    unidade_exercicio = models.CharField(
        max_length=255, blank=True, verbose_name="Unidade de Exercício"
    )
    coordenacao = models.CharField(
        max_length=255, blank=True, verbose_name="Coordenação"
    )
    diretoria = models.CharField(max_length=255, blank=True, verbose_name="Diretoria")
    secretaria = models.CharField(max_length=255, blank=True, verbose_name="Secretaria")
    orgao_origem = models.CharField(
        max_length=255, blank=True, verbose_name="Órgão Origem"
    )
    email_institucional = models.EmailField(
        blank=True, verbose_name="e-Mail Institucional"
    )
    siape_titular_chefe = models.CharField(
        max_length=50, blank=True, verbose_name="Siape do Titular Chefe"
    )
    siape_substituto = models.CharField(
        max_length=50, blank=True, verbose_name="Siape do Substituto"
    )

    class Meta:
        verbose_name = "Dados de Gratificações"
        verbose_name_plural = "Dados de Gratificações"
        ordering = ["nome_servidor"]

    def __str__(self):
        return f"{self.nome_servidor} - {self.cargo}"


class RelatorioOrgaosCentrais(models.Model):
    """
    Modelo para armazenar dados de órgãos centrais e setoriais.
    """

    data_importacao = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação"
    )
    tipo_orgao = models.CharField(
        max_length=20,
        choices=[("central", "Central"), ("setorial", "Setorial")],
        verbose_name="Tipo de Órgão",
    )
    nivel_cargo = models.CharField(max_length=50, verbose_name="Nível do Cargo")
    valor_maximo = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Máximo da GSISTE"
    )
    efeitos_financeiros_data = models.CharField(
        max_length=100, blank=True, verbose_name="Efeitos Financeiros a partir de"
    )

    class Meta:
        verbose_name = "Dados de Órgãos"
        verbose_name_plural = "Dados de Órgãos"
        ordering = ["tipo_orgao", "nivel_cargo"]

    def __str__(self):
        return f"{self.get_tipo_orgao_display()} - {self.nivel_cargo} - R$ {self.valor_maximo}"


class RelatorioGratificacoesPlan1(models.Model):
    """
    Modelo para dados da aba Plan1 - Gratificações e Valores por Órgão
    """

    data_importacao = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação"
    )
    tipo_orgao = models.CharField(
        max_length=20,
        choices=[
            ("central", "Órgãos Centrais"),
            ("setorial", "Órgãos Setoriais"),
            ("limites", "Limites GSISTE"),
        ],
        verbose_name="Tipo de Órgão",
    )
    nivel_cargo = models.CharField(max_length=50, verbose_name="Nível do Cargo")
    valor_maximo_gsiste = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Máximo da GSISTE"
    )
    efeitos_financeiros_data = models.CharField(
        max_length=100, blank=True, verbose_name="Efeitos Financeiros a partir de"
    )

    class Meta:
        verbose_name = "Gratificação por Órgão (Plan1)"
        verbose_name_plural = "Gratificações por Órgão (Plan1)"
        ordering = ["tipo_orgao", "nivel_cargo"]

    def __str__(self):
        return f"{self.get_tipo_orgao_display()} - {self.nivel_cargo} - R$ {self.valor_maximo_gsiste}"


class RelatorioEfetivo(models.Model):
    """
    Modelo para armazenar dados de efetivo de funcionários.
    """

    data_importacao = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação"
    )
    ordem_planilha = models.IntegerField(
        verbose_name="Ordem na Planilha",
        help_text="Posição original na planilha",
        default=0,
    )
    qt = models.IntegerField(verbose_name="QT")
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    funcao = models.CharField(max_length=255, verbose_name="Função")
    unidade_macro = models.CharField(
        max_length=100, blank=True, verbose_name="Unidade Macro"
    )
    horario = models.CharField(max_length=100, blank=True, verbose_name="Horário")
    bloco_andar = models.CharField(
        max_length=100, blank=True, verbose_name="Bloco/Andar"
    )

    class Meta:
        verbose_name = "Dados de Efetivo"
        verbose_name_plural = "Dados de Efetivo"
        ordering = ["ordem_planilha"]  # Ordenar pela ordem original da planilha

    def __str__(self):
        return f"{self.qt} - {self.nome_completo} - {self.funcao}"


# === MODELOS ADICIONAIS PARA SISTEMA DE RELATÓRIOS ===


class Decreto(models.Model):
    """
    Modelo para armazenar histórico de decretos.
    """

    numero = models.CharField(
        max_length=100, verbose_name="Número do Decreto", unique=True
    )
    data_publicacao = models.DateField(verbose_name="Data de Publicação")
    titulo = models.TextField(verbose_name="Título/Ementa")
    tipo = models.CharField(
        max_length=50,
        choices=[
            ("estrutura_regimental", "Estrutura Regimental"),
            ("reorganizacao", "Reorganização"),
            ("criacao", "Criação de Órgão"),
            ("extincao", "Extinção de Órgão"),
            ("alteracao", "Alteração"),
            ("outro", "Outro"),
        ],
        verbose_name="Tipo de Decreto",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("vigente", "Vigente"),
            ("revogado", "Revogado"),
            ("alterado", "Alterado"),
        ],
        default="vigente",
        verbose_name="Status",
    )
    arquivo = models.FileField(
        upload_to="decretos/", blank=True, null=True, verbose_name="Arquivo do Decreto"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro"
    )
    usuario_cadastro = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="Usuário que Cadastrou"
    )

    class Meta:
        verbose_name = "Decreto"
        verbose_name_plural = "Decretos"
        ordering = ["-data_publicacao"]

    def __str__(self):
        return f"{self.numero} - {self.titulo[:50]}..."


class SolicitacaoRealocacao(models.Model):
    """
    Modelo para solicitações de realocação de servidores.
    """

    nome_servidor = models.CharField(max_length=255, verbose_name="Nome do Servidor")
    matricula_siape = models.CharField(max_length=50, verbose_name="Matrícula SIAPE")
    unidade_atual = models.CharField(max_length=255, verbose_name="Unidade Atual")
    unidade_destino = models.CharField(max_length=255, verbose_name="Unidade Destino")
    justificativa = models.TextField(verbose_name="Justificativa")

    status = models.CharField(
        max_length=20,
        choices=[
            ("pendente", "Pendente"),
            ("em_analise", "Em Análise"),
            ("aprovada", "Aprovada"),
            ("rejeitada", "Rejeitada"),
        ],
        default="pendente",
        verbose_name="Status",
    )

    data_solicitacao = models.DateTimeField(
        auto_now_add=True, verbose_name="Data da Solicitação"
    )
    usuario_solicitante = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Usuário Solicitante"
    )

    data_analise = models.DateTimeField(
        blank=True, null=True, verbose_name="Data da Análise"
    )
    usuario_analista = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analises_realocacao",
        verbose_name="Usuário Analista",
    )

    observacoes_analise = models.TextField(
        blank=True, verbose_name="Observações da Análise"
    )

    class Meta:
        verbose_name = "Solicitação de Realocação"
        verbose_name_plural = "Solicitações de Realocação"
        ordering = ["-data_solicitacao"]

    def __str__(self):
        return f"{self.nome_servidor} - {self.unidade_atual} → {self.unidade_destino}"


class SolicitacaoPermuta(models.Model):
    """
    Modelo para solicitações de permuta entre servidores.
    """

    # Servidor 1
    nome_servidor1 = models.CharField(max_length=255, verbose_name="Nome do Servidor 1")
    matricula_servidor1 = models.CharField(
        max_length=50, verbose_name="Matrícula SIAPE Servidor 1"
    )
    unidade_servidor1 = models.CharField(
        max_length=255, verbose_name="Unidade do Servidor 1"
    )

    # Servidor 2
    nome_servidor2 = models.CharField(max_length=255, verbose_name="Nome do Servidor 2")
    matricula_servidor2 = models.CharField(
        max_length=50, verbose_name="Matrícula SIAPE Servidor 2"
    )
    unidade_servidor2 = models.CharField(
        max_length=255, verbose_name="Unidade do Servidor 2"
    )

    # Informações da permuta
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    status = models.CharField(
        max_length=20,
        choices=[
            ("pendente", "Pendente"),
            ("em_analise", "Em Análise"),
            ("aprovada", "Aprovada"),
            ("rejeitada", "Rejeitada"),
        ],
        default="pendente",
        verbose_name="Status",
    )

    data_solicitacao = models.DateTimeField(
        auto_now_add=True, verbose_name="Data da Solicitação"
    )
    usuario_solicitante = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Usuário Solicitante"
    )

    data_analise = models.DateTimeField(
        blank=True, null=True, verbose_name="Data da Análise"
    )
    usuario_analista = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analises_permuta",
        verbose_name="Usuário Analista",
    )

    observacoes_analise = models.TextField(
        blank=True, verbose_name="Observações da Análise"
    )

    class Meta:
        verbose_name = "Solicitação de Permuta"
        verbose_name_plural = "Solicitações de Permuta"
        ordering = ["-data_solicitacao"]

    def __str__(self):
        return f"Permuta: {self.nome_servidor1} ↔ {self.nome_servidor2}"


class ConfiguracaoRelatorio(models.Model):
    """
    Modelo para configurações do sistema de relatórios.
    """

    chave = models.CharField(
        max_length=100, unique=True, verbose_name="Chave de Configuração"
    )
    valor = models.TextField(verbose_name="Valor")
    descricao = models.CharField(max_length=255, blank=True, verbose_name="Descrição")
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Data de Atualização"
    )
    usuario_atualizacao = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="Usuário que Atualizou"
    )

    class Meta:
        verbose_name = "Configuração de Relatório"
        verbose_name_plural = "Configurações de Relatórios"
        ordering = ["chave"]

    def __str__(self):
        return f"{self.chave}: {self.valor[:50]}..."


# === NOVOS MODELOS PARA SISTEMA DE RELATÓRIOS ===


class RelatorioGratificacoes(models.Model):
    """
    Modelo para armazenar dados de gratificações e lotações dos funcionários.
    """

    data_importacao = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação"
    )
    nome_servidor = models.CharField(max_length=255, verbose_name="Nome do Servidor")
    matricula_siape = models.CharField(max_length=50, verbose_name="Matrícula SIAPE")
    situacao_funcional = models.CharField(
        max_length=100, blank=True, verbose_name="Situação Funcional"
    )
    cargo = models.CharField(max_length=255, blank=True, verbose_name="Cargo")
    nivel = models.CharField(max_length=50, blank=True, verbose_name="Nível")
    gsiste = models.CharField(max_length=100, blank=True, verbose_name="Gsiste")
    gsiste_nivel = models.CharField(
        max_length=50, blank=True, verbose_name="Gsiste Nível"
    )
    funcao = models.CharField(max_length=255, blank=True, verbose_name="Função")
    nivel_funcao = models.CharField(
        max_length=50, blank=True, verbose_name="Nível da Função"
    )
    atividade_funcao = models.CharField(
        max_length=255, blank=True, verbose_name="Atividade da Função"
    )
    jornada_trabalho = models.CharField(
        max_length=50, blank=True, verbose_name="Jornada de Trabalho"
    )
    unidade_lotacao = models.CharField(
        max_length=255, blank=True, verbose_name="Unidade de Lotação"
    )
    secretaria_lotacao = models.CharField(
        max_length=255, blank=True, verbose_name="Secretaria da Lotação"
    )
    uf = models.CharField(max_length=2, blank=True, verbose_name="UF")
    uorg_exercicio = models.CharField(
        max_length=100, blank=True, verbose_name="UORG de Exercício"
    )
    unidade_exercicio = models.CharField(
        max_length=255, blank=True, verbose_name="Unidade de Exercício"
    )
    coordenacao = models.CharField(
        max_length=255, blank=True, verbose_name="Coordenação"
    )
    diretoria = models.CharField(max_length=255, blank=True, verbose_name="Diretoria")
    secretaria = models.CharField(max_length=255, blank=True, verbose_name="Secretaria")
    orgao_origem = models.CharField(
        max_length=255, blank=True, verbose_name="Órgão Origem"
    )
    email_institucional = models.EmailField(
        blank=True, verbose_name="e-Mail Institucional"
    )
    siape_titular_chefe = models.CharField(
        max_length=50, blank=True, verbose_name="Siape do Titular Chefe"
    )
    siape_substituto = models.CharField(
        max_length=50, blank=True, verbose_name="Siape do Substituto"
    )

    class Meta:
        verbose_name = "Dados de Gratificações"
        verbose_name_plural = "Dados de Gratificações"
        ordering = ["nome_servidor"]

    def __str__(self):
        return f"{self.nome_servidor} - {self.cargo}"


class RelatorioOrgaosCentrais(models.Model):
    """
    Modelo para armazenar dados de órgãos centrais e setoriais.
    """

    data_importacao = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação"
    )
    tipo_orgao = models.CharField(
        max_length=20,
        choices=[("central", "Central"), ("setorial", "Setorial")],
        verbose_name="Tipo de Órgão",
    )
    nivel_cargo = models.CharField(max_length=50, verbose_name="Nível do Cargo")
    valor_maximo = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Máximo da GSISTE"
    )
    efeitos_financeiros_data = models.CharField(
        max_length=100, blank=True, verbose_name="Efeitos Financeiros a partir de"
    )

    class Meta:
        verbose_name = "Dados de Órgãos"
        verbose_name_plural = "Dados de Órgãos"
        ordering = ["tipo_orgao", "nivel_cargo"]

    def __str__(self):
        return f"{self.get_tipo_orgao_display()} - {self.nivel_cargo} - R$ {self.valor_maximo}"


class RelatorioGratificacoesPlan1(models.Model):
    """
    Modelo para dados da aba Plan1 - Gratificações e Valores por Órgão
    """

    data_importacao = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação"
    )
    tipo_orgao = models.CharField(
        max_length=20,
        choices=[
            ("central", "Órgãos Centrais"),
            ("setorial", "Órgãos Setoriais"),
            ("limites", "Limites GSISTE"),
        ],
        verbose_name="Tipo de Órgão",
    )
    nivel_cargo = models.CharField(max_length=50, verbose_name="Nível do Cargo")
    valor_maximo_gsiste = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Máximo da GSISTE"
    )
    efeitos_financeiros_data = models.CharField(
        max_length=100, blank=True, verbose_name="Efeitos Financeiros a partir de"
    )

    class Meta:
        verbose_name = "Gratificação por Órgão (Plan1)"
        verbose_name_plural = "Gratificações por Órgão (Plan1)"
        ordering = ["tipo_orgao", "nivel_cargo"]

    def __str__(self):
        return f"{self.get_tipo_orgao_display()} - {self.nivel_cargo} - R$ {self.valor_maximo_gsiste}"


class RelatorioEfetivo(models.Model):
    """
    Modelo para armazenar dados de efetivo de funcionários.
    """

    data_importacao = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name="Data de Importação"
    )
    ordem_planilha = models.IntegerField(
        verbose_name="Ordem na Planilha",
        help_text="Posição original na planilha",
        default=0,
    )
    qt = models.IntegerField(verbose_name="QT")
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    funcao = models.CharField(max_length=255, verbose_name="Função")
    unidade_macro = models.CharField(
        max_length=100, blank=True, verbose_name="Unidade Macro"
    )
    horario = models.CharField(max_length=100, blank=True, verbose_name="Horário")
    bloco_andar = models.CharField(
        max_length=100, blank=True, verbose_name="Bloco/Andar"
    )

    class Meta:
        verbose_name = "Dados de Efetivo"
        verbose_name_plural = "Dados de Efetivo"
        ordering = ["ordem_planilha"]  # Ordenar pela ordem original da planilha

    def __str__(self):
        return f"{self.qt} - {self.nome_completo} - {self.funcao}"
