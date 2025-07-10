from django.core.management.base import BaseCommand
from core.models import SimulacaoSalva, obter_tipo_usuario


class Command(BaseCommand):
    help = "Atualiza o tipo_usuario de todas as simulações baseado no TipoUsuario atual"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "Iniciando atualização dos tipos de usuário das simulações..."
            )
        )

        simulacoes = SimulacaoSalva.objects.all()
        total = simulacoes.count()
        atualizadas = 0

        for simulacao in simulacoes:
            tipo_atual = obter_tipo_usuario(simulacao.usuario)
            if simulacao.tipo_usuario != tipo_atual:
                simulacao.tipo_usuario = tipo_atual
                simulacao.save()
                atualizadas += 1
                self.stdout.write(
                    f'Simulação "{simulacao.nome}" do usuário {simulacao.usuario.username} '
                    f'atualizada de "{simulacao.tipo_usuario}" para "{tipo_atual}"'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Atualização concluída! {atualizadas} de {total} simulações foram atualizadas."
            )
        )
