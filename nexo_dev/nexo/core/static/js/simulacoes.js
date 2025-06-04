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
    
    // Função para limpar o contexto de simulação atual
    function limparContextoSimulacao() {
        if (simulacaoAtual) {
            console.log('🧹 Limpando contexto da simulação:', simulacaoAtual.nome);
        }
        simulacaoAtual = null;
    }
    
    // Inicialização
    document.addEventListener('DOMContentLoaded', function() {
        setupEventListeners();
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
                renderizarListaSimulacoes(data.simulacoes, listaDiv, 'carregar');
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
        e.preventDefault();
        
        // Limpar tabela e alerta
        const tabelaBody = document.getElementById('tabelaSimulacoes');
        const alertDiv = document.getElementById('alertaGerenciar');
        const contadorSpan = document.getElementById('contadorSimulacoes');
        
        tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner-border" role="status"></div></td></tr>';
        alertDiv.classList.add('d-none');
        
        // Abrir modal
        const modal = new bootstrap.Modal(document.getElementById('modalGerenciarSimulacoes'));
        modal.show();
        
        // Carregar lista de simulações
        try {
            const response = await fetch('/api/simulacoes/');
            const data = await response.json();
            
            if (response.ok) {
                const total = data.total || 0;
                const limite = 5;
                const restantes = limite - total;
                
                // Atualizar contador com informações mais detalhadas
                let contadorTexto = `Você tem <strong>${total}</strong> de <strong>${limite}</strong> simulações salvas`;
                
                if (restantes > 0) {
                    contadorTexto += ` (restam <strong class="text-success">${restantes} slots</strong>)`;
                } else {
                    contadorTexto += ` (<strong class="text-danger">limite atingido</strong>)`;
                }
                
                contadorTexto += '.';
                contadorSpan.innerHTML = contadorTexto;
                
                // Mostrar dica adicional
                if (total === 0) {
                    mostrarAlerta(alertDiv, 'info', '💡 Dica: Você pode salvar até 5 simulações diferentes. Cada simulação deve ter um nome único.');
                } else if (restantes === 1) {
                    mostrarAlerta(alertDiv, 'warning', '⚠️ Atenção: Você pode salvar apenas mais 1 simulação. Para criar mais, delete alguma existente.');
                } else if (restantes === 0) {
                    mostrarAlerta(alertDiv, 'danger', '🚫 Limite atingido! Delete uma simulação existente para poder criar novas.');
                }
                
                // Renderizar tabela
                renderizarTabelaSimulacoes(data.simulacoes, tabelaBody);
            } else {
                mostrarAlerta(alertDiv, 'danger', 'Erro ao carregar simulações');
                tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center">Erro ao carregar dados</td></tr>';
            }
        } catch (error) {
            console.error('Erro ao carregar simulações:', error);
            mostrarAlerta(alertDiv, 'danger', 'Erro de rede ao carregar simulações');
            tabelaBody.innerHTML = '<tr><td colspan="6" class="text-center">Erro ao carregar dados</td></tr>';
        }
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
                <p class="mb-1">${sim.descricao || '<em>Sem descrição</em>'}</p>
                <small class="text-muted">Unidade: ${sim.unidade_base || 'N/A'}</small>
            `;
            
            item.addEventListener('click', () => carregarSimulacao(sim.id));
            container.appendChild(item);
        });
    }
    
    // Renderizar tabela de simulações para gerenciar
    function renderizarTabelaSimulacoes(simulacoes, tbody) {
        tbody.innerHTML = '';
        
        if (simulacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Nenhuma simulação salva</td></tr>';
            return;
        }
        
        simulacoes.forEach(sim => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${sim.nome}</td>
                <td>${sim.descricao || '<em>Sem descrição</em>'}</td>
                <td>${sim.unidade_base || 'N/A'}</td>
                <td>${sim.criado_em}</td>
                <td>${sim.atualizado_em}</td>
                <td>
                    <button class="btn btn-sm btn-primary me-1" onclick="carregarSimulacao(${sim.id})" title="Carregar">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deletarSimulacao(${sim.id}, '${sim.nome}')" title="Deletar">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
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
    
    // Exportar funções globais
    window.carregarSimulacao = carregarSimulacao;
    window.deletarSimulacao = deletarSimulacao;
    window.limparContextoSimulacao = limparContextoSimulacao;
})(); 