// Comparador de Unidades - simulacao.js

// Variáveis globais
let unidades = [];
let dadosUnidade1 = [];
let dadosUnidade2 = [];
let siglaSelecionada1 = '';
let siglaSelecionada2 = '';
let lookupCargoSIORG = new Map(); // Para consulta rápida dos valores de CargoSIORG

// Executa quando o DOM é carregado
document.addEventListener('DOMContentLoaded', function() {
  console.log('Inicializando Comparador de Unidades');
  
  // Inicializa a interface
  inicializarInterface();
  
  // Busca os dados do organograma para popular a lista de unidades
  buscarUnidades();
});

// Função para inicializar a interface
function inicializarInterface() {
  console.log('Inicializando interface');
  
  // Inicializa os selects com Select2
  inicializarSelect2();
  
  // Configurar eventos de interface
  document.getElementById('filterOrgao1').addEventListener('change', () => atualizarOpcoesUnidades(1));
  document.getElementById('filterOrgao2').addEventListener('change', () => atualizarOpcoesUnidades(2));
  document.getElementById('btnCompare').addEventListener('click', compararUnidades);
  
  // Adicionar event listeners para os botões de download
  document.getElementById('btnDownloadHTML').addEventListener('click', downloadComparisonHTML);
  document.getElementById('btnDownloadPDF').addEventListener('click', downloadComparisonPDF);
  
  // Eventos para os selects de unidades são configurados após inicializar o Select2
}

// Inicializa os selects com Select2
function inicializarSelect2() {
  // Função para formatar as opções na lista suspensa
  function formatUnidade(unidade) {
    if (!unidade.id || unidade.id === '') {
      return unidade.text; // Retorna texto simples para a opção padrão
    }
    
    // Extrair o nome e a sigla
    let nome = unidade.text;
    let sigla = unidade.id;
    
    // Extrair a sigla dos parênteses, se presente
    const matches = nome.match(/\(([^)]+)\)/);
    if (matches) {
      sigla = matches[1];
      nome = nome.replace(/ \([^)]+\)$/, ''); // Remove a sigla dos parênteses
    }
    
    // Criar o elemento HTML com o nome e a sigla formatada como badge
    const $unidade = $(
      '<span>' + nome + ' <span class="sigla-badge">' + sigla + '</span></span>'
    );
    
    return $unidade;
  }

  // Inicializa o Select2 para os dropdowns de unidades
  $('#filterTable1').select2({
    placeholder: 'Buscar unidade...',
    allowClear: true,
    width: '100%',
    minimumInputLength: 0, // Permitir busca com qualquer número de caracteres
    minimumResultsForSearch: 0, // Mostrar a caixa de busca sempre
    templateResult: formatUnidade, // Função para formatar as opções
    language: {
      noResults: function() {
        return "Nenhuma unidade encontrada";
      },
      searching: function() {
        return "Buscando...";
      }
    },
    // Função simples para correspondência de texto
    matcher: function(params, data) {
      // Se não houver termo de busca, retornar todos os itens
      if ($.trim(params.term) === '') {
        return data;
      }
      
      // Pular a opção de placeholder ou se o ID (sigla) está vazio
      if (!data.id || data.id === '') { 
        return null;
      }
      
      const term = params.term.toLowerCase();
      const text = data.text.toLowerCase(); // Formato: "Nome Completo da Unidade (SIGLA)"
      const id = data.id.toLowerCase();   // Sigla da unidade (valor da option)

      // 1. Prioridade: Correspondência com a sigla (ID da option)
      if (id === term || id.startsWith(term)) {
        return data;
      }
      
      // 2. Correspondência com a sigla dentro do texto (ex: "(SIGLA)")
      const siglaInTextMatch = text.match(/\(([^)]+)\)/);
      if (siglaInTextMatch) {
        const siglaFromText = siglaInTextMatch[1].toLowerCase();
        if (siglaFromText === term || siglaFromText.startsWith(term)) {
          return data;
        }
      }

      // 3. Para termos curtos (1-2 caracteres), se não houve correspondência de sigla, parar por aqui.
      // Isso evita que "SE" corresponda a "Assessoria" por exemplo.
      if (term.length <= 2) {
        return null; 
      }

      // 4. Para termos mais longos (3+ caracteres), permitir busca no nome completo da unidade.
      // Remover a parte "(SIGLA)" do texto para evitar dupla correspondência ou comportamento inesperado.
      const nomeSemSigla = text.replace(/\s*\(([^)]+)\)$/, '');
      if (nomeSemSigla.indexOf(term) > -1) {
        return data;
      }
      
      // Sem correspondência
      return null;
    }
  }).on('change', function() {
    onChangeUnidade1({ target: { value: $(this).val(), options: $(this).find('option:selected') } });
  });
  
  $('#filterTable2').select2({
    placeholder: 'Buscar unidade...',
    allowClear: true,
    width: '100%',
    minimumInputLength: 0, // Permitir busca com qualquer número de caracteres
    minimumResultsForSearch: 0, // Mostrar a caixa de busca sempre
    templateResult: formatUnidade, // Função para formatar as opções
    language: {
      noResults: function() {
        return "Nenhuma unidade encontrada";
      },
      searching: function() {
        return "Buscando...";
      }
    },
    // Função simples para correspondência de texto
    matcher: function(params, data) {
      // Se não houver termo de busca, retornar todos os itens
      if ($.trim(params.term) === '') {
        return data;
      }
      
      // Pular a opção de placeholder ou se o ID (sigla) está vazio
      if (!data.id || data.id === '') { 
        return null;
      }
      
      const term = params.term.toLowerCase();
      const text = data.text.toLowerCase(); // Formato: "Nome Completo da Unidade (SIGLA)"
      const id = data.id.toLowerCase();   // Sigla da unidade (valor da option)

      // 1. Prioridade: Correspondência com a sigla (ID da option)
      if (id === term || id.startsWith(term)) {
        return data;
      }
      
      // 2. Correspondência com a sigla dentro do texto (ex: "(SIGLA)")
      const siglaInTextMatch = text.match(/\(([^)]+)\)/);
      if (siglaInTextMatch) {
        const siglaFromText = siglaInTextMatch[1].toLowerCase();
        if (siglaFromText === term || siglaFromText.startsWith(term)) {
          return data;
        }
      }

      // 3. Para termos curtos (1-2 caracteres), se não houve correspondência de sigla, parar por aqui.
      // Isso evita que "SE" corresponda a "Assessoria" por exemplo.
      if (term.length <= 2) {
        return null; 
      }

      // 4. Para termos mais longos (3+ caracteres), permitir busca no nome completo da unidade.
      // Remover a parte "(SIGLA)" do texto para evitar dupla correspondência ou comportamento inesperado.
      const nomeSemSigla = text.replace(/\s*\(([^)]+)\)$/, '');
      if (nomeSemSigla.indexOf(term) > -1) {
        return data;
      }
      
      // Sem correspondência
      return null;
    }
  }).on('change', function() {
    onChangeUnidade2({ target: { value: $(this).val(), options: $(this).find('option:selected') } });
  });
}

// Busca os dados do organograma para extrair a lista de unidades
function buscarUnidades() {
  console.log('Buscando dados do organograma');
  
  fetch('/api/organograma-filter/')
    .then(response => {
      if (!response.ok) {
        throw new Error(`Falha ao buscar dados do organograma: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Dados do organograma recebidos');
      processarDadosOrganograma(data);
    })
    .catch(error => {
      console.error('Erro ao buscar unidades:', error);
      alert('Erro ao carregar os dados das unidades. Tente recarregar a página.');
    });
}

// Processa os dados do organograma para extrair a lista de unidades e cargos SIORG
function processarDadosOrganograma(data) {
  console.log('Processando dados do organograma e SIORG');
  
  try {
    // Processar core_unidadecargo para a lista de seleção de unidades
    if (data.core_unidadecargo && Array.isArray(data.core_unidadecargo)) {
      const unidadesVistas = new Set();
      unidades = []; 

      data.core_unidadecargo.forEach(item => {
        if (item && item.sigla && item.denominacao_unidade && item.codigo_unidade && item.grafo) {
          if (!unidadesVistas.has(item.codigo_unidade)) {
            unidades.push({
              sigla: item.sigla.trim(),
              nome: item.denominacao_unidade,
              orgao: obterOrgaoDeUnidade(item),
              codigo_unidade: item.codigo_unidade,
              grafo: item.grafo
            });
            unidadesVistas.add(item.codigo_unidade);
          }
        }
      });
      unidades.sort((a, b) => a.nome.localeCompare(b.nome));
      console.log(`${unidades.length} unidades únicas encontradas para os seletores.`);
      atualizarOpcoesUnidades(1);
      atualizarOpcoesUnidades(2);
    } else {
      console.error('Dados de core_unidadecargo ausentes ou em formato inválido.');
      alert('Erro ao carregar dados das unidades. Tente recarregar a página.');
      return; // Interrompe se não puder carregar unidades
    }

    // Processar core_cargosiorg para o lookup map
    if (data.core_cargosiorg && Array.isArray(data.core_cargosiorg)) {
      lookupCargoSIORG.clear(); // Limpar mapa antes de preencher
      data.core_cargosiorg.forEach(siorg => {
        if (siorg && siorg.cargo) {
          // siorg.cargo é a chave como "FCE 1 15"
          // siorg.unitario são os pontos (anteriormente)
          // siorg.nivel é agora considerado a fonte dos pontos, conforme solicitado
          // siorg.valor é a string R$ "XX.XXX,XX"
          let valorNumerico = 0;
          if (siorg.valor && typeof siorg.valor === 'string') {
            valorNumerico = parseFloat(siorg.valor.replace("R$", "").replace(/\./g, "").replace(",", ".").trim());
          }
          // Atualizado para usar siorg.nivel para pontos
          lookupCargoSIORG.set(siorg.cargo.trim(), {
            pontos: parseFloat(siorg.nivel) || 0, // Alterado de siorg.unitario para siorg.nivel
            custoBase: valorNumerico || 0
          });
        }
      });
      console.log(`${lookupCargoSIORG.size} cargos SIORG carregados para lookup.`);
    } else {
      console.warn('Dados de core_cargosiorg ausentes ou em formato inválido. Cálculos de custo/pontos podem falhar.');
    }

  } catch (error) {
    console.error('Erro geral ao processar dados do organograma e SIORG:', error);
    alert('Erro crítico ao processar dados. Tente recarregar a página.');
  }
}

// Função para identificar o órgão a partir dos dados da unidade
function obterOrgaoDeUnidade(unidade) {
  // Por padrão, assumimos que todas unidades são do MPO
  // No futuro, poderá ser aprimorado para identificar outros órgãos
  return "MPO";
}

// Atualiza as opções de unidades no select com base no órgão selecionado
function atualizarOpcoesUnidades(numeroTabela) {
  const orgaoSelect = document.getElementById(`filterOrgao${numeroTabela}`);
  const unidadeSelect = $(`#filterTable${numeroTabela}`);
  
  if (!orgaoSelect || !unidadeSelect) {
    console.error('Elementos de interface não encontrados para tabela', numeroTabela);
    return;
  }
  
  const orgaoSelecionado = orgaoSelect.value;
  const valorAtual = unidadeSelect.val(); // Salvar o código da unidade atualmente selecionado
  
  unidadeSelect.empty();
  unidadeSelect.append(new Option('Selecione uma Unidade', '', true, false));
  
  const unidadesFiltradasPorOrgao = unidades.filter(unidade => 
    !orgaoSelecionado || unidade.orgao === orgaoSelecionado
  );
  
  unidadesFiltradasPorOrgao.forEach(unidade => {
    // Texto da opção: "Nome da Unidade (SIGLA)"
    // Valor da opção: codigo_unidade
    const optionText = `${unidade.nome} (${unidade.sigla})`;
    unidadeSelect.append(new Option(optionText, unidade.codigo_unidade, false, false));
  });
  
  // Restaurar o valor selecionado (codigo_unidade), se ainda estiver disponível
  if (valorAtual && unidadesFiltradasPorOrgao.some(u => u.codigo_unidade === valorAtual)) {
    unidadeSelect.val(valorAtual).trigger('change.select2'); // Usar change.select2 para Select2
    } else {
    unidadeSelect.val('').trigger('change.select2');
  }
}

// Evento ao selecionar uma unidade no select 1
function onChangeUnidade1(event) {
  const codigoUnidadeSelecionada = event.target.value; // Agora é codigo_unidade
  siglaSelecionada1 = codigoUnidadeSelecionada; // Manter para compatibilidade ou renomear globalmente depois

  if (codigoUnidadeSelecionada) {
    let nomeUnidadeExibicao = '';
    if (event.target.options && event.target.options.text) {
      nomeUnidadeExibicao = event.target.options.text(); // jQuery/Select2
    } else if (event.target.options && event.target.options.selectedIndex !== undefined) {
      nomeUnidadeExibicao = event.target.options[event.target.options.selectedIndex].text; // DOM nativo
    }
    
    const titleElement = document.querySelector('.table-section:nth-of-type(1) .table-title');
    if (titleElement) {
      titleElement.textContent = nomeUnidadeExibicao || 'Unidade 1';
    }
    
    // Buscar dados usando o código da unidade
    buscarDadosUnidade(codigoUnidadeSelecionada, 1, nomeUnidadeExibicao);
  } else {
    // Limpar tabela e totais se nenhuma unidade for selecionada
    atualizarTabela(1, []);
    atualizarTotalizadores(1, 0, 0, 0);
    const titleElement = document.querySelector('.table-section:nth-of-type(1) .table-title');
    if (titleElement) titleElement.textContent = 'Unidade 1';
  }
}

// Evento ao selecionar uma unidade no select 2
function onChangeUnidade2(event) {
  const codigoUnidadeSelecionada = event.target.value; // Agora é codigo_unidade
  siglaSelecionada2 = codigoUnidadeSelecionada; // Manter para compatibilidade ou renomear globalmente depois

  if (codigoUnidadeSelecionada) {
    let nomeUnidadeExibicao = '';
    if (event.target.options && event.target.options.text) {
      nomeUnidadeExibicao = event.target.options.text(); // jQuery/Select2
    } else if (event.target.options && event.target.options.selectedIndex !== undefined) {
      nomeUnidadeExibicao = event.target.options[event.target.options.selectedIndex].text; // DOM nativo
    }
    
    const titleElement = document.querySelector('.table-section:nth-of-type(2) .table-title');
    if (titleElement) {
      titleElement.textContent = nomeUnidadeExibicao || 'Unidade 2';
    }
    
    // Buscar dados usando o código da unidade
    buscarDadosUnidade(codigoUnidadeSelecionada, 2, nomeUnidadeExibicao);
  } else {
    // Limpar tabela e totais se nenhuma unidade for selecionada
    atualizarTabela(2, []);
    atualizarTotalizadores(2, 0, 0, 0);
    const titleElement = document.querySelector('.table-section:nth-of-type(2) .table-title');
    if (titleElement) titleElement.textContent = 'Unidade 2';
  }
}

// Busca os dados específicos de uma unidade
function buscarDadosUnidade(codigoUnidadeSelecionada, numeroTabela, nomeUnidadeExibicao) {
  console.log(`Buscando dados para unidade com código ${codigoUnidadeSelecionada} para tabela ${numeroTabela}`);
  
  const tableBody = document.querySelector(`#table${numeroTabela} tbody`);
  if (!tableBody) {
    console.error(`Elemento tbody da tabela ${numeroTabela} não encontrado`);
    return;
  }
  
  tableBody.innerHTML = '<tr><td colspan="6" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Carregando dados...</td></tr>';
  
  const unidadeSelecionadaGlobal = unidades.find(u => u.codigo_unidade === codigoUnidadeSelecionada);
  
  if (!unidadeSelecionadaGlobal) { // Checar se a unidade foi encontrada
    console.error(`Não foi possível encontrar dados globais para o código de unidade: ${codigoUnidadeSelecionada}`);
    tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Erro: Dados da unidade não encontrados no sistema.</td></tr>`;
    return;
  }

  const siglaParaAPI = unidadeSelecionadaGlobal.sigla;
  const grafoDaUnidadeSelecionada = unidadeSelecionadaGlobal.grafo; // Obter o grafo da unidade selecionada

  if (!siglaParaAPI) {
    console.error(`Não foi possível encontrar a sigla para o código de unidade: ${codigoUnidadeSelecionada}`);
    tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Erro: Sigla não encontrada para a unidade.</td></tr>`;
    return;
  }
  if (!grafoDaUnidadeSelecionada) { // Checar se o grafo foi encontrado
    console.error(`Não foi possível encontrar o grafo para o código de unidade: ${codigoUnidadeSelecionada}`);
    tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Erro: Hierarquia (grafo) não encontrada para a unidade.</td></tr>`;
    return;
  }

  fetch(`/api/organograma-filter/?sigla=${siglaParaAPI}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Erro ao buscar dados: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log(`Dados recebidos da API para sigla ${siglaParaAPI}:`, data);
      
      if (!data || !data.core_unidadecargo || !Array.isArray(data.core_unidadecargo)) {
        throw new Error('Formato de dados inválido retornado pela API');
      }
      
      // Filtrar os dados para exibir apenas a unidade selecionada e seus descendentes hierárquicos
      const itensParaTabela = data.core_unidadecargo.filter(item => {
        if (!item || !item.codigo_unidade || !item.grafo) return false;
        
        // Inclui o item se:
        // 1. For a própria unidade selecionada.
        // 2. O grafo do item começar com o grafo da unidade selecionada + '-', indicando descendência.
        return item.codigo_unidade === codigoUnidadeSelecionada || 
               item.grafo.startsWith(grafoDaUnidadeSelecionada + '-');
      });
      
      console.log(`${itensParaTabela.length} itens filtrados para a tabela ${numeroTabela} (unidade ${codigoUnidadeSelecionada} e seus descendentes)`);
      
      if (numeroTabela === 1) {
        dadosUnidade1 = itensParaTabela;
      } else {
        dadosUnidade2 = itensParaTabela;
      }
      
      if (itensParaTabela.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum cargo encontrado para esta unidade ou sua hierarquia.</td></tr>';
        atualizarTotalizadores(numeroTabela, 0, 0, 0);
        return;
      }
      
      atualizarTabela(numeroTabela, itensParaTabela);
      
      if (dadosUnidade1.length > 0 && dadosUnidade2.length > 0) {
        atualizarMetricasComparativas();
      }
    })
    .catch(error => {
      console.error(`Erro ao buscar dados para unidade ${codigoUnidadeSelecionada}:`, error);
      tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Erro ao carregar dados: ${error.message}</td></tr>`;
      if (numeroTabela === 1) dadosUnidade1 = []; else dadosUnidade2 = [];
      atualizarTotalizadores(numeroTabela, 0, 0, 0);
    });
}

// Atualiza a tabela com os dados da unidade
function atualizarTabela(numeroTabela, dados) {
  console.log(`Atualizando tabela ${numeroTabela} com ${dados.length} itens.`);
  
  const tableBody = document.querySelector(`#table${numeroTabela} tbody`);
  if (!tableBody) {
    console.error(`Elemento tbody da tabela ${numeroTabela} não encontrado`);
    return;
  }
  
  if (!dados || dados.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Sem dados disponíveis para esta unidade.</td></tr>';
    atualizarTotalizadores(numeroTabela, 0, 0, 0); // Passando qtd, pontos, custo
    return;
  }
  
  tableBody.innerHTML = ''; 
  
  let totalQuantidadeTabela = 0;
  let totalPontosTabela = 0;
  let totalCustoTabela = 0;
  
  dados.forEach(item => {
    const tipoCargo = item.tipo_cargo || '';
    const categoria = parseInt(item.categoria) || 0;
    const nivel = parseInt(item.nivel) || 0;
    const quantidadeItem = parseInt(item.quantidade) || 0;

    const nivelFormatado = nivel.toString().padStart(2, '0');
    const lookupKey = `${tipoCargo} ${categoria} ${nivelFormatado}`.trim();
    
    const siorgValores = lookupCargoSIORG.get(lookupKey);
    
    let pontosSIORG = 0;
    let custoBaseSIORG = 0;
    if (siorgValores) {
      pontosSIORG = siorgValores.pontos;
      custoBaseSIORG = siorgValores.custoBase;
    } else {
      console.warn(`Valores SIORG não encontrados para a chave: ${lookupKey} (item: ${item.denominacao})`);
    }
    
    const pontosParaEsteItem = pontosSIORG * quantidadeItem;
    const custoParaEsteItem = custoBaseSIORG * quantidadeItem;
    
    totalQuantidadeTabela += quantidadeItem;
    totalPontosTabela += pontosParaEsteItem;
    totalCustoTabela += custoParaEsteItem;
    
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.denominacao || 'N/A'}</td>
      <td>${tipoCargo}</td>
      <td>${categoria}</td>
      <td>${nivel}</td>
      <td>${quantidadeItem}</td>
      <td>${pontosParaEsteItem.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
    `;
    tableBody.appendChild(tr);
  });
  
  atualizarTotalizadores(numeroTabela, totalQuantidadeTabela, totalPontosTabela, totalCustoTabela);
}

// Atualiza os totalizadores da tabela (totais de quantidade, pontos e custos)
function atualizarTotalizadores(numeroTabela, totalQuantidade, totalPontosSIORG, totalCustoSIORG) {
  console.log(`Atualizando totalizadores para Tabela ${numeroTabela}: Qtd=${totalQuantidade}, PontosSIORG=${totalPontosSIORG}, CustoSIORG=${totalCustoSIORG}`);
  
  const footerPtsDisplayElement = document.getElementById(`footerPtsDisplay${numeroTabela}`);
  const footerCustoDisplayElement = document.getElementById(`footerCustoDisplay${numeroTabela}`);
  const totalPointsBadgeElement = document.getElementById(`totalPointsBadge${numeroTabela}`); // Header badge
  
  // Atualizar o badge no cabeçalho da tabela (continua o mesmo)
  if (totalPointsBadgeElement) {
    totalPointsBadgeElement.textContent = `${totalPontosSIORG.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} pts`;
    if (totalPontosSIORG > 100) { 
      totalPointsBadgeElement.style.backgroundColor = '#dc3545'; 
    } else {
      totalPointsBadgeElement.style.backgroundColor = '#4a90e2'; 
    }
  }
  
  // Atualizar a nova linha de Pontos Totais no footer
  if (footerPtsDisplayElement) {
    const formattedPts = totalPontosSIORG.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    footerPtsDisplayElement.innerHTML = `<strong>Pts Totais:</strong> <span class="footer-value-badge">${formattedPts} pts</span>`;
  }
  
  // Atualizar a nova linha de Custo Total no footer
  if (footerCustoDisplayElement) {
    const formattedCusto = `R$ ${totalCustoSIORG.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    footerCustoDisplayElement.innerHTML = `<strong>Custo Total:</strong> <span class="footer-value-badge">${formattedCusto}</span>`;
  }
}

// Função chamada quando o botão "Comparar" é clicado
function compararUnidades() {
  console.log('Comparando unidades');
  
  // Verifica se ambas as unidades foram selecionadas
  if (!siglaSelecionada1 || !siglaSelecionada2) {
    alert('Por favor, selecione duas unidades para comparar.');
    return;
  }
  
  // Se ambas as unidades têm dados, atualiza as métricas comparativas
  if (dadosUnidade1.length > 0 && dadosUnidade2.length > 0) {
    atualizarMetricasComparativas();
  } else {
    // Se não tiver dados, busca novamente
    const select1 = document.getElementById('filterTable1');
    const select2 = document.getElementById('filterTable2');
    
    if (!select1 || !select2) {
      console.error('Elementos de select não encontrados');
      return;
    }
    
    buscarDadosUnidade(
      siglaSelecionada1, 
      1, 
      select1.options[select1.selectedIndex].text
    );
    
    buscarDadosUnidade(
      siglaSelecionada2, 
      2, 
      select2.options[select2.selectedIndex].text
    );
  }
}

// Função auxiliar para calcular os valores agregados (pontos e custo) de uma unidade com base no SIORG
function calcularValoresAgregadosSIORG(dadosDaUnidade) {
  let totalPontos = 0;
  let totalCusto = 0;

  if (dadosDaUnidade && dadosDaUnidade.length > 0) {
    dadosDaUnidade.forEach(item => {
      const tipoCargo = item.tipo_cargo || '';
      const categoria = parseInt(item.categoria) || 0;
      const nivel = parseInt(item.nivel) || 0;
      const quantidadeItem = parseInt(item.quantidade) || 0;

      const nivelFormatado = nivel.toString().padStart(2, '0');
      const lookupKey = `${tipoCargo} ${categoria} ${nivelFormatado}`.trim();
      const siorgValores = lookupCargoSIORG.get(lookupKey);

      if (siorgValores) {
        totalPontos += (siorgValores.pontos * quantidadeItem);
        totalCusto += (siorgValores.custoBase * quantidadeItem);
      }
    });
  }
  return { totalPontos, totalCusto };
}

// Atualiza as métricas comparativas entre as duas unidades
function atualizarMetricasComparativas() {
  console.log('Atualizando métricas comparativas com base nos valores SIORG');
  
  const agregados1 = calcularValoresAgregadosSIORG(dadosUnidade1);
  const agregados2 = calcularValoresAgregadosSIORG(dadosUnidade2);

  const totalPontos1 = agregados1.totalPontos;
  const totalCusto1 = agregados1.totalCusto;
  const totalPontos2 = agregados2.totalPontos;
  const totalCusto2 = agregados2.totalCusto;
  
  const diffPontos = totalPontos1 - totalPontos2;
  const diffCusto = totalCusto1 - totalCusto2;
  
  const diffPontosElement = document.getElementById('diffPontos');
  const diffGastosElement = document.getElementById('diffGastos');
  
  if (!diffPontosElement || !diffGastosElement) {
    console.error('Elementos de métricas comparativas não encontrados');
    return;
  }
  
  const diffPontosFormatado = `${Math.abs(diffPontos).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} pts`;
  if (diffPontos === 0) {
    diffPontosElement.textContent = 'Igual';
    diffPontosElement.className = 'metric-value';
  } else {
    diffPontosElement.textContent = `${diffPontosFormatado} ${diffPontos > 0 ? 'a mais (Unidade 1)' : 'a menos (Unidade 1)'}`;
    diffPontosElement.className = diffPontos > 0 ? 'metric-value diff-negative' : 'metric-value diff-positive';
  }
  
  const diffCustoFormatado = `R$ ${Math.abs(diffCusto).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (diffCusto === 0) {
    diffGastosElement.textContent = 'Igual';
    diffGastosElement.className = 'metric-value';
  } else {
    diffGastosElement.textContent = `${diffCustoFormatado} ${diffCusto > 0 ? 'a mais (Unidade 1)' : 'a menos (Unidade 1)'}`;
    diffGastosElement.className = diffCusto > 0 ? 'metric-value diff-negative' : 'metric-value diff-positive';
  }
}

// Função para download da comparação em HTML
function downloadComparisonHTML() {
  console.log('Iniciando download HTML da comparação');
  try {
    const filterSection = document.querySelector('.filter-section').cloneNode(true);
    const metricsSection = document.querySelector('.metrics-card').cloneNode(true);
    const tablesContainer = document.querySelector('.tables-container').cloneNode(true);

    // Remover interatividade desnecessária dos clones (ex: Select2)
    filterSection.querySelectorAll('select').forEach(select => {
      const selectedOption = unidades.find(u => u.codigo_unidade === select.value);
      const selectDisplay = document.createElement('p');
      selectDisplay.textContent = selectedOption ? `${selectedOption.nome} (${selectedOption.sigla})` : 'Nenhuma unidade selecionada';
      if (select.id === 'filterOrgao1' || select.id === 'filterOrgao2') {
           selectDisplay.textContent = select.options[select.selectedIndex].text;
      }
      select.parentNode.replaceChild(selectDisplay, select);
    });
    filterSection.querySelectorAll('button').forEach(btn => btn.remove()); // Remover botões de filtro/comparação

    const htmlContent = `
      <!DOCTYPE html>
      <html lang="pt-BR">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Comparação de Unidades</title>
        <style>
          body { font-family: sans-serif; margin: 20px; }
          .filter-section, .metrics-card, .table-section { margin-bottom: 20px; border: 1px solid #ccc; padding: 15px; border-radius: 5px; }
          .tables-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
          .table-header { background-color: #f0f0f0; padding: 10px; border-bottom: 1px solid #ccc; }
          .table-title { margin: 0; font-size: 1.1em; }
          .comparison-badge { background-color: #4a90e2; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-left: 10px; display: inline-block; }
          table { width: 100%; border-collapse: collapse; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f8f9fa; }
          .total-row { font-weight: bold; background-color: #f0f0f0; }
          .metric-item { margin-bottom: 5px; }
          .metric-label { font-weight: bold; }
          .metric-value { margin-left: 10px; }
          /* Adicione aqui os estilos inline copiados ou um link para o CSS externo se preferir */
        </style>
      </head>
      <body>
        <h1>Comparador de Unidades - Relatório</h1>
        <h2>Filtros Aplicados:</h2>
        ${filterSection.innerHTML}
        <h2>Resumo Comparativo:</h2>
        ${metricsSection.innerHTML}
        <h2>Detalhes das Unidades:</h2>
        ${tablesContainer.innerHTML}
      </body>
      </html>
    `;

    const blob = new Blob([htmlContent], { type: 'text/html' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'comparacao_unidades.html';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    console.log('Download HTML concluído');
  } catch (error) {
    console.error('Erro ao gerar HTML para download:', error);
    alert('Erro ao gerar HTML. Verifique o console para mais detalhes.');
  }
}

// Função para download da comparação em PDF
function downloadComparisonPDF() {
  console.log('Iniciando download PDF da comparação');
  const { jsPDF } = window.jspdf;
  const comparisonContent = document.querySelector('.comparison-container'); // Captura todo o container

  if (!comparisonContent) {
    console.error('Área de comparação não encontrada para captura PDF.');
    alert('Não foi possível encontrar a área de comparação para gerar o PDF.');
    return;
  }

  // Temporariamente tornar visível o conteúdo que pode estar escondido ou precisa de estilo específico para PDF
  // Ex: Se houver elementos com overflow: hidden que precisam ser totalmente capturados.
  // Isso pode ser complexo e depender do CSS exato.

  html2canvas(comparisonContent, {
    scale: 2, // Aumentar a escala para melhor qualidade no PDF
    useCORS: true, // Se houver imagens externas
    onclone: (documentCloned) => {
      // Oportunidade de modificar o DOM clonado antes da renderização
      // Por exemplo, remover os botões de download do clone para não aparecerem no PDF
      documentCloned.getElementById('btnDownloadHTML')?.remove();
      documentCloned.getElementById('btnDownloadPDF')?.remove();
      documentCloned.getElementById('btnCompare')?.remove(); // Remover botão de comparar também
      // Simplificar selects para texto no PDF
      documentCloned.querySelectorAll('.filter-section select').forEach(select => {
        const selectedOptionText = select.options[select.selectedIndex]?.text || 'N/A';
        const p = documentCloned.createElement('p');
        p.style.margin = '0';
        p.style.padding = '6px 0'; // Simular altura do select
        p.textContent = select.previousElementSibling?.textContent + ': ' + selectedOptionText;
        select.parentNode.replaceChild(p, select);
      });
    }
  }).then(canvas => {
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'landscape',
      unit: 'pt', // Usar pontos para que as dimensões do canvas se traduzam melhor
      format: 'a4'
    });

    const imgProps = pdf.getImageProperties(imgData);
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    
    // Calcular a largura e altura da imagem no PDF mantendo a proporção
    let imgWidth = imgProps.width;
    let imgHeight = imgProps.height;
    const ratio = imgWidth / imgHeight;

    if (imgWidth > pdfWidth - 40) { // 20pt margem de cada lado
        imgWidth = pdfWidth - 40;
        imgHeight = imgWidth / ratio;
    }
    if (imgHeight > pdfHeight - 40) {
        imgHeight = pdfHeight - 40;
        imgWidth = imgHeight * ratio;
    }

    const x = (pdfWidth - imgWidth) / 2;
    const y = 20; // Margem superior

    pdf.addImage(imgData, 'PNG', x, y, imgWidth, imgHeight);
    pdf.save('comparacao_unidades.pdf');
    console.log('Download PDF concluído');
  }).catch(error => {
    console.error('Erro ao gerar PDF para download:', error);
    alert('Erro ao gerar PDF. Verifique o console para mais detalhes.');
  });
}

// Exibe mensagem de erro
function mostrarErro(mensagem) {
  console.error(mensagem);
  alert(mensagem);
}
