/**
 * Comparador de Organogramas - JavaScript
 * 
 * Este script gerencia a interface do comparador, permitindo:
 * - Visualização lado a lado das estruturas atuais e editáveis
 * - Filtragem de dados por unidade
 * - Pesquisa nas tabelas
 * - Exportação de dados em diferentes formatos
 */

document.addEventListener('DOMContentLoaded', function() {
  console.log("Inicializando página do comparador");
  
  // Elementos DOM
  const unitSelect = document.getElementById('unitSelect');
  const searchBtn = document.getElementById('searchBtn');
  const searchInput = document.getElementById('searchInput');
  const currentTable = document.getElementById('currentTable');
  const editableTable = document.getElementById('editableTable');
  const diffReport = document.getElementById('diffReport');
  const downloadCSV = document.getElementById('downloadCSV');
  const downloadHTML = document.getElementById('downloadHTML');
  const downloadWord = document.getElementById('downloadWord');
  const downloadPDF = document.getElementById('downloadPDF');
  const downloadXLSX = document.getElementById('downloadXLSX');
  const exportTypeSelect = document.getElementById('exportType');
  const baixarAnexoBtn = document.getElementById('baixarAnexoBtn');
  
  // Dados
  let originalData = [];
  let editedData = [];
  let unidades = {};
  let filteredOriginalData = [];
  let filteredEditedData = [];
  let isFiltered = false;
  
  // Controle de paginação no estado inicial
  let currentPage = 1;
  const itemsPerPage = 25;
  let isInitialView = true;
  
  function renderPage() {
    // Definir quais dados usar (filtrados ou completos)
    const dataOriginal = isFiltered ? filteredOriginalData : originalData;
    const dataEdited = isFiltered ? filteredEditedData : editedData;
    
    // Verificar se há dados para exibir
    if (!dataOriginal.length || !dataEdited.length) {
      return;
    }
    
    // Calcular o total de páginas
    const totalPages = Math.max(1, Math.ceil(dataOriginal.length / itemsPerPage));
    
    // Garantir que a página atual esteja dentro dos limites válidos
    if (currentPage > totalPages) {
      currentPage = totalPages;
    } else if (currentPage < 1) {
      currentPage = 1;
    }
    
    // Slicing dos dados para página
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const sliceOrig = dataOriginal.slice(start, end);
    const sliceEdit = dataEdited.slice(start, end);
    
    // Povoar as tabelas
    populateCurrentTable(sliceOrig);
    populateEditableTable(sliceEdit);
    
    // Atualiza status de página
    const status = document.getElementById('paginationStatus');
    if (status) {
      const statusText = `Página ${currentPage} de ${totalPages}`;
      status.textContent = isFiltered ? `${statusText} (Filtrado)` : statusText;
    }
    
    // Atualizar estados dos botões de paginação
    updatePaginationButtons(totalPages);
  }
  
  /**
   * Atualiza o estado dos botões de paginação
   * @param {number} totalPages - Total de páginas
   */
  function updatePaginationButtons(totalPages) {
    const prevBtn = document.querySelector('#paginationControls .btn:first-child');
    const nextBtn = document.querySelector('#paginationControls .btn:last-child');
    
    if (prevBtn) {
      prevBtn.disabled = currentPage <= 1;
      prevBtn.classList.toggle('disabled', currentPage <= 1);
    }
    
    if (nextBtn) {
      nextBtn.disabled = currentPage >= totalPages;
      nextBtn.classList.toggle('disabled', currentPage >= totalPages);
    }
  }
  
  /**
   * Configura os controles de paginação
   */
  function setupPaginationControls() {
    // Remover controles antigos primeiro se existirem
    const oldControls = document.getElementById('paginationControls');
    if (oldControls) {
      oldControls.remove();
    }
    
    const container = document.createElement('div');
    container.id = 'paginationControls';
    container.style = 'text-align:center; margin:10px 0;';
    
    const prev = document.createElement('button');
    prev.textContent = 'Anterior';
    prev.className = 'btn btn-sm btn-outline-secondary me-2';
    
    const next = document.createElement('button');
    next.textContent = 'Próxima';
    next.className = 'btn btn-sm btn-outline-secondary ms-2';
    
    const status = document.createElement('span');
    status.id = 'paginationStatus';
    
    // Função para atualizar a paginação e os relatórios
    function updatePageAndReports(newPage) {
      const oldPage = currentPage;
      currentPage = newPage;
      
      // Só renderizar novamente se a página mudou
      if (oldPage !== newPage) {
        renderPage();
        
        // Atualizar o relatório de pontos após a mudança de página
        setTimeout(updatePointsReport, 100);
      }
    }
    
    prev.addEventListener('click', () => {
      const dataToUse = isFiltered ? filteredOriginalData : originalData;
      const totalPages = Math.ceil(dataToUse.length / itemsPerPage);
      
      if (currentPage > 1) {
        updatePageAndReports(currentPage - 1);
      }
    });
    
    next.addEventListener('click', () => {
      const dataToUse = isFiltered ? filteredOriginalData : originalData;
      const totalPages = Math.ceil(dataToUse.length / itemsPerPage);
      
      if (currentPage < totalPages) {
        updatePageAndReports(currentPage + 1);
      }
    });
    
    container.append(prev, status, next);
    const parent = document.querySelector('.tables-container');
    if (parent) parent.after(container);
    
    // Renderizar a página inicial
    renderPage();
  }
  
  // Inicialização
  initializeUnits();
  setupEventListeners();
  setupResizableCols();
  
  // Estado inicial: carregar toda base e montar paginação
  if (window.organogramaData && Array.isArray(window.organogramaData.core_unidadecargo)) {
    // Prepara dados originais para toda base
    originalData = window.organogramaData.core_unidadecargo.map(item => ({
      sigla: item.sigla || '',
      tipo_cargo: item.tipo_cargo || '',
      denominacao: item.denominacao || '',
      categoria: item.categoria || '',
      nivel: item.nivel || '',
      quantidade: item.quantidade || 0,
      pontos: item.pontos || 0,
      valor_unitario: item.valor_unitario || 0
    }));
    editedData = JSON.parse(JSON.stringify(originalData));
    setupPaginationControls();
    renderPage();
  }
  
  // Adicionar estilos personalizados
  addCustomStyles();
  
  // Configura ouvintes específicos para download XLSX
  downloadXLSX.addEventListener('click', exportToXLSX);
  
  /**
   * Adiciona estilos personalizados para melhorar a interatividade dos controles
   */
  function addCustomStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .editable-cell {
        background-color: #fff8e1 !important;
        border: 1px solid #ffecb3 !important;
        padding: 4px !important;
      }

      .editable-cell select.form-select {
        width: 100%;
        border: none;
        background-color: transparent;
        padding: 2px 6px;
        height: 28px;
        margin: 0;
        display: block;
        cursor: pointer;
        color: #212529;
        appearance: auto;
        -webkit-appearance: menulist;
        -moz-appearance: menulist;
      }
      
      .editable-cell select.form-select:hover {
        background-color: #ffffff;
      }
      
      .editable-cell select.form-select:focus {
        outline: none;
        background-color: #ffffff;
      }
      
      .editable-cell input[type="number"] {
        width: 100%;
        height: 28px;
        border: none;
        padding: 2px 6px;
        background-color: transparent;
      }
      
      .editable-cell input[type="number"]:focus {
        outline: none;
        background-color: #ffffff;
      }
    `;
    document.head.appendChild(style);
  }
  
  /**
   * Inicializa o dropdown de unidades
   */
  function initializeUnits() {
    // Popular o dropdown de unidades a partir dos dados
    if (window.organogramaData && Array.isArray(window.organogramaData.core_unidadecargo)) {
      // Agrupar por código de unidade para evitar duplicações
      window.organogramaData.core_unidadecargo.forEach(item => {
        const codigo = item.codigo_unidade;
        if (!unidades[codigo]) {
          unidades[codigo] = {
            codigo: codigo,
            nome: item.denominacao_unidade,
            sigla: item.sigla
          };
        }
      });
      
      // Limpar o select, mantendo apenas a opção padrão
      while (unitSelect.options.length > 1) {
        unitSelect.remove(1);
      }
      
      // Primeiro, adicionar a opção SE (Secretaria Executiva) no topo se existir nos dados
      const secretariaExecutiva = Object.values(unidades).find(u => u.sigla === 'SE');
      if (secretariaExecutiva) {
        const seOption = document.createElement('option');
        seOption.value = secretariaExecutiva.codigo;
        seOption.textContent = `${secretariaExecutiva.sigla} - ${secretariaExecutiva.nome}`;
        unitSelect.appendChild(seOption);
      }
      
      // Depois adicionar as demais opções
      Object.values(unidades)
      .filter(unidade => unidade.sigla !== 'SE') // Excluir SE pois já foi adicionado acima
      // Ordenação especial: siglas curtas (2 caracteres) primeiro, depois ordem alfabética
      .sort((a, b) => {
          const siglaA = a.sigla || '';
          const siglaB = b.sigla || '';
          
          // Se uma sigla tem 2 caracteres e a outra não, priorize a de 2 caracteres
          if (siglaA.length === 2 && siglaB.length !== 2) return -1;
          if (siglaB.length === 2 && siglaA.length !== 2) return 1;
          
          // Caso contrário, ordenação alfabética normal
          return siglaA.localeCompare(siglaB);
      })
      .forEach(unidade => {
        const option = document.createElement('option');
        option.value = unidade.codigo;
        option.textContent = `${unidade.sigla} - ${unidade.nome}`;
        unitSelect.appendChild(option);
      });
      
      // Verificar se estamos usando Select2 e reinicializar
      if (typeof $ !== 'undefined' && $.fn.select2) {
        try {
          $(unitSelect).select2('destroy');
        } catch (e) {
          // Ignorar erro se o Select2 ainda não foi inicializado
        }
        
        $(unitSelect).select2({
          placeholder: "Digite para pesquisar uma unidade...",
          allowClear: true,
          width: '350px',
          minimumInputLength: 0,
          minimumResultsForSearch: 0,
          language: {
            noResults: function() {
              return "Nenhuma unidade encontrada";
            },
            searching: function() {
              return "Pesquisando...";
            },
            inputTooShort: function(args) {
              // Não mostrar mensagem "Digite mais 1 caractere"
              return "";
            }
          }
        });
      }
    }
  }
  
  /**
   * Configura as colunas redimensionáveis
   */
  function setupResizableCols() {
    const tables = [currentTable, editableTable];
    
    tables.forEach(table => {
      const cols = table.querySelectorAll('th');
      
      Array.from(cols).forEach(col => {
        // Criar elemento de redimensionamento
        const resizer = document.createElement('div');
        resizer.classList.add('column-resizer');
        resizer.style.position = 'absolute';
        resizer.style.top = '0';
        resizer.style.right = '0';
        resizer.style.width = '5px';
        resizer.style.height = '100%';
        resizer.style.cursor = 'col-resize';
        resizer.style.userSelect = 'none';
        
        // Aplicar posicionamento relativo à célula do cabeçalho
        col.style.position = 'relative';
        col.appendChild(resizer);
        
        let startX, startWidth;
        
        resizer.addEventListener('mousedown', function(e) {
          startX = e.pageX;
          startWidth = col.offsetWidth;
          
          const index = Array.from(cols).indexOf(col);
          const tableSelector = table === currentTable ? '#currentTable' : '#editableTable';
          
          // Capturar eventos de mouse durante o redimensionamento
          document.addEventListener('mousemove', onMouseMove);
          document.addEventListener('mouseup', onMouseUp);
          
          function onMouseMove(e) {
            // Calcular nova largura e aplicar
            const newWidth = startWidth + (e.pageX - startX);
            if (newWidth > 50) { // Largura mínima
              // Definir largura para todas as células nesta coluna
              const cells = document.querySelectorAll(`${tableSelector} tr > *:nth-child(${index + 1})`);
              cells.forEach(cell => {
                cell.style.width = `${newWidth}px`;
                cell.style.minWidth = `${newWidth}px`;
                cell.style.maxWidth = `${newWidth}px`;
              });
            }
          }
          
          function onMouseUp() {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
          }
          
          e.preventDefault();
        });
      });
    });
  }
  
  /**
   * Configura os ouvintes de eventos
   */
  function setupEventListeners() {
    // Botão de pesquisa
    searchBtn.addEventListener('click', function() {
      let selectedUnit;
      
      // Verificar se estamos usando Select2
      if (typeof $ !== 'undefined' && $.fn.select2) {
        selectedUnit = $(unitSelect).val();
      } else {
        selectedUnit = unitSelect.value;
      }
      
      if (!selectedUnit) {
        alert('Por favor, selecione uma unidade');
        return;
      }
      
      // Obter o texto da opção selecionada para extrair a sigla
      let siglaUnidade;
      if (typeof $ !== 'undefined' && $.fn.select2) {
        const selectedText = $(unitSelect).select2('data')[0].text;
        siglaUnidade = selectedText.split(' - ')[0];
      } else {
        const selectedOption = unitSelect.options[unitSelect.selectedIndex];
        siglaUnidade = selectedOption.textContent.split(' - ')[0];
      }
      
      loadUnitData(selectedUnit, siglaUnidade);
    });
    
    // Botão limpar filtro - restaura tabela ao estado inicial completo
    const clearFilterBtn = document.getElementById('clearFilterBtn');
    if (clearFilterBtn) {
      clearFilterBtn.addEventListener('click', function() {
        // Limpar seleção de unidade
        if (typeof $ !== 'undefined' && $.fn.select2) {
          $(unitSelect).val(null).trigger('change');
        } else {
          unitSelect.value = '';
        }
        // Restaurar dados originais completos
        if (window.organogramaData && Array.isArray(window.organogramaData.core_unidadecargo)) {
          originalData = window.organogramaData.core_unidadecargo.map(item => ({
            sigla: item.sigla || '',
            tipo_cargo: item.tipo_cargo || '',
            denominacao: item.denominacao || '',
            categoria: item.categoria || '',
            nivel: item.nivel || '',
            quantidade: item.quantidade || 0,
            pontos: item.pontos || 0,
            valor_unitario: item.valor_unitario || 0
          }));
          editedData = JSON.parse(JSON.stringify(originalData));
        }
        // Recriar paginação e renderizar página inicial
        const pagControls = document.getElementById('paginationControls');
        if (pagControls) pagControls.remove();
        setupPaginationControls();
        currentPage = 1;
        renderPage();
        // Limpar relatório de diferenças
        clearDiffReport();
        // Atualizar relatório de pontos 
        updatePointsReport();
      });
    }
    
    // Campo de pesquisa em tempo real
    if (searchInput) {
      searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        if (searchTerm.length < 2) {
          // Restaurar todas as linhas se o termo de pesquisa for muito curto
          showAllRows();
          // Renderizar a primeira página novamente para atualizar a visualização
          currentPage = 1;
          renderPage();
          return;
        }
        
        // Filtrar as linhas das tabelas
        filterTableRows(searchTerm);
      });
    }
    
    // Botões de exportação
    downloadCSV.addEventListener('click', function() {
      exportToCSV();
    });
    
    downloadHTML.addEventListener('click', function() {
      exportToHTML();
    });
    
    downloadWord.addEventListener('click', function() {
      exportToWord();
    });
    
    downloadPDF.addEventListener('click', function() {
      exportToPDF();
    });
    // Novo listener para exportar XLSX
    downloadXLSX.addEventListener('click', function() {
      exportToXLSX();
    });
  }
  
  /**
   * Carrega os dados da unidade selecionada
   * @param {string} unitCode - Código da unidade
   * @param {string} unitSigla - Sigla da unidade
   */
  function loadUnitData(unitCode, unitSigla) {
    // Limpar dados anteriores
    originalData = [];
    editedData = [];
    
    // Mostrar indicador de carregamento
    const currentTbody = currentTable.querySelector('tbody');
    const editableTbody = editableTable.querySelector('tbody');
    
    currentTbody.innerHTML = '<tr><td colspan="8" class="text-center"><div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>Carregando dados...</td></tr>';
    editableTbody.innerHTML = '<tr><td colspan="8" class="text-center"><div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>Carregando dados...</td></tr>';
    
    // Fazer chamada à API para buscar todos os cargos associados à sigla
    console.log(`Buscando cargos para a sigla: ${unitSigla}, código: ${unitCode}`);
    
    // Construir URL para a API
    const url = `/api/cargos_diretos/?sigla=${encodeURIComponent(unitSigla)}&tamanho=100`;
    
    fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Erro HTTP: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Dados recebidos da API:', data);
        
        if (!data.cargos || !Array.isArray(data.cargos)) {
          throw new Error('Resposta da API não contém a lista de cargos esperada');
        }
        
        // Converter os dados recebidos para o formato esperado
        originalData = data.cargos.map(cargo => ({
          sigla: cargo.area || cargo.sigla_unidade || unitSigla,
          codigo_unidade: cargo.codigo_unidade || unitCode,
          denominacao_unidade: cargo.denominacao_unidade || '',
          tipo_unidade: cargo.tipo_unidade || cargo.categoria_unidade || '',
          sigla_unidade: cargo.sigla_unidade || cargo.area || unitSigla,
          tipo_cargo: cargo.tipo_cargo || '',
          denominacao: cargo.denominacao || '',
          categoria: cargo.categoria || '',
          nivel: cargo.nivel || '',
          quantidade: cargo.quantidade || 0,
          pontos: cargo.pontos || 0,
          valor_unitario: cargo.valor_unitario || 0
        }));
        
        console.log(`Encontrados ${originalData.length} registros para a unidade ${unitSigla}`);
        
        // Clonar dados para a versão editável
        editedData = JSON.parse(JSON.stringify(originalData));
        
        // Resetar filtro e página atual
        isFiltered = false;
        currentPage = 1;
        
        // Recriar controles de paginação para os novos dados
        setupPaginationControls();
        
        // Preencher as tabelas
        populateCurrentTable(originalData);
        populateEditableTable(editedData);
        
        // Limpar relatório de diferenças
        clearDiffReport();
        
        // Garantir que o relatório de pontos seja atualizado
        setTimeout(updatePointsReport, 100);
      })
      .catch(error => {
        console.error('Erro ao buscar dados:', error);
        
        // Em caso de erro, tentar usar os dados locais como fallback
        fallbackLocalDataLoad(unitCode, unitSigla);
      });
  }
  
  /**
   * Função de fallback para carregar dados localmente se a API falhar
   * @param {string} unitCode - Código da unidade
   * @param {string} unitSigla - Sigla da unidade
   */
  function fallbackLocalDataLoad(unitCode, unitSigla) {
    console.log('Usando dados locais como fallback');
    
    // Filtrar os dados relacionados à unidade selecionada
    if (window.organogramaData && Array.isArray(window.organogramaData.core_unidadecargo)) {
      // Buscar todos os registros que têm o mesmo código de unidade
      originalData = window.organogramaData.core_unidadecargo.filter(item => 
        item.codigo_unidade === unitCode
      );
      
      // Se não encontrou pelo código, tentar buscar pela sigla
      if (originalData.length === 0 && unitSigla) {
        console.log(`Nenhum item encontrado com código ${unitCode}, tentando buscar pela sigla ${unitSigla}`);
        originalData = window.organogramaData.core_unidadecargo.filter(item =>
          item.sigla && item.sigla.toUpperCase() === unitSigla.toUpperCase()
        );
      }
      
      console.log(`Encontrados ${originalData.length} registros para a unidade ${unitSigla} (${unitCode}) usando dados locais`);
      
      // Clonar dados para a versão editável
      editedData = JSON.parse(JSON.stringify(originalData));
      
      // Preencher as tabelas
      populateCurrentTable(originalData);
      populateEditableTable(editedData);
      
      // Limpar relatório de diferenças
      clearDiffReport();
      
      // Atualizar relatório de pontos
      setTimeout(updatePointsReport, 100);
    } else {
      const currentTbody = currentTable.querySelector('tbody');
      const editableTbody = editableTable.querySelector('tbody');
      
      currentTbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Não foi possível carregar os dados. Por favor, tente novamente.</td></tr>';
      editableTbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Não foi possível carregar os dados. Por favor, tente novamente.</td></tr>';
    }
  }
  
  /**
   * Formata um valor para exibição, evitando "Nan"
   * @param {*} value - Valor a ser formatado
   * @returns {string} - Valor formatado
   */
  function formatValue(value) {
    // Verificar se o valor é undefined, null, NaN ou string "nan"
    if (value === undefined || value === null) return '';
    if (typeof value === 'string' && (value.toLowerCase() === 'nan' || value.toLowerCase() === 'null')) return '';
    if (typeof value === 'number' && isNaN(value)) return '';
    
    // Formatar qualquer valor numérico com duas casas decimais
    if (typeof value === 'number') {
      // Usar toFixed(2) para garantir exatamente duas casas decimais
      return Number(value.toFixed(2)).toString();
    }
    
    return value.toString();
  }
  
  /**
   * Preenche a tabela de estrutura atual
   * @param {Array} data - Dados da unidade
   */
  function populateCurrentTable(data) {
    const tbody = currentTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum dado encontrado para esta unidade</td></tr>';
      return;
    }
    
    data.forEach(item => {
      const row = document.createElement('tr');
      
      // Calcular pontos totais
      const pontosTotais = parseFloat(item.pontos || 0) * parseInt(item.quantidade || 1);
      
      row.innerHTML = `
        <td>${formatValue(item.sigla)}</td>
        <td>${formatValue(item.tipo_cargo)}</td>
        <td>${formatValue(item.denominacao)}</td>
        <td>${formatValue(item.categoria)}</td>
        <td>${formatValue(item.nivel)}</td>
        <td>${formatValue(item.quantidade)}</td>
        <td>${formatValue(pontosTotais)}</td>
      `;
      
      tbody.appendChild(row);
    });
  }
  
  /**
   * Preenche a tabela de estrutura editável
   * @param {Array} data - Dados da unidade
   */
  function populateEditableTable(data) {
    const tbody = editableTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center">Nenhum dado encontrado para esta unidade</td></tr>';
      return;
    }
    
    data.forEach((item, index) => {
      const row = document.createElement('tr');
      
      // Calcular pontos totais
      const pontosTotais = parseFloat(item.pontos || 0) * parseInt(item.quantidade || 1);
      
      row.innerHTML = `
        <td class="editable-cell"><input type="text" class="form-control form-control-sm" data-field="sigla" data-index="${index}" value="${formatValue(item.sigla)}" style="background-color:#fff8e1; border:none; width:100%;"></td>
        <td class="editable-cell">
          <select class="form-select form-select-sm" data-field="tipo_cargo" data-index="${index}" style="background-color:#fff8e1; border:none; width:100%;">
            <option value="FCE" ${item.tipo_cargo === 'FCE' ? 'selected' : ''}>FCE</option>
            <option value="CCE" ${item.tipo_cargo === 'CCE' ? 'selected' : ''}>CCE</option>
          </select>
        </td>
        <td class="editable-cell col-denom"><input type="text" class="form-control form-control-sm" data-field="denominacao" data-index="${index}" value="${formatValue(item.denominacao)}" style="background-color:#fff8e1; border:none; width:100%;"></td>
        <td class="editable-cell"><input type="number" min="1" max="3" data-field="categoria" data-index="${index}" value="${formatValue(item.categoria)}" style="background-color:#fff8e1; border:none; width:100%;"></td>
        <td class="editable-cell"><input type="number" min="1" max="18" data-field="nivel" data-index="${index}" value="${formatValue(item.nivel)}" style="background-color:#fff8e1; border:none; width:100%;"></td>
        <td class="editable-cell"><input type="number" min="1" data-field="quantidade" data-index="${index}" value="${formatValue(item.quantidade)}" style="background-color:#fff8e1; border:none; width:100%;"></td>
        <td id="pontos-${index}">${formatValue(pontosTotais)}</td>
        <td class="text-center">
          <button class="btn btn-sm btn-outline-danger delete-cargo" data-index="${index}" title="Excluir cargo">
            <i class="fas fa-trash"></i>
          </button>
        </td>
      `;
      
      tbody.appendChild(row);
    });
    
    setupEditableFields();
    setupDeleteButtons();
  }
  
  /**
   * Configura os campos editáveis
   */
  function setupEditableFields() {
    // Capturar tanto inputs quanto selects
    const inputs = document.querySelectorAll('#editableTable input[data-field]');
    const selects = document.querySelectorAll('#editableTable select[data-field]');
    
    // Remover listeners anteriores (para evitar duplicação)
    inputs.forEach(input => {
      input.removeEventListener('change', handleInputChange);
      input.addEventListener('change', handleInputChange);
    });
    
    // Função para tratar mudanças em inputs
    function handleInputChange() {
        const field = this.dataset.field;
        const index = parseInt(this.dataset.index);
        let value = this.value.trim();
        
        console.log(`Input alterado: campo=${field}, índice=${index}, valor=${value}`);
        
        // Validar os valores
        if (field === 'categoria') {
          const numValue = parseInt(value);
          if (numValue < 1 || numValue > 3) {
            alert('A categoria deve estar entre 1 e 3');
            this.value = editedData[index][field];
            return;
          }
        } else if (field === 'nivel') {
          const numValue = parseInt(value);
          if (numValue < 1 || numValue > 18) {
            alert('O nível deve estar entre 1 e 18');
            this.value = editedData[index][field];
            return;
          }
        } else if (field === 'quantidade') {
          const numValue = parseInt(value);
          if (isNaN(numValue) || numValue < 1) {
            alert('A quantidade deve ser pelo menos 1');
            // Restaurar valor original
            this.value = editedData[index][field] || 1;
            return;
          }
          // Garantir que value seja um número para quantidade
          value = numValue;
        } else if (field === 'sigla' && value === '') {
          alert('A área não pode estar vazia');
          this.value = editedData[index][field];
          return;
        } else if (field === 'denominacao' && value === '') {
          alert('A denominação não pode estar vazia');
          this.value = editedData[index][field];
          return;
        }
        
        // Atualizar o valor no objeto de dados
        if (editedData[index]) {
          // Salvar valor anterior para comparação
          const oldValue = editedData[index][field];
          
          // Atualizar com novo valor
          editedData[index][field] = value;
          
          console.log(`Valor alterado: ${field} de ${oldValue} para ${value}`);
          
          // Se houve mudança em categoria, nível ou quantidade, recalcular os valores
          if (oldValue !== value && (field === 'categoria' || field === 'nivel' || field === 'quantidade')) {
            // Recalcular valores usando a função normal, agora melhorada
            recalcularValores(index);
          }
          
          // Verificar diferenças e atualizar os relatórios
          updateDiffReport();
          updatePointsReport();
        }
    }
    
    // Remover listeners anteriores para selects (para evitar duplicação)
    selects.forEach(select => {
      select.removeEventListener('change', handleSelectChange);
      select.addEventListener('change', handleSelectChange);
      
      // Adicionar também eventos de foco para garantir interatividade
      select.addEventListener('focus', function() {
        this.style.backgroundColor = '#ffffff';
      });
      
      select.addEventListener('blur', function() {
        this.style.backgroundColor = 'transparent';
      });
    });
    
    // Função para tratar mudanças em selects
    function handleSelectChange() {
      const field = this.dataset.field;
      const index = parseInt(this.dataset.index);
      const value = this.value;
      
      console.log(`Select changed: ${field} at index ${index} to value ${value}`);
      
      // Atualizar o valor no objeto de dados
      if (editedData[index]) {
        // Salvar valor anterior para comparação
        const oldValue = editedData[index][field];
        
        // Atualizar com novo valor
        editedData[index][field] = value;
        
        // Se houve mudança no tipo de cargo, recalcular os valores
        if (oldValue !== value && field === 'tipo_cargo') {
          console.log(`Tipo de cargo alterado de ${oldValue} para ${value}`);
          recalcularValores(index);
        }
        
        // Verificar diferenças e atualizar os relatórios
        updateDiffReport();
        updatePointsReport();
      }
    }
  }
  
  /**
   * Recalcula os valores de pontos com base nas alterações
   * @param {number} index - Índice do item nos dados editados
   */
  function recalcularValores(index) {
    const item = editedData[index];
    const tipoCargo = item.tipo_cargo;
    const categoria = parseInt(item.categoria);
    const nivel = parseInt(item.nivel);
    const quantidade = parseInt(item.quantidade || 1);
    
    console.log(`Recalculando valores para o item ${index}: tipo=${tipoCargo}, categoria=${categoria}, nivel=${nivel}, quantidade=${quantidade}`);
    
    // Buscar os valores de pontos e valor unitário na tabela de cargos
    const cargoSIORG = buscarCargoSIORG(tipoCargo, categoria, nivel);
    
    if (cargoSIORG) {
      console.log(`Valores recalculados para o item ${index}:`, cargoSIORG, `Pontos totais: ${cargoSIORG.pontos * quantidade}`);
      
      // Atualizar pontos e valor unitário no objeto de dados
      item.pontos = cargoSIORG.pontos;
      item.valor_unitario = cargoSIORG.valor_unitario;
      
      // Calcular valores totais - garantir que são números válidos
      const pontosTotais = parseFloat(item.pontos) * quantidade;
      
      // Atualizar a exibição - armazenar em variáveis para garantir precisão
      const pontosCell = document.getElementById(`pontos-${index}`);
      
      // Usar formatValue para garantir formatação consistente
      if (pontosCell) {
        pontosCell.textContent = formatValue(pontosTotais);
        pontosCell.dataset.valor = pontosTotais; // Armazenar valor não formatado
      }
      
      // Destacar visualmente as células que foram atualizadas
      if (pontosCell) pontosCell.classList.add('updated-value');
      
      // Remover destaque após 1.5 segundos
      setTimeout(() => {
        if (pontosCell) pontosCell.classList.remove('updated-value');
      }, 1500);
      
      // Verificar e atualizar o input com o valor atual para manter consistência
      const qtyInput = document.querySelector(`#editableTable input[data-field="quantidade"][data-index="${index}"]`);
      if (qtyInput && qtyInput.value != quantidade) {
        qtyInput.value = quantidade;
      }
      
      return true; // Indicar que a atualização foi bem-sucedida
    } else {
      console.warn(`Não foi possível encontrar valores para o cargo ${tipoCargo}, categoria ${categoria}, nível ${nivel}`);
      
      // Manter os valores anteriores se não encontrar valores novos
      // Em vez de deixar como 0, manter os valores anteriores
      console.log(`Mantendo valores anteriores: pontos=${item.pontos}`);
      
      // Calcular com os valores existentes
      const pontosTotais = parseFloat(item.pontos || 0) * quantidade;
      
      // Atualizar a exibição
      const pontosCell = document.getElementById(`pontos-${index}`);
      
      if (pontosCell) pontosCell.textContent = formatValue(pontosTotais);
      
      // Verificar e atualizar o input com o valor atual
      const qtyInput = document.querySelector(`#editableTable input[data-field="quantidade"][data-index="${index}"]`);
      if (qtyInput && qtyInput.value != quantidade) {
        qtyInput.value = quantidade;
      }
      
      return false; // Indicar que não encontrou valores novos
    }
  }
  
  /**
   * Função para converter string de moeda (R$ X.XXX,XX) para número
   * @param {string} valorStr - String formatada como moeda brasileira
   * @returns {number} - Valor numérico
   */
  function converterMoedaParaNumero(valorStr) {
    if (!valorStr || typeof valorStr !== 'string') return 0;
    
    // Remove R$, pontos e substitui vírgula por ponto
    return parseFloat(valorStr.replace(/[R$\s.]/g, '').replace(',', '.')) || 0;
  }
  
  /**
   * Busca os valores de pontos e valor unitário na tabela de cargos
   * @param {string} tipoCargo - Tipo de cargo (FCE, CCE, etc.)
   * @param {number} categoria - Categoria do cargo
   * @param {number} nivel - Nível do cargo
   * @returns {Object|null} - Objeto com valores de pontos e valor unitário, ou null se não encontrado
   */
  function buscarCargoSIORG(tipoCargo, categoria, nivel) {
    console.log(`Buscando valores para cargo: ${tipoCargo} ${categoria} ${nivel}`);
    
    // Verificar se os dados de cargos estão disponíveis
    if (!window.organogramaData || !Array.isArray(window.organogramaData.core_cargosiorg)) {
      console.error('Dados de cargos não disponíveis');
      return null;
    }
    
    // Formatar a string de cargo para busca exata: "FCE 2 13" por exemplo
    const cargoExato = `${tipoCargo} ${categoria} ${nivel}`.trim();
    console.log('Buscando cargo exato:', cargoExato);
    
    // Tentar múltiplas representações do nível (para lidar com "7", "07", etc.)
    const nivelStr = nivel.toString();
    const nivelZeroPadded = nivel < 10 ? `0${nivel}` : nivel.toString();
    
    console.log(`Tentando formatos alternativos para nível: "${nivelStr}" e "${nivelZeroPadded}"`);
    
    // Imprimir os primeiros cargos disponíveis para debug (limitar a 10 para não sobrecarregar o console)
    console.log('Primeiros cargos disponíveis:', window.organogramaData.core_cargosiorg.slice(0, 10).map(c => c.cargo));
    
    // Converter arrays para formatos comparáveis
    const buscaFCEFormatos = [
      `${tipoCargo} ${categoria} ${nivel}`.toUpperCase(),
      `${tipoCargo} ${categoria} ${nivelZeroPadded}`.toUpperCase(),
      `${tipoCargo}${categoria}${nivel}`.toUpperCase(),
      `${tipoCargo}${categoria}${nivelZeroPadded}`.toUpperCase(),
      `${tipoCargo} ${categoria}-${nivel}`.toUpperCase(),
      `${tipoCargo} ${categoria}-${nivelZeroPadded}`.toUpperCase()
    ];
    
    console.log('Formatos de busca:', buscaFCEFormatos);
    
    // Buscar o cargo que corresponda a qualquer um dos formatos
    const cargoEncontrado = window.organogramaData.core_cargosiorg.find(c => {
      if (!c.cargo) return false;
      
      const cargoFormatado = c.cargo.trim().toUpperCase();
      
      // Verificar se o cargo corresponde a algum dos formatos de busca
      const correspondencia = buscaFCEFormatos.some(formato => cargoFormatado.includes(formato));
      
      if (correspondencia) {
        console.log('Correspondência encontrada:', c);
        return true;
      }
      
      return false;
    });
    
    if (cargoEncontrado) {
      console.log('Cargo encontrado:', cargoEncontrado);
      // Converter valor de R$ X.XXX,XX para número
      const valorUnitario = converterMoedaParaNumero(cargoEncontrado.valor);
      const pontos = parseFloat(cargoEncontrado.unitario) || 0;
      
      console.log(`Valores extraídos: pontos=${pontos}, valor_unitario=${valorUnitario}`);
      
      return {
        pontos: pontos,
        valor_unitario: valorUnitario
      };
    }
    
    // Busca alternativa - verificar por partes separadas
    console.log('Tentando busca por partes separadas');
    const cargoAlternativo = window.organogramaData.core_cargosiorg.find(c => {
      if (!c.cargo) return false;
      
      const cargoStr = c.cargo.trim().toUpperCase();
      const partes = cargoStr.split(/[\s\-_]+/); // Separar por espaço, hífen ou underscore
      
      if (partes.length < 3) return false;
      
      const tipoCorresponde = partes[0] === tipoCargo.toUpperCase();
      const categoriaCorresponde = partes[1] === categoria.toString();
      
      // Para o nível, precisamos verificar se é exatamente o que buscamos
      // ou se está em formato diferente (com zero à esquerda ou não)
      let nivelCorresponde = false;
      const terceiroElemento = partes[2];
      
      // Buscar por nível exato ou com zero à esquerda
      if (terceiroElemento === nivelStr || terceiroElemento === nivelZeroPadded) {
        nivelCorresponde = true;
      } 
      // Se o terceiro elemento tem mais caracteres, verificar se começa com o nível
      else if (terceiroElemento.startsWith(nivelStr) || terceiroElemento.startsWith(nivelZeroPadded)) {
        // Verificar se o restante é apenas caracteres não numéricos
        const restante = terceiroElemento.substring(nivelStr.length);
        if (!/^\d+/.test(restante)) {
          nivelCorresponde = true;
        }
      }
      
      const resultado = tipoCorresponde && categoriaCorresponde && nivelCorresponde;
      
      if (resultado) {
        console.log('Correspondência por partes encontrada:', c);
      }
      
      return resultado;
    });
    
    if (cargoAlternativo) {
      console.log('Cargo encontrado (formato alternativo):', cargoAlternativo);
      // Converter valor de R$ X.XXX,XX para número
      const valorUnitario = converterMoedaParaNumero(cargoAlternativo.valor);
      const pontos = parseFloat(cargoAlternativo.unitario) || 0;
      
      console.log(`Valores extraídos (alt): pontos=${pontos}, valor_unitario=${valorUnitario}`);
      
      return {
        pontos: pontos,
        valor_unitario: valorUnitario
      };
    }
    
    // Busca mais genérica apenas por tipo e categoria
    console.log('Tentando busca mais genérica por tipo e categoria');
    const cargoGenerico = window.organogramaData.core_cargosiorg
      .filter(c => c.cargo && c.cargo.trim().toUpperCase().startsWith(`${tipoCargo} ${categoria}`.toUpperCase()))
      .sort((a, b) => {
        // Ordenar para encontrar o mais próximo do nível desejado
        const nivelA = extrairNivel(a.cargo, nivel);
        const nivelB = extrairNivel(b.cargo, nivel);
        
        // Calcular diferença absoluta ao nível desejado
        const difA = Math.abs(nivelA - nivel);
        const difB = Math.abs(nivelB - nivel);
        
        return difA - difB; // Menor diferença primeiro
      });
    
    if (cargoGenerico.length > 0) {
      const melhorCorrespondencia = cargoGenerico[0];
      console.log('Melhor correspondência de cargo genérico:', melhorCorrespondencia);
      
      // Converter valor de R$ X.XXX,XX para número
      const valorUnitario = converterMoedaParaNumero(melhorCorrespondencia.valor);
      const pontos = parseFloat(melhorCorrespondencia.unitario) || 0;
      
      console.log(`Valores extraídos (genérico): pontos=${pontos}, valor_unitario=${valorUnitario}`);
      
      return {
        pontos: pontos,
        valor_unitario: valorUnitario
      };
    }
    
    // Nenhuma correspondência encontrada
    console.warn(`ATENÇÃO: Nenhum cargo encontrado para: ${tipoCargo} ${categoria} ${nivel}`);
    return null;
  }
  
  /**
   * Extrai o nível numérico de uma string de cargo
   * @param {string} cargoStr - String do cargo
   * @param {number} defaultNivel - Nível padrão se não encontrar
   * @returns {number} - Nível extraído ou padrão
   */
  function extrairNivel(cargoStr, defaultNivel) {
    if (!cargoStr) return defaultNivel;
    
    const partes = cargoStr.trim().split(/[\s\-_]+/);
    if (partes.length < 3) return defaultNivel;
    
    // Extrair terceira parte e tentar converter para número
    const terceiroElemento = partes[2];
    const match = terceiroElemento.match(/^(\d+)/);
    
    if (match && match[1]) {
      return parseInt(match[1]);
    }
    
    return defaultNivel;
  }
  
  /**
   * Atualiza o relatório de diferenças
   */
  function updateDiffReport() {
    const diffContainer = document.getElementById('diffReport');
    diffContainer.innerHTML = '';
    
    if (originalData.length === 0 || editedData.length === 0) {
      diffContainer.innerHTML = '<div class="text-center">Nenhum dado disponível para comparar</div>';
      return;
    }
    
    let hasDiff = false;
    
    // Criar tabela para exibir todas as mudanças
    const diffTable = document.createElement('table');
    diffTable.className = 'table table-sm table-striped table-hover';
    diffTable.innerHTML = `
      <thead>
        <tr>
          <th>Cargo</th>
          <th>Categoria (Original)</th>
          <th>Categoria (Editada)</th>
          <th>Nível (Original)</th>
          <th>Nível (Editado)</th>
          <th>Quantidade (Original)</th>
          <th>Quantidade (Editada)</th>
          <th>Pontos (Original)</th>
          <th>Pontos (Editado)</th>
          <th>Valor (Original)</th>
          <th>Valor (Editado)</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;
    
    const diffTableBody = diffTable.querySelector('tbody');
    
    // Para cada item, verificar se houve alterações
    originalData.forEach((original, index) => {
      if (index < editedData.length) {
        const edited = editedData[index];
        
        // Calcular os valores totais (originais e editados)
        const pontosTotaisOriginal = parseFloat(original.pontos || 0) * parseInt(original.quantidade || 1);
        const valorTotalOriginal = parseFloat(original.valor_unitario || 0) * parseInt(original.quantidade || 1);
        
        const pontosTotaisEditado = parseFloat(edited.pontos || 0) * parseInt(edited.quantidade || 1);
        const valorTotalEditado = parseFloat(edited.valor_unitario || 0) * parseInt(edited.quantidade || 1);
        
        // Verificar se houve alguma alteração
        const categoriaChanged = original.categoria !== edited.categoria;
        const nivelChanged = original.nivel !== edited.nivel;
        const quantidadeChanged = original.quantidade !== edited.quantidade;
        const pontosChanged = pontosTotaisOriginal !== pontosTotaisEditado;
        const valorChanged = valorTotalOriginal !== valorTotalEditado;
        
        if (categoriaChanged || nivelChanged || quantidadeChanged || pontosChanged || valorChanged) {
          hasDiff = true;
          
          // Criar linha na tabela
          const row = document.createElement('tr');
          
          row.innerHTML = `
            <td>${formatValue(original.denominacao)}</td>
            <td>${formatValue(original.categoria)}</td>
            <td class="${categoriaChanged ? 'diff-changed' : ''}">${formatValue(edited.categoria)}</td>
            <td>${formatValue(original.nivel)}</td>
            <td class="${nivelChanged ? 'diff-changed' : ''}">${formatValue(edited.nivel)}</td>
            <td>${formatValue(original.quantidade)}</td>
            <td class="${quantidadeChanged ? 'diff-changed' : ''}">${formatValue(edited.quantidade)}</td>
            <td>${formatValue(pontosTotaisOriginal)}</td>
            <td class="${pontosChanged ? 'diff-changed' : ''}">${formatValue(pontosTotaisEditado)}</td>
            <td>${formatValue(valorTotalOriginal)}</td>
            <td class="${valorChanged ? 'diff-changed' : ''}">${formatValue(valorTotalEditado)}</td>
          `;
          
          diffTableBody.appendChild(row);
        }
      }
    });
    
    if (hasDiff) {
      diffContainer.appendChild(diffTable);
    } else {
      diffContainer.innerHTML = '<div class="text-center">Não há diferenças para exibir</div>';
    }
  }
  
  /**
   * Formata um valor numérico com duas casas decimais
   * @param {number} value - O valor a ser formatado
   * @returns {string} - Valor formatado com duas casas decimais
   */
  function formatarPontos(value) {
    // Verificar se é um número válido
    if (isNaN(value) || value === null || value === undefined) {
      return '0.00';
    }
    
    // Formatar com 2 casas decimais e garantir que é um número
    return parseFloat(value).toFixed(2);
  }

  /**
   * Atualiza o Total Geral com os pontos
   */
  function updateTotalGeral(totalDiv, nomeSecretaria, totalPontosGeral, totalPontosOriginais) {
    // Limpar conteúdo anterior
    totalDiv.innerHTML = '';
    
    // Adicionar nome da secretaria
    if (nomeSecretaria) {
      const secretariaLabel = document.createElement('div');
      secretariaLabel.textContent = nomeSecretaria;
      totalDiv.appendChild(secretariaLabel);
    }
    
    // Centralizar os pontos sem o label "Total Geral:"
    const totalValue = document.createElement('div');
    totalValue.textContent = `${formatarPontos(totalPontosGeral)}/${formatarPontos(totalPontosOriginais)} pontos`;
    totalDiv.appendChild(totalValue);
    
    // Adicionar diferença total como terceiro elemento
    const diferencaTotal = totalPontosGeral - totalPontosOriginais;
    if (diferencaTotal !== 0) {
      const diferencaDiv = document.createElement('div');
      
      if (diferencaTotal < 0) {
        diferencaDiv.className = 'economy-message';
        diferencaDiv.innerHTML = `<i class="fas fa-check-circle"></i> Economia total: ${formatarPontos(Math.abs(diferencaTotal))} pontos`;
        diferencaDiv.style.color = '#28a745';
      } else {
        diferencaDiv.className = 'excess-message';
        diferencaDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> Excesso total: ${formatarPontos(diferencaTotal)} pontos`;
        diferencaDiv.style.color = '#dc3545';
      }
      
      totalDiv.appendChild(diferencaDiv);
    }
  }

  /**
   * Atualiza o relatório de pontos
   */
  function updatePointsReport() {
    console.log("Atualizando relatório de pontos...");
    
    const pointsContainer = document.getElementById('pointsReport');
    if (!pointsContainer) {
      console.error("Elemento pointsReport não encontrado!");
      return;
    }
    
    // Remover todo o conteúdo existente exceto botão de atualização
    const refreshBtn = document.getElementById('refreshPointsReport');
    pointsContainer.innerHTML = '';
    
    // Readicionar botão se existia
    if (refreshBtn) {
      pointsContainer.appendChild(refreshBtn);
    }
    
    // Criando o card do relatório mesmo sem dados
    const reportCard = document.createElement('div');
    reportCard.className = 'points-report-card';
    
    // Título do relatório com ícone
    const titleDiv = document.createElement('div');
    titleDiv.className = 'points-report-title';
    titleDiv.innerHTML = '<i class="fas fa-chart-pie"></i> Relatório de Pontos';
    reportCard.appendChild(titleDiv);
    
    // Verificar se há dados para exibir
    if (!originalData || !editedData || originalData.length === 0 || editedData.length === 0) {
      // Total Geral vazio
      const totalDiv = document.createElement('div');
      totalDiv.className = 'report-total';
      updateTotalGeral(totalDiv, '', 0, 0);
      reportCard.appendChild(totalDiv);
      pointsContainer.appendChild(reportCard);
      return;
    }
    
    console.log(`Dados originais: ${originalData.length} itens, Dados editados: ${editedData.length} itens`);
    
    try {
      // Agrupar itens por área
      const areaGroups = {};
      originalData.forEach(item => {
        if (!item.sigla) return;
        
        const area = item.sigla.trim();
        // Criar uma chave única que inclui área, tipo_cargo e denominação
        const chaveUnica = `${area}|${item.tipo_cargo}|${item.denominacao}`;
        
        if (!areaGroups[chaveUnica]) {
          areaGroups[chaveUnica] = {
            sigla: area,
            nome: item.denominacao_unidade || getDenominacaoFromTable(area) || area,
            tipo_cargo: item.tipo_cargo,
            denominacao: item.denominacao,
            itensOriginais: [],
            itensEditados: []
          };
        }
        areaGroups[chaveUnica].itensOriginais.push(item);
      });
      
      // Adicionar itens editados aos grupos
      editedData.forEach(item => {
        if (!item.sigla) return;
        
        const area = item.sigla.trim();
        // Criar uma chave única que inclui área, tipo_cargo e denominação
        const chaveUnica = `${area}|${item.tipo_cargo}|${item.denominacao}`;
        
        // Criar um novo grupo se a combinação não existir
        if (!areaGroups[chaveUnica]) {
          areaGroups[chaveUnica] = {
            sigla: area,
            nome: item.denominacao_unidade || getDenominacaoFromTable(area) || area,
            tipo_cargo: item.tipo_cargo,
            denominacao: item.denominacao,
            itensOriginais: [],
            itensEditados: []
          };
        }
        areaGroups[chaveUnica].itensEditados.push(item);
      });
      
      // Obter áreas/secretarias únicas, removendo valores vazios
      const areas = Object.keys(areaGroups).filter(chaveUnica => {
        const area = chaveUnica.split('|')[0];
        return area && area.trim() !== '';
      });
      
      console.log(`Chaves únicas encontradas: ${areas.join(', ')}`);
      
      if (areas.length === 0) {
        // Total Geral vazio
        const totalDiv = document.createElement('div');
        totalDiv.className = 'report-total';
        updateTotalGeral(totalDiv, '', 0, 0);
        reportCard.appendChild(totalDiv);
        pointsContainer.appendChild(reportCard);
        return;
      }
      
      // Variáveis para o total geral
      let totalPontosGeral = 0;
      let totalPontosOriginais = 0;
      let nomeUnidade = '';
      
      // Tentar obter a sigla e nome da unidade principal
      let siglaUnidade = '';
      if (unitSelect && unitSelect.value) {
        if (typeof $ !== 'undefined' && $.fn.select2) {
          const selectedText = $(unitSelect).select2('data')[0].text;
          const partes = selectedText.split(' - ');
          siglaUnidade = partes[0];
          if (partes.length > 1) {
            nomeUnidade = partes[1];
          }
        } else {
          const selectedOption = unitSelect.options[unitSelect.selectedIndex];
          const partes = selectedOption.textContent.split(' - ');
          siglaUnidade = partes[0];
          if (partes.length > 1) {
            nomeUnidade = partes[1];
          }
        }
      }
      
      // Criar grid para exibir áreas em layout adaptável
      const areasGrid = document.createElement('div');
      areasGrid.className = 'areas-grid';
      
      // Adicionar classe específica se houver muitas áreas (para melhor espaçamento)
      if (areas.length > 8) {
        areasGrid.classList.add('many-areas');
      }
      
      reportCard.appendChild(areasGrid);
      
      // Variável para controlar quantas áreas foram adicionadas
      let areasAdded = 0;
      
      areas.forEach(chaveUnica => {
        try {
          const areaData = areaGroups[chaveUnica];
          const area = chaveUnica.split('|')[0];
          
          // Calcular pontos totais para cada grupo
          const pontosOriginais = calcularPontosArea(areaData.itensOriginais);
          const pontosEditados = calcularPontosArea(areaData.itensEditados);
          
          console.log(`Grupo: ${chaveUnica}, Pontos originais: ${pontosOriginais}, Pontos editados: ${pontosEditados}`);
          
          totalPontosGeral += pontosEditados;
          totalPontosOriginais += pontosOriginais;
          
          // Obter a denominação para exibição
          let denominacaoArea = `${areaData.denominacao || ''} - ${area}`;
          if (areaData.tipo_cargo) {
            denominacaoArea = `${areaData.tipo_cargo} - ${areaData.denominacao || ''} - ${area}`;
          }
          
          // Criar item da área
          const areaDiv = document.createElement('div');
          areaDiv.className = 'area-container';
          
          // Nome da área e pontos em uma linha
          const areaHeader = document.createElement('div');
          areaHeader.className = 'area-item';
          
          const areaName = document.createElement('div');
          areaName.className = 'area-name';
          areaName.textContent = denominacaoArea;
          areaName.title = denominacaoArea;
          
          const areaPoints = document.createElement('div');
          areaPoints.className = 'area-points';
          // Mostrar pontos editados/pontos originais (x/y) com 2 casas decimais
          areaPoints.textContent = `${formatarPontos(pontosEditados)}/${formatarPontos(pontosOriginais)} pts`;
          
          areaHeader.appendChild(areaName);
          areaHeader.appendChild(areaPoints);
          areaDiv.appendChild(areaHeader);
          
          // Barra de progresso
          const progressContainer = document.createElement('div');
          progressContainer.className = 'progress-bar-container';
          
          const progressBar = document.createElement('div');
          progressBar.className = 'progress-bar';
          
          // A largura da barra representa a proporção em relação ao valor original
          const proporcao = pontosOriginais > 0 ? (pontosEditados / pontosOriginais) * 100 : 0;
          progressBar.style.width = `${Math.min(100, proporcao)}%`;
          
          // Determinar cor da barra com base na diferença
          const diferenca = pontosEditados - pontosOriginais;
          if (diferenca > 0) {
            progressBar.style.backgroundColor = '#dc3545'; // Vermelho para aumento
          } else if (diferenca < 0) {
            progressBar.style.backgroundColor = '#28a745'; // Verde para redução
          } else {
            progressBar.style.backgroundColor = '#4a90e2'; // Azul se não houver alteração
          }
          
          progressContainer.appendChild(progressBar);
          areaDiv.appendChild(progressContainer);
          
          // Mensagem de economia ou excesso sempre mostrada abaixo da barra
          if (diferenca !== 0) {
            const messageDiv = document.createElement('div');
            
            if (diferenca < 0) {
              messageDiv.className = 'economy-message';
              messageDiv.innerHTML = `<i class="fas fa-check-circle"></i> Economia: ${formatarPontos(Math.abs(diferenca))} pontos`;
              messageDiv.style.color = '#28a745'; // Verde para economia
            } else {
              messageDiv.className = 'excess-message';
              messageDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> Excesso: ${formatarPontos(diferenca)} pontos`;
              messageDiv.style.color = '#dc3545'; // Vermelho para excesso
            }
            
            areaDiv.appendChild(messageDiv);
          }
          
          // Adicionar área ao grid
          areasGrid.appendChild(areaDiv);
          areasAdded++;
        } catch (areaError) {
          console.error(`Erro ao processar área ${area}:`, areaError);
        }
      });
      
      // Divisor - criar um divisor maior quando há mais áreas
      const divider = document.createElement('div');
      divider.className = areasAdded > 8 ? 'report-divider big-divider' : 'report-divider';
      reportCard.appendChild(divider);
      
      // Total Geral centralizado
      const totalDiv = document.createElement('div');
      
      // Adicionar classe especial quando há muitas áreas para dar mais espaço
      totalDiv.className = areasAdded > 8 ? 'report-total more-spacing' : 'report-total';
      
      // Usar a função updateTotalGeral para preencher o conteúdo
      updateTotalGeral(totalDiv, nomeUnidade || siglaUnidade, totalPontosGeral, totalPontosOriginais);
      
      reportCard.appendChild(totalDiv);
      
      // Adicionar o card ao container
      pointsContainer.appendChild(reportCard);
      
      console.log("Relatório de pontos atualizado com sucesso!");
    } catch (error) {
      console.error("Erro ao atualizar relatório de pontos:", error);
      
      // Mostrar mensagem de erro e incluir detalhes para ajudar no diagnóstico
      const errorMsg = document.createElement('div');
      errorMsg.className = 'alert alert-danger mt-3';
      errorMsg.innerHTML = `<strong>Erro ao gerar relatório:</strong> ${error.message}<br>
                            <small>Detalhes: ${error.stack || 'Sem stack trace disponível'}</small>`;
      pointsContainer.appendChild(errorMsg);
      
      // Adicionar botão para tentar novamente
      const retryBtn = document.createElement('button');
      retryBtn.className = 'btn btn-sm btn-outline-danger mt-2';
      retryBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Tentar novamente';
      retryBtn.addEventListener('click', updatePointsReport);
      pointsContainer.appendChild(retryBtn);
    }
  }
  
  /**
   * Obtém a denominação de uma área a partir da tabela
   * @param {string} sigla - Sigla da área a ser pesquisada
   * @returns {string} - Denominação completa da área
   */
  function getDenominacaoFromTable(sigla) {
    // Primeiro, tentar encontrar nos dados originais
    for (const item of originalData) {
      if (item.sigla === sigla) {
        // Retornar a denominação + sigla
        if (item.denominacao) {
          return `${item.denominacao} - ${sigla}`;
        }
      }
    }
    
    // Se não encontrar, verificar no organogramaData
    if (window.organogramaData) {
      if (Array.isArray(window.organogramaData.core_unidade)) {
        const unidade = window.organogramaData.core_unidade.find(u => u.sigla === sigla);
        if (unidade && unidade.denominacao) {
          return `${unidade.denominacao} - ${sigla}`;
        }
      }
    }
    
    // Fallback: retornar apenas a sigla
    return sigla;
  }

  // Modificar a função filterTableRows para melhorar o comportamento da paginação
  function filterTableRows(searchTerm) {
    // Desativar temporariamente a chamada da renderPage para evitar chamadas duplicadas
    const isFilteredBefore = isFiltered;
    
    // Filtrar os dados originais
    filteredOriginalData = originalData.filter(item => {
      return JSON.stringify(item).toLowerCase().includes(searchTerm);
    });
    
    // Filtrar os dados editados
    filteredEditedData = editedData.filter(item => {
      return JSON.stringify(item).toLowerCase().includes(searchTerm);
    });
    
    // Ativar flag de filtro
    isFiltered = true;
    
    // Resetar para a primeira página
    if (!isFilteredBefore || currentPage > 1) {
      currentPage = 1;
    }
    
    // Renderizar a página com os dados filtrados
    renderPage();
    
    // Se não houver resultados, mostrar mensagem
    if (filteredOriginalData.length === 0) {
      const tbody1 = currentTable.querySelector('tbody');
      tbody1.innerHTML = `<tr><td colspan="8" class="text-center">Nenhum resultado encontrado para "${searchTerm}"</td></tr>`;
    }
    
    if (filteredEditedData.length === 0) {
      const tbody2 = editableTable.querySelector('tbody');
      tbody2.innerHTML = `<tr><td colspan="8" class="text-center">Nenhum resultado encontrado para "${searchTerm}"</td></tr>`;
    }
    
    // Atualizar o relatório de pontos
    setTimeout(updatePointsReport, 100);
  }
  
  // Modificar a função showAllRows para melhorar o comportamento da paginação
  function showAllRows() {
    // Verificar se já estava filtrado
    const wasFiltered = isFiltered;
    
    // Desativar filtro
    isFiltered = false;
    
    // Resetar para a primeira página se estava filtrado
    if (wasFiltered) {
      currentPage = 1;
    }
    
    // Renderizar novamente sem filtro
    renderPage();
    
    // Atualizar o relatório de pontos
    setTimeout(updatePointsReport, 100);
  }
  
  // Calcula a soma de pontos para uma área específica
  function calcularPontosArea(itens) {
    if (!itens || !Array.isArray(itens) || itens.length === 0) {
      console.log('Nenhum item para calcular pontos');
      return 0;
    }
    
    console.log(`Calculando pontos para ${itens.length} itens`);
    
    return itens.reduce((total, item) => {
      // Garantir que pontos e quantidade sejam números válidos
      const pontos = parseFloat(item.pontos || 0);
      const quantidade = parseInt(item.quantidade || 1);
      
      if (isNaN(pontos) || isNaN(quantidade)) {
        console.warn('Valores inválidos em item:', item);
        return total;
      }
      
      const subtotal = pontos * quantidade;
      console.log(`Item: ${item.denominacao}, Pontos: ${pontos}, Quantidade: ${quantidade}, Subtotal: ${subtotal}`);
      
      return total + subtotal;
    }, 0);
  }
  
  /**
   * Limpa o relatório de diferenças
   */
  function clearDiffReport() {
    const diffContainer = document.getElementById('diffReport');
    if (diffContainer) {
      diffContainer.innerHTML = ''; // Removida a mensagem de seleção
    }
    
    // Limpar também o relatório de pontos, mas mostrar o Total Geral vazio
    const pointsContainer = document.getElementById('pointsReport');
    if (pointsContainer) {
      pointsContainer.innerHTML = '';
      
      // Criar o card mesmo sem dados
      const reportCard = document.createElement('div');
      reportCard.className = 'points-report-card';
      
      // Título do relatório com ícone
      const titleDiv = document.createElement('div');
      titleDiv.className = 'points-report-title';
      titleDiv.innerHTML = '<i class="fas fa-chart-pie"></i> Relatório de Pontos';
      reportCard.appendChild(titleDiv);
      
      // Criar um Total Geral vazio centralizado
      const totalDiv = document.createElement('div');
      totalDiv.className = 'report-total';
      
      const totalValue = document.createElement('div');
      totalValue.textContent = '0.00/0.00 pontos';
      totalDiv.appendChild(totalValue);
      
      reportCard.appendChild(totalDiv);
      pointsContainer.appendChild(reportCard);
    }
  }
  
  /**
   * Exporta os dados para CSV
   */
  function exportToCSV() {
    const exportType = exportTypeSelect.value;
    if ((exportType === 'nova' && editedData.length === 0) || 
        (exportType !== 'nova' && originalData.length === 0)) {
      alert('Não há dados para exportar');
      return;
    }
    let headers = [];
    let dataRows = [];

    if (exportType === 'comparacao') {
      headers = ['Área','Tipo Cargo (Orig)','Tipo Cargo (Novo)','Denominação','Cat. (Orig)','Cat. (Novo)','Nvl. (Orig)','Nvl. (Novo)','Qtd. (Orig)','Qtd. (Novo)','Pts. (Orig)','Pts. (Novo)'];
      dataRows = originalData.map((orig, idx) => {
        const edit = editedData[idx] || {};
        return [
          orig.sigla,
          orig.tipo_cargo,
          edit.tipo_cargo || '',
          orig.denominacao,
          orig.categoria,
          edit.categoria || '',
          orig.nivel,
          edit.nivel || '',
          orig.quantidade,
          edit.quantidade || '',
          parseFloat(orig.pontos) * parseInt(orig.quantidade || 1),
          parseFloat(edit.pontos || 0) * parseInt(edit.quantidade || 1)
        ];
      });
    } else if (exportType === 'nova') {
      headers = ['Área','Tipo Cargo','Denominação','Cat.','Nvl.','Qtd.','Pts.'];
      dataRows = editedData.map(item => [
        item.sigla,
        item.tipo_cargo,
        item.denominacao,
        item.categoria,
        item.nivel,
        item.quantidade,
        item.pontos * item.quantidade
      ]);
    } else {
      // completa
      headers = ['Área','Tipo Cargo','Denominação','Categoria','Nível','Quantidade','Pontos'];
      dataRows = originalData.map(item => [
        item.sigla,
        item.tipo_cargo,
        item.denominacao,
        item.categoria,
        item.nivel,
        item.quantidade,
        item.pontos * item.quantidade
      ]);

      // Adiciona relatório de diferenças abaixo da tabela
      dataRows.push([]);
      const diffHeaders = ['Denominação','Categoria (Original)','Categoria (Editada)','Nível (Original)','Nível (Editado)','Quantidade (Original)','Quantidade (Editada)','Pontos (Original)','Pontos (Editado)'];
      dataRows.push(diffHeaders);
      originalData.forEach((orig, idx) => {
        const edited = editedData[idx] || {};
        const ptsOrig = orig.pontos * orig.quantidade;
        const ptsEdit = edited.pontos * edited.quantidade;
        if (orig.categoria != edited.categoria || orig.nivel != edited.nivel || orig.quantidade != edited.quantidade || ptsOrig != ptsEdit) {
          dataRows.push([
            orig.denominacao,
            orig.categoria,
            edited.categoria || '',
            orig.nivel,
            edited.nivel || '',
            orig.quantidade,
            edited.quantidade || '',
            ptsOrig,
            ptsEdit
          ]);
        }
      });
    }

    let csvContent = headers.join(',') + '\n';
    dataRows.forEach(row => {
      const line = row.map(val => `"${val}"`).join(',');
      csvContent += line + '\n';
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `export_${exportType}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
  /**
   * Exporta os dados para HTML
   */
  function exportToHTML() {
    const exportType = exportTypeSelect.value;
    if ((exportType === 'nova' && editedData.length === 0) || 
        (exportType !== 'nova' && originalData.length === 0)) {
      alert('Não há dados para exportar');
      return;
    }
    let unidadeName;
    if (typeof $ !== 'undefined' && $.fn.select2) {
      unidadeName = $(unitSelect).find(':selected').text();
    } else {
      unidadeName = unitSelect.options[unitSelect.selectedIndex].text;
    }
    // Título conforme tipo
    let title;
    if (exportType === 'comparacao') {
      title = 'Comparativo de Organograma';
    } else if (exportType === 'nova') {
      title = 'Estrutura Nova';
    } else {
      title = 'Tabela Completa';
    }
    // Cabeçalho HTML e estilos
    let html = `<!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
  <title>${title} - ${unidadeName}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
    h1 { color: #2c5282; text-align: center; margin-bottom: 10px; }
    h2 { color: #2c5282; text-align: center; margin-bottom: 20px; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th, td { border: 1px solid #dee2e6; padding: 8px; text-align: left; }
          th { background-color: #f8f9fa; }
          tr:nth-child(even) { background-color: #f9f9f9; }
    .report { width: 100%; border: 1px solid #dee2e6; padding: 10px; background: #f8f9fa; }
    .report h3 { margin-top: 0; }
          .diff-changed { color: #fd7e14; }
        </style>
      </head>
      <body>
  <h1>${title}</h1>
  <h2>${unidadeName}</h2>\n`;
    // Gerar conteúdo conforme tipo
    if (exportType === 'comparacao') {
      // Tabela comparativa
      html += '<table><thead><tr>' +
        ['Área','Tipo Cargo (Orig)','Tipo Cargo (Novo)','Denominação','Cat. (Orig)','Cat. (Novo)','Nvl. (Orig)','Nvl. (Novo)','Qtd. (Orig)','Qtd. (Novo)','Pts. (Orig)','Pts. (Novo)']
          .map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>';
      originalData.forEach((orig, idx) => {
        const edit = editedData[idx] || {};
        const ptsOrig = parseFloat(orig.pontos || 0) * parseInt(orig.quantidade || 1);
        const ptsEdit = parseFloat(edit.pontos || 0) * parseInt(edit.quantidade || 1);
        html += '<tr>' +
          `<td>${formatValue(orig.sigla)}</td>` +
          `<td>${formatValue(orig.tipo_cargo)}</td>` +
          `<td>${formatValue(edit.tipo_cargo)}</td>` +
          `<td>${formatValue(orig.denominacao)}</td>` +
          `<td>${formatValue(orig.categoria)}</td>` +
          `<td>${formatValue(edit.categoria)}</td>` +
          `<td>${formatValue(orig.nivel)}</td>` +
          `<td>${formatValue(edit.nivel)}</td>` +
          `<td>${formatValue(orig.quantidade)}</td>` +
          `<td>${formatValue(edit.quantidade)}</td>` +
          `<td>${formatValue(ptsOrig)}</td>` +
          `<td>${formatValue(ptsEdit)}</td>` +
        '</tr>';
      });
      html += '</tbody></table>';
      // Relatório de diferenças
      html += '<div class="report"><h3>Relatório de Diferenças</h3>' + document.getElementById('diffReport').innerHTML + '</div>';
    } else if (exportType === 'nova') {
      // Tabela nova estrutura
      html += '<table><thead><tr>' +
        ['Denominação','Tipo Cargo','Categoria','Nível','Quantidade','Pontos']
        .map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>';
      editedData.forEach(item => {
        html += '<tr>' +
          `<td>${formatValue(item.denominacao)}</td>` +
          `<td>${formatValue(item.tipo_cargo)}</td>` +
          `<td>${formatValue(item.categoria)}</td>` +
          `<td>${formatValue(item.nivel)}</td>` +
          `<td>${formatValue(item.quantidade)}</td>` +
          `<td>${formatValue(item.pontos * item.quantidade)}</td>` +
        '</tr>';
      });
      html += '</tbody></table>';
    } else {
      // Tabela completa
      html += '<table><thead><tr>' +
        ['Denominação','Tipo Cargo','Categoria','Nível','Quantidade','Pontos']
        .map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>';
      originalData.forEach(item => {
        html += '<tr>' +
          `<td>${formatValue(item.denominacao)}</td>` +
          `<td>${formatValue(item.tipo_cargo)}</td>` +
          `<td>${formatValue(item.categoria)}</td>` +
          `<td>${formatValue(item.nivel)}</td>` +
          `<td>${formatValue(item.quantidade)}</td>` +
          `<td>${formatValue(item.pontos * item.quantidade)}</td>` +
        '</tr>';
      });
      html += '</tbody></table>';
      // Relatório de diferenças, se houver
      html += '<div class="report"><h3>Relatório de Diferenças</h3>' + document.getElementById('diffReport').innerHTML + '</div>';
    }
    html += '</body></html>';
    const blob = new Blob([html], { type: 'text/html;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `export_${exportType}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
  /**
   * Exporta os dados para Word (docx)
   */
  function exportToWord() {
    const exportType = exportTypeSelect.value;
    if ((exportType === 'nova' && editedData.length === 0) ||
        (exportType !== 'nova' && originalData.length === 0)) {
      alert('Não há dados para exportar');
      return;
    }

    // Nome da unidade
    let unidadeName;
    if (typeof $ !== 'undefined' && $.fn.select2) {
      unidadeName = $(unitSelect).find(':selected').text();
    } else {
      unidadeName = unitSelect.options[unitSelect.selectedIndex].text;
    }

    // Definir título conforme tipo
    let title;
    if (exportType === 'comparacao') {
      title = 'Comparativo de Organograma';
    } else if (exportType === 'nova') {
      title = 'Estrutura Nova';
    } else {
      title = 'Tabela Completa';
    }

    // Construir HTML interno
    let html = `<!DOCTYPE html><html><head><meta charset='UTF-8'><title>${title} - ${unidadeName}</title></head><body>`;
    html += `<h1 style="text-align:center;">${title}</h1>`;
    html += `<h2 style="text-align:center;">${unidadeName}</h2>`;

    const formatValueWord = val => {
      if (val === undefined || val === null) return '';
      if (typeof val === 'number') return Number(val.toFixed ? val.toFixed(2) : val).toString();
      return val.toString();
    };

    if (exportType === 'comparacao') {
      html += '<table border="1" cellpadding="4" cellspacing="0" style="width:100%;border-collapse:collapse;">';
      html += '<thead><tr>' +
        ['Área','Tipo Cargo (Orig)','Tipo Cargo (Novo)','Denominação','Cat. (Orig)','Cat. (Novo)','Nvl. (Orig)','Nvl. (Novo)','Qtd. (Orig)','Qtd. (Novo)','Pts. (Orig)','Pts. (Novo)']
        .map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>';
      originalData.forEach((orig, idx) => {
        const edit = editedData[idx] || {};
        const ptsOrig = parseFloat(orig.pontos || 0) * parseInt(orig.quantidade || 1);
        const ptsEdit = parseFloat(edit.pontos || 0) * parseInt(edit.quantidade || 1);
        html += '<tr>' +
          `<td>${formatValueWord(orig.sigla)}</td>` +
          `<td>${formatValueWord(orig.tipo_cargo)}</td>` +
          `<td>${formatValueWord(edit.tipo_cargo)}</td>` +
          `<td>${formatValueWord(orig.denominacao)}</td>` +
          `<td>${formatValueWord(orig.categoria)}</td>` +
          `<td>${formatValueWord(edit.categoria)}</td>` +
          `<td>${formatValueWord(orig.nivel)}</td>` +
          `<td>${formatValueWord(edit.nivel)}</td>` +
          `<td>${formatValueWord(orig.quantidade)}</td>` +
          `<td>${formatValueWord(edit.quantidade)}</td>` +
          `<td>${formatValueWord(ptsOrig)}</td>` +
          `<td>${formatValueWord(ptsEdit)}</td>` +
        '</tr>';
      });
      html += '</tbody></table>';
    } else if (exportType === 'nova') {
      html += '<table border="1" cellpadding="4" cellspacing="0" style="width:100%;border-collapse:collapse;">';
      html += '<thead><tr>' +
        ['Denominação','Tipo Cargo','Categoria','Nível','Quantidade','Pontos']
        .map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>';
      editedData.forEach(item => {
        html += '<tr>' +
          `<td>${formatValueWord(item.denominacao)}</td>` +
          `<td>${formatValueWord(item.tipo_cargo)}</td>` +
          `<td>${formatValueWord(item.categoria)}</td>` +
          `<td>${formatValueWord(item.nivel)}</td>` +
          `<td>${formatValueWord(item.quantidade)}</td>` +
          `<td>${formatValueWord(item.pontos * item.quantidade)}</td>` +
        '</tr>';
      });
      html += '</tbody></table>';
    } else { // completa
      html += '<table border="1" cellpadding="4" cellspacing="0" style="width:100%;border-collapse:collapse;">';
      html += '<thead><tr>' +
        ['Denominação','Tipo Cargo','Categoria','Nível','Quantidade','Pontos']
        .map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>';
      originalData.forEach(item => {
        html += '<tr>' +
          `<td>${formatValueWord(item.denominacao)}</td>` +
          `<td>${formatValueWord(item.tipo_cargo)}</td>` +
          `<td>${formatValueWord(item.categoria)}</td>` +
          `<td>${formatValueWord(item.nivel)}</td>` +
          `<td>${formatValueWord(item.quantidade)}</td>` +
          `<td>${formatValueWord(item.pontos * item.quantidade)}</td>` +
        '</tr>';
      });
      html += '</tbody></table>';
      // Relatório de diferenças
      html += '<h3>Relatório de Diferenças</h3>' + document.getElementById('diffReport').innerHTML;
    }

    html += '</body></html>';

    const blob = new Blob(['\ufeff', html], { type: 'application/msword;charset=utf-8;' });
    saveAs(blob, `export_${exportType}.doc`);
  }
  
  /**
   * Exporta os dados para PDF
   */
  function exportToPDF() {
    const exportType = exportTypeSelect.value;
    if ((exportType === 'nova' && editedData.length === 0) || 
        (exportType !== 'nova' && originalData.length === 0)) {
      alert('Não há dados para exportar');
      return;
    }
    const type = exportType;
    // Nome da unidade
    let unidadeName;
    if (typeof $ !== 'undefined' && $.fn.select2) {
      unidadeName = $(unitSelect).find(':selected').text();
    } else {
      unidadeName = unitSelect.options[unitSelect.selectedIndex].text;
    }
    // Definir cabeçalhos e linhas conforme tipo
    let headers = [];
    let rows = [];
    if (type === 'comparacao') {
      headers = ['Área','Tipo Cargo Orig','Tipo Cargo Novo','Denominação','Cat. Orig','Cat. Novo','Nvl. Orig','Nvl. Novo','Qtd. Orig','Qtd. Novo','Pts. Orig','Pts. Novo'];
      rows = originalData.map((orig, idx) => {
        const edit = editedData[idx] || {};
        return [orig.sigla, orig.tipo_cargo, edit.tipo_cargo||'', orig.denominacao, orig.categoria, edit.categoria||'', orig.nivel, edit.nivel||'', orig.quantidade, edit.quantidade||'', orig.pontos*orig.quantidade, (edit.pontos||0)*edit.quantidade];
      });
    } else if (type === 'nova') {
      headers = ['Área','Tipo Cargo','Denominação','Cat.','Nvl.','Qtd.','Pts.'];
      rows = editedData.map(item => [
        item.sigla,
        item.tipo_cargo,
        item.denominacao,
        item.categoria,
        item.nivel,
        item.quantidade,
        item.pontos * item.quantidade
      ]);
    } else { // completa
      headers = ['Área','Tipo Cargo','Denominação','Categoria','Nível','Quantidade','Pontos'];
      rows = originalData.map(item => [
        item.sigla,
        item.tipo_cargo,
        item.denominacao,
        item.categoria,
        item.nivel,
        item.quantidade,
        item.pontos * item.quantidade
      ]);

      // Adiciona relatório de diferenças abaixo da tabela
      rows.push([]);
      const diffHeaders = ['Denominação','Categoria (Original)','Categoria (Editada)','Nível (Original)','Nível (Editado)','Quantidade (Original)','Quantidade (Editada)','Pontos (Original)','Pontos (Editado)'];
      rows.push(diffHeaders);
      originalData.forEach((orig, idx) => {
        const edited = editedData[idx] || {};
        const ptsOrig = orig.pontos * orig.quantidade;
        const ptsEdit = edited.pontos * edited.quantidade;
        if (orig.categoria != edited.categoria || orig.nivel != edited.nivel || orig.quantidade != edited.quantidade || ptsOrig != ptsEdit) {
          rows.push([
            orig.denominacao,
            orig.categoria,
            edited.categoria || '',
            orig.nivel,
            edited.nivel || '',
            orig.quantidade,
            edited.quantidade || '',
            ptsOrig,
            ptsEdit
          ]);
        }
      });
    }
    // Montar HTML para PDF
    const tempDiv = document.createElement('div');
    let html = '<h1 style="text-align:center;">Export ' + type + '</h1>';
    html += '<h2 style="text-align:center;">' + unidadeName + '</h2>';
    html += '<table style="width:100%;border-collapse:collapse;">';
    html += '<thead><tr>';
    headers.forEach(h => { html += '<th style="border:1px solid #ddd;padding:8px;background:#f8f9fa;">' + h + '</th>'; });
    html += '</tr></thead><tbody>';
    rows.forEach(r => {
      html += '<tr>';
      r.forEach(c => { html += '<td style="border:1px solid #ddd;padding:8px;">' + c + '</td>'; });
      html += '</tr>';
    });
    html += '</tbody></table>';
    // Relatório de diferenças
    html += '<div class="report"><h3>Relatório de Diferenças</h3>' + document.getElementById('diffReport').innerHTML + '</div>';
    tempDiv.innerHTML = html;
    document.body.appendChild(tempDiv);
    // Opções do PDF
    const options = {
      margin: 1,
      filename: 'export_' + type + '.pdf',
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'cm', format: 'a4', orientation: 'portrait' }
    };
    html2pdf().from(tempDiv).set(options).save().then(() => {
      document.body.removeChild(tempDiv);
    });
  }
  
  /**
   * Exporta os dados para XLSX, baseado no tipo de exportação selecionado
   */
  function exportToXLSX() {
    const exportType = exportTypeSelect.value;
    if ((exportType === 'nova' && editedData.length === 0) || 
        (exportType !== 'nova' && originalData.length === 0)) {
      alert('Não há dados para exportar');
      return;
    }
    let rows = [];
    if (exportType === 'comparacao') {
      // Exportar comparação: lado a lado original x editado
      rows = originalData.map((orig, idx) => {
        const edit = editedData[idx] || {};
        return {
          'Área': orig.sigla,
          'Tipo Cargo (Orig)': orig.tipo_cargo,
          'Tipo Cargo (Novo)': edit.tipo_cargo,
          'Denominação': orig.denominacao,
          'Cat. (Orig)': orig.categoria,
          'Cat. (Novo)': edit.categoria,
          'Nvl. (Orig)': orig.nivel,
          'Nvl. (Novo)': edit.nivel,
          'Qtd. (Orig)': orig.quantidade,
          'Qtd. (Novo)': edit.quantidade,
          'Pts. (Orig)': orig.pontos * orig.quantidade,
          'Pts. (Novo)': edit.pontos * edit.quantidade
        };
      });
    } else if (exportType === 'nova') {
      // Exportar apenas estrutura nova (editada)
      rows = editedData.map(item => ({
        'Área': item.sigla,
        'Tipo Cargo': item.tipo_cargo,
        'Denominação': item.denominacao,
        'Cat.': item.categoria,
        'Nvl.': item.nivel,
        'Qtd.': item.quantidade,
        'Pts.': item.pontos * item.quantidade
      }));
    } else if (exportType === 'completa') {
      // Exportar tabela completa com dados originais do banco
      rows = originalData.map(item => ({
        'Área': item.sigla,
        'Tipo Cargo': item.tipo_cargo,
        'Denominação': item.denominacao,
        'Categoria': item.categoria,
        'Nível': item.nivel,
        'Quantidade': item.quantidade,
        'Pontos': item.pontos * item.quantidade
      }));
      // Criar planilha de relatório de diferenças
      const diffRows = [];
      originalData.forEach((orig, idx) => {
        const edited = editedData[idx] || {};
        const ptsOrig = orig.pontos * orig.quantidade;
        const ptsEdit = edited.pontos * edited.quantidade;
        if (orig.categoria != edited.categoria || orig.nivel != edited.nivel || orig.quantidade != edited.quantidade || ptsOrig != ptsEdit) {
          diffRows.push({
            'Denominação': orig.denominacao,
            'Categoria (Original)': orig.categoria,
            'Categoria (Editada)': edited.categoria || '',
            'Nível (Original)': orig.nivel,
            'Nível (Editado)': edited.nivel || '',
            'Quantidade (Original)': orig.quantidade,
            'Quantidade (Editada)': edited.quantidade || '',
            'Pontos (Original)': ptsOrig,
            'Pontos (Editado)': ptsEdit
          });
        }
      });
    }

    // Gerar worksheet e workbook
    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Export');
    if (exportType === 'completa' && diffRows && diffRows.length) {
      const ws2 = XLSX.utils.json_to_sheet(diffRows);
      XLSX.utils.book_append_sheet(wb, ws2, 'Relatório');
    }

    // Baixar arquivo
    XLSX.writeFile(wb, `export_${exportType}.xlsx`);
  }

  // Função para adicionar uma nova linha na tabela editável
  function addNewCargoRow() {
    // Obter a sigla da unidade atual selecionada
    let siglaUnidade = '';
    if (unitSelect.value) {
      if (typeof $ !== 'undefined' && $.fn.select2) {
        // Se estiver usando Select2, obter o texto selecionado
        const selectedOption = $(unitSelect).find(':selected');
        if (selectedOption.length) {
          // Extrair a sigla da opção selecionada (assumindo que está no formato "SIGLA - Nome")
          const fullText = selectedOption.text();
          const match = fullText.match(/^([A-Za-z0-9]+)/);
          if (match && match[1]) {
            siglaUnidade = match[1];
          }
        }
      } else {
        // Se não estiver usando Select2, usar o texto da opção selecionada
        const selectedOption = unitSelect.options[unitSelect.selectedIndex];
        if (selectedOption) {
          const fullText = selectedOption.text;
          const match = fullText.match(/^([A-Za-z0-9]+)/);
          if (match && match[1]) {
            siglaUnidade = match[1];
          }
        }
      }
    }
    
    const newItem = {
      sigla: siglaUnidade,
      tipo_cargo: 'FCE',
      denominacao: '',
      categoria: 1,
      nivel: 1,
      quantidade: 1,
      pontos: 0,
      valor_unitario: 0
    };
    
    // Adiciona ao array editado e recalcula paginação
    editedData.push(newItem);
    // Atualiza a primeira página para incluir o novo item
    currentPage = Math.ceil(editedData.length / itemsPerPage);
    renderPage();
  }

  // Configura o botão 'Adicionar Cargo'
  function setupAddNewButton() {
    const btn = document.getElementById('addCargoBtn');
    if (btn) {
      btn.addEventListener('click', function() {
        addNewCargoRow();
        setupEditableFields();
        setupDeleteButtons();
      });
    }
  }

  // Configura botões de excluir em cada linha
  function setupDeleteButtons() {
    const deleteBtns = document.querySelectorAll('.delete-cargo');
    deleteBtns.forEach(btn => {
      btn.removeEventListener('click', onDeleteCargo);
      btn.addEventListener('click', onDeleteCargo);
    });
  }

  function onDeleteCargo() {
    const idx = parseInt(this.dataset.index);
    if (!isNaN(idx) && idx > -1) {
      editedData.splice(idx, 1);
      renderPage();
      updateDiffReport();
      updatePointsReport();
    }
  }

  // Inicializa o botão de adicionar e excluir cargos
  setupAddNewButton();

  // Adiciona evento de "input" para todos os campos editáveis
  document.addEventListener('DOMContentLoaded', function() {
    // Forçar atualização do relatório quando o botão de pesquisa for clicado
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
      searchBtn.addEventListener('click', function() {
        // Após carregar dados, atualizar relatório
        setTimeout(function() {
          console.log('Atualizando relatório após busca...');
          updatePointsReport();
        }, 500);
      });
    }
    
    // Adicionar botão para alternar entre os relatórios
    const reportSection = document.querySelector('.report-section');
    if (reportSection) {
      const pointsReport = document.getElementById('pointsReport');
      const diffReport = document.getElementById('diffReport');
      
      if (pointsReport && diffReport) {
        // Criar o container para os botões de alternância
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'report-toggle-container';
        toggleContainer.style.cssText = 'display: flex; gap: 10px; margin-bottom: 15px;';
        
        // Botão para o relatório de pontos
        const pointsBtn = document.createElement('button');
        pointsBtn.innerHTML = '<i class="fas fa-chart-pie me-1"></i> Relatório de Pontos';
        pointsBtn.className = 'btn btn-sm btn-primary active';
        pointsBtn.id = 'togglePointsReport';
        
        // Botão para o relatório de diferenças
        const diffBtn = document.createElement('button');
        diffBtn.innerHTML = '<i class="fas fa-exchange-alt me-1"></i> Relatório de Diferenças';
        diffBtn.className = 'btn btn-sm btn-outline-secondary';
        diffBtn.id = 'toggleDiffReport';
        
        toggleContainer.appendChild(pointsBtn);
        toggleContainer.appendChild(diffBtn);
        
        // Adicionar antes do primeiro relatório
        reportSection.insertBefore(toggleContainer, reportSection.firstChild);
        
        // Estado inicial: mostrar relatório de pontos, esconder relatório de diferenças
        diffReport.style.display = 'none';
        
        // Evento para o botão de relatório de pontos
        pointsBtn.addEventListener('click', function() {
          // Ativar botão de pontos, desativar botão de diferenças
          pointsBtn.className = 'btn btn-sm btn-primary active';
          diffBtn.className = 'btn btn-sm btn-outline-secondary';
          
          // Mostrar relatório de pontos, esconder relatório de diferenças
          pointsReport.style.display = 'block';
          diffReport.style.display = 'none';
        });
        
        // Evento para o botão de relatório de diferenças
        diffBtn.addEventListener('click', function() {
          // Ativar botão de diferenças, desativar botão de pontos
          diffBtn.className = 'btn btn-sm btn-primary active';
          pointsBtn.className = 'btn btn-sm btn-outline-secondary';
          
          // Mostrar relatório de diferenças, esconder relatório de pontos
          diffReport.style.display = 'block';
          pointsReport.style.display = 'none';
        });
      }
    }
    
    // Adicionar botão de atualização manual do relatório de pontos
    const pointsContainer = document.getElementById('pointsReport');
    if (pointsContainer) {
      const refreshButton = document.createElement('button');
      refreshButton.id = 'refreshPointsReport';
      refreshButton.className = 'btn btn-sm btn-outline-primary mt-2';
      refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar Relatório';
      refreshButton.style.display = 'block';
      refreshButton.style.margin = '5px auto';
      
      refreshButton.addEventListener('click', function() {
        console.log('Atualizando relatório manualmente...');
        updatePointsReport();
      });
      
      // Inserir antes do texto existente
      if (pointsContainer.firstChild) {
        pointsContainer.insertBefore(refreshButton, pointsContainer.firstChild);
      } else {
        pointsContainer.appendChild(refreshButton);
      }
    }
    
    // Forçar atualização quando qualquer campo editável for alterado
    document.body.addEventListener('change', function(e) {
      const target = e.target;
      
      // Verificar se é um campo editável em editableTable
      if (target.closest('#editableTable') && 
          (target.hasAttribute('data-field') || target.tagName === 'SELECT')) {
        setTimeout(function() {
          console.log('Campo editado, atualizando relatório...');
          updatePointsReport();
        }, 300);
      }
    });

    // Forçar inicialização do relatório após o DOM estar pronto
    setTimeout(function() {
      console.log('Inicializando relatório de pontos...');
      updatePointsReport();
    }, 1000);
  });

  function getTableData(tableId) {
    console.log(`Attempting to get data from table with ID: ${tableId}`);
    const tableElement = document.getElementById(tableId); // Changed from getElementById(tableId) to a more descriptive name
    
    if (!tableElement) {
        console.error(`Table with ID '${tableId}' not found.`);
        return [];
    }
    
    const tbodyElement = tableElement.querySelector('tbody'); // Changed from querySelector('tbody') to a more descriptive name
    if (!tbodyElement) {
        console.warn(`No tbody found in table with ID '${tableId}'. Table HTML:`, tableElement.innerHTML);
        // Fallback: If no tbody, try to get rows directly from table if it's a simple table
        // This might not be robust if headers are not in thead
        const directRows = tableElement.querySelectorAll('tr');
        if (directRows.length > 1) { // Assuming first row might be header
             console.log(`Found ${directRows.length} rows directly in table '${tableId}', attempting to process.`);
             // Process directRows, skipping first if it's likely a header
        } else {
            return [];
        }
    } else {
        console.log(`Found tbody in table '${tableId}'. Processing rows...`);
    }

    const data = [];
    // Use tbodyElement if found, otherwise fallback to tableElement for rows (less ideal)
    const rows = tbodyElement ? tbodyElement.querySelectorAll('tr') : tableElement.querySelectorAll('tr');
    console.log(`Found ${rows.length} rows in table '${tableId}'.`);

    rows.forEach((row, rowIndex) => {
        const cells = row.querySelectorAll('td');
        // console.log(`Row ${rowIndex} in ${tableId}, cells found: ${cells.length}`);
        if (cells.length >= 5) { // Changed from 6 to 5, as Pts. might be calculated, not read
            const rowData = {
                area: cells[0]?.textContent.trim(),
                tipo_cargo: cells[1]?.textContent.trim(),
                denominacao: cells[2]?.textContent.trim(),
                categoria: cells[3]?.textContent.trim(),
                nivel: cells[4]?.textContent.trim(),
                // quantidade: cells[5]?.textContent.trim(), // Assuming Qtd. is the 6th cell
            };
            // console.log(`Row ${rowIndex} data for ${tableId}:`, rowData);
            data.push(rowData);
        } else if (cells.length > 0) {
            // Log rows that don't meet the cell count criteria but are not empty
            // console.warn(`Row ${rowIndex} in ${tableId} has only ${cells.length} cells, expected at least 5. Skipping.`);
        }
    });
    console.log(`Extracted ${data.length} data rows from table '${tableId}'.`);
    return data;
  }

  if (baixarAnexoBtn) {
    baixarAnexoBtn.addEventListener('click', async function() {
      // Use the JavaScript variables originalData and editedData directly
      // These variables should already be populated by your existing logic (e.g., loadUnitData)
      
      // We need to ensure the data format matches what _prepare_data_for_excel expects:
      // list of dicts with keys: 'area', 'denominacao', 'tipo_cargo', 'categoria', 'nivel'
      // The current `originalData` and `editedData` might have slightly different keys (e.g., 'sigla' instead of 'area')
      // or might contain more fields than needed. We should map them.

      const mapDataForExcel = (dataArray) => {
          if (!Array.isArray(dataArray)) {
              console.warn('Data for mapping is not an array:', dataArray);
              return [];
          }
          
          // Debug: verificar primeiro item antes do filtro
          if (dataArray.length > 0) {
              console.log("Primeiro item ANTES do filtro:", dataArray[0]);
          }
          
          return dataArray
              .filter(item => {
                  // Filter out invalid items like headers or empty rows
                  // Check if item has valid data (not a header row)
                  const isHeader = item.denominacao === 'DENOMINAÇÃO CARGO/FUNÇÃO' || 
                                 item.denominacao === 'Denominação' ||
                                 item.area === 'ÁREA' || 
                                 item.area === 'UNIDADE' ||
                                 item.sigla === 'ÁREA' ||
                                 item.tipo_cargo === 'CARGO/FUNÇÃO Nº' ||
                                 (item.area === 'ÁREA' && item.denominacao === 'DENOMINAÇÃO CARGO/FUNÇÃO');
                  
                  // Also filter out items that look like template headers
                  const isTemplateHeader = (typeof item.area === 'string' && item.area.toUpperCase() === 'ÁREA') ||
                                         (typeof item.denominacao === 'string' && item.denominacao.includes('DENOMINAÇÃO'));
                  
                  const hasValidData = item.area || item.sigla || item.tipo_cargo || item.denominacao;
                  const hasNumericData = item.categoria || item.nivel || item.quantidade || item.pontos;
                  
                  return !isHeader && !isTemplateHeader && (hasValidData || hasNumericData);
              })
              .map((item, index) => {
                  const mapped = {
                      area: item.sigla || item.area || item.sigla_unidade || 'N/D', // Prefer sigla, fallback to area
                      tipo_cargo: item.tipo_cargo || '',
                      denominacao: item.denominacao || '',
                      categoria: item.categoria || '',
                      nivel: item.nivel || '',
                      grafo: item.grafo || '', // Include grafo field for hierarchical ordering
                      codigo_unidade: item.codigo_unidade || '', // Include unit code
                      denominacao_unidade: item.denominacao_unidade || '', // Include unit name
                      sigla_unidade: item.sigla_unidade || item.sigla || item.area || '', // Include unit acronym
                      quantidade: item.quantidade || 1, // Include quantity for reference
                      pontos: item.pontos || 0, // Include points for reference
                      valor_unitario: item.valor_unitario || 0 // Include unit value for reference
                  };
                  
                  // Debug: log primeiro item mapeado
                  if (index === 0) {
                      console.log("Primeiro item DEPOIS do mapeamento:", mapped);
                      console.log("Quantidade original:", item.quantidade, "Quantidade mapeada:", mapped.quantidade);
                  }
                  
                  return mapped;
              });
      };

      const estruturaAtualDataForExcel = mapDataForExcel(window.originalDataGlobal || originalData || []);
      const estruturaNovaDataForExcel = mapDataForExcel(window.editedDataGlobal || editedData || []);

      if (!estruturaAtualDataForExcel.length && !estruturaNovaDataForExcel.length) {
          alert('Não há dados nas estruturas para exportar. Carregue ou adicione dados primeiro.');
          return;
      }
      
      console.log("Dados para anexo (Atual):", estruturaAtualDataForExcel);
      console.log("Dados para anexo (Nova):", estruturaNovaDataForExcel);
      
      // Debug: verificar se quantidade está presente
      if (estruturaAtualDataForExcel.length > 0) {
          console.log("Exemplo de item (Atual) com quantidade:", estruturaAtualDataForExcel[0]);
      }
      if (estruturaNovaDataForExcel.length > 0) {
          console.log("Exemplo de item (Nova) com quantidade:", estruturaNovaDataForExcel[0]);
      }

      try {
          const response = await fetch('/api/baixar_anexo_simulacao/', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'X-CSRFToken': getCookie('csrftoken') 
              },
              body: JSON.stringify({
                  estrutura_atual: estruturaAtualDataForExcel,
                  estrutura_nova: estruturaNovaDataForExcel
              })
          });

          if (response.ok) {
              const blob = await response.blob();
              const filenameHeader = response.headers.get('content-disposition');
              let filename = "Anexo_Simulacao.xlsx"; // Default filename
              if (filenameHeader) {
                  const filenameMatch = filenameHeader.match(/filename[^;=\n]*=((['"])(?<filename>.*?)\2|(?<filename_no_quotes>[^;\n]*))/i);
                  if (filenameMatch && filenameMatch.groups && (filenameMatch.groups.filename || filenameMatch.groups.filename_no_quotes)) {
                      filename = filenameMatch.groups.filename || filenameMatch.groups.filename_no_quotes;
                  }
              }
              
              if (window.navigator && window.navigator.msSaveOrOpenBlob) {
                  window.navigator.msSaveOrOpenBlob(blob, filename);
              } else {
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = filename;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  window.URL.revokeObjectURL(url);
              }
          } else {
              const errorData = await response.json();
              alert(`Erro ao baixar anexo: ${errorData.error || response.statusText}`);
          }
      } catch (error) {
          console.error('Erro ao baixar anexo:', error);
          alert('Ocorreu um erro de rede ou inesperado ao tentar baixar o anexo.');
      }
    });
  }
  
  // Ensure getCookie function exists if you use it for CSRF token
  function getCookie(name) {
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
});

// Adicionar estilos para os campos editáveis e destacar valores atualizados
const style = document.createElement('style');
style.textContent = `
  .editable-cell {
    background-color: #fff8e1 !important;
  }
  
  .editable-cell input,
  .editable-cell input[type="text"],
  .editable-cell input[type="number"] {
    width: 100%;
    border: none;
    padding: 2px 4px;
    background-color: #fff8e1 !important;
    border: none !important;
  }
  
  .editable-cell input:focus,
  .editable-cell input[type="text"]:focus,
  .editable-cell input[type="number"]:focus,
  .editable-cell select:focus {
    background-color: #ffffff !important;
    outline: none;
    box-shadow: none;
  }
  
  .updated-value {
    animation: highlight 1.5s ease-out;
  }
  
  @keyframes highlight {
    0% { background-color: #fffacd; }
    100% { background-color: transparent; }
  }
  
  .diff-changed {
    color: #fd7e14;
    font-weight: bold;
  }
`;
document.head.appendChild(style);