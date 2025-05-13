// simulacao.js

// Variáveis globais
let nodes = [] // Array de nós
let links = [] // Array de links (conexões) entre nós
let svg, g // Referências ao SVG e ao grupo principal
let i = 0 // Contador de IDs para nós
let tooltip // Tooltip para informações adicionais
let simulation // Simulação de forças para o layout do grafo
let autoOrganize = true // Flag para controlar a organização automática
let isDarkMode = false // Flag para controlar o modo escuro

// Configurações do grafo
const width = 1000
const height = 700
const nodeRadius = 30
const LIMITE_PONTOS_SECRETARIA = 100
const CUSTO_POR_PONTO = 1500 // Valor em reais por ponto

// Paleta de cores minimalista
const colors = {
  node: {
    default: '#f8f9fa',
    selected: '#e9ecef',
    hover: '#e9ecef',
    stroke: '#dee2e6',
    // Cores para modo escuro
    darkDefault: '#1a1a1a',
    darkSelected: '#222222',
    darkHover: '#222222',
    darkStroke: '#333333'
  },
  text: {
    light: '#333333',
    dark: '#e0e0e0'
  },
  link: {
    light: '#a4c5f4',
    dark: '#666666'
  },
  secretarias: {
    Administração: { light: '#4a90e2', dark: '#4a90e2' },
    Educação: { light: '#28a745', dark: '#28a745' },
    Saúde: { light: '#dc3545', dark: '#dc3545' },
    Infraestrutura: { light: '#fd7e14', dark: '#fd7e14' },
    Finanças: { light: '#6f42c1', dark: '#6f42c1' },
    default: { light: '#6c757d', dark: '#6c757d' }
  }
}

// Elementos do DOM
const searchInput = document.getElementById('searchInput')
const searchResults = document.getElementById('searchResults')
const addNodeBtn = document.getElementById('addNodeBtn')
const resetBtn = document.getElementById('resetBtn')
const nodeList = document.getElementById('nodeList')
const sourceNodeSelect = document.getElementById('sourceNode')
const targetNodeSelect = document.getElementById('targetNode')
const connectNodesBtn = document.getElementById('connectNodesBtn')
const reportContent = document.getElementById('reportContent')
const nodeHierarchy = document.getElementById('nodeHierarchy')
const nodeSecretaria = document.getElementById('nodeSecretaria')
const nodeCargo = document.getElementById('nodeCargo')

// Inicialização
document.addEventListener('DOMContentLoaded', initSimulacao)

function initSimulacao() {
  // Verificar o modo atual (claro/escuro)
  isDarkMode =
    localStorage.getItem('darkMode') === 'true' ||
    document.body.classList.contains('dark-mode')

  // Seleciona o container da simulação
  const container = d3.select('#simulacaoContainer')

  // Cria o tooltip
  tooltip = container.append('div').attr('class', 'tooltip').style('opacity', 0)

  // Cria o SVG
  svg = container
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet')
    .style('background-color', isDarkMode ? '#121212' : '#f5f5f5') // Cor de fundo padrão

  // Cria o grupo principal para os nós e links
  g = svg.append('g')

  // Configura o comportamento de zoom e pan
  const zoomBehavior = d3
    .zoom()
    .scaleExtent([0.5, 2])
    .on('zoom', event => {
      g.attr('transform', event.transform)
    })

  svg.call(zoomBehavior)

  // Inicializa a simulação de forças
  initSimulation()

  // Adiciona listeners aos botões
  searchInput.addEventListener('input', handleSearch)
  searchInput.addEventListener('keypress', e => {
    if (e.key === 'Enter') {
      addNodeFromInput()
    }
  })
  searchInput.addEventListener('focusout', () => {
    // Pequeno atraso para permitir cliques nos resultados da pesquisa
    setTimeout(() => {
      searchResults.classList.remove('active')
    }, 200)
  })
  searchInput.addEventListener('focus', () => {
    if (searchInput.value.length > 0) {
      searchResults.classList.add('active')
    }
  })

  addNodeBtn.addEventListener('click', addNodeFromInput)
  resetBtn.addEventListener('click', resetSimulation)
  connectNodesBtn.addEventListener('click', connectNodes)

  // Eventos para mudanças em valores de nós
  nodeHierarchy.addEventListener('change', () => {
    updateReport()
    // Mostrar uma visualização prévia de como ficaria a hierarquia
    previewHierarchy()
  })
  nodeHierarchy.addEventListener('input', () => {
    document.getElementById('hierarchyValue').textContent = nodeHierarchy.value
    previewHierarchy()
  })
  nodeSecretaria.addEventListener('change', updateReport)

  // Adicionar um botão de autoconexão global para reorganizar todas as secretarias
  if (!document.getElementById('autoOrganizeBtn')) {
    document.querySelector('.controls-panel').insertAdjacentHTML(
      'beforeend',
      `
      <button id="autoOrganizeBtn" class="btn btn-outline-primary ms-2" title="Reorganizar automaticamente todas as conexões">
        <i class="fas fa-magic"></i> Auto-organizar
      </button>
    `
    )

    document.getElementById('autoOrganizeBtn').addEventListener('click', () => {
      reorganizarTodasConexoes()
    })
  }

  // Adicionar listener para o toggle de auto-organização
  const autoOrganizeToggle = document.getElementById('autoOrganizeToggle')
  const autoOrganizeStatus = document.getElementById('autoOrganizeStatus')

  autoOrganizeToggle.addEventListener('change', () => {
    autoOrganize = autoOrganizeToggle.checked

    // Atualizar o status visual
    if (autoOrganize) {
      autoOrganizeStatus.textContent = 'Ativo'
      autoOrganizeStatus.className = 'badge bg-success'
      // Reorganizar todas as conexões existentes
      if (nodes.length > 0) {
        reorganizarTodasConexoes()
      }
    } else {
      autoOrganizeStatus.textContent = 'Inativo'
      autoOrganizeStatus.className = 'badge bg-secondary'
    }
  })

  // Listener para mudanças no tema (escuro/claro)
  document.addEventListener('themeChange', e => {
    isDarkMode = e.detail.isDarkMode
    // Atualizar o fundo do SVG
    svg.style('background-color', isDarkMode ? '#121212' : '#f5f5f5')
    // Atualizar os nós e links com as cores do novo tema
    updateThemeColors()
  })

  // Adicionando listener ao botão de alternância de tema
  const toggleThemeBtn = document.getElementById('toggleThemeBtn')
  if (toggleThemeBtn) {
    toggleThemeBtn.addEventListener('click', () => {
      // O evento será disparado pelo código no HTML
      isDarkMode = document.body.classList.contains('dark-mode')
      // Disparar um evento customizado para atualizar o tema no gráfico
      document.dispatchEvent(
        new CustomEvent('themeChange', {
          detail: { isDarkMode }
        })
      )
    })
  }

  // Adicionar botão para salvar organograma na inicialização
  document.addEventListener('DOMContentLoaded', function () {
    const controlsPanel = document.querySelector('.controls-panel')

    if (controlsPanel && !document.getElementById('saveOrganogramaBtn')) {
      // Adicionar botão salvar no painel de controles
      controlsPanel.insertAdjacentHTML(
        'beforeend',
        `
        <button id="saveOrganogramaBtn" class="btn btn-outline-primary ms-2" title="Salvar este organograma">
          <i class="fas fa-save"></i> Salvar
        </button>
        `
      )

      // Adicionar listener ao botão
      document
        .getElementById('saveOrganogramaBtn')
        .addEventListener('click', salvarOrganograma)

      // Adicionar container para organogramas salvos
      const simulacaoContainer = document.getElementById('simulacaoContainer')

      if (
        simulacaoContainer &&
        !document.getElementById('organogramasSalvosContainer')
      ) {
        // Inserir após container de simulação
        simulacaoContainer.insertAdjacentHTML(
          'afterend',
          `
          <div id="organogramasSalvosContainer" class="card mt-3">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h5 class="mb-0">Organogramas Salvos</h5>
              <button id="refreshOrganogramasBtn" class="btn btn-sm btn-outline-secondary" title="Atualizar lista">
                <i class="fas fa-sync-alt"></i>
              </button>
            </div>
            <div class="card-body">
              <div class="row mb-3">
                <div class="col">
                  <div class="input-group">
                    <input type="text" id="organogramaSearchInput" class="form-control" placeholder="Pesquisar organogramas...">
                    <button class="btn btn-outline-secondary" type="button" id="organogramaSearchBtn" title="Pesquisar">
                      <i class="fas fa-search"></i>
                    </button>
                  </div>
                </div>
              </div>
              <div id="organogramasSalvos"></div>
            </div>
          </div>
          `
        )

        // Adicionar listener ao botão de atualizar
        document
          .getElementById('refreshOrganogramasBtn')
          .addEventListener('click', () => atualizarListaOrganogramas())

        // Carregar a lista inicial
        atualizarListaOrganogramas()
      }
    }

    // Adicionar evento de pesquisa de organogramas
    const organogramaSearchInput = document.getElementById(
      'organogramaSearchInput'
    )
    const organogramaSearchBtn = document.getElementById('organogramaSearchBtn')

    if (organogramaSearchInput && organogramaSearchBtn) {
      // Função de pesquisa
      const pesquisarOrganogramas = () => {
        const termo = organogramaSearchInput.value.trim()
        atualizarListaOrganogramas(termo)
      }

      // Adicionar listener ao botão de pesquisa
      organogramaSearchBtn.addEventListener('click', pesquisarOrganogramas)

      // Adicionar listener para pesquisa ao pressionar Enter
      organogramaSearchInput.addEventListener('keypress', e => {
        if (e.key === 'Enter') {
          pesquisarOrganogramas()
        }
      })

      // Limpar resultados quando o campo é apagado
      organogramaSearchInput.addEventListener('input', () => {
        if (organogramaSearchInput.value.trim() === '') {
          atualizarListaOrganogramas()
        }
      })
    }
  })
}

// Atualiza as cores dos nós e links baseado no tema atual
function updateThemeColors() {
  // Atualizar o fundo do SVG
  svg
    .transition()
    .duration(300)
    .style('background-color', isDarkMode ? '#121212' : '#f5f5f5')

  // Atualizar nós
  g.selectAll('.node circle')
    .transition()
    .duration(300)
    .attr('fill', d => getSecretariaColor(d.secretaria))
    .attr('stroke', isDarkMode ? colors.node.darkStroke : colors.node.stroke)

  // Atualizar textos
  g.selectAll('.node text')
    .style('fill', '#ffffff')
    .style(
      'text-shadow',
      isDarkMode ? '0px 0px 3px rgba(0,0,0,0.9)' : '0px 0px 2px rgba(0,0,0,0.7)'
    )

  // Atualizar o indicador de nível hierárquico
  g.selectAll('.node text:nth-child(3)').style(
    'fill',
    isDarkMode ? '#aaaaaa' : '#333333'
  )

  // Atualizar links
  g.selectAll('.link')
    .transition()
    .duration(300)
    .attr('stroke', isDarkMode ? colors.link.dark : colors.link.light)
    .attr('stroke-opacity', isDarkMode ? 0.8 : 0.6)
}

// Retorna a cor associada à secretaria ou a cor padrão
function getSecretariaColor(secretaria) {
  const colorSet = colors.secretarias[secretaria] || colors.secretarias.default
  return isDarkMode ? colorSet.dark : colorSet.light
}

// Configurar a simulação de forças para posicionar os nós
function initSimulation() {
  simulation = d3
    .forceSimulation(nodes)
    .force(
      'link',
      d3
        .forceLink(links)
        .id(d => d.id)
        .distance(
          d =>
            100 + (15 - Math.min(d.source.hierarchy, d.target.hierarchy)) * 10
        )
    )
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force(
      'collision',
      d3.forceCollide().radius(d => nodeRadius + d.hierarchy)
    )
    .force(
      'y',
      d3
        .forceY()
        .strength(d => (d.hierarchy ? 0.3 : 0.1))
        .y(d => height / 3 - d.hierarchy * 30)
    )
    .force(
      'x',
      d3
        .forceX()
        .strength(d => 0.05)
        .x(d => {
          // Agrupar por secretaria horizontalmente
          const secretarias = [...new Set(nodes.map(n => n.secretaria))].filter(
            Boolean
          )
          const index = secretarias.indexOf(d.secretaria)
          const segmentWidth = width / (secretarias.length || 1)
          return segmentWidth * (index + 0.5)
        })
    )
    .on('tick', ticked)
}

// Função chamada a cada "tick" da simulação para atualizar as posições
function ticked() {
  // Atualiza posições dos links
  g.selectAll('.link')
    .attr('x1', d => d.source.x)
    .attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x)
    .attr('y2', d => d.target.y)

  // Atualiza posições dos nós
  g.selectAll('.node').attr('transform', d => `translate(${d.x},${d.y})`)
}

// Renderizar o grafo com os nós e links atuais
function update() {
  // Atualizar a simulação com novos dados
  simulation.nodes(nodes)
  simulation.force('link').links(links)
  simulation.alpha(1).restart()

  // LINKS
  const link = g
    .selectAll('.link')
    .data(links, d => `${d.source.id}-${d.target.id}`)

  // Remover links que não existem mais
  link.exit().remove()

  // Adicionar novos links
  const linkEnter = link
    .enter()
    .append('line')
    .attr('class', 'link')
    .attr('stroke', d => {
      // Cores diferentes para conexões manuais e automáticas
      if (d.type === 'manual') {
        return isDarkMode ? '#90b2e5' : '#4a90e2' // Azul mais forte para conexões manuais
      }
      return isDarkMode ? colors.link.dark : colors.link.light // Cor padrão para automáticas
    })
    .attr('stroke-width', d => Math.sqrt(d.value) * 2)
    .attr('stroke-opacity', d => {
      // Maior opacidade para conexões manuais
      return d.type === 'manual' ? 0.8 : isDarkMode ? 0.6 : 0.5
    })
    .attr('stroke-dasharray', d => (d.type === 'auto' ? '5,5' : 'none')) // Linha tracejada para automáticas

  // NÓS
  const node = g.selectAll('.node').data(nodes, d => d.id)

  // Remover nós que não existem mais
  node.exit().remove()

  // Adicionar novos nós
  const nodeEnter = node
    .enter()
    .append('g')
    .attr('class', 'node')
    .call(
      d3
        .drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
    )
    .on('mouseover', (event, d) => {
      // Mostra tooltip
      tooltip.transition().duration(200).style('opacity', 1)

      // Destacar links conectados
      g.selectAll('.link')
        .filter(link => link.source.id === d.id || link.target.id === d.id)
        .transition()
        .duration(200)
        .attr('stroke-width', l =>
          Math.max(3, Math.min(l.source.hierarchy, l.target.hierarchy) / 2)
        )
        .attr('stroke-opacity', 1)
        .attr('stroke', '#ffbb33')

      tooltip
        .html(
          `
          <strong>${d.nome}</strong><br>
          Cargo: ${d.cargo}<br>
          Secretaria: ${d.secretaria}<br>
          Nível: ${d.hierarchy} (${d.hierarchy} pontos)
        `
        )
        .style('left', event.pageX + 10 + 'px')
        .style('top', event.pageY - 28 + 'px')

      // Destaca o nó
      d3.select(event.currentTarget)
        .select('circle')
        .transition()
        .duration(200)
        .attr('r', nodeRadius + d.hierarchy / 2)
        .attr('stroke-width', 3)
        .attr('stroke', '#ffbb33')
    })
    .on('mouseout', (event, d) => {
      // Esconde tooltip
      tooltip.transition().duration(500).style('opacity', 0)

      // Restaura links
      g.selectAll('.link')
        .filter(link => link.source.id === d.id || link.target.id === d.id)
        .transition()
        .duration(200)
        .attr('stroke-width', l =>
          Math.max(1, Math.min(l.source.hierarchy, l.target.hierarchy) / 3)
        )
        .attr('stroke-opacity', 0.6)
        .attr('stroke', colors.link.light)

      // Remove destaque
      d3.select(event.currentTarget)
        .select('circle')
        .transition()
        .duration(200)
        .attr('r', nodeRadius)
        .attr('stroke-width', d => Math.max(1, d.hierarchy / 5))
        .attr('stroke', colors.node.stroke)
    })

  // Adicionar círculos aos novos nós
  nodeEnter
    .append('circle')
    .attr('r', 0)
    .attr('fill', d => getSecretariaColor(d.secretaria))
    .attr('stroke', isDarkMode ? colors.node.darkStroke : colors.node.stroke)
    .attr('stroke-width', d => Math.max(1, d.hierarchy / 5))
    .attr('opacity', d => 0.7 + (d.hierarchy / 15) * 0.3) // Mais opaco para níveis mais altos
    .transition()
    .duration(300)
    .attr('r', d => nodeRadius)

  // Adicionar texto aos novos nós
  nodeEnter
    .append('text')
    .attr('dy', '.3em')
    .attr('text-anchor', 'middle')
    .text(d => d.nome)
    .style('font-size', '12px')
    .style('fill', '#ffffff')
    .style('text-shadow', '0px 0px 2px rgba(0,0,0,0.7)')
    .style('pointer-events', 'none')

  // Adicionar indicador de nível
  nodeEnter
    .append('text')
    .attr('dy', -nodeRadius - 5)
    .attr('text-anchor', 'middle')
    .text(d => d.hierarchy)
    .style('font-size', '10px')
    .style('font-weight', 'bold')
    .style('fill', '#333')
    .style('pointer-events', 'none')

  // Organizar automaticamente o grafo com base nos níveis hierárquicos
  organizarHierarquia()

  // Atualizar o relatório
  updateReport()

  // Atualiza a legenda
  adicionarLegenda()
}

// Buscar nomes na lista de nós/pessoas existentes
function handleSearch() {
  const query = searchInput.value.trim().toLowerCase()

  // Limpar resultados anteriores
  searchResults.innerHTML = ''

  if (query.length < 2) {
    searchResults.classList.remove('active')
    return
  }

  // Buscar na API (simulado por enquanto)
  // Em produção, fazer uma chamada fetch para um endpoint de pesquisa
  const mockResults = getMockSearchResults().filter(item =>
    item.nome.toLowerCase().includes(query)
  )

  if (mockResults.length > 0) {
    mockResults.forEach(result => {
      const resultItem = document.createElement('div')
      resultItem.className = 'search-result-item'
      resultItem.textContent = result.nome
      resultItem.addEventListener('click', () => {
        searchInput.value = result.nome
        searchResults.classList.remove('active')
        nodeCargo.value = result.cargo || ''
        addNodeFromResult(result)
      })
      searchResults.appendChild(resultItem)
    })
    searchResults.classList.add('active')
  } else {
    searchResults.classList.remove('active')
  }
}

// Retorna alguns resultados de exemplo para a pesquisa
function getMockSearchResults() {
  return [
    {
      id: 'mock1',
      nome: 'João Silva',
      cargo: 'Diretor',
      secretaria: 'Administração',
      hierarchy: 12
    },
    {
      id: 'mock2',
      nome: 'Maria Oliveira',
      cargo: 'Gerente',
      secretaria: 'Finanças',
      hierarchy: 10
    },
    {
      id: 'mock3',
      nome: 'Pedro Santos',
      cargo: 'Coordenador',
      secretaria: 'Educação',
      hierarchy: 8
    },
    {
      id: 'mock4',
      nome: 'Ana Costa',
      cargo: 'Analista',
      secretaria: 'Saúde',
      hierarchy: 5
    },
    {
      id: 'mock5',
      nome: 'Carlos Ferreira',
      cargo: 'Supervisor',
      secretaria: 'Infraestrutura',
      hierarchy: 7
    },
    {
      id: 'mock6',
      nome: 'Juliana Lima',
      cargo: 'Assistente',
      secretaria: 'Administração',
      hierarchy: 3
    },
    {
      id: 'mock7',
      nome: 'Roberto Alves',
      cargo: 'Técnico',
      secretaria: 'Saúde',
      hierarchy: 4
    },
    {
      id: 'mock8',
      nome: 'Patricia Mendes',
      cargo: 'Especialista',
      secretaria: 'Educação',
      hierarchy: 6
    }
  ]
}

// Adicionar um nó a partir do input de texto
function addNodeFromInput() {
  const nome = searchInput.value.trim()
  if (nome.length < 1) return

  const secretaria = nodeSecretaria.value
  if (!secretaria) {
    alert('Por favor, selecione uma secretaria!')
    return
  }

  const hierarchy = parseInt(nodeHierarchy.value)
  const cargo = nodeCargo.value.trim() || 'Não especificado'

  // Verificar se já existe um nó com este nome
  if (nodes.some(node => node.nome === nome)) {
    alert('Este nome já foi adicionado!')
    return
  }

  const newNode = {
    id: `user-${i++}`,
    nome: nome,
    cargo: cargo,
    secretaria: secretaria,
    hierarchy: hierarchy,
    x: width / 2 + (Math.random() - 0.5) * 100,
    y: height / 2 + (Math.random() - 0.5) * 100
  }

  addNode(newNode)
  searchInput.value = ''
  nodeCargo.value = ''
  nodeHierarchy.value = 5
  document.getElementById('hierarchyValue').textContent = '5'
}

// Adicionar um nó a partir de um resultado de pesquisa
function addNodeFromResult(result) {
  // Verificar se já existe um nó com este nome
  if (nodes.some(node => node.nome === result.nome)) {
    alert('Este nome já foi adicionado!')
    return
  }

  const secretaria = nodeSecretaria.value
  if (!secretaria) {
    alert('Por favor, selecione uma secretaria!')
    return
  }

  const hierarchy = parseInt(nodeHierarchy.value)

  const newNode = {
    id: `user-${i++}`,
    nome: result.nome,
    cargo: nodeCargo.value || result.cargo || 'Não especificado',
    secretaria: secretaria,
    hierarchy: hierarchy,
    x: width / 2 + (Math.random() - 0.5) * 100,
    y: height / 2 + (Math.random() - 0.5) * 100
  }

  addNode(newNode)
  searchInput.value = ''
  nodeCargo.value = ''
  nodeHierarchy.value = 5
  document.getElementById('hierarchyValue').textContent = '5'
}

// Adicionar um nó ao grafo e à lista
function addNode(newNode) {
  // Verificar limite de pontos por secretaria
  const secretariaPontos = calcularPontosSecretaria(newNode.secretaria)
  if (secretariaPontos + newNode.hierarchy > LIMITE_PONTOS_SECRETARIA) {
    const excesso =
      secretariaPontos + newNode.hierarchy - LIMITE_PONTOS_SECRETARIA
    if (
      !confirm(
        `Aviso: A secretaria ${newNode.secretaria} excederá o limite de ${LIMITE_PONTOS_SECRETARIA} pontos por ${excesso} pontos. Deseja continuar?`
      )
    ) {
      return
    }
  }

  nodes.push(newNode)
  updateNodeList()
  updateNodeSelects()

  // Tentar conectar automaticamente apenas se auto-organização estiver ativa
  if (autoOrganize) {
    conectarAutomaticamente(newNode)
  }

  update()
}

// Função para verificar se já existe uma conexão entre dois nós
function existeConexao(sourceId, targetId) {
  return links.some(
    link =>
      (link.source.id === sourceId && link.target.id === targetId) ||
      (link.source.id === targetId && link.target.id === sourceId)
  )
}

// Função para remover uma conexão existente entre dois nós
function removerConexao(sourceId, targetId) {
  // Encontra o índice da conexão no array de links
  const linkIndex = links.findIndex(
    link =>
      (link.source.id === sourceId && link.target.id === targetId) ||
      (link.source.id === targetId && link.target.id === sourceId)
  )

  // Se encontrar a conexão, remove-a
  if (linkIndex !== -1) {
    links.splice(linkIndex, 1)
    return true
  }

  return false
}

// Função para conectar nós, substitui a função connectNodes()
function connectNodes() {
  const sourceId = sourceNodeSelect.value
  const targetId = targetNodeSelect.value

  if (!sourceId || !targetId || sourceId === targetId) {
    alert('Selecione dois nós diferentes para conectar.')
    return
  }

  // Encontra os objetos dos nós pelos IDs
  const source = nodes.find(node => node.id === sourceId)
  const target = nodes.find(node => node.id === targetId)

  if (!source || !target) {
    alert('Nós não encontrados.')
    return
  }

  // Verifica se já existe uma conexão entre esses nós
  if (existeConexao(sourceId, targetId)) {
    // Encontra a conexão existente
    const conexaoExistente = links.find(
      link =>
        (link.source.id === sourceId && link.target.id === targetId) ||
        (link.source.id === targetId && link.target.id === sourceId)
    )

    // Se for uma conexão automática, remove-a e cria uma manual
    if (conexaoExistente.type === 'auto') {
      removerConexao(sourceId, targetId)

      // Cria uma nova conexão manual
      links.push({
        source,
        target,
        type: 'manual', // Marca como conexão manual
        value: 1
      })

      console.log(
        `Conexão automática entre ${source.nome} e ${target.nome} substituída por conexão manual.`
      )
    } else {
      // Se já for manual, apenas avisa ao usuário
      alert(
        `Já existe uma conexão manual entre ${source.nome} e ${target.nome}.`
      )
      return
    }
  } else {
    // Cria uma nova conexão manual se não existe nenhuma
    links.push({
      source,
      target,
      type: 'manual', // Marca como conexão manual
      value: 1
    })

    console.log(`Conexão manual criada entre ${source.nome} e ${target.nome}.`)
  }

  // Atualiza a visualização
  update()
}

// Modificação da função conectarAutomaticamente para corrigir conexões para cargos mais altos
function conectarAutomaticamente(newNode) {
  // Se auto-organização estiver desativada, não fazer nada
  if (!autoOrganize) return

  const { secretaria } = newNode

  // Se for o primeiro nó desta secretaria, não tem com o que conectar
  const nosMesmaSecretaria = nodes.filter(
    node => node.secretaria === secretaria && node.id !== newNode.id
  )

  if (nosMesmaSecretaria.length === 0) return

  // Ordenar nós da mesma secretaria por hierarquia (do maior para o menor valor)
  // Note que hierarquia maior significa valor menor (ex: nível 1 é mais alto que nível 10)
  const nosOrdenados = [...nosMesmaSecretaria].sort(
    (a, b) => a.hierarchy - b.hierarchy
  )

  // CORREÇÃO: Se o novo nó tem hierarquia MAIOR (valor menor), ele deve conectar-se a nós com hierarquia MENOR (valor maior)
  if (newNode.hierarchy < nosOrdenados[0].hierarchy) {
    // O novo nó é o de nível mais alto da hierarquia
    // Em vez de conectar com outro nó de nível alto, devemos fazer nós de nível menor se conectarem a ele
    // Vamos buscar todos os nós com nível hierárquico menor (valor maior)
    const subordinados = nosMesmaSecretaria.filter(
      node => node.hierarchy > newNode.hierarchy
    )

    // Encontrar nós que não têm superior
    subordinados.forEach(subordinado => {
      // Verificar se o subordinado já tem alguma conexão automática
      const jaTemConexaoAutomatica = links.some(
        link =>
          (link.target.id === subordinado.id ||
            link.source.id === subordinado.id) &&
          link.type === 'auto'
      )

      // Se já tem conexão automática, não fazer nada
      if (jaTemConexaoAutomatica) return

      // Se não tem conexão, conectar ao novo nó
      if (!existeConexao(newNode.id, subordinado.id)) {
        links.push({
          source: newNode,
          target: subordinado,
          type: 'auto',
          value: 1
        })
      }
    })
  } else {
    // O novo nó tem hierarquia menor (valor maior), então deve conectar-se a um nó de hierarquia maior (valor menor)

    // Encontrar o nó de hierarquia maior que seja imediatamente superior
    const superiorImediato = nosOrdenados.find(
      node => node.hierarchy < newNode.hierarchy
    )

    if (superiorImediato) {
      // Verificar se já existe uma conexão
      if (!existeConexao(newNode.id, superiorImediato.id)) {
        links.push({
          source: superiorImediato,
          target: newNode,
          type: 'auto',
          value: 1
        })
      }
    } else {
      // Se não encontrar um superior imediato (situação rara), conectar ao nó de maior hierarquia
      const noMaisAlto = nosOrdenados[0]

      // Verificar se já existe uma conexão
      if (!existeConexao(newNode.id, noMaisAlto.id)) {
        links.push({
          source: noMaisAlto,
          target: newNode,
          type: 'auto',
          value: 1
        })
      }
    }
  }

  // Após a conexão automática, reorganizar a secretaria para garantir hierarquia correta
  reorganizarConexoesSecretaria(secretaria)
}

// Modificação da função reorganizarConexoesSecretaria para garantir conexões corretas
function reorganizarConexoesSecretaria(secretaria) {
  // Identifica os nós desta secretaria
  const nosSecretaria = nodes.filter(node => node.secretaria === secretaria)

  if (nosSecretaria.length <= 1) return // Precisa de pelo menos 2 nós

  // Ordena os nós por hierarquia (do maior para o menor hierarquicamente, ou seja, do menor para o maior valor)
  const nosOrdenados = [...nosSecretaria].sort(
    (a, b) => a.hierarchy - b.hierarchy
  )

  // Remove todas as conexões automáticas existentes entre nós desta secretaria
  links = links.filter(link => {
    const sourceEhDaSecretaria = nosSecretaria.some(
      n => n.id === link.source.id
    )
    const targetEhDaSecretaria = nosSecretaria.some(
      n => n.id === link.target.id
    )

    // Mantém as conexões manuais e as que não são desta secretaria
    if (!sourceEhDaSecretaria || !targetEhDaSecretaria) return true
    if (link.type === 'manual') return true

    // Remove conexões automáticas desta secretaria
    return false
  })

  // CORREÇÃO: Cria novas conexões automáticas, respeitando a hierarquia
  // Os nós de maior hierarquia (valor menor) devem ser sources para os de menor hierarquia (valor maior)
  for (let i = 1; i < nosOrdenados.length; i++) {
    const noAtual = nosOrdenados[i]
    let superiorEncontrado = false

    // Procurar o superior mais próximo na hierarquia (valor menor)
    for (let j = i - 1; j >= 0; j--) {
      const potencialSuperior = nosOrdenados[j]

      // Se o potencial superior tem hierarquia maior (valor menor) e não existe conexão manual
      if (
        potencialSuperior.hierarchy < noAtual.hierarchy &&
        !existeConexao(potencialSuperior.id, noAtual.id)
      ) {
        links.push({
          source: potencialSuperior,
          target: noAtual,
          type: 'auto',
          value: 1
        })
        superiorEncontrado = true
        break
      }
    }

    // Se não encontrou um superior, conectar ao nó de maior hierarquia (índice 0)
    if (!superiorEncontrado && !existeConexao(nosOrdenados[0].id, noAtual.id)) {
      links.push({
        source: nosOrdenados[0],
        target: noAtual,
        type: 'auto',
        value: 1
      })
    }
  }

  // Atualiza a visualização
  update()
}

// Organiza o grafo com base nos níveis hierárquicos
function organizarHierarquia() {
  // Aplicar força vertical baseada na hierarquia
  simulation
    .force('y')
    .strength(d => 0.3)
    .y(d => height / 3 - d.hierarchy * 30)

  // Agrupar por secretaria horizontalmente
  simulation
    .force('x')
    .strength(d => 0.1)
    .x(d => {
      const secretarias = [...new Set(nodes.map(n => n.secretaria))].filter(
        Boolean
      )
      const index = secretarias.indexOf(d.secretaria)
      const segmentWidth = width / (secretarias.length || 1)
      return segmentWidth * (index + 0.5)
    })

  simulation.alpha(0.5).restart()
}

// Remover um nó pelo ID
function removeNode(nodeId) {
  // Remover links relacionados a este nó
  links = links.filter(
    link => link.source.id !== nodeId && link.target.id !== nodeId
  )

  // Remover o nó
  nodes = nodes.filter(node => node.id !== nodeId)

  updateNodeList()
  updateNodeSelects()
  update()
}

// Atualizar a lista de nós visível
function updateNodeList() {
  nodeList.innerHTML = ''

  if (nodes.length === 0) {
    nodeList.innerHTML =
      '<div class="text-muted small text-center p-3">Nenhum nome adicionado</div>'
    return
  }

  // Ordenar por secretaria e hierarquia
  const sortedNodes = [...nodes].sort((a, b) => {
    if (a.secretaria === b.secretaria) {
      return b.hierarchy - a.hierarchy // Maior hierarquia primeiro
    }
    return a.secretaria.localeCompare(b.secretaria)
  })

  sortedNodes.forEach(node => {
    const nodeItem = document.createElement('div')
    nodeItem.className = 'node-item'

    const infoDiv = document.createElement('div')
    infoDiv.className = 'node-item-info'

    const nameSpan = document.createElement('span')
    nameSpan.className = 'node-item-name'
    nameSpan.textContent = node.nome

    const detailsSpan = document.createElement('span')
    detailsSpan.className = 'node-item-details'
    detailsSpan.textContent = `${node.secretaria} - Nível ${node.hierarchy}`

    infoDiv.appendChild(nameSpan)
    infoDiv.appendChild(detailsSpan)

    const actionsDiv = document.createElement('div')
    actionsDiv.className = 'node-item-actions'

    const removeBtn = document.createElement('button')
    removeBtn.innerHTML = '<i class="fas fa-times"></i>'
    removeBtn.title = 'Remover'
    removeBtn.addEventListener('click', () => removeNode(node.id))

    actionsDiv.appendChild(removeBtn)
    nodeItem.appendChild(infoDiv)
    nodeItem.appendChild(actionsDiv)
    nodeList.appendChild(nodeItem)
  })
}

// Atualizar os selects de origem e destino
function updateNodeSelects() {
  // Salvar valores atuais para restaurar a seleção depois
  const currentSource = sourceNodeSelect.value
  const currentTarget = targetNodeSelect.value

  // Limpar opções
  sourceNodeSelect.innerHTML = '<option value="">Selecione um nome</option>'
  targetNodeSelect.innerHTML = '<option value="">Selecione um nome</option>'

  // Ordenar por hierarquia
  const sortedNodes = [...nodes].sort((a, b) => b.hierarchy - a.hierarchy)

  // Adicionar opções para cada nó
  sortedNodes.forEach(node => {
    // Opção para origem
    const sourceOpt = document.createElement('option')
    sourceOpt.value = node.id
    sourceOpt.textContent = `${node.nome} (${node.secretaria} - Nível ${node.hierarchy})`
    sourceNodeSelect.appendChild(sourceOpt)

    // Opção para destino
    const targetOpt = document.createElement('option')
    targetOpt.value = node.id
    targetOpt.textContent = `${node.nome} (${node.secretaria} - Nível ${node.hierarchy})`
    targetNodeSelect.appendChild(targetOpt)
  })

  // Restaurar valores anteriores se ainda existirem
  if (nodes.some(node => node.id === currentSource)) {
    sourceNodeSelect.value = currentSource
  }

  if (nodes.some(node => node.id === currentTarget)) {
    targetNodeSelect.value = currentTarget
  }
}

// Calcular pontos por secretaria
function calcularPontosSecretaria(secretariaNome) {
  return nodes
    .filter(node => node.secretaria === secretariaNome)
    .reduce((total, node) => total + node.hierarchy, 0)
}

// Atualizar o relatório de pontos
function updateReport() {
  if (nodes.length === 0) {
    reportContent.innerHTML =
      '<div class="text-muted small text-center p-3">Adicione nomes e secretarias para gerar o relatório</div>'
    return
  }

  // Obter lista única de secretarias
  const secretarias = [...new Set(nodes.map(node => node.secretaria))].filter(
    Boolean
  )

  reportContent.innerHTML = ''

  let totalGeralPontos = 0
  let totalCusto = 0

  secretarias.forEach(secretaria => {
    const pontos = calcularPontosSecretaria(secretaria)
    totalGeralPontos += pontos

    const secretariaDiv = document.createElement('div')
    secretariaDiv.className = 'secretaria-item'

    const headerDiv = document.createElement('div')
    headerDiv.className = 'secretaria-header'

    const nomeSpan = document.createElement('span')
    nomeSpan.className = 'secretaria-nome'
    nomeSpan.textContent = secretaria

    const pontosSpan = document.createElement('span')
    pontosSpan.className = 'secretaria-pontos'
    pontosSpan.textContent = `${pontos}/${LIMITE_PONTOS_SECRETARIA} pts`

    headerDiv.appendChild(nomeSpan)
    headerDiv.appendChild(pontosSpan)

    const progressoDiv = document.createElement('div')
    progressoDiv.className = 'secretaria-progresso'

    const barraDiv = document.createElement('div')
    barraDiv.className = 'secretaria-barra'
    barraDiv.style.width = `${Math.min(
      100,
      (pontos / LIMITE_PONTOS_SECRETARIA) * 100
    )}%`
    barraDiv.style.backgroundColor = getSecretariaColor(secretaria)

    progressoDiv.appendChild(barraDiv)

    secretariaDiv.appendChild(headerDiv)
    secretariaDiv.appendChild(progressoDiv)

    // Adicionar aviso se ultrapassar o limite
    if (pontos > LIMITE_PONTOS_SECRETARIA) {
      const excesso = pontos - LIMITE_PONTOS_SECRETARIA
      const custoExcesso = excesso * CUSTO_POR_PONTO

      const avisoDiv = document.createElement('div')
      avisoDiv.className = 'secretaria-aviso'
      avisoDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i> Excesso: ${excesso} pontos (R$ ${custoExcesso.toLocaleString(
        'pt-BR'
      )})`

      secretariaDiv.appendChild(avisoDiv)
      totalCusto += custoExcesso
    } else if (pontos < LIMITE_PONTOS_SECRETARIA) {
      const economia = LIMITE_PONTOS_SECRETARIA - pontos

      const economiaDiv = document.createElement('div')
      economiaDiv.className = 'secretaria-aviso secretaria-economia'
      economiaDiv.innerHTML = `<i class="fas fa-check-circle me-1"></i> Economia: ${economia} pontos`

      secretariaDiv.appendChild(economiaDiv)
    }

    reportContent.appendChild(secretariaDiv)
  })

  // Adicionar resumo geral
  const resumoDiv = document.createElement('div')
  resumoDiv.className = 'mt-3 pt-2 border-top'

  resumoDiv.innerHTML = `
    <div class="d-flex justify-content-between align-items-center">
      <span><strong>Total Geral:</strong></span>
      <span><strong>${totalGeralPontos} pontos</strong></span>
    </div>
  `

  if (totalCusto > 0) {
    resumoDiv.innerHTML += `
      <div class="d-flex justify-content-between align-items-center text-danger mt-1">
        <span>Custo Adicional:</span>
        <span>R$ ${totalCusto.toLocaleString('pt-BR')}</span>
      </div>
    `
  }

  reportContent.appendChild(resumoDiv)
}

// Reiniciar a simulação
function resetSimulation() {
  if (!confirm('Tem certeza que deseja limpar todos os dados da simulação?')) {
    return
  }

  nodes = []
  links = []
  i = 0

  // Limpar SVG
  g.selectAll('.node').remove()
  g.selectAll('.link').remove()

  // Resetar listas e selects
  updateNodeList()
  updateNodeSelects()
  updateReport()

  // Resetar campos
  searchInput.value = ''
  nodeCargo.value = ''
  nodeSecretaria.value = ''
  nodeHierarchy.value = 5
  document.getElementById('hierarchyValue').textContent = '5'

  // Resetar a simulação
  simulation.nodes(nodes)
  simulation.force('link').links(links)
  simulation.alpha(1).restart()
}

// Funções para arrastar nós
function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

function dragged(event, d) {
  d.fx = event.x
  d.fy = event.y
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null
}

// Redimensionar o grafo quando a janela for redimensionada
window.addEventListener('resize', () => {
  svg.attr('width', '100%').attr('height', '100%')
})

// Mostra uma prévia da posição do novo nó com base no nível hierárquico selecionado
function previewHierarchy() {
  // Se existir um nó preview, remove-o
  g.selectAll('.node-preview').remove()

  const hierarchy = parseInt(nodeHierarchy.value)
  const secretaria = nodeSecretaria.value

  if (!secretaria) return

  // Criar um nó de preview para mostrar onde o novo nó ficaria
  const previewNode = g
    .append('g')
    .attr('class', 'node-preview')
    .attr('transform', `translate(${width / 2},${height / 3 - hierarchy * 30})`)
    .style('opacity', 0.6)

  previewNode
    .append('circle')
    .attr('r', nodeRadius)
    .attr('fill', getSecretariaColor(secretaria))
    .attr('stroke', colors.node.stroke)
    .attr('stroke-width', Math.max(1, hierarchy / 5))
    .attr('stroke-dasharray', '5,5')

  previewNode
    .append('text')
    .attr('dy', '.3em')
    .attr('text-anchor', 'middle')
    .text('Novo nó')
    .style('font-size', '12px')
    .style('fill', '#ffffff')
    .style('text-shadow', '0px 0px 2px rgba(0,0,0,0.7)')

  previewNode
    .append('text')
    .attr('dy', -nodeRadius - 5)
    .attr('text-anchor', 'middle')
    .text(hierarchy)
    .style('font-size', '10px')
    .style('font-weight', 'bold')
    .style('fill', '#333')

  // Após 2 segundos, remover o preview
  setTimeout(() => {
    previewNode.transition().duration(500).style('opacity', 0).remove()
  }, 2000)
}

// Função para reorganizar todas as conexões do grafo
function reorganizarTodasConexoes() {
  // Se a auto-organização estiver desativada, perguntar ao usuário se deseja continuar
  if (!autoOrganize) {
    if (
      !confirm(
        'A auto-organização está desativada. Deseja reorganizar todas as conexões mesmo assim?'
      )
    ) {
      return
    }
  }

  // Obter todas as secretarias presentes no grafo
  const secretarias = [...new Set(nodes.map(node => node.secretaria))]

  // Para cada secretaria, reorganizar suas conexões
  secretarias.forEach(secretaria => {
    reorganizarConexoesSecretaria(secretaria)
  })

  // Atualizar a visualização
  update()

  // Exibir mensagem de confirmação
  console.log(
    'Todas as conexões foram reorganizadas, mantendo as conexões manuais existentes.'
  )

  // Exibir resumo de conexões
  const conexoesAutomaticas = links.filter(link => link.type === 'auto').length
  const conexoesManuais = links.filter(link => link.type === 'manual').length

  console.log(
    `Resumo de conexões: ${conexoesAutomaticas} automáticas, ${conexoesManuais} manuais.`
  )
}

// Adiciona uma legenda para identificar os tipos de conexões
function adicionarLegenda() {
  // Remove qualquer legenda existente
  svg.selectAll('.legend').remove()

  // Adiciona a legenda
  const legend = svg
    .append('g')
    .attr('class', 'legend')
    .attr('transform', 'translate(20, 20)')

  // Título da legenda
  legend
    .append('text')
    .attr('x', 0)
    .attr('y', 0)
    .attr('font-weight', 'bold')
    .style('fill', isDarkMode ? '#ffffff' : '#333333')
    .text('Tipos de Conexões:')

  // Conexão automática
  legend
    .append('line')
    .attr('x1', 0)
    .attr('y1', 25)
    .attr('x2', 30)
    .attr('y2', 25)
    .attr('stroke', isDarkMode ? colors.link.dark : colors.link.light)
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', '5,5')

  legend
    .append('text')
    .attr('x', 40)
    .attr('y', 30)
    .style('fill', isDarkMode ? '#e0e0e0' : '#333333')
    .text('Automática')

  // Conexão manual
  legend
    .append('line')
    .attr('x1', 0)
    .attr('y1', 55)
    .attr('x2', 30)
    .attr('y2', 55)
    .attr('stroke', isDarkMode ? '#90b2e5' : '#4a90e2')
    .attr('stroke-width', 2)

  legend
    .append('text')
    .attr('x', 40)
    .attr('y', 60)
    .style('fill', isDarkMode ? '#e0e0e0' : '#333333')
    .text('Manual')

  // Adicionando um fundo para a legenda para melhor legibilidade
  const box = legend.node().getBBox()

  legend
    .insert('rect', ':first-child')
    .attr('x', box.x - 10)
    .attr('y', box.y - 10)
    .attr('width', box.width + 20)
    .attr('height', box.height + 20)
    .attr('rx', 5)
    .attr('ry', 5)
    .attr(
      'fill',
      isDarkMode ? 'rgba(30, 30, 30, 0.7)' : 'rgba(255, 255, 255, 0.7)'
    )
    .attr('stroke', isDarkMode ? '#444' : '#ddd')
    .attr('stroke-width', 1)
}

// Adicionar função para salvar o organograma atual
function salvarOrganograma() {
  // Criar objeto com todos os dados do organograma
  const dadosOrganograma = {
    nodes: nodes.map(node => ({
      id: node.id,
      nome: node.nome,
      cargo: node.cargo,
      secretaria: node.secretaria,
      hierarchy: node.hierarchy
    })),
    links: links.map(link => ({
      source: link.source.id,
      target: link.target.id,
      type: link.type || 'auto',
      value: link.value || 1
    }))
  }

  // Solicitar um nome para o organograma
  const nomeOrganograma = prompt(
    'Digite um nome para este organograma:',
    'Organograma ' + new Date().toLocaleDateString()
  )

  if (!nomeOrganograma) return // Usuário cancelou

  // Adicionar timestamp
  dadosOrganograma.nome = nomeOrganograma
  dadosOrganograma.timestamp = new Date().toISOString()

  // Salvar no localStorage
  try {
    // Obter organogramas salvos anteriormente
    const organogramasSalvos = JSON.parse(
      localStorage.getItem('organogramas') || '[]'
    )

    // Adicionar o novo
    organogramasSalvos.push(dadosOrganograma)

    // Salvar de volta no localStorage
    localStorage.setItem('organogramas', JSON.stringify(organogramasSalvos))

    alert(`Organograma "${nomeOrganograma}" salvo com sucesso!`)

    // Atualizar a lista de organogramas
    atualizarListaOrganogramas()
  } catch (error) {
    console.error('Erro ao salvar organograma:', error)
    alert(
      'Erro ao salvar o organograma. Verifique o console para mais detalhes.'
    )
  }
}

// Função para carregar um organograma salvo
function carregarOrganograma(index) {
  try {
    // Obter organogramas salvos
    const organogramasSalvos = JSON.parse(
      localStorage.getItem('organogramas') || '[]'
    )

    if (!organogramasSalvos[index]) {
      alert('Organograma não encontrado!')
      return
    }

    const organograma = organogramasSalvos[index]

    // Confirmar carregamento (isso substituirá o organograma atual)
    if (
      !confirm(
        `Tem certeza que deseja carregar o organograma "${organograma.nome}"? Isso substituirá o organograma atual.`
      )
    ) {
      return
    }

    // Limpar organograma atual
    nodes = []
    links = []
    g.selectAll('.node').remove()
    g.selectAll('.link').remove()

    // Carregar nós
    organograma.nodes.forEach(nodeData => {
      const newNode = {
        id: nodeData.id,
        nome: nodeData.nome,
        cargo: nodeData.cargo,
        secretaria: nodeData.secretaria,
        hierarchy: nodeData.hierarchy,
        x: width / 2 + (Math.random() - 0.5) * 100,
        y: height / 2 + (Math.random() - 0.5) * 100
      }

      nodes.push(newNode)
    })

    // Contador de IDs para continuar de onde parou
    const maxId = nodes.reduce((max, node) => {
      const idNum = parseInt(node.id.replace('user-', ''))
      return Math.max(max, idNum)
    }, 0)

    i = maxId + 1

    // Carregar links (precisa fazer em duas etapas para garantir que todos os nós já estejam carregados)
    organograma.links.forEach(linkData => {
      const source = nodes.find(node => node.id === linkData.source)
      const target = nodes.find(node => node.id === linkData.target)

      if (source && target) {
        links.push({
          source,
          target,
          type: linkData.type,
          value: linkData.value
        })
      }
    })

    // Atualizar a interface
    updateNodeList()
    updateNodeSelects()
    update()

    alert(`Organograma "${organograma.nome}" carregado com sucesso!`)
  } catch (error) {
    console.error('Erro ao carregar organograma:', error)
    alert(
      'Erro ao carregar o organograma. Verifique o console para mais detalhes.'
    )
  }
}

// Função para atualizar a lista de organogramas salvos
function atualizarListaOrganogramas(filtro = '') {
  const container = document.getElementById('organogramasSalvos')
  if (!container) return

  try {
    const organogramasSalvos = JSON.parse(
      localStorage.getItem('organogramas') || '[]'
    )

    // Filtrar organogramas se um termo de pesquisa foi fornecido
    const organogramasFiltrados = filtro
      ? organogramasSalvos.filter(
          org =>
            org.nome.toLowerCase().includes(filtro.toLowerCase()) ||
            org.nodes.some(
              node =>
                node.nome.toLowerCase().includes(filtro.toLowerCase()) ||
                node.cargo.toLowerCase().includes(filtro.toLowerCase()) ||
                node.secretaria.toLowerCase().includes(filtro.toLowerCase())
            )
        )
      : organogramasSalvos

    if (organogramasFiltrados.length === 0) {
      container.innerHTML = filtro
        ? `<div class="text-muted small p-3">Nenhum organograma encontrado para "${filtro}"</div>`
        : '<div class="text-muted small p-3">Nenhum organograma salvo</div>'
      return
    }

    // Limpar conteúdo
    container.innerHTML = ''

    // Adicionar cada organograma filtrado
    organogramasFiltrados.forEach((org, index) => {
      const originalIndex = organogramasSalvos.indexOf(org) // Índice original para carregar/excluir
      const data = new Date(org.timestamp).toLocaleDateString()
      const numNos = org.nodes.length

      const orgItem = document.createElement('div')
      orgItem.className =
        'org-item d-flex justify-content-between align-items-center p-2 border-bottom'

      const infoDiv = document.createElement('div')
      infoDiv.innerHTML = `
        <div class="fw-bold">${org.nome}</div>
        <div class="small text-muted">${data} - ${numNos} nós</div>
      `

      const botoesDiv = document.createElement('div')

      // Botão Carregar
      const btnCarregar = document.createElement('button')
      btnCarregar.className = 'btn btn-sm btn-outline-primary me-1'
      btnCarregar.innerHTML = '<i class="fas fa-upload"></i>'
      btnCarregar.title = 'Carregar este organograma'
      btnCarregar.addEventListener('click', () =>
        carregarOrganograma(originalIndex)
      )

      // Botão Excluir
      const btnExcluir = document.createElement('button')
      btnExcluir.className = 'btn btn-sm btn-outline-danger'
      btnExcluir.innerHTML = '<i class="fas fa-trash"></i>'
      btnExcluir.title = 'Excluir este organograma'
      btnExcluir.addEventListener('click', () =>
        excluirOrganograma(originalIndex)
      )

      botoesDiv.appendChild(btnCarregar)
      botoesDiv.appendChild(btnExcluir)

      orgItem.appendChild(infoDiv)
      orgItem.appendChild(botoesDiv)

      container.appendChild(orgItem)
    })
  } catch (error) {
    console.error('Erro ao atualizar lista de organogramas:', error)
    container.innerHTML =
      '<div class="text-danger p-3">Erro ao carregar organogramas salvos</div>'
  }
}

// Função para excluir um organograma salvo
function excluirOrganograma(index) {
  try {
    const organogramasSalvos = JSON.parse(
      localStorage.getItem('organogramas') || '[]'
    )

    if (!organogramasSalvos[index]) {
      alert('Organograma não encontrado!')
      return
    }

    const nome = organogramasSalvos[index].nome

    if (!confirm(`Tem certeza que deseja excluir o organograma "${nome}"?`)) {
      return
    }

    // Remover o organograma
    organogramasSalvos.splice(index, 1)

    // Salvar de volta no localStorage
    localStorage.setItem('organogramas', JSON.stringify(organogramasSalvos))

    // Atualizar a lista
    atualizarListaOrganogramas()

    alert(`Organograma "${nome}" excluído com sucesso!`)
  } catch (error) {
    console.error('Erro ao excluir organograma:', error)
    alert(
      'Erro ao excluir o organograma. Verifique o console para mais detalhes.'
    )
  }
}
