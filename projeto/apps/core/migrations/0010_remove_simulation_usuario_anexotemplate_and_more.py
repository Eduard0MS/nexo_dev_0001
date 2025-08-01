# Generated by Django 5.1.5 on 2025-05-29 14:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_simulation_position'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='simulation',
            name='usuario',
        ),
        migrations.CreateModel(
            name='AnexoTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome do Template')),
                ('descricao', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('arquivo', models.FileField(help_text='Faça upload do arquivo Excel que será usado como template', upload_to='templates_anexos/', verbose_name='Arquivo Template (.xlsx)')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('data_upload', models.DateTimeField(auto_now_add=True, verbose_name='Data de Upload')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Template de Anexo',
                'verbose_name_plural': 'Templates de Anexos',
                'ordering': ['-data_upload'],
            },
        ),
        migrations.DeleteModel(
            name='Position',
        ),
        migrations.DeleteModel(
            name='Simulation',
        ),
    ]
