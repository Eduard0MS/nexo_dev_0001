// financeira_organograma.js
// Script para integrar dados financeiros com o organograma

// Variáveis globais
let financialData = null;
let orgData = null;
let originalOrgData = null; // Armazena dados originais para filtragem
let orgTree = null;
let svg, g;
let i = 0; // Contador de IDs para nós
const width = 1200;
const height = 800;
let tooltip;
let viewMode = 'orcamento'; // Modo padrão

// Paleta de cores para indicadores financeiros
const colors = {
  node: {
    default: '#f8fafd',
    expanded: '#e9f0f9',
    hover: '#e9f0f9',
    stroke: '#d1d9e6'
  },
  text: '#333333',
  link: '#a4c5f4',
  financial: {
    good: '#4CAF50',
    medium: '#FFC107',
    poor: '#F44336',
    default: '#78909C'
  }
};

// Inicializa a visualização
function initOrganogramaFinanceiro() {
  console.log('Inicializando organograma financeiro...');
  
  // Seleciona o container do organograma
  const container = d3.select('#financialOrgContainer');
  
  // Cria o tooltip
  tooltip = container.append('div')
    .attr('class', 'tooltip')
    .style('opacity', 0);
  
  // Cria o SVG
  svg = container.append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet');
  
  // Cria o grupo principal para os nós e links
  g = svg.append('g')
    .attr('class', 'org-group')
    .attr('transform', `translate(${width / 2}, ${height / 2 - 150})`);
  
  // Configura o comportamento de zoom e pan
  const zoomBehavior = d3.zoom()
    .scaleExtent([0.3, 2])
    .on('zoom', event => {
      g.attr('transform', event.transform);
    });
  
  svg.call(zoomBehavior);
  
  // Define o layout da árvore com D3
  const treeLayout = d3.tree()
    .nodeSize([75, 120])
    .separation((a, b) => (a.parent === b.parent ? 2.0 : 2.5));
  
  // Carrega os dados do organograma
  d3.json('/api/organograma/')
    .then(orgResponse => {
      // Armazenar dados originais para filtragem futura
      originalOrgData = orgResponse;
      
      // Processar os dados para o formato esperado pelo organograma
      const transformData = (data) => {
        console.log("Transformando dados para o organograma financeiro:", data);
        
        // Criamos o nó raiz com as propriedades do organograma completo
        const rootNode = {
          nome: "Ministério do Planejamento e Orçamento - MPO",
          cargo: "Organograma Financeiro",
          secretaria: "MPO",
          codigo: "308804",
          tipo_unidade: "Ministério",
          children: []
        };
        
        // Procurar especificamente o nó MPO
        const mpoNode = data.unidades.find(unit => unit.codigo === "308804");
        
        // Se encontramos a unidade MPO, usar suas propriedades no nó raiz
        if (mpoNode) {
          console.log("Unidade MPO encontrada:", mpoNode);
          rootNode.nome = mpoNode.nome || rootNode.nome;
          rootNode.cargo = mpoNode.tipo_cargo ? `${mpoNode.tipo_cargo} ${mpoNode.nivel || ''}` : rootNode.cargo;
          rootNode.secretaria = mpoNode.sigla_unidade || "MPO";
          rootNode.tipo_unidade = mpoNode.tipo_unidade || rootNode.tipo_unidade;
          rootNode.nivel = mpoNode.nivel;
          rootNode.valor_total = mpoNode.valor_total;
          rootNode.grafo = mpoNode.grafo || "";
        } else {
          console.warn("Unidade MPO não encontrada nos dados financeiros!");
        }
        
        // Verificar se temos unidades para processar
        const unidades = data.unidades || [];
        
        // Se não temos unidades, retornar apenas o nó raiz
        if (!unidades || !Array.isArray(unidades) || unidades.length === 0) {
          console.log("Nenhuma unidade encontrada nos dados financeiros");
          return rootNode;
        }
        
        console.log(`Processando ${unidades.length} unidades para organograma financeiro`);
        
        // Procurar unidades diretamente subordinadas ao MPO
        const unidadesSubordinadas = unidades.filter(unit => {
          if (!unit || !unit.codigo || !unit.grafo) return false;
          
          // Não incluir o próprio MPO nas unidades subordinadas
          if (unit.codigo === "308804") return false;
          
          // Verificar se o grafo contém o código do MPO como pai direto
          const codigosGrafo = unit.grafo.split('-');
          return codigosGrafo.includes("308804") && codigosGrafo[codigosGrafo.length - 2] === "308804";
        });
        
        console.log(`Unidades subordinadas à MPO (financeiro): ${unidadesSubordinadas.length}`);
        
        // Ordenar unidades subordinadas
        unidadesSubordinadas.sort((a, b) => {
          return (a.nivel_hierarquico || 0) - (b.nivel_hierarquico || 0);
        });
        
        // Adicionar unidades subordinadas como filhos do nó raiz
        unidadesSubordinadas.forEach(unit => {
          const childNode = {
            nome: unit.nome || unit.denominacao_unidade || "Unidade sem nome",
            codigo: unit.codigo,
            cargo: unit.tipo_cargo ? `${unit.tipo_cargo} ${unit.nivel || ''}` : "Sem cargo",
            secretaria: unit.sigla_unidade || unit.sigla || "MPO",
            tipo_unidade: unit.tipo_unidade || "",
            nivel: unit.nivel,
            valor_total: unit.valor_total,
            grafo: unit.grafo || "",
            children: []
          };
          
          rootNode.children.push(childNode);
        });
        
        return rootNode;
      };
      
      orgData = transformData(originalOrgData);
      
      // Mesclar com dados financeiros
      mergeFinancialData(orgData, financialData);
      
      // Recriar a hierarquia
      orgTree = d3.hierarchy(orgData);
      
      // Resetar posições
      orgTree.x0 = 0;
      orgTree.y0 = 0;
      
      // Expandir apenas o primeiro nível
      if (orgTree.children) {
        orgTree.children.forEach(child => collapseAtLevel(child, 0));
      }
      
      // Atualizar visualização
      update(orgTree);
      
      // Centralizar
      const initialTransform = d3.zoomIdentity
        .translate(width / 3, height / 3)
        .scale(0.75);
      svg.call(zoomBehavior.transform, initialTransform);
    })
    .then(finResponse => {
      financialData = finResponse;
      
      // Mescla os dados
      mergeFinancialData(orgData, financialData);
      
      // Cria a hierarquia dos dados
      orgTree = d3.hierarchy(orgData);
      
      // Define posições iniciais para transição
      orgTree.x0 = 0;
      orgTree.y0 = 0;
      
      // Colapsa todos os nós exceto o primeiro nível
      if (orgTree.children) {
        orgTree.children.forEach(child => collapseAtLevel(child, 0));
      }
      
      // Renderiza a árvore
      update(orgTree);
      
      // Centraliza inicialmente
      const initialTransform = d3.zoomIdentity
        .translate(width / 3.5, height / 3)
        .scale(0.75);
      svg.call(zoomBehavior.transform, initialTransform);
      
      // Configura os botões
      setupEventListeners();
    })
    .catch(err => {
      console.error('Erro ao carregar dados para o organograma financeiro:', err);
      // Exibe mensagem de erro no container
      container.append('div')
        .attr('class', 'alert alert-danger')
        .html("<i class='fas fa-exclamation-circle me-2'></i>Não foi possível carregar os dados financeiros para o organograma.");
    });

  // Configura listeners de eventos
  setupEventListeners();
}

// Mescla os dados financeiros com os do organograma
function mergeFinancialData(orgNode, financialData) {
  // Associa dados financeiros ao nó raiz se disponível
  if (orgNode.codigo) {
    const unitData = findFinancialDataForUnit(orgNode.codigo, financialData);
    if (unitData) {
      orgNode.financialData = unitData;
    } else {
      // Dados financeiros padrão para unidades sem dados específicos
      orgNode.financialData = {
        orcamento: 0,
        executado: 0,
        percentual: 0,
        status: "Não Disponível"
      };
    }
  }
  
  // Processa recursivamente para filhos
  if (orgNode.children && orgNode.children.length > 0) {
    orgNode.children.forEach(child => {
      mergeFinancialData(child, financialData);
    });
  }
}

// Encontra dados financeiros para uma unidade específica
function findFinancialDataForUnit(unitCode, financialData) {
  if (!financialData || !financialData.unidades) return null;
  
  // Procura nos dados financeiros
  const unitData = financialData.unidades.find(unit => unit.codigo === unitCode);
  return unitData || null;
}

// Função principal de atualização do organograma
function update(source) {
  // Modo de visualização atual (orcamento, executado, percentual)
  const viewMode = d3.select('.control-btn.active').attr('data-mode') || 'orcamento';
  
  // Duração da transição em ms
  const duration = 500;
  
  // Define o layout da árvore
  const treeLayout = d3.tree()
    .nodeSize([75, 120])
    .separation((a, b) => (a.parent === b.parent ? 2.0 : 2.5));
  
  // Aplica o layout da árvore
  treeLayout(orgTree);
  
  // Ajusta espaçamento horizontal com base no número de níveis visíveis
  const visibleDepth = getMaxVisibleDepth(orgTree);
  const horizontalSpacingFactor = visibleDepth > 3 ? 0.7 : (visibleDepth > 2 ? 0.8 : 0.9);
  const verticalSpacingFactor = 0.7; // Espaçamento vertical moderado
  
  // Normaliza para layout horizontal (y = horizontal, x = vertical)
  orgTree.descendants().forEach(d => {
    // Troca x e y para layout horizontal e ajusta proporcionalmente
    const temp = d.x * verticalSpacingFactor;
    d.x = d.y * horizontalSpacingFactor;
    d.y = temp;
  });
  
  // Selecione todos os nós
  const nodes = g.selectAll('g.node')
    .data(orgTree.descendants(), d => d.id || (d.id = ++i));
  
  // ENTRADA: Cria novos nós
  const nodeEnter = nodes.enter()
    .append('g')
    .attr('class', d => `node ${d.children || d._children ? 'node--internal' : 'node--leaf'} ${d._children ? 'collapsed' : ''}`)
    .attr('transform', d => `translate(${source.x0},${source.y0})`)
    .style('opacity', 0)
    .on('click', (event, d) => {
      event.stopPropagation();
      toggleChildren(d);
      update(d);
    })
    .on('mouseover', (event, d) => {
      // Mostra tooltip com dados financeiros
      tooltip.transition()
        .duration(200)
        .style('opacity', 1);
      
      // Obtém a posição do nó no documento
      const nodeElement = event.currentTarget;
      const nodeRect = nodeElement.getBoundingClientRect();
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
      
      // Posicionamento diferente dependendo se é raiz ou não
      let tooltipX, tooltipY;
      
      if (d.depth === 0) {
        // Raiz: mais à esquerda
        tooltipX = nodeRect.left + scrollLeft - 60;
        tooltipY = nodeRect.top + scrollTop - 25;
      } else {
        // Outros nós: mais à direita
        tooltipX = nodeRect.left + scrollLeft - 20;
        tooltipY = nodeRect.top + scrollTop - 25;
      }
      
      // Formata os dados financeiros para o tooltip
      const financialData = d.data.financialData || {};
      const formatterBRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
      
      // Formatar cargo e nível
      let cargoText = d.data.cargo || 'Cargo não especificado';
      
      // Formatar valor monetário, se disponível
      let valorFormatado = '';
      if (d.data.valor_total) {
        valorFormatado = formatterBRL.format(d.data.valor_total);
      }
      
      tooltip.html(`
        <div class="tooltip-title">${d.data.nome}</div>
        <div class="tooltip-cargo">${cargoText}</div>
        <div class="tooltip-field">
          <span class="tooltip-label">Sigla:</span>
          <span class="tooltip-value">${d.data.secretaria || 'Não especificada'}</span>
        </div>
        <div class="tooltip-field">
          <span class="tooltip-label">Tipo:</span>
          <span class="tooltip-value">${d.data.tipo_unidade || 'Não especificado'}</span>
        </div>
        ${d.data.nivel ? 
          `<div class="tooltip-field">
            <span class="tooltip-label">Nível:</span>
            <span class="tooltip-value">${d.data.nivel}</span>
          </div>` : ''
        }
        ${valorFormatado ? 
          `<div class="tooltip-field">
            <span class="tooltip-label">Valor Total:</span>
            <span class="tooltip-value">${valorFormatado}</span>
          </div>` : ''
        }
        ${d.data.codigo ? 
          `<div class="tooltip-field">
            <span class="tooltip-label">Código:</span>
            <span class="tooltip-value">${d.data.codigo}</span>
          </div>` : ''
        }
        <hr>
        <div class="tooltip-field">
          <span class="tooltip-label">Orçamento:</span>
          <span class="tooltip-value">${formatterBRL.format(financialData.orcamento || 0)}</span>
        </div>
        <div class="tooltip-field">
          <span class="tooltip-label">Executado:</span>
          <span class="tooltip-value">${formatterBRL.format(financialData.executado || 0)}</span>
        </div>
        <div class="tooltip-field">
          <span class="tooltip-label">% Execução:</span>
          <span class="tooltip-value">${(financialData.percentual || 0).toFixed(1)}%</span>
        </div>
        <div class="tooltip-field">
          <span class="tooltip-label">Status:</span>
          <span class="tooltip-value">${financialData.status || 'Não disponível'}</span>
        </div>
      `)
        .style('left', tooltipX + 'px')
        .style('top', tooltipY + 'px');
      
      // Destaca o nó
      d3.select(event.currentTarget)
        .select('circle')
        .transition()
        .duration(200)
        .attr('r', 12);
    })
    .on('mouseout', (event, d) => {
      // Esconde tooltip
      tooltip.transition()
        .duration(500)
        .style('opacity', 0);
      
      // Remove destaque
      d3.select(event.currentTarget)
        .select('circle')
        .transition()
        .duration(200)
        .attr('r', 8);
    });
  
  // Adiciona círculos aos novos nós
  nodeEnter.append('circle')
    .attr('r', 0)
    .attr('fill', d => {
      // Estilo especial para o nó raiz (MPO)
      if (d.depth === 0) {
        return '#e9f0f9'; // Uma cor mais destacada para a raiz
      }
      return getNodeColor(d, viewMode);
    })
    .attr('stroke', d => d.depth === 0 ? '#4e73df' : colors.node.stroke) // Borda destacada para a raiz
    .attr('stroke-width', d => d.depth === 0 ? 2.5 : 1.5); // Borda mais grossa para a raiz
  
  // Adiciona o indicador financeiro (anel ao redor do nó)
  nodeEnter.append('circle')
    .attr('class', 'financial-indicator')
    .attr('r', d => d.depth === 0 ? 16 : 12) // Indicador maior para o nó raiz
    .attr('fill', 'none')
    .attr('stroke', d => getFinancialStatusColor(d.data.financialData))
    .attr('stroke-width', d => d.depth === 0 ? 4 : 3) // Stroke mais grosso para raiz
    .attr('stroke-dasharray', d => getFinancialStatusDashArray(d.data.financialData, d.depth === 0 ? 16 : 12)) // Ajusta o dasharray para o raio correto
    .style('opacity', 0);
  
  // Adiciona texto para o nome
  nodeEnter.append('text')
    .attr('class', 'label-nome')
    .attr('dy', -15)
    .attr('x', 0)
    .attr('text-anchor', 'middle')
    .text(d => d.data.nome)
    .style('fill-opacity', 0);
  
  // Adiciona texto para o valor financeiro
  nodeEnter.append('text')
    .attr('class', 'label-financial')
    .attr('dy', 0)
    .attr('x', 0)
    .attr('text-anchor', 'middle')
    .text(d => formatFinancialValue(d.data.financialData, viewMode))
    .style('fill-opacity', 0)
    .style('font-size', '10px')
    .style('fill', '#666');
  
  // Links entre nós (linhas de conexão)
  const links = g.selectAll('path.link')
    .data(orgTree.links(), d => d.target.id);
  
  // Adiciona novos links
  links.enter()
    .append('path')
    .attr('class', 'link')
    .attr('d', d => {
      const o = {x: source.x0, y: source.y0};
      return diagonal(o, o);
    })
    .attr('fill', 'none')
    .attr('stroke', colors.link)
    .attr('stroke-width', 1.5)
    .style('opacity', 0)
  .merge(links)
    .transition()
    .duration(duration)
    .attr('d', diagonal)
    .style('opacity', 1);
  
  // Remove os links antigos
  links.exit()
    .transition()
    .duration(duration)
    .style('opacity', 0)
    .attr('d', d => {
      const o = {x: source.x, y: source.y};
      return diagonal(o, o);
    })
    .remove();
  
  // Atualização: Transição dos nós para suas novas posições
  const nodeUpdate = nodeEnter.merge(nodes);
  
  nodeUpdate.transition()
    .duration(duration)
    .attr('transform', d => `translate(${d.x},${d.y})`)
    .style('opacity', 1);
  
  // Atualiza aparência do nó para refletir se é expandido/colapsado
  nodeUpdate.select('circle')
    .transition()
    .duration(duration)
    .attr('r', d => d.depth === 0 ? 12 : 8) // Raiz maior
    .attr('fill', d => {
      if (d.depth === 0) {
        return '#e9f0f9'; // Cor destacada para a raiz
      }
      return getNodeColor(d, viewMode);
    })
    .attr('stroke', d => d.depth === 0 ? '#4e73df' : colors.node.stroke)
    .attr('stroke-width', d => d.depth === 0 ? 2.5 : 1.5);
  
  // Atualiza o indicador financeiro
  nodeUpdate.select('.financial-indicator')
    .transition()
    .duration(duration)
    .attr('r', d => d.depth === 0 ? 16 : 12)
    .style('opacity', 1)
    .attr('stroke', d => getFinancialStatusColor(d.data.financialData))
    .attr('stroke-width', d => d.depth === 0 ? 4 : 3)
    .attr('stroke-dasharray', d => getFinancialStatusDashArray(d.data.financialData, d.depth === 0 ? 16 : 12));
  
  // Atualiza rótulos
  nodeUpdate.select('.label-nome')
    .transition()
    .duration(duration)
    .style('fill-opacity', 1);
  
  nodeUpdate.select('.label-financial')
    .transition()
    .duration(duration)
    .text(d => formatFinancialValue(d.data.financialData, viewMode))
    .style('fill-opacity', 1);
  
  // Saída: Transição dos nós sendo removidos
  const nodeExit = nodes.exit()
    .transition()
    .duration(duration)
    .attr('transform', d => `translate(${source.x},${source.y})`)
    .style('opacity', 0)
    .remove();
  
  nodeExit.select('circle')
    .attr('r', 0);
  
  nodeExit.select('text')
    .style('fill-opacity', 0);
  
  // Armazena as posições para a próxima transição
  orgTree.descendants().forEach(d => {
    d.x0 = d.x;
    d.y0 = d.y;
  });
}

// Função auxiliar para alternar filhos (expandir/colapsar)
function toggleChildren(d) {
  if (d.children) {
    // Possui filhos visíveis - colapsar
    d._children = d.children
    d.children = null
  } else {
    // Filhos colapsados ou sem filhos carregados ainda
    if (d._children) {
      // Já carregou filhos antes, restaura eles
      d.children = d._children
      d._children = null
    } else {
      // Nunca carregou filhos, tenta carregar do grafo
      expandLoadChildren(d);
    }
  }
}

// Expande todos os nós
function expandAll(d) {
  if (d._children) {
    d.children = d._children;
    d._children = null;
  }
  if (d.children) d.children.forEach(expandAll);
}

// Colapsa todos os nós abaixo de um certo nível
function collapseAtLevel(d, level = 0) {
  if (d.depth > level) {
    if (d.children) {
      d._children = d.children;
      d.children = null;
    }
  }
  if (d.children) d.children.forEach(child => collapseAtLevel(child, level));
}

// Obtém a profundidade máxima visível na árvore
function getMaxVisibleDepth(node) {
  if (!node) return 0;
  if (!node.children) return node.depth;
  
  return Math.max(node.depth, ...node.children.map(getMaxVisibleDepth));
}

// Colapsa todos os nós
function collapseAll(d) {
  if (d.children) {
    d._children = d.children;
    d.children = null;
  }
  if (d._children) d._children.forEach(collapseAll);
}

// Função para calcular o caminho diagonal
function diagonal(source, target) {
  return `M ${source.x} ${source.y}
          C ${source.x} ${(source.y + target.y) / 2},
            ${target.x} ${(source.y + target.y) / 2},
            ${target.x} ${target.y}`;
}

// Obtém a cor do nó com base no modo de visualização
function getNodeColor(d, viewMode) {
  if (!d.data.financialData) return colors.node.default;
  
  const data = d.data.financialData;
  
  if (viewMode === 'orcamento') {
    return colors.node.default;
  }
  else if (viewMode === 'executado') {
    return colors.node.default;
  }
  else if (viewMode === 'percentual') {
    // Cor baseada no percentual de execução
    if (data.percentual >= 80) return '#E8F5E9'; // Verde claro
    if (data.percentual >= 50) return '#FFF8E1'; // Amarelo claro
    return '#FFEBEE'; // Vermelho claro
  }
  
  return colors.node.default;
}

// Formata o valor financeiro dependendo do modo de visualização
function formatFinancialValue(data, viewMode) {
  if (!data) return 'N/A';
  
  const formatterBRL = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    notation: 'compact',
    maximumFractionDigits: 1
  });
  
  if (viewMode === 'orcamento') {
    return formatterBRL.format(data.orcamento || 0);
  }
  else if (viewMode === 'executado') {
    return formatterBRL.format(data.executado || 0);
  }
  else if (viewMode === 'percentual') {
    return `${(data.percentual || 0).toFixed(1)}%`;
  }
  
  return 'N/A';
}

// Obtém a cor para o indicador de status financeiro
function getFinancialStatusColor(data) {
  if (!data) return colors.financial.default;
  
  if (data.status === 'Adequado') return colors.financial.good;
  if (data.status === 'Atenção') return colors.financial.medium;
  if (data.status === 'Crítico') return colors.financial.poor;
  
  return colors.financial.default;
}

// Atualiza a função getFinancialStatusDashArray para aceitar um raio personalizado
function getFinancialStatusDashArray(data, customRadius) {
  if (!data) return '0';
  
  const percentual = data.percentual || 0;
  const radius = customRadius || 12; // Usa o raio customizado ou 12 como padrão
  const circumference = 2 * Math.PI * radius; // 2πr
  const dashLength = (percentual / 100) * circumference;
  
  if (percentual >= 98) return '0'; // Linha sólida para 100%
  return `${dashLength} ${circumference - dashLength}`;
}

// Função de redimensionamento para ajuste responsivo
function resizeOrganogramaFinanceiro() {
  // Ajusta o SVG ao tamanho do container
  const container = document.getElementById('financialOrgContainer');
  if (!container) return;
  
  const containerWidth = container.clientWidth;
  const containerHeight = container.clientHeight || 600;
  
  svg.attr('width', containerWidth)
     .attr('height', containerHeight);
}

// Registra manipulador de redimensionamento
window.addEventListener('resize', resizeOrganogramaFinanceiro);

// Função para expandir um nó e carregar seus filhos a partir do grafo
function expandLoadChildren(d) {
  // Se já tem filhos, não precisa carregar
  if (d.children || !d.data || !d.data.codigo) return;
  
  // Carrega os filhos a partir do grafo
  const codigo = d.data.codigo;
  
  try {
    // Encontra todas as unidades que têm esse código como parte do grafo
    const filhos = [];
    
    if (originalOrgData && originalOrgData.unidades) {
      originalOrgData.unidades.forEach(unit => {
        // Verifica apenas unidades com grafo
        if (!unit.grafo || !unit.codigo) return;
        
        // Verifica se o grafo contém o código do pai
        const codigosGrafo = unit.grafo.split('-');
        
        // Verifica se o código do pai está no grafo e se é o penúltimo elemento
        // (o último é o código da própria unidade)
        const indexPai = codigosGrafo.indexOf(codigo);
        if (indexPai >= 0 && indexPai === codigosGrafo.length - 2) {
          // Esta unidade é filha direta
          const node = {
            nome: unit.nome || unit.denominacao_unidade || "Unidade sem nome",
            codigo: unit.codigo,
            cargo: unit.tipo_cargo ? `${unit.tipo_cargo} ${unit.nivel || ''}` : "Sem cargo",
            secretaria: unit.sigla_unidade || unit.sigla || "MPO",
            tipo_unidade: unit.tipo_unidade || "",
            nivel: unit.nivel,
            grafo: unit.grafo || "",
            children: []
          };
          
          filhos.push(node);
        }
      });
    }
    
    // Ordenar filhos
    filhos.sort((a, b) => {
      if (a.codigo === "308804") return -1;
      if (b.codigo === "308804") return 1;
      return 0;
    });
    
    // Se encontrou filhos, adiciona ao nó
    if (filhos.length > 0) {
      d.data.children = filhos;
      // Adicionar dados financeiros aos filhos
      if (financialData) {
        mergeFinancialData(d.data, financialData);
      }
      d.children = d3.hierarchy(d.data).children;
    }
  } catch (error) {
    console.error("Erro ao carregar filhos:", error);
  }
}

// Exporta funções para uso externo
window.financialOrgChart = {
  init: initOrganogramaFinanceiro,
  update: update,
  expandAll: () => { expandAll(orgTree); update(orgTree); },
  collapseAll: () => { collapseAll(orgTree); update(orgTree); }
};

// Configura os eventos após a inicialização
function setupEventListeners() {
  // Botões de controle
  d3.select('#expandAllFinBtn').on('click', expandAll);
  d3.select('#collapseFinBtn').on('click', collapseAll);
  d3.select('#resetFinBtn').on('click', resetZoom);
  
  // Botões de modo de visualização
  d3.selectAll('.view-mode-btn').on('click', function() {
    // Remove classe ativa de todos os botões
    d3.selectAll('.view-mode-btn').classed('active', false);
    
    // Adiciona classe ativa ao botão clicado
    d3.select(this).classed('active', true);
    
    // Obtém o modo selecionado
    viewMode = d3.select(this).attr('data-mode');
    
    // Atualiza a visualização
    if (orgTree) {
      update(orgTree);
    }
  });
} 