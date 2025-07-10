/**
 * Módulo de Gerenciamento de Simulações
 * 
 * Este módulo gerencia o salvamento, carregamento e manipulação de simulações
 * de estrutura organizacional no sistema.
 */

(function() {
    'use strict';
    
    // Variáveis globais do módulo
    let simulacoesCarregadas = [];
    let simulacaoAtual = null;
    let tipoUsuario = 'externo'; // Será definido pela API
    
    // Função para limpar o contexto de simulação atual
    function limparContextoSimulacao() {
        if (simulacaoAtual) {
            console.log('🧹 Limpando contexto da simulação:', simulacaoAtual.nome);
        }
        simulacaoAtual = null;
    }
    
    // Função para carregar o tipo de usuário na inicialização
    async function carregarTipoUsuario() {
        try {
            const response = await fetch('/api/simulacoes/');
            if (response.ok) {
                const data = await response.json();
                tipoUsuario = data.user_type || 'externo';
                console.log('👤 Tipo de usuário carregado:', tipoUsuario);
                
                // Configurar interface baseada no tipo de usuário
                configurarInterfacePorTipo();
            }
        } catch (error) {
            console.warn('Erro ao carregar tipo de usuário:', error);
            tipoUsuario = 'externo';
        }
    }
    
    // Função para configurar interface baseada no tipo de usuário
    function configurarInterfacePorTipo() {
        console.log('🔧 configurarInterfacePorTipo() chamado - tipoUsuario:', tipoUsuario);
        
        const criarTabLi = document.getElementById('criar-tab-li');
        const carregarTexto = document.getElementById('carregarSimulacaoTexto');
        const modalTitulo = document.getElementById('modalCarregarTitulo');
        
        console.log('📋 Elementos encontrados:', {
            criarTabLi: !!criarTabLi,
            carregarTexto: !!carregarTexto, 
            modalTitulo: !!modalTitulo
        });
        
        if (tipoUsuario === 'gerente') {
            console.log('👑 CONFIGURANDO PARA GERENTE!');
            
            // Mostrar aba de criar solicitação para gerentes
            if (criarTabLi) {
                criarTabLi.style.display = 'block';
            }
            
            // Alterar texto para "Mesclar Simulações" para gerentes
            if (carregarTexto) {
                console.log('📝 Alterando texto do botão para "Mesclar Simulações"');
                carregarTexto.textContent = 'Mesclar Simulações';
                carregarTexto.style.fontWeight = 'bold'; 
                carregarTexto.style.color = '#ff6600';
                carregarTexto.style.backgroundColor = '#ffeecc';
                carregarTexto.style.padding = '2px 4px';
                carregarTexto.style.borderRadius = '3px';
            } else {
                console.error('❌ Elemento carregarSimulacaoTexto NÃO ENCONTRADO!');
            }
            
            if (modalTitulo) {
                console.log('📝 Alterando título do modal para "Mesclar Simulações"');
                modalTitulo.textContent = 'Mesclar Simulações';
            } else {
                console.error('❌ Elemento modalCarregarTitulo NÃO ENCONTRADO!');
            }
            
            console.log('✅ Interface configurada para gerente - Mesclar Simulações disponível');
        } else {
            console.log('👤 Configurando para usuário normal:', tipoUsuario);
            
            // Ocultar aba de criar solicitação para não-gerentes
            if (criarTabLi) {
                criarTabLi.style.display = 'none';
            }
            
            // Manter texto original para outros usuários
            if (carregarTexto) {
                carregarTexto.textContent = 'Carregar Simulação';
                carregarTexto.style.fontWeight = '';
                carregarTexto.style.color = '';
                carregarTexto.style.backgroundColor = '';
                carregarTexto.style.padding = '';
                carregarTexto.style.borderRadius = '';
            }
            if (modalTitulo) {
                modalTitulo.textContent = 'Carregar Simulação';
            }
            
            console.log('✅ Interface configurada para', tipoUsuario);
        }
        
        // Forçar uma nova verificação após 2 segundos (caso os elementos ainda não existam)
        setTimeout(() => {
            const carregarTextoAgain = document.getElementById('carregarSimulacaoTexto');
            if (carregarTextoAgain && tipoUsuario === 'gerente') {
                console.log('🔄 Verificação após 2s - forçando alteração do texto');
                carregarTextoAgain.textContent = 'Mesclar Simulações';
                carregarTextoAgain.style.fontWeight = 'bold';
                carregarTextoAgain.style.color = '#ff6600';
                carregarTextoAgain.style.backgroundColor = '#ffeecc';
                carregarTextoAgain.style.padding = '2px 4px';
                carregarTextoAgain.style.borderRadius = '3px';
            }
        }, 2000);
    }
    
    // Inicialização
    document.addEventListener('DOMContentLoaded', function() {
        setupEventListeners();
        carregarTipoUsuario();
        carregarNotificacoes();
    });
    
    // Configurar event listeners
    function setupEventListeners() {
        // Botões do dropdown
        const salvarBtn = document.getElementById('salvarSimulacaoBtn');
        const carregarBtn = document.getElementById('carregarSimulacaoBtn');
        const gerenciarBtn = document.getElementById('gerenciarSimulacoesBtn');
        
        if (salvarBtn) salvarBtn.addEventListener('click', abrirModalSalvar);
        if (carregarBtn) carregarBtn.addEventListener('click', abrirModalCarregar);
        if (gerenciarBtn) gerenciarBtn.addEventListener('click', abrirModalGerenciar);
        
        // Botão confirmar salvar
        const confirmarSalvarBtn = document.getElementById('confirmarSalvarSimulacao');
        if (confirmarSalvarBtn) confirmarSalvarBtn.addEventListener('click', salvarSimulacao);
        
        // Novos botões para sistema de três níveis
        const solicitacoesBtn = document.getElementById('solicitacoesSimulacaoBtn');
        const notificacoesBtn = document.getElementById('notificacoesBtn');
        
        if (solicitacoesBtn) solicitacoesBtn.addEventListener('click', abrirModalSolicitacoes);
        if (notificacoesBtn) notificacoesBtn.addEventListener('click', abrirModalNotificacoes);
    }
    
    // Abrir modal de salvar simulação
    async function abrirModalSalvar(e) {
        e.preventDefault();
        
        // Verificar se há dados para salvar
        if (!window.editedData || window.editedData.length === 0) {
            alert('Não há dados para salvar. Carregue uma unidade primeiro.');
            return;
        }
        
        // CORREÇÃO: Limpar simulação atual para garantir que uma NOVA simulação seja criada
        limparContextoSimulacao();
        console.log('🆕 Preparando para criar nova simulação (simulacaoAtual limpa)');
        
        // Limpar formulário
        document.getElementById('nomeSimulacao').value = '';
        document.getElementById('descricaoSimulacao').value = '';
        document.getElementById('alertaSalvar').classList.add('d-none');
        
        // Carregar quantidade atual de simulações
        try {
            const response = await fetch('/api/simulacoes/');
            if (response.ok) {
                const data = await response.json();
                const total = data.total || 0;
                
                // Atualizar o texto informativo no modal
                const modalLabel = document.getElementById('modalSalvarSimulacaoLabel');
                modalLabel.innerHTML = `Salvar Simulação <small class="text-muted">(${total}/5 simulações salvas)</small>`;
                
                // Mostrar aviso se está próximo do limite
                if (total >= 4) {
                    const alertDiv = document.getElementById('alertaSalvar');
                    const mensagem = total === 4 
                        ? '⚠️ Atenção: Esta será sua última simulação (5/5). Para salvar mais, delete uma existente.'
                        : '🚫 Limite atingido! Você já tem 5 simulações. Delete uma existente para criar uma nova.';
                    
                    mostrarAlerta(alertDiv, total === 4 ? 'warning' : 'danger', mensagem);
                    
                    // Se já tem 5, desabilitar o botão de salvar
                    const salvarBtn = document.getElementById('confirmarSalvarSimulacao');
                    if (total >= 5) {
                        salvarBtn.disabled = true;
                        salvarBtn.textContent = 'Limite Atingido';
                        return; // Não abrir o modal se já tem 5
                    } else {
                        salvarBtn.disabled = false;
                        salvarBtn.textContent = 'Salvar';
                    }
                } else {
                    // Garantir que o botão esteja habilitado
                    const salvarBtn = document.getElementById('confirmarSalvarSimulacao');
                    salvarBtn.disabled = false;
                    salvarBtn.textContent = 'Salvar';
                }
            }
        } catch (error) {
            console.warn('Erro ao verificar simulações existentes:', error);
        }
        
        // Abrir modal
        const modal = new bootstrap.Modal(document.getElementById('modalSalvarSimulacao'));
        modal.show();
    }
    
    // Salvar simulação
    async function salvarSimulacao() {
        const nome = document.getElementById('nomeSimulacao').value.trim();
        const descricao = document.getElementById('descricaoSimulacao').value.trim();
        const alertDiv = document.getElementById('alertaSalvar');
        
        if (!nome) {
            mostrarAlerta(alertDiv, 'danger', 'Por favor, informe um nome para a simulação.');
            return;
        }
        
        // Validação adicional do nome
        if (nome.length < 3) {
            mostrarAlerta(alertDiv, 'danger', 'O nome da simulação deve ter pelo menos 3 caracteres.');
            return;
        }
        
        // Obter unidade base
        let unidadeBase = '';
        const unitSelect = document.getElementById('unitSelect');
        if (unitSelect) {
            if (typeof $ !== 'undefined' && $.fn.select2) {
                const selectedData = $(unitSelect).select2('data');
                if (selectedData && selectedData.length > 0) {
                    unidadeBase = selectedData[0].text.split(' - ')[0];
                }
            } else if (unitSelect.value) {
                unidadeBase = unitSelect.options[unitSelect.selectedIndex].text.split(' - ')[0];
            }
        }
        
        // Verificar se há dados para salvar
        if (!window.editedData || window.editedData.length === 0) {
            mostrarAlerta(alertDiv, 'danger', 'Não há dados na estrutura para salvar. Carregue uma unidade primeiro.');
            return;
        }
        
        // Preparar dados
        const dados = {
            nome: nome,
            descricao: descricao,
            dados_estrutura: window.editedData || [],
            unidade_base: unidadeBase,
            id: simulacaoAtual ? simulacaoAtual.id : null // Para atualização
        };
        
        // Log para debug
        if (simulacaoAtual) {
            console.log('🔄 ATUALIZANDO simulação existente:', simulacaoAtual.nome, '(ID:', simulacaoAtual.id, ')');
        } else {
            console.log('🆕 CRIANDO nova simulação:', nome);
        }
        
        try {
            const csrfToken = getCSRFToken();
            if (!csrfToken) {
                mostrarAlerta(alertDiv, 'danger', 'Erro: Token CSRF não encontrado. Recarregue a página.');
                return;
            }
            
            console.log('💾 Salvando simulação...');
            console.log('📝 Nome:', nome);
            console.log('📊 Dados:', dados.dados_estrutura.length, 'registros');
            console.log('🏢 Unidade:', unidadeBase);
            
            const response = await fetch('/api/simulacoes/salvar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(dados)
            });
            
            console.log('📡 Resposta recebida:', response.status, response.statusText);
            
            // Verificar se a resposta é JSON válido
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const result = await response.json();
                
                if (response.ok) {
                    mostrarAlerta(alertDiv, 'success', result.mensagem);
                    
                    // Limpar formulário
                    document.getElementById('nomeSimulacao').value = '';
                    document.getElementById('descricaoSimulacao').value = '';
                    
                    // Fechar modal após 2 segundos
                    setTimeout(() => {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('modalSalvarSimulacao'));
                        if (modal) modal.hide();
                    }, 2000);
                    
                    console.log('✅ Simulação salva com sucesso!');
                } else {
                    // Mensagens de erro mais específicas
                    let mensagemErro = result.erro || 'Erro ao salvar simulação';
                    
                    if (mensagemErro.includes('Já existe uma simulação com o nome')) {
                        mensagemErro = `❌ Nome já utilizado!\n\nVocê já tem uma simulação chamada "${nome}".\nEscolha um nome diferente.`;
                    } else if (mensagemErro.includes('Limite de 5 simulações atingido')) {
                        mensagemErro = `📊 Limite atingido!\n\nVocê já tem 5 simulações salvas (máximo permitido).\nDelete uma simulação existente antes de criar uma nova.`;
                    }
                    
                    mostrarAlerta(alertDiv, 'danger', mensagemErro);
                    console.log('❌ Erro ao salvar:', mensagemErro);
                }
            } else {
                // Resposta não é JSON, provavelmente HTML de erro
                const responseText = await response.text();
                console.error('Resposta não é JSON:', responseText.substring(0, 500));
                
                let mensagemErro;
                if (response.status === 403) {
                    mensagemErro = 'Erro de permissão: Token CSRF inválido. Recarregue a página e tente novamente.';
                } else if (response.status === 404) {
                    mensagemErro = 'Erro: Endpoint não encontrado. Verifique se o servidor está funcionando corretamente.';
                } else if (response.status >= 500) {
                    mensagemErro = 'Erro interno do servidor. Tente novamente mais tarde.';
                } else {
                    mensagemErro = `Erro inesperado (${response.status}): ${response.statusText}`;
                }
                
                mostrarAlerta(alertDiv, 'danger', mensagemErro);
            }
        } catch (error) {
            console.error('💥 Erro ao salvar simulação:', error);
            
            let mensagemErro;
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                mensagemErro = 'Erro de conexão: Verifique sua conexão com a internet.';
            } else {
                mensagemErro = 'Erro de rede ao salvar simulação: ' + error.message;
            }
            
            mostrarAlerta(alertDiv, 'danger', mensagemErro);
        }
    }
    
    // Abrir modal de carregar simulação
    async function abrirModalCarregar(e) {
        e.preventDefault();
        
        console.log('🔗 abrirModalCarregar() - Tipo de usuário:', tipoUsuario);
        
        // Limpar lista e alerta
        const listaDiv = document.getElementById('listaSimulacoesCarregar');
        const alertDiv = document.getElementById('alertaCarregar');
        listaDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
        alertDiv.classList.add('d-none');
        
        // Abrir modal
        const modal = new bootstrap.Modal(document.getElementById('modalCarregarSimulacao'));
        modal.show();
        
        // Carregar lista de simulações
        try {
            const response = await fetch('/api/simulacoes/');
            const data = await response.json();
            
            if (response.ok) {
                console.log('📊 Dados recebidos:', data);
                
                if (tipoUsuario === 'gerente') {
                    console.log('👑 Renderizando interface de MESCLAGEM para gerente');
                    renderizarInterfaceMesclagem(data.simulacoes, listaDiv);
                } else {
                    console.log('👤 Renderizando interface normal de carregamento');
                    renderizarListaSimulacoes(data.simulacoes, listaDiv, 'carregar');
                }
            } else {
                mostrarAlerta(alertDiv, 'danger', 'Erro ao carregar simulações');
                listaDiv.innerHTML = '';
            }
        } catch (error) {
            console.error('Erro ao carregar simulações:', error);
            mostrarAlerta(alertDiv, 'danger', 'Erro de rede ao carregar simulações');
            listaDiv.innerHTML = '';
        }
    }
    
    // Abrir modal de gerenciar simulações
    async function abrirModalGerenciar(e) {
        if (e) e.preventDefault();
        
        const alertDiv = document.getElementById('alertaGerenciar');
        const contadorSpan = document.getElementById('contadorSimulacoes');
        const tabelaBody = document.getElementById('tabelaSimulacoes');
        
        // Limpar alertas
        alertDiv.classList.add('d-none');
        
        try {
            const response = await fetch('/api/simulacoes/');
            const data = await response.json();
            
            if (response.ok) {
                // Atualizar tipo de usuário
                tipoUsuario = data.user_type || 'externo';
                
                const total = data.total || 0;
                const limite = data.limite; // Agora vem da API
                const isGerente = data.is_gerente || false;
                
                // Atualizar contador com informações mais detalhadas
                let contadorTexto;
                
                if (isGerente) {
                    contadorTexto = `Você tem <strong>${total}</strong> simulações salvas <strong class="text-success">(sem limite)</strong>`;
                } else {
                    const restantes = limite - total;
                    contadorTexto = `Você tem <strong>${total}</strong> de <strong>${limite}</strong> simulações salvas`;
                    
                    if (restantes > 0) {
                        contadorTexto += ` (restam <strong class="text-success">${restantes} slots</strong>)`;
                    } else {
                        contadorTexto += ` (<strong class="text-danger">limite atingido</strong>)`;
                    }
                }
                
                contadorTexto += '.';
                contadorSpan.innerHTML = contadorTexto;
                
                // Mostrar informações sobre o tipo de usuário
                if (tipoUsuario === 'gerente') {
                    mostrarAlerta(alertDiv, 'info', '👥 Como gerente, você pode ver simulações enviadas para análise por usuários internos.');
                } else if (tipoUsuario === 'interno') {
                    mostrarAlerta(alertDiv, 'info', '📊 Como usuário interno, você pode enviar simulações para análise dos gerentes.');
                }
                
                // Renderizar tabela
                renderizarTabelaSimulacoes(data.simulacoes, tabelaBody);
            } else {
                mostrarAlerta(alertDiv, 'danger', 'Erro ao carregar simulações');
                tabelaBody.innerHTML = '<tr><td colspan="8" class="text-center">Erro ao carregar dados</td></tr>';
            }
        } catch (error) {
            console.error('Erro ao carregar simulações:', error);
            mostrarAlerta(alertDiv, 'danger', 'Erro de rede ao carregar simulações');
            tabelaBody.innerHTML = '<tr><td colspan="8" class="text-center">Erro ao carregar dados</td></tr>';
        }
        
        // Abrir modal
        const modal = new bootstrap.Modal(document.getElementById('modalGerenciarSimulacoes'));
        modal.show();
    }
    
    // Renderizar lista de simulações para carregar
    function renderizarListaSimulacoes(simulacoes, container, tipo) {
        container.innerHTML = '';
        
        if (simulacoes.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">Nenhuma simulação salva</div>';
            return;
        }
        
        simulacoes.forEach(sim => {
            const item = document.createElement('div');
            item.className = 'list-group-item list-group-item-action';
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${sim.nome}</h6>
                    <small>${sim.criado_em}</small>
                </div>
                <small class="text-muted">Unidade: ${sim.unidade_base || 'N/A'}</small>
            `;
            
            item.addEventListener('click', () => carregarSimulacao(sim.id));
            container.appendChild(item);
        });
    }
    
    // Renderizar interface de mesclagem para gerentes
    function renderizarInterfaceMesclagem(simulacoes, container) {
        console.log('🎯 renderizarInterfaceMesclagem() - Simulações:', simulacoes.length);
        
        container.innerHTML = '';
        
        if (simulacoes.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">Nenhuma simulação disponível para mesclagem</div>';
            return;
        }
        
        // Contar simulações aprovadas
        const simulacoesAprovadas = simulacoes.filter(sim => sim.status_code === 'aprovada');
        console.log(`📊 Total: ${simulacoes.length} simulações, Aprovadas: ${simulacoesAprovadas.length}`);
        
        // Adicionar contador de simulações aprovadas
        if (simulacoesAprovadas.length === 0) {
            const alerta = document.createElement('div');
            alerta.className = 'alert alert-warning mb-3';
            alerta.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i> 
                <strong>Nenhuma simulação aprovada disponível.</strong> Para mesclar simulações, é necessário ter pelo menos 2 simulações com status "Aprovada".
            `;
            container.appendChild(alerta);
        } else if (simulacoesAprovadas.length === 1) {
            const alerta = document.createElement('div');
            alerta.className = 'alert alert-warning mb-3';
            alerta.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i> 
                <strong>Apenas 1 simulação aprovada disponível.</strong> Para mesclar, é necessário ter pelo menos 2 simulações aprovadas.
            `;
            container.appendChild(alerta);
        }
        
        // Instruções para gerentes
        const instrucoes = document.createElement('div');
        instrucoes.className = 'alert alert-info mb-3';
        instrucoes.innerHTML = `
            <i class="fas fa-info-circle"></i> 
            <strong>Mesclar Simulações:</strong> Selecione 2 ou mais simulações <strong>aprovadas</strong> para mesclar em uma nova.
            <br><small>💡 <strong>Dica:</strong> ${simulacoesAprovadas.length} de ${simulacoes.length} simulações estão aprovadas e podem ser mescladas. Simulações em outros status aparecerão desabilitadas.</small>
        `;
        container.appendChild(instrucoes);
        
        // Container para simulações com checkboxes
        const listaContainer = document.createElement('div');
        listaContainer.className = 'list-group mb-3';
        
        simulacoes.forEach(sim => {
            const item = document.createElement('div');
            const isAprovada = sim.status_code === 'aprovada';
            const itemClass = isAprovada ? 'list-group-item' : 'list-group-item list-group-item-secondary';
            const checkboxDisabled = !isAprovada ? 'disabled' : '';
            const titleText = !isAprovada ? 'title="Apenas simulações aprovadas podem ser mescladas"' : '';
            
            // Determinar cor do status
            let statusBadge = '';
            switch(sim.status_code) {
                case 'aprovada':
                    statusBadge = '<span class="badge bg-success">Aprovada</span>';
                    break;
                case 'rascunho':
                    statusBadge = '<span class="badge bg-secondary">Rascunho</span>';
                    break;
                case 'enviada_analise':
                    statusBadge = '<span class="badge bg-warning">Em Análise</span>';
                    break;
                case 'rejeitada':
                    statusBadge = '<span class="badge bg-danger">Rejeitada</span>';
                    break;
                case 'rejeitada_editada':
                    statusBadge = '<span class="badge bg-warning text-dark">Rejeitada (Editada)</span>';
                    break;
                default:
                    statusBadge = `<span class="badge bg-light text-dark">${sim.status}</span>`;
            }
            
            item.className = itemClass;
            item.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input simulacao-checkbox" type="checkbox" 
                           value="${sim.id}" id="sim-${sim.id}" ${checkboxDisabled} ${titleText}>
                    <label class="form-check-label w-100" for="sim-${sim.id}" ${titleText}>
                        <div class="d-flex w-100 justify-content-between align-items-start">
                            <div>
                                <h6 class="mb-1 ${!isAprovada ? 'text-muted' : ''}">${sim.nome}</h6>
                                <small class="text-muted">
                                    Unidade: ${sim.unidade_base || 'N/A'} | 
                                    Usuário: ${sim.usuario}
                                </small>
                            </div>
                            <div class="text-end">
                                <small class="text-muted d-block">${sim.criado_em}</small>
                                ${statusBadge}
                            </div>
                        </div>
                        ${!isAprovada ? '<small class="text-warning"><i class="fas fa-exclamation-triangle"></i> Não pode ser mesclada (não aprovada)</small>' : ''}
                    </label>
                </div>
            `;
            
            listaContainer.appendChild(item);
        });
        
        container.appendChild(listaContainer);
        
        // Formulário de mesclagem
        const formContainer = document.createElement('div');
        formContainer.id = 'formMesclagem';
        formContainer.style.display = 'none';
        formContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-cogs"></i> Configurar Mesclagem</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <label for="metodoMesclagem" class="form-label">Método de Mesclagem</label>
                            <select class="form-select" id="metodoMesclagem">
                                <option value="somar">Somar - Agrupa itens iguais e soma quantidades</option>
                                <option value="media">Média - Calcula média das quantidades para itens iguais</option>
                                <option value="substituir">Substituir - Últimas simulações prevalecem</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label for="nomeMesclagem" class="form-label">Nome da Nova Simulação</label>
                            <input type="text" class="form-control" id="nomeMesclagem" 
                                   placeholder="Ex: Mesclagem MPO 2024" maxlength="100">
                        </div>
                    </div>
                    <div class="mt-3">
                        <label for="descricaoMesclagem" class="form-label">Descrição (opcional)</label>
                        <textarea class="form-control" id="descricaoMesclagem" rows="2" 
                                  placeholder="Descreva o objetivo desta mesclagem..."></textarea>
                    </div>
                    <div class="mt-3 text-end">
                        <button type="button" class="btn btn-secondary me-2" onclick="cancelarMesclagem()">
                            Cancelar
                        </button>
                        <button type="button" class="btn btn-success" onclick="executarMesclagem()">
                            <i class="fas fa-magic"></i> Mesclar Simulações
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(formContainer);
        
        // Event listeners para checkboxes
        const checkboxes = container.querySelectorAll('.simulacao-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', atualizarFormMesclagem);
        });
        
        console.log('✅ Interface de mesclagem renderizada com', simulacoes.length, 'simulações');
    }
    
    // Atualizar visibilidade do formulário de mesclagem
    function atualizarFormMesclagem() {
        // Contar apenas checkboxes habilitados (aprovados) que estão marcados
        const checkboxes = document.querySelectorAll('.simulacao-checkbox:checked:not(:disabled)');
        const formContainer = document.getElementById('formMesclagem');
        
        console.log('🔍 Checkboxes aprovados selecionados:', checkboxes.length);
        
        if (checkboxes.length >= 2) {
            formContainer.style.display = 'block';
            
            // Gerar nome sugestivo automaticamente
            const nomeInput = document.getElementById('nomeMesclagem');
            if (!nomeInput.value) {
                const dataHora = new Date().toLocaleDateString('pt-BR');
                nomeInput.value = `Mesclagem ${checkboxes.length} simulações aprovadas - ${dataHora}`;
            }
        } else {
            formContainer.style.display = 'none';
            
            // Mostrar alerta se há simulações selecionadas mas insuficientes/inválidas
            const todasSelecionadas = document.querySelectorAll('.simulacao-checkbox:checked');
            if (todasSelecionadas.length > 0 && checkboxes.length < 2) {
                console.log('⚠️ Simulações selecionadas não aprovadas ou insuficientes');
            }
        }
    }
    
    // Cancelar processo de mesclagem
    function cancelarMesclagem() {
        // Desmarcar todos os checkboxes
        const checkboxes = document.querySelectorAll('.simulacao-checkbox');
        checkboxes.forEach(checkbox => checkbox.checked = false);
        
        // Esconder formulário
        const formContainer = document.getElementById('formMesclagem');
        formContainer.style.display = 'none';
        
        // Limpar campos
        document.getElementById('nomeMesclagem').value = '';
        document.getElementById('descricaoMesclagem').value = '';
        document.getElementById('metodoMesclagem').value = 'somar';
    }
    
    // Executar mesclagem de simulações
    async function executarMesclagem() {
        console.log('🔄 Iniciando mesclagem...');
        
        // Obter apenas simulações aprovadas selecionadas
        const checkboxes = document.querySelectorAll('.simulacao-checkbox:checked:not(:disabled)');
        const simulacaoIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
        
        // Verificar se há simulações não aprovadas selecionadas
        const checkboxesDesabilitados = document.querySelectorAll('.simulacao-checkbox:checked:disabled');
        if (checkboxesDesabilitados.length > 0) {
            alert('❌ Algumas simulações selecionadas não estão aprovadas e foram ignoradas. Apenas simulações aprovadas podem ser mescladas.');
        }
        
        // Obter dados do formulário
        const metodo = document.getElementById('metodoMesclagem').value;
        const nome = document.getElementById('nomeMesclagem').value.trim();
        const descricao = document.getElementById('descricaoMesclagem').value.trim();
        
        // Validações
        if (simulacaoIds.length < 2) {
            alert('❌ Selecione pelo menos 2 simulações aprovadas para mesclar.');
            return;
        }
        
        if (!nome) {
            alert('Informe um nome para a nova simulação.');
            document.getElementById('nomeMesclagem').focus();
            return;
        }
        
        try {
            const csrfToken = getCSRFToken();
            
            console.log('📤 Enviando dados:', {
                simulacao_ids: simulacaoIds,
                metodo: metodo,
                nome: nome,
                descricao: descricao
            });
            
            const response = await fetch('/api/simulacoes/mesclar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    simulacao_ids: simulacaoIds,
                    metodo: metodo,
                    nome: nome,
                    descricao: descricao
                })
            });
            
            const result = await response.json();
            console.log('📥 Resposta recebida:', result);
            
            if (response.ok) {
                alert(`✅ ${result.mensagem}`);
                
                // Fechar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalCarregarSimulacao'));
                modal.hide();
                
                // Limpar seleções
                cancelarMesclagem();
                
                console.log('🎉 Mesclagem concluída com sucesso!');
            } else {
                alert(`❌ Erro: ${result.erro}`);
                console.error('Erro na mesclagem:', result);
            }
            
        } catch (error) {
            console.error('Erro ao executar mesclagem:', error);
            alert('❌ Erro de rede ao executar mesclagem. Tente novamente.');
        }
    }
    
    // Renderizar tabela de simulações para gerenciar
    function renderizarTabelaSimulacoes(simulacoes, tbody) {
        tbody.innerHTML = '';
        
        if (simulacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Nenhuma simulação salva</td></tr>';
            return;
        }
        
        simulacoes.forEach(sim => {
            const tr = document.createElement('tr');
            
            // Definir classe para status
            let statusClass = '';
            switch(sim.status_code) {
                case 'rascunho':
                    statusClass = 'badge bg-secondary';
                    break;
                case 'enviada_analise':
                    statusClass = 'badge bg-warning';
                    break;
                case 'aprovada':
                    statusClass = 'badge bg-success';
                    break;
                case 'rejeitada':
                    statusClass = 'badge bg-danger';
                    break;
                case 'rejeitada_editada':
                    statusClass = 'badge bg-warning text-dark';
                    break;
                default:
                    statusClass = 'badge bg-light text-dark';
            }
            
            // Botões de ação baseados no tipo de usuário e status
            let botoesAcao = `
                    <button class="btn btn-sm btn-primary me-1" onclick="carregarSimulacao(${sim.id})" title="Carregar">
                        <i class="fas fa-download"></i>
                    </button>
            `;
            
            // Botão de editar - disponível para donos e gerentes (com permissão)
            if (sim.is_owner || (sim.pode_avaliar && ['enviada_analise', 'rejeitada', 'rejeitada_editada'].includes(sim.status_code))) {
                botoesAcao += `
                    <button class="btn btn-sm btn-success me-1 btn-editar-simulacao" onclick="editarSimulacao(${sim.id})" title="Editar Simulação">
                        <i class="fas fa-edit"></i>
                    </button>
                `;
            }
            
            if (sim.is_owner) {
                // Primeiro o botão de excluir
                botoesAcao += `
                    <button class="btn btn-sm btn-danger me-1" onclick="deletarSimulacao(${sim.id}, '${sim.nome}')" title="Deletar">
                        <i class="fas fa-trash"></i>
                    </button>`;
                
                // IMEDIATAMENTE ao lado direito: botão REENVIAR (se aplicável)
                if (sim.pode_enviar_analise && ['rejeitada', 'rejeitada_editada'].includes(sim.status_code)) {
                    botoesAcao += `<button class="btn btn-sm btn-warning reenviar-btn" onclick="enviarParaAnalise(${sim.id})" title="Reenviar para Análise (Corrigida)">
                            <i class="fas fa-redo"></i>
                            <span style="font-size: 0.65rem;">REENVIAR</span>
                        </button>`;
                }
                
                // Botão enviar para análise (para outras situações)
                if (sim.pode_enviar_analise && !['rejeitada', 'rejeitada_editada'].includes(sim.status_code)) {
                    botoesAcao += `
                        <button class="btn btn-sm btn-warning me-1" onclick="enviarParaAnalise(${sim.id})" title="Enviar para Análise">
                            <i class="fas fa-paper-plane"></i>
                        </button>`;
                }
            }
            
            if (sim.pode_avaliar) {
                if (['rejeitada', 'rejeitada_editada'].includes(sim.status_code)) {
                    botoesAcao += `
                        <button class="btn btn-sm btn-success me-1" onclick="avaliarSimulacao(${sim.id}, 'aprovar')" title="Aprovar (Reavaliação)">
                            <i class="fas fa-check"></i>
                    </button>
                        <button class="btn btn-sm btn-danger me-1" onclick="avaliarSimulacao(${sim.id}, 'rejeitar')" title="Rejeitar Novamente">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                } else {
                    botoesAcao += `
                        <button class="btn btn-sm btn-success me-1" onclick="avaliarSimulacao(${sim.id}, 'aprovar')" title="Aprovar">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-sm btn-danger me-1" onclick="avaliarSimulacao(${sim.id}, 'rejeitar')" title="Rejeitar">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                }
            }
            
            tr.innerHTML = `
                <td>${sim.nome}</td>
                <td>${sim.unidade_base || 'N/A'}</td>
                <td><span class="${statusClass}">${sim.status}</span></td>
                <td>${sim.usuario}</td>
                <td>${sim.tipo_usuario}</td>
                <td>${sim.atualizado_em}</td>
                <td>${botoesAcao}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    // Carregar simulação específica
    async function carregarSimulacao(id) {
        try {
            console.log('🔄 Iniciando carregamento da simulação ID:', id);
            
            const response = await fetch(`/api/simulacoes/${id}/`);
            const simulacao = await response.json();
            
            if (response.ok) {
                console.log('✅ Simulação carregada:', simulacao.nome);
                console.log('📊 Dados:', simulacao.dados_estrutura.length, 'registros');
                console.log('🏢 Unidade base:', simulacao.unidade_base);
                
                // CORREÇÃO: Primeiro carregar dados originais da unidade, depois aplicar simulação
                if (simulacao.unidade_base) {
                    console.log('🔄 Carregando dados originais da unidade:', simulacao.unidade_base);
                    
                    try {
                        // Carregar dados originais da API
                        const apiResponse = await fetch(`/api/cargos_diretos/?sigla=${encodeURIComponent(simulacao.unidade_base)}&tamanho=100`);
                        
                        if (apiResponse.ok) {
                            const apiData = await apiResponse.json();
                            console.log('✅ Dados originais carregados:', apiData.cargos.length, 'registros');
                            
                            // Aplicar dados originais à estrutura atual
                            if (window.originalData && window.editedData) {
                                // Limpar arrays
                                window.originalData.length = 0;
                                window.editedData.length = 0;
                                
                                // ESTRUTURA ATUAL = Dados originais da API
                                apiData.cargos.forEach(cargo => {
                                    const originalItem = {
                                        sigla: cargo.area || cargo.sigla_unidade || simulacao.unidade_base,
                                        tipo_cargo: cargo.tipo_cargo || '',
                                        denominacao: cargo.denominacao || '',
                                        categoria: cargo.categoria || '',
                                        nivel: cargo.nivel || '',
                                        quantidade: cargo.quantidade || 0,
                                        pontos: cargo.pontos || 0,
                                        valor_unitario: cargo.valor_unitario || 0,
                                        codigo_unidade: cargo.codigo_unidade || '',
                                        denominacao_unidade: cargo.denominacao_unidade || '',
                                        sigla_unidade: cargo.sigla_unidade || simulacao.unidade_base
                                    };
                                    window.originalData.push(originalItem);
                                });
                                
                                // ESTRUTURA NOVA = Dados da simulação
                                simulacao.dados_estrutura.forEach(item => {
                                    window.editedData.push(JSON.parse(JSON.stringify(item)));
                                });
                                
                                console.log('✅ Aplicação corrigida - originalData:', window.originalData.length, 'editedData:', window.editedData.length);
                                
                            } else {
                                console.error('❌ Variáveis globais originalData/editedData não encontradas');
                                alert('Erro: Sistema não inicializado corretamente. Recarregue a página.');
                                return;
                            }
                        } else {
                            console.warn('⚠️ Falha ao carregar dados originais da API, usando fallback');
                            // Fallback: usar dados da simulação para ambos (comportamento anterior)
                            aplicarSimulacaoFallback(simulacao.dados_estrutura);
                        }
                    } catch (apiError) {
                        console.warn('⚠️ Erro na API, usando fallback:', apiError);
                        // Fallback: usar dados da simulação para ambos
                        aplicarSimulacaoFallback(simulacao.dados_estrutura);
                    }
                } else {
                    console.warn('⚠️ Simulação sem unidade base, usando fallback');
                    // Fallback: usar dados da simulação para ambos
                    aplicarSimulacaoFallback(simulacao.dados_estrutura);
                }
                
                // Função de fallback
                function aplicarSimulacaoFallback(dadosSimulacao) {
                    if (window.originalData && window.editedData) {
                        window.originalData.length = 0;
                        window.editedData.length = 0;
                        
                        dadosSimulacao.forEach(item => {
                            window.originalData.push(JSON.parse(JSON.stringify(item)));
                            window.editedData.push(JSON.parse(JSON.stringify(item)));
                        });
                    }
                }
                
                // Atualizar interface
                if (window.aplicarFiltroSimulacao) {
                    // Usar a função aplicarFiltroSimulacao só para interface, mas dados já estão corretos
                    window.aplicarFiltroSimulacao(window.editedData, simulacao.unidade_base);
                } else {
                    // Fallback: atualizar interface manualmente
                    if (window.populateCurrentTable && window.populateEditableTable) {
                        const pageSize = 25;
                        window.populateCurrentTable(window.originalData.slice(0, pageSize));
                        window.populateEditableTable(window.editedData.slice(0, pageSize));
                    }
                    
                    // Atualizar relatórios
                    setTimeout(() => {
                        if (window.updateDiffReport) {
                            window.updateDiffReport();
                        }
                        if (window.updatePointsReport) {
                            window.updatePointsReport();
                        }
                    }, 100);
                }
                
                // Atualizar simulação atual
                simulacaoAtual = simulacao;
                
                // Fechar modais
                const modals = ['modalCarregarSimulacao', 'modalGerenciarSimulacoes'];
                modals.forEach(modalId => {
                    const modalEl = document.getElementById(modalId);
                    if (modalEl) {
                        const modal = bootstrap.Modal.getInstance(modalEl);
                        if (modal) modal.hide();
                    }
                });
                
                // Mensagem de sucesso
                setTimeout(() => {
                    alert(`🎉 Simulação "${simulacao.nome}" carregada!\n\n📊 ${simulacao.dados_estrutura.length} registros da simulação\n📋 ${window.originalData.length} registros da estrutura atual\n🏢 Unidade: ${simulacao.unidade_base}`);
                }, 300);
                
                console.log('🎉 Processo de carregamento concluído com sucesso!');
                
            } else {
                console.error('❌ Erro na resposta:', simulacao);
                alert('Erro ao carregar simulação: ' + (simulacao.erro || 'Erro desconhecido'));
            }
        } catch (error) {
            console.error('❌ Erro no carregamento:', error);
            alert('Erro de rede: ' + error.message);
        }
    }
    
    // Deletar simulação
    async function deletarSimulacao(id, nome) {
        if (!confirm(`Tem certeza que deseja deletar a simulação "${nome}"?`)) {
            return;
        }
        
        try {
            const csrfToken = getCSRFToken();
            if (!csrfToken) {
                alert('Erro: Token CSRF não encontrado. Recarregue a página.');
                return;
            }
            
            console.log(`Deletando simulação ${id}: ${nome}`);
            
            const response = await fetch(`/api/simulacoes/${id}/deletar/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            
            console.log('Resposta do delete:', response.status, response.statusText);
            
            // Verificar o tipo de conteúdo da resposta
            const contentType = response.headers.get('content-type');
            let result;
            
            if (contentType && contentType.includes('application/json')) {
                result = await response.json();
            } else {
                // Se não for JSON, usar uma mensagem padrão baseada no status
                result = {
                    mensagem: response.ok ? 'Simulação deletada com sucesso!' : 'Erro ao deletar simulação',
                    erro: response.ok ? null : `Erro HTTP ${response.status}: ${response.statusText}`
                };
            }
            
            if (response.ok) {
                console.log('Simulação deletada com sucesso');
                
                // CORREÇÃO: Atualizar lista de forma mais robusta (evita travamento)
                try {
                    // Mostrar mensagem de sucesso primeiro
                    const alertDiv = document.getElementById('alertaGerenciar');
                    if (alertDiv) {
                        mostrarAlerta(alertDiv, 'success', result.mensagem);
                    }
                    
                    // Aguardar um pouco antes de atualizar a lista para evitar conflitos
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    // Fazer nova requisição para obter a lista atualizada
                    const listaResponse = await fetch('/api/simulacoes/');
                    
                    if (listaResponse.ok) {
                        const listaData = await listaResponse.json();
                        
                        // Atualizar contador
                        const contadorSpan = document.getElementById('contadorSimulacoes');
                        if (contadorSpan) {
                            contadorSpan.innerHTML = `Você tem <strong>${listaData.total}</strong> simulações salvas.`;
                        }
                        
                        // Atualizar tabela
                        const tabelaBody = document.getElementById('tabelaSimulacoes');
                        if (tabelaBody) {
                            renderizarTabelaSimulacoes(listaData.simulacoes, tabelaBody);
                        }
                        
                        console.log('Lista de simulações atualizada com sucesso');
                    } else {
                        console.warn('Não foi possível atualizar a lista de simulações');
                        // Não mostrar erro ao usuário, pois a exclusão foi bem-sucedida
                        // Apenas sugerir recarregar a página
                        setTimeout(() => {
                            if (alertDiv) {
                                mostrarAlerta(alertDiv, 'info', 'Simulação deletada! Recarregue a página para ver a lista atualizada.');
                            }
                        }, 2000);
                    }
                } catch (updateError) {
                    console.warn('Erro ao atualizar lista após deletar:', updateError);
                    // Não travar a interface, apenas sugerir recarregar
                    const alertDiv = document.getElementById('alertaGerenciar');
                    if (alertDiv) {
                        setTimeout(() => {
                            mostrarAlerta(alertDiv, 'info', 'Simulação deletada! Recarregue a página para ver a lista atualizada.');
                        }, 1000);
                    }
                }
            } else {
                console.error('Erro ao deletar simulação:', result.erro || response.statusText);
                const mensagemErro = result.erro || `Erro ${response.status}: ${response.statusText}`;
                alert('Erro ao deletar simulação: ' + mensagemErro);
            }
        } catch (error) {
            console.error('Erro de rede ao deletar simulação:', error);
            
            // Tratamento de erro mais específico
            let mensagemErro;
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                mensagemErro = 'Erro de conexão: Verifique sua conexão com a internet.';
            } else if (error.name === 'SyntaxError') {
                mensagemErro = 'Erro de comunicação com o servidor. Tente novamente.';
            } else {
                mensagemErro = 'Erro inesperado: ' + error.message;
            }
            
            alert('Erro ao deletar simulação: ' + mensagemErro);
        }
    }
    
    // Função auxiliar para mostrar alertas
    function mostrarAlerta(alertDiv, tipo, mensagem) {
        alertDiv.className = `alert alert-${tipo}`;
        alertDiv.textContent = mensagem;
        alertDiv.classList.remove('d-none');
    }
    
    // Funções utilitárias para loading
    function mostrarLoading(id, mensagem = 'Carregando...') {
        // Criar elemento de loading se não existir
        let loadingElement = document.getElementById(id);
        if (!loadingElement) {
            loadingElement = document.createElement('div');
            loadingElement.id = id;
            loadingElement.className = 'loading-overlay';
            loadingElement.innerHTML = `
                <div class="loading-content">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div class="mt-2">${mensagem}</div>
                </div>
            `;
            loadingElement.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                color: white;
            `;
            document.body.appendChild(loadingElement);
        }
        loadingElement.style.display = 'flex';
    }
    
    function esconderLoading(id) {
        const loadingElement = document.getElementById(id);
        if (loadingElement) {
            loadingElement.style.display = 'none';
            // Remover após um tempo para não acumular elementos
            setTimeout(() => {
                if (loadingElement.parentNode) {
                    loadingElement.parentNode.removeChild(loadingElement);
                }
            }, 1000);
        }
    }
    
    // Função para obter CSRF token
    function getCSRFToken() {
        // Método 0: Verificar se existe uma variável global com o token
        if (window.CSRF_TOKEN) {
            console.log('CSRF Token obtido da variável global window.CSRF_TOKEN');
            return window.CSRF_TOKEN;
        }
        
        // Método 1: Tentar obter do cookie
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Django default cookie name is 'csrftoken'
                if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                    break;
                }
            }
        }
        
        // Método 2: Se não encontrou o cookie, tentar obter do input hidden no template
        if (!cookieValue) {
            const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');
            if (csrfInput) {
                cookieValue = csrfInput.value;
                console.log('CSRF Token obtido do input hidden');
            }
        }
        
        // Método 3: Tentar obter de um meta tag
        if (!cookieValue) {
            const csrfMeta = document.querySelector('meta[name=csrf-token]');
            if (csrfMeta) {
                cookieValue = csrfMeta.getAttribute('content');
                console.log('CSRF Token obtido do meta tag');
            }
        }
        
        // Método 4: Tentar obter usando a função global se disponível
        if (!cookieValue && typeof window.getCSRFTokenGlobal === 'function') {
            try {
                cookieValue = window.getCSRFTokenGlobal();
                console.log('CSRF Token obtido da função global');
            } catch (e) {
                console.warn('Erro ao obter CSRF token da função global:', e);
            }
        }
        
        // Método 5: Tentar obter usando a função padrão do template base se disponível
        if (!cookieValue && typeof window.getCSRFToken === 'function') {
            try {
                cookieValue = window.getCSRFToken();
                console.log('CSRF Token obtido da função padrão do base template');
            } catch (e) {
                console.warn('Erro ao obter CSRF token da função padrão:', e);
            }
        }
        
        // Log para debug
        if (!cookieValue) {
            console.error('CSRF Token não encontrado!');
            console.log('Cookies disponíveis:', document.cookie);
            console.log('Inputs CSRF encontrados:', document.querySelectorAll('input[name=csrfmiddlewaretoken]').length);
            
            // Última tentativa: criar token temporário se possível
            const tokenElements = document.querySelectorAll('[name*="csrf"], [id*="csrf"], [class*="csrf"]');
            if (tokenElements.length > 0) {
                console.log('Elementos relacionados a CSRF encontrados:', tokenElements);
                for (let elem of tokenElements) {
                    if (elem.value && elem.value.length > 10) {
                        cookieValue = elem.value;
                        console.log('CSRF Token obtido de elemento genérico');
                        break;
                    }
                }
            }
        } else {
            console.log('CSRF Token encontrado:', cookieValue.substring(0, 20) + '... (length: ' + cookieValue.length + ')');
        }
        
        return cookieValue;
    }
    
    // Manter a função getCookie para compatibilidade
    function getCookie(name) {
        if (name === 'csrftoken') {
            return getCSRFToken();
        }
        
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Nova função para enviar simulação para análise
    async function enviarParaAnalise(simulacaoId) {
        // Verificar se é uma simulação rejeitada (reenvio)
        const tabelaBody = document.getElementById('tabelaSimulacoes');
        let isRejeitada = false;
        
        if (tabelaBody) {
            const rows = tabelaBody.querySelectorAll('tr');
            rows.forEach(row => {
                const button = row.querySelector(`button[onclick*="enviarParaAnalise(${simulacaoId})"]`);
                if (button && button.textContent.includes('Reenviar')) {
                    isRejeitada = true;
                }
            });
        }
        
        const mensagem = isRejeitada 
            ? 'Tem certeza que deseja reenviar esta simulação corrigida para nova análise?'
            : 'Tem certeza que deseja enviar esta simulação para análise?';
            
        if (!confirm(mensagem)) {
            return;
        }
        
        try {
            const csrfToken = getCSRFToken();
            const response = await fetch('/api/simulacoes/enviar-analise/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    simulacao_id: simulacaoId
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                alert(result.mensagem || 'Simulação enviada para análise com sucesso!');
                // Recarregar apenas a tabela, não o modal inteiro
                const modalElement = document.getElementById('modalGerenciarSimulacoes');
                if (modalElement && bootstrap.Modal.getInstance(modalElement)) {
                    // Se o modal ainda está aberto, recarregar dados
                    const simResponse = await fetch('/api/simulacoes/');
                    if (simResponse.ok) {
                        const simData = await simResponse.json();
                        const tabelaBody = document.getElementById('tabelaSimulacoes');
                        renderizarTabelaSimulacoes(simData.simulacoes, tabelaBody);
                    }
                }
            } else {
                alert('Erro: ' + (result.erro || 'Erro desconhecido'));
            }
        } catch (error) {
            console.error('Erro ao enviar simulação para análise:', error);
            alert('Erro de rede ao enviar simulação para análise');
        }
    }
    
    // Nova função para avaliar simulação (aprovar/rejeitar)
    async function avaliarSimulacao(simulacaoId, acao) {
        const observacoes = prompt(`${acao === 'aprovar' ? 'Aprovar' : 'Rejeitar'} simulação. Observações (opcional):`);
        
        if (observacoes === null) return; // Usuário cancelou
        
        try {
            const csrfToken = getCSRFToken();
            const response = await fetch('/api/simulacoes/avaliar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    simulacao_id: simulacaoId,
                    acao: acao,
                    observacoes: observacoes
                })
            });
            
            const result = await response.json();
            
                    if (response.ok) {
            alert(`Simulação ${acao === 'aprovar' ? 'aprovada' : 'rejeitada'} com sucesso!`);
            // Recarregar apenas a tabela, não o modal inteiro
            const modalElement = document.getElementById('modalGerenciarSimulacoes');
            if (modalElement && bootstrap.Modal.getInstance(modalElement)) {
                // Se o modal ainda está aberto, recarregar dados
                const simResponse = await fetch('/api/simulacoes/');
                if (simResponse.ok) {
                    const simData = await simResponse.json();
                    const tabelaBody = document.getElementById('tabelaSimulacoes');
                    renderizarTabelaSimulacoes(simData.simulacoes, tabelaBody);
                }
            }
        } else {
                alert('Erro: ' + (result.erro || 'Erro desconhecido'));
            }
        } catch (error) {
            console.error('Erro ao avaliar simulação:', error);
            alert('Erro de rede ao avaliar simulação');
        }
    }
    
    // Nova função para abrir modal de solicitações
    async function abrirModalSolicitacoes() {
        const loadingId = 'loading-' + Date.now();
        
        try {
            console.log('🔄 Abrindo modal de solicitações para tipo:', tipoUsuario);
            
            // Mostrar indicador de loading
            mostrarLoading(loadingId, 'Carregando solicitações...');
            
            // Configurar interface baseada no tipo de usuário
            configurarInterfacePorTipo();
            
            // Carregar solicitações recebidas
            const response = await fetch('/api/solicitacoes-simulacao/minhas/');
            if (response.ok) {
                const data = await response.json();
                renderizarSolicitacoes(data.solicitacoes);
                console.log('📝 Solicitações carregadas:', data.solicitacoes.length);
                
                // Se for gerente, carregar também usuários internos para criar solicitações
                if (tipoUsuario === 'gerente') {
                    const usuariosResponse = await fetch('/api/usuarios-internos/');
                    if (usuariosResponse.ok) {
                        const usuariosData = await usuariosResponse.json();
                        renderizarUsuariosInternos(usuariosData.usuarios);
                        console.log('👥 Modal configurado para gerente com', usuariosData.usuarios.length, 'usuários internos');
                    } else {
                        console.error('❌ Erro ao carregar usuários internos:', usuariosResponse.status);
                    }
                    
                    // Configurar event listener para o formulário de criar solicitação
                    const formCriar = document.getElementById('formCriarSolicitacao');
                    if (formCriar) {
                        // Remover listener anterior para evitar duplicatas
                        formCriar.onsubmit = null;
                        formCriar.onsubmit = async function(e) {
                            e.preventDefault();
                            await criarSolicitacao();
                        };
                    }
                }
                
                // Esconder loading e mostrar modal
                esconderLoading(loadingId);
                const modal = new bootstrap.Modal(document.getElementById('modalSolicitacoes'));
                modal.show();
            } else {
                console.error('❌ Erro ao carregar solicitações:', response.status);
                esconderLoading(loadingId);
                alert('Erro ao carregar solicitações');
            }
        } catch (error) {
            console.error('❌ Erro de rede:', error);
            esconderLoading(loadingId);
            alert('Erro de rede ao carregar solicitações');
        }
    }
    
    // Função para renderizar solicitações
    function renderizarSolicitacoes(solicitacoes) {
        const container = document.getElementById('listaSolicitacoes');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (solicitacoes.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">Nenhuma solicitação encontrada</div>';
            return;
        }
        
        solicitacoes.forEach(sol => {
            const item = document.createElement('div');
            item.className = 'card mb-3';
            
            let statusClass = '';
            switch(sol.status) {
                case 'Pendente':
                    statusClass = 'badge bg-warning';
                    break;
                case 'Em Andamento':
                    statusClass = 'badge bg-info';
                    break;
                case 'Concluída':
                    statusClass = 'badge bg-success';
                    break;
                case 'Cancelada':
                    statusClass = 'badge bg-danger';
                    break;
            }
            
            let acoes = '';
            if (sol.status === 'Pendente') {
                acoes = `
                    <button class="btn btn-sm btn-success me-2" onclick="aceitarSolicitacao(${sol.id})">
                        <i class="fas fa-check"></i> Aceitar
                    </button>
                `;
            }
            
            item.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <h6 class="card-title">${sol.titulo}</h6>
                        <span class="${statusClass}">${sol.status}</span>
                    </div>
                    <p class="card-text">${sol.descricao}</p>
                    <small class="text-muted">
                        <strong>Solicitante:</strong> ${sol.solicitante} (${sol.solicitante_email})<br>
                        <strong>Criada em:</strong> ${sol.criada_em}<br>
                        ${sol.prazo_estimado ? `<strong>Prazo:</strong> ${sol.prazo_estimado}<br>` : ''}
                        <strong>Prioridade:</strong> ${sol.prioridade}
                    </small>
                    <div class="mt-2">
                        ${acoes}
                    </div>
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    // Função para renderizar usuários internos no dropdown
    function renderizarUsuariosInternos(usuarios) {
        const select = document.getElementById('usuarioDesignado');
        if (!select) return;
        
        // Limpar opções existentes (exceto a primeira)
        select.innerHTML = '<option value="">Selecione um usuário interno</option>';
        
        if (usuarios && usuarios.length > 0) {
            usuarios.forEach(usuario => {
                const option = document.createElement('option');
                option.value = usuario.id;
                // Usar nome_completo da API
                const nomeExibir = usuario.nome_completo || usuario.username || 'Usuário sem nome';
                const emailExibir = usuario.email || 'Sem email';
                option.textContent = `${nomeExibir} (${emailExibir})`;
                select.appendChild(option);
            });
        } else {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Nenhum usuário interno encontrado';
            option.disabled = true;
            select.appendChild(option);
        }
        
        console.log('👥 Usuários internos carregados:', usuarios.length);
    }
    
    // Função para criar nova solicitação (apenas gerentes)
    async function criarSolicitacao() {
        const usuarioDesignado = document.getElementById('usuarioDesignado').value;
        const titulo = document.getElementById('tituloSolicitacao').value.trim();
        const descricao = document.getElementById('descricaoSolicitacao').value.trim();
        const prioridade = document.getElementById('prioridadeSolicitacao').value;
        const unidadeBaseSugerida = document.getElementById('unidadeBaseSugerida').value.trim();
        const prazoEstimado = document.getElementById('prazoEstimado').value;
        
        // Validações
        if (!usuarioDesignado) {
            alert('Por favor, selecione um usuário interno.');
            return;
        }
        
        if (!titulo) {
            alert('Por favor, informe o título da solicitação.');
            return;
        }
        
        if (!descricao) {
            alert('Por favor, informe a descrição da solicitação.');
            return;
        }
        
        const loadingId = 'creating-request-' + Date.now();
        
        try {
            // Mostrar loading
            mostrarLoading(loadingId, 'Criando solicitação...');
            
            const csrfToken = getCSRFToken();
            
            // Criar controller para timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 segundos
            
            const response = await fetch('/api/solicitacoes-simulacao/criar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    usuario_designado_id: usuarioDesignado,
                    titulo: titulo,
                    descricao: descricao,
                    prioridade: prioridade,
                    unidade_base_sugerida: unidadeBaseSugerida,
                    prazo_estimado: prazoEstimado
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            const result = await response.json();
            
            if (response.ok) {
                esconderLoading(loadingId);
                alert('Solicitação criada com sucesso!');
                
                // Limpar formulário
                document.getElementById('formCriarSolicitacao').reset();
                
                // Voltar para a aba de solicitações recebidas
                const recebdasTab = document.getElementById('recebidas-tab');
                if (recebdasTab) {
                    recebdasTab.click();
                }
                
                // Recarregar apenas as solicitações (sem loading adicional)
                try {
                    const reloadResponse = await fetch('/api/solicitacoes-simulacao/minhas/');
                    if (reloadResponse.ok) {
                        const data = await reloadResponse.json();
                        renderizarSolicitacoes(data.solicitacoes);
                    }
                } catch (reloadError) {
                    console.warn('Erro ao recarregar solicitações:', reloadError);
                    // Não mostrar erro para o usuário, apenas log
                }
            } else {
                esconderLoading(loadingId);
                alert('Erro: ' + (result.erro || 'Erro desconhecido'));
            }
        } catch (error) {
            esconderLoading(loadingId);
            console.error('Erro ao criar solicitação:', error);
            
            if (error.name === 'AbortError') {
                alert('Tempo limite excedido. Tente novamente.');
            } else {
                alert('Erro de rede ao criar solicitação');
            }
        }
    }
    
    // Função para aceitar solicitação
    async function aceitarSolicitacao(solicitacaoId) {
        const observacoes = prompt('Observações sobre a aceitação (opcional):');
        if (observacoes === null) return;
        
        const loadingId = 'accepting-request-' + Date.now();
        
        try {
            // Mostrar loading
            mostrarLoading(loadingId, 'Aceitando solicitação...');
            
            const csrfToken = getCSRFToken();
            
            // Timeout de 20 segundos
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 20000);
            
            const response = await fetch('/api/solicitacoes-simulacao/aceitar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    solicitacao_id: solicitacaoId,
                    observacoes: observacoes
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            const result = await response.json();
            
            if (response.ok) {
                esconderLoading(loadingId);
                alert('Solicitação aceita com sucesso!');
                
                // Recarregar apenas as solicitações, não o modal inteiro
                const modalElement = document.getElementById('modalSolicitacoes');
                if (modalElement && bootstrap.Modal.getInstance(modalElement)) {
                    // Se o modal ainda está aberto, recarregar apenas os dados
                    try {
                        const solResponse = await fetch('/api/solicitacoes-simulacao/minhas/');
                        if (solResponse.ok) {
                            const solData = await solResponse.json();
                            renderizarSolicitacoes(solData.solicitacoes);
                        }
                    } catch (reloadError) {
                        console.warn('Erro ao recarregar solicitações:', reloadError);
                    }
                }
                
                console.log('✅ Solicitação aceita com sucesso');
            } else {
                esconderLoading(loadingId);
                alert('Erro: ' + (result.erro || 'Erro desconhecido'));
            }
        } catch (error) {
            esconderLoading(loadingId);
            console.error('❌ Erro de rede:', error);
            
            if (error.name === 'AbortError') {
                alert('Tempo limite excedido. Tente novamente.');
            } else {
                alert('Erro de rede ao aceitar solicitação');
            }
        }
    }
    
    // Função para carregar notificações
    async function carregarNotificacoes() {
        try {
            const response = await fetch('/api/notificacoes/');
            if (response.ok) {
                const data = await response.json();
                
                // Atualizar badge de notificações não lidas
                const badge = document.getElementById('notificacoesBadge');
                const button = document.getElementById('notificacoesBtn');
                
                if (badge && data.nao_lidas > 0) {
                    badge.textContent = data.nao_lidas;
                    badge.style.display = 'inline-flex';
                    
                    // Adicionar classe visual para indicar novas notificações
                    if (button) {
                        button.classList.add('has-notifications');
                    }
                } else if (badge) {
                    badge.style.display = 'none';
                    
                    // Remover classe visual
                    if (button) {
                        button.classList.remove('has-notifications');
                    }
                }
                
                console.log('🔔 Badge atualizado:', data.nao_lidas, 'não lidas');
            }
        } catch (error) {
            console.error('❌ Erro ao carregar badge de notificações:', error);
        }
    }
    
    // Função para abrir modal de notificações
    async function abrirModalNotificacoes() {
        const loadingId = 'loading-notifications-' + Date.now();
        
        try {
            // Mostrar loading
            mostrarLoading(loadingId, 'Carregando notificações...');
            
            // Timeout de 10 segundos para notificações
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);
            
            const response = await fetch('/api/notificacoes/', {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const data = await response.json();
                renderizarNotificacoes(data.notificacoes);
                
                // Esconder loading e mostrar modal
                esconderLoading(loadingId);
                const modal = new bootstrap.Modal(document.getElementById('modalNotificacoes'));
                modal.show();
                
                console.log('📢 Notificações carregadas:', data.notificacoes.length);
            } else {
                esconderLoading(loadingId);
                console.error('❌ Erro ao carregar notificações:', response.status);
                alert('Erro ao carregar notificações');
            }
        } catch (error) {
            esconderLoading(loadingId);
            console.error('❌ Erro de rede:', error);
            
            if (error.name === 'AbortError') {
                alert('Tempo limite excedido ao carregar notificações');
            } else {
                alert('Erro de rede ao carregar notificações');
            }
        }
    }
    
    // Função para renderizar notificações
    function renderizarNotificacoes(notificacoes) {
        const container = document.getElementById('listaNotificacoes');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (notificacoes.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">Nenhuma notificação</div>';
            return;
        }
        
        // Adicionar cabeçalho com botão "Excluir Todas"
        const headerDiv = document.createElement('div');
        headerDiv.className = 'mb-3 d-flex justify-content-between align-items-center';
        headerDiv.innerHTML = `
            <h6 class="mb-0">Suas Notificações</h6>
            <button class="btn btn-sm btn-outline-danger" onclick="excluirTodasNotificacoes()">
                <i class="fas fa-trash-alt me-1"></i> Excluir Todas
            </button>
        `;
        container.appendChild(headerDiv);
        
        notificacoes.forEach(notif => {
            const item = document.createElement('div');
            item.className = `list-group-item ${notif.lida ? '' : 'list-group-item-primary'}`;
            
            // Criar botões com event listeners em vez de onclick inline
            const btnGroup = document.createElement('div');
            btnGroup.className = 'btn-group btn-group-sm mt-2';
            btnGroup.setAttribute('role', 'group');
            
            // Botão marcar como lida (apenas se não foi lida)
            if (!notif.lida) {
                const btnMarcarLida = document.createElement('button');
                btnMarcarLida.className = 'btn btn-outline-primary';
                btnMarcarLida.innerHTML = '<i class="fas fa-check me-1"></i>Marcar como lida';
                btnMarcarLida.addEventListener('click', (e) => marcarComoLida(notif.id, e.target));
                btnGroup.appendChild(btnMarcarLida);
            }
            
            // Botão excluir
            const btnExcluir = document.createElement('button');
            btnExcluir.className = 'btn btn-outline-danger';
            btnExcluir.innerHTML = '<i class="fas fa-trash me-1"></i>Excluir';
            btnExcluir.addEventListener('click', (e) => excluirNotificacao(notif.id, e.target));
            btnGroup.appendChild(btnExcluir);
            
            // Montar o conteúdo do item
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${notif.titulo}</h6>
                    <small>${notif.criada_em}</small>
                </div>
                <p class="mb-1">${notif.mensagem}</p>
            `;
            
            // Adicionar os botões
            item.appendChild(btnGroup);
            container.appendChild(item);
        });
    }
    
    // Função para marcar notificação como lida
    async function marcarComoLida(notificacaoId, buttonElement = null) {
        const loadingId = 'marking-read-' + Date.now();
        
        try {
            // Mostrar feedback visual imediato
            let notifElement = null;
            if (buttonElement) {
                notifElement = buttonElement.closest('.list-group-item');
                if (notifElement) {
                    notifElement.style.opacity = '0.5';
                    buttonElement.disabled = true;
                    buttonElement.textContent = 'Marcando...';
                }
            }
            
            const csrfToken = getCSRFToken();
            
            // Timeout de 15 segundos para esta operação mais simples
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000);
            
            const response = await fetch('/api/notificacoes/marcar-lida/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    notificacao_id: notificacaoId
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                // Recarregar apenas as notificações, não o modal inteiro
                const modalElement = document.getElementById('modalNotificacoes');
                if (modalElement && bootstrap.Modal.getInstance(modalElement)) {
                    // Se o modal ainda está aberto, recarregar apenas os dados
                    const notifResponse = await fetch('/api/notificacoes/');
                    if (notifResponse.ok) {
                        const notifData = await notifResponse.json();
                        renderizarNotificacoes(notifData.notificacoes);
                    }
                }
                
                // Atualizar badge
                carregarNotificacoes();
                
                console.log('✅ Notificação marcada como lida com sucesso');
            } else {
                console.error('❌ Erro ao marcar notificação como lida:', response.status);
                // Reverter estado visual
                if (notifElement && buttonElement) {
                    notifElement.style.opacity = '1';
                    buttonElement.disabled = false;
                    buttonElement.textContent = 'Marcar como lida';
                }
                alert('Erro ao marcar notificação como lida');
            }
        } catch (error) {
            console.error('❌ Erro de rede:', error);
            
            // Reverter estado visual
            if (notifElement && buttonElement) {
                notifElement.style.opacity = '1';
                buttonElement.disabled = false;
                buttonElement.textContent = 'Marcar como lida';
            }
            
            if (error.name === 'AbortError') {
                alert('Tempo limite excedido. Tente novamente.');
            } else {
                alert('Erro de rede ao marcar notificação');
            }
        }
    }
    
    // Função para excluir uma notificação específica
    async function excluirNotificacao(notificacaoId, buttonElement = null) {
        if (!confirm('Tem certeza que deseja excluir esta notificação?')) {
            return;
        }
        
        try {
            // Mostrar feedback visual imediato
            let notifElement = null;
            if (buttonElement) {
                notifElement = buttonElement.closest('.list-group-item');
                if (notifElement) {
                    notifElement.style.opacity = '0.5';
                    buttonElement.disabled = true;
                    buttonElement.textContent = 'Excluindo...';
                }
            }
            
            const csrfToken = getCSRFToken();
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000);
            
            const response = await fetch('/api/notificacoes/excluir/', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    notificacao_id: notificacaoId
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                // Remover elemento da interface imediatamente
                if (notifElement) {
                    notifElement.remove();
                }
                
                // Recarregar notificações para atualizar contadores
                const modalElement = document.getElementById('modalNotificacoes');
                if (modalElement && bootstrap.Modal.getInstance(modalElement)) {
                    const notifResponse = await fetch('/api/notificacoes/');
                    if (notifResponse.ok) {
                        const notifData = await notifResponse.json();
                        renderizarNotificacoes(notifData.notificacoes);
                    }
                }
                
                // Atualizar badge
                carregarNotificacoes();
                
                console.log('✅ Notificação excluída com sucesso');
            } else {
                const result = await response.json();
                console.error('❌ Erro ao excluir notificação:', result.erro);
                
                // Reverter estado visual
                if (notifElement && buttonElement) {
                    notifElement.style.opacity = '1';
                    buttonElement.disabled = false;
                    buttonElement.textContent = 'Excluir';
                }
                
                alert('Erro ao excluir notificação: ' + (result.erro || 'Erro desconhecido'));
            }
        } catch (error) {
            console.error('❌ Erro de rede:', error);
            
            // Reverter estado visual
            if (notifElement && buttonElement) {
                notifElement.style.opacity = '1';
                buttonElement.disabled = false;
                buttonElement.textContent = 'Excluir';
            }
            
            if (error.name === 'AbortError') {
                alert('Tempo limite excedido. Tente novamente.');
            } else {
                alert('Erro de rede ao excluir notificação');
            }
        }
    }
    
    // Função para excluir todas as notificações
    async function excluirTodasNotificacoes() {
        if (!confirm('Tem certeza que deseja excluir TODAS as notificações? Esta ação não pode ser desfeita.')) {
            return;
        }
        
        try {
            const csrfToken = getCSRFToken();
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 20000);
            
            const response = await fetch('/api/notificacoes/excluir-todas/', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const result = await response.json();
                
                // Limpar a lista de notificações
                const container = document.getElementById('listaNotificacoes');
                if (container) {
                    container.innerHTML = '<div class="text-center text-muted">Nenhuma notificação</div>';
                }
                
                // Atualizar badge
                carregarNotificacoes();
                
                alert(result.mensagem);
                console.log('✅ Todas as notificações excluídas com sucesso');
            } else {
                const result = await response.json();
                console.error('❌ Erro ao excluir todas as notificações:', result.erro);
                alert('Erro ao excluir notificações: ' + (result.erro || 'Erro desconhecido'));
            }
        } catch (error) {
            console.error('❌ Erro de rede:', error);
            
            if (error.name === 'AbortError') {
                alert('Tempo limite excedido. Tente novamente.');
            } else {
                alert('Erro de rede ao excluir notificações');
            }
        }
    }
    
    // === FUNCIONALIDADE DE EDIÇÃO COM AUTO-SAVE ===
    
    let simulacaoEmEdicao = null;
    let timeoutAutoSave = null;
    
    // Função para editar simulação
    async function editarSimulacao(simulacaoId) {
        try {
            mostrarLoading('loading-editar', 'Carregando simulação para edição...');
            console.log('🔄 Iniciando edição da simulação ID:', simulacaoId);
            
            // Carregar simulação
            const response = await fetch(`/api/simulacoes/${simulacaoId}/`);
            const simulacao = await response.json();
            
            if (response.ok) {
                console.log('✅ Simulação carregada para edição:', simulacao.nome);
                
                // Definir simulação em edição
                simulacaoEmEdicao = {
                    id: simulacaoId,
                    nome: simulacao.nome,
                    descricao: simulacao.descricao,
                    unidade_base: simulacao.unidade_base,
                    dados_estrutura: simulacao.dados_estrutura
                };
                
                // Fechar modal de gerenciamento
                const modalGerenciar = bootstrap.Modal.getInstance(document.getElementById('modalGerenciarSimulacoes'));
                if (modalGerenciar) {
                    modalGerenciar.hide();
                }
                
                // Carregar dados no simulador principal
                await carregarSimulacaoNoEditor(simulacao);
                
                // Mostrar modo de edição
                mostrarModoEdicao();
                
                esconderLoading('loading-editar');
                mostrarMensagem('success', `🎯 Simulação "${simulacao.nome}" carregada para edição! Auto-save ativado.`);
                
            } else {
                esconderLoading('loading-editar');
                mostrarMensagem('error', 'Erro ao carregar simulação para edição');
            }
        } catch (error) {
            console.error('Erro ao editar simulação:', error);
            esconderLoading('loading-editar');
            mostrarMensagem('error', 'Erro de rede ao carregar simulação');
        }
    }
    
    // Função para carregar simulação no editor
    async function carregarSimulacaoNoEditor(simulacao) {
        try {
            // Aplicar lógica similar ao carregarSimulacao
            if (simulacao.unidade_base) {
                // Carregar dados originais da API
                const apiResponse = await fetch(`/api/cargos_diretos/?sigla=${encodeURIComponent(simulacao.unidade_base)}&tamanho=100`);
                
                if (apiResponse.ok) {
                    const apiData = await apiResponse.json();
                    
                    // Aplicar dados ao simulador
                    if (window.originalData && window.editedData) {
                        window.originalData.length = 0;
                        window.editedData.length = 0;
                        
                        // ESTRUTURA ATUAL = Dados originais da API
                        apiData.cargos.forEach(cargo => {
                            const originalItem = {
                                sigla: cargo.area || cargo.sigla_unidade || simulacao.unidade_base,
                                tipo_cargo: cargo.tipo_cargo || '',
                                denominacao: cargo.denominacao || '',
                                categoria: cargo.categoria || '',
                                nivel: cargo.nivel || '',
                                quantidade: cargo.quantidade || 0,
                                pontos: cargo.pontos || 0,
                                valor_unitario: cargo.valor_unitario || 0,
                                codigo_unidade: cargo.codigo_unidade || '',
                                denominacao_unidade: cargo.denominacao_unidade || '',
                                sigla_unidade: cargo.sigla_unidade || simulacao.unidade_base
                            };
                            window.originalData.push(originalItem);
                        });
                        
                        // ESTRUTURA NOVA = Dados da simulação
                        simulacao.dados_estrutura.forEach(item => {
                            window.editedData.push(JSON.parse(JSON.stringify(item)));
                        });
                    }
                }
            }
            
            // Atualizar interface
            if (window.aplicarFiltroSimulacao) {
                window.aplicarFiltroSimulacao(simulacao.unidade_base);
            }
            
            // Configurar listeners para auto-save
            configurarAutoSave();
            
        } catch (error) {
            console.error('Erro ao carregar simulação no editor:', error);
        }
    }
    
    // Função para mostrar modo de edição
    function mostrarModoEdicao() {
        // Criar banner de modo de edição
        const banner = document.createElement('div');
        banner.id = 'edicao-banner';
        banner.className = 'alert alert-warning d-flex justify-content-between align-items-center';
        banner.innerHTML = `
            <div>
                <i class="fas fa-edit me-2"></i>
                <strong>Modo Edição:</strong> ${simulacaoEmEdicao.nome} - Auto-save ativado
            </div>
            <div>
                <button class="btn btn-sm btn-success me-2" onclick="finalizarEdicao()">
                    <i class="fas fa-check me-1"></i> Finalizar Edição
                </button>
                <button class="btn btn-sm btn-secondary" onclick="cancelarEdicao()">
                    <i class="fas fa-times me-1"></i> Cancelar
                </button>
            </div>
        `;
        
        // Inserir banner no topo da página
        const cardHeader = document.querySelector('.card-header');
        if (cardHeader) {
            cardHeader.insertAdjacentElement('afterend', banner);
        }
    }
    
    // Função para configurar auto-save
    function configurarAutoSave() {
        console.log('🔧 Configurando auto-save para simulação:', simulacaoEmEdicao.id);
        
        // Observar mudanças nas tabelas
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' || mutation.type === 'attributes') {
                    agendarAutoSave();
                }
            });
        });
        
        // Observar tabelas
        const tabelas = document.querySelectorAll('.comparison-table tbody');
        tabelas.forEach(tabela => {
            observer.observe(tabela, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['data-field']
            });
        });
        
        // Observar inputs também
        document.addEventListener('input', function(e) {
            if (e.target.matches('.editable-cell input, .editable-cell select')) {
                agendarAutoSave();
            }
        });
    }
    
    // Função para agendar auto-save
    function agendarAutoSave() {
        if (!simulacaoEmEdicao) return;
        
        // Cancelar timeout anterior
        if (timeoutAutoSave) {
            clearTimeout(timeoutAutoSave);
        }
        
        // Agendar novo auto-save em 2 segundos
        timeoutAutoSave = setTimeout(() => {
            executarAutoSave();
        }, 2000);
    }
    
    // Função para executar auto-save
    async function executarAutoSave() {
        if (!simulacaoEmEdicao) return;
        
        try {
            console.log('💾 Executando auto-save...');
            
            // Obter dados atuais
            const dadosAtuais = window.editedData || [];
            
            // Preparar dados para envio
            const dadosParaEnvio = {
                dados_estrutura: dadosAtuais,
                nome: simulacaoEmEdicao.nome,
                descricao: simulacaoEmEdicao.descricao,
                unidade_base: simulacaoEmEdicao.unidade_base
            };
            
            // Enviar atualização
            const response = await fetch(`/api/simulacoes/${simulacaoEmEdicao.id}/atualizar/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(dadosParaEnvio)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Auto-save realizado com sucesso');
                mostrarIndicadorAutoSave('success');
                
                // Atualizar dados da simulação em edição
                simulacaoEmEdicao.dados_estrutura = dadosAtuais;
            } else {
                console.warn('⚠️ Falha no auto-save:', response.status);
                mostrarIndicadorAutoSave('error');
            }
            
        } catch (error) {
            console.error('❌ Erro no auto-save:', error);
            mostrarIndicadorAutoSave('error');
        }
    }
    
    // Função para mostrar indicador de auto-save
    function mostrarIndicadorAutoSave(tipo) {
        const banner = document.getElementById('edicao-banner');
        if (!banner) return;
        
        const indicador = banner.querySelector('.autosave-indicator') || document.createElement('span');
        indicador.className = 'autosave-indicator ms-2';
        
        if (tipo === 'success') {
            indicador.innerHTML = '<i class="fas fa-check-circle text-success"></i>';
        } else {
            indicador.innerHTML = '<i class="fas fa-exclamation-circle text-danger"></i>';
        }
        
        if (!banner.querySelector('.autosave-indicator')) {
            banner.querySelector('div:first-child').appendChild(indicador);
        }
        
        // Remover indicador após 3 segundos
        setTimeout(() => {
            if (indicador.parentNode) {
                indicador.remove();
            }
        }, 3000);
    }
    
    // Função para finalizar edição
    async function finalizarEdicao() {
        if (!simulacaoEmEdicao) return;
        
        try {
            // Executar último auto-save
            await executarAutoSave();
            
            // Limpar estado de edição
            simulacaoEmEdicao = null;
            timeoutAutoSave = null;
            
            // Remover banner
            const banner = document.getElementById('edicao-banner');
            if (banner) {
                banner.remove();
            }
            
            mostrarMensagem('success', '✅ Edição finalizada com sucesso!');
            
        } catch (error) {
            console.error('Erro ao finalizar edição:', error);
            mostrarMensagem('error', 'Erro ao finalizar edição');
        }
    }
    
    // Função para cancelar edição
    function cancelarEdicao() {
        if (!simulacaoEmEdicao) return;
        
        if (confirm('Tem certeza que deseja cancelar a edição? As alterações podem ser perdidas.')) {
            // Limpar estado de edição
            simulacaoEmEdicao = null;
            timeoutAutoSave = null;
            
            // Remover banner
            const banner = document.getElementById('edicao-banner');
            if (banner) {
                banner.remove();
            }
            
            // Recarregar página para limpar dados
            location.reload();
        }
    }
    
    // Função auxiliar para mostrar mensagens
    function mostrarMensagem(tipo, mensagem) {
        const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
        const icone = tipo === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        
        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            <i class="fas ${icone} me-2"></i>
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remover após 5 segundos
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    // Expor funções globalmente para uso nos templates
    window.carregarSimulacao = carregarSimulacao;
    window.deletarSimulacao = deletarSimulacao;
    window.editarSimulacao = editarSimulacao;
    window.finalizarEdicao = finalizarEdicao;
    window.cancelarEdicao = cancelarEdicao;
    window.enviarParaAnalise = enviarParaAnalise;
    window.avaliarSimulacao = avaliarSimulacao;
    window.aceitarSolicitacao = aceitarSolicitacao;
    window.marcarComoLida = marcarComoLida;
    window.excluirNotificacao = excluirNotificacao;
    window.excluirTodasNotificacoes = excluirTodasNotificacoes;
    // Funções de mesclagem para gerentes
    window.cancelarMesclagem = cancelarMesclagem;
    window.executarMesclagem = executarMesclagem;
})(); 