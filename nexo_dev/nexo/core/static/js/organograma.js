// organograma.js

// Variáveis globais
const width = 1024;
const height = 600;
let originalData = null;
let filteredData = null;
let root;
let i = 0; // Contador para IDs
let container, svg, g, tooltip;
let zoomBehavior;

// Seleção do elemento atual para detalhes
let selectedNode = null;

// Cores e estilos
const colors = {
  node: {
    default: '#f8fafd',
    expanded: '#e9f0f9',
    hover: '#e9f0f9',
    stroke: '#d1d9e6'
  },
  text: '#333333',
  link: '#a4c5f4'
};

// Inicialização da visualização
document.addEventListener('DOMContentLoaded', function() {
  // Configurar container e área de visualização
  container = d3.select('#organogramaContainer');
  
  // Adicionar opções de zoom/expandir/colapsar
  const controls = container.append('div')
    .attr('class', 'organograma-controls');
  
  // Botão para expandir todos os nós
  const expandAllBtn = controls.append('button')
    .attr('id', 'expandAllBtn')
    .attr('class', 'btn btn-sm btn-outline-primary me-2')
    .on('click', function() {
      if (root) {
        expandAll(root);
        update(root);
        
        // Reajusta o zoom quando expandir todos para garantir que caiba na tela
        setTimeout(() => {
          // Determina o nível de zoom com base na profundidade máxima
          const maxDepth = getMaxVisibleDepth(root);
          const scale = Math.max(0.5, 0.9 - (maxDepth * 0.07)); // Reduz o zoom conforme aumenta a profundidade
          
          const initialTransform = d3.zoomIdentity
            .translate(width / 3.5, height / 3)
            .scale(scale);
          svg.call(zoomBehavior.transform, initialTransform);
        }, 600); // Aguarda a animação de expansão terminar
      }
    });
  
  expandAllBtn.append('i')
    .attr('class', 'fas fa-expand-arrows-alt me-1');
  
  expandAllBtn.append('span')
    .text('Expandir Todos');
  
  // Botão para colapsar todos os nós
  const collapseBtn = controls.append('button')
    .attr('id', 'collapseBtn')
    .attr('class', 'btn btn-sm btn-outline-primary me-2')
    .on('click', function() {
      if (root) {
        collapseAll(root);
        update(root);
      }
    });
  
  collapseBtn.append('i')
    .attr('class', 'fas fa-compress-arrows-alt me-1');
  
  collapseBtn.append('span')
    .text('Recolher Todos');
  
  // Botão para resetar zoom
  const resetBtn = controls.append('button')
    .attr('id', 'resetBtn')
    .attr('class', 'btn btn-sm btn-outline-primary')
    .on('click', function() {
      if (svg) {
        svg.transition()
          .duration(750)
          .call(zoomBehavior.transform, d3.zoomIdentity.translate(width / 3.5, height / 3).scale(0.75));
      }
    });
  
  resetBtn.append('i')
    .attr('class', 'fas fa-sync me-1');
  
  resetBtn.append('span')
    .text('Resetar Zoom');
  
  // Adicionar tooltip
  tooltip = container.append('div')
    .attr('class', 'organograma-tooltip')
    .style('opacity', 0);
  
  // Criar SVG
  svg = container.append('svg')
  .attr('width', '100%')
  .attr('height', '100%')
  .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet');
  
  // Criar grupo para os nós
  g = svg.append('g')
    .attr('class', 'organograma-group');
  
  // Configurar zoom
  zoomBehavior = d3.zoom()
    .scaleExtent([0.1, 3])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
    });
  
  svg.call(zoomBehavior);

  // Define o layout da árvore com D3 - USANDO FLEXTREE
const treeLayout = d3
  .tree()
    .nodeSize([100, 300])  // [altura, largura] - Aumentando o espaçamento horizontal
    .separation((a, b) => 2);  // Separação entre nós - Aumentando para dar mais espaço
    
  // Tornando treeLayout acessível globalmente
  window.treeLayout = treeLayout;

  // Função para transformar os dados no formato hierárquico
  function transformData(data) {
    console.log("Transformando dados para o organograma:", data);
    
    // Função auxiliar para encontrar o cargo de maior nível
    function getCargoMaiorNivel(cargos) {
        if (!cargos || !cargos.length) return null;
        return cargos.reduce((maior, atual) => {
            return (atual.nivel > maior.nivel) ? atual : maior;
        }, cargos[0]);
    }
    
    // Função para criar um nó do organograma
    function createNode(unidade) {
        const cargoMaiorNivel = getCargoMaiorNivel(unidade.cargos);
        return {
            nome: unidade.nome,
            codigo: unidade.codigo,
            cargo: cargoMaiorNivel ? `${cargoMaiorNivel.tipo} ${cargoMaiorNivel.nivel}` : "Sem cargo",
            secretaria: unidade.sigla || "",
            tipo_unidade: unidade.tipo_unidade || "",
            nivel: cargoMaiorNivel ? cargoMaiorNivel.nivel : 0,
            cargos: unidade.cargos || [],
            valores: unidade.valores || { valor_total: 0, pontos_total: 0 },
            children: []
        };
    }
    
    // Processar os dados recebidos da API
    if (!data || !data.data || !Array.isArray(data.data)) {
        console.error("Dados inválidos recebidos da API");
        return null;
    }
    
    // Criar nós para todas as unidades
    const nodesMap = new Map();
    data.data.forEach(unidade => {
        const node = createNode(unidade);
        nodesMap.set(unidade.codigo, node);
        
        // Processar filhos recursivamente
        if (unidade.children && Array.isArray(unidade.children)) {
            processChildren(unidade.children, node);
        }
    });
    
    // Função recursiva para processar filhos
    function processChildren(children, parentNode) {
        children.forEach(child => {
            const childNode = createNode(child);
            parentNode.children.push(childNode);
            
            if (child.children && Array.isArray(child.children)) {
                processChildren(child.children, childNode);
            }
        });
        
        // Ordenar filhos pelo nível do cargo (decrescente)
        parentNode.children.sort((a, b) => b.nivel - a.nivel);
    }
    
    // Encontrar a raiz (ou criar uma raiz artificial se houver múltiplas raízes)
    if (data.data.length === 0) {
        return {
            nome: "Organograma Vazio",
            cargo: "",
            secretaria: "",
            codigo: "EMPTY",
            children: []
        };
    } else if (data.data.length === 1) {
        return nodesMap.get(data.data[0].codigo);
    } else {
        // Criar raiz artificial para múltiplas raízes
        const rootNode = {
            nome: "Ministério do Planejamento e Orçamento - MPO",
            cargo: "Organograma Completo",
            secretaria: "MPO",
            codigo: "ROOT",
            children: data.data.map(unidade => nodesMap.get(unidade.codigo))
        };
        
        // Ordenar raízes pelo nível do cargo (decrescente)
        rootNode.children.sort((a, b) => b.nivel - a.nivel);
        
        return rootNode;
    }
}
  
  // Carrega os dados do organograma
  try {
    // Verificar se temos dados embutidos no HTML
    if (window.organogramaData) {
      console.log("Usando dados embutidos no HTML");
      const data = window.organogramaData;
      processarDados(data);
    } else {
      // Fallback para dados básicos
      console.error("Dados do organograma não encontrados no template!");
      exibirErro("Não foi possível carregar os dados do organograma. Tente atualizar a página.");
    }
  } catch (err) {
    console.error('Erro ao processar dados do organograma:', err);
    exibirErro("Ocorreu um erro ao processar os dados: " + err.message);
  }

  function processarDados(data) {
    // Armazena os dados originais para futuras filtragens
    originalData = data;
    console.log("Dados originais carregados:", originalData);
    
    // Processar os dados para o formato esperado pelo organograma
    const hierarchicalData = transformData(data);
    filteredData = hierarchicalData;
    
    // Cria a hierarquia dos dados
    root = d3.hierarchy(hierarchicalData);

    // Define posições iniciais para transição
    root.x0 = 0;
    root.y0 = 0;

    // Colapsa todos os nós exceto o primeiro nível
    if (root.children) {
      root.children.forEach(child => collapseAtLevel(child, 0));
    }

    // Renderiza a árvore
    update(root);

    // Centraliza inicialmente com muito espaço à direita para a expansão
    const initialTransform = d3.zoomIdentity
      .translate(10, height / 2) // Posição extrema à esquerda para dar espaço máximo à direita
      .scale(0.4);  // Reduzindo o zoom inicial para acomodar mais níveis
    svg.call(zoomBehavior.transform, initialTransform);
  }

  function exibirErro(mensagem) {
    // Exibe mensagem de erro no container
    container.append('div')
      .attr('class', 'alert alert-danger m-3')
      .html(`<i class='fas fa-exclamation-circle me-2'></i>${mensagem}`);
  }
});

// Função principal de atualização do organograma
function update(source) {
  // Calcula o layout da árvore
  const duration = 500; // duração da transição em ms

  // Aplica o layout da árvore
  window.treeLayout(root);

  // NOVO LAYOUT HORIZONTAL:
  // Este é um passo crucial para garantir um layout horizontal adequado
  const horizontalSpacing = 300; // Espaçamento horizontal entre níveis

  root.each(d => {
    // Para layout horizontal: y se torna x, e x se torna y
    // Para cada nível de profundidade, movemos mais para a direita
    const oldX = d.x;
    const oldY = d.y;
    
    // Na direção horizontal (antes era a coordenada y):
    d.x = oldY; 
    
    // Na direção vertical (antes era a coordenada x):
    d.y = oldX;
    
    // Forçar distância fixa entre níveis
    d.x = d.depth * horizontalSpacing;
  });

  // Selecione todos os nós
  const nodes = g
    .selectAll('g.node')
    .data(root.descendants(), d => d.id || (d.id = ++i));

  // ENTRADA: Cria novos nós
  const nodeEnter = nodes
    .enter()
    .append('g')
    .attr(
      'class',
      d =>
        `node ${d.children || d._children ? 'node--internal' : 'node--leaf'} ${
          d._children ? 'collapsed' : ''
        }`
    )
    .attr('transform', d => `translate(${source.x0},${source.y0})`)
    .style('opacity', 0)
    .on('click', (event, d) => {
      // Prevenimos a propagação do evento para evitar que o zoom seja acionado
      event.stopPropagation();
      
      // Registramos o tempo do último clique para prevenir duplo clique
      const agora = new Date().getTime();
      const ultimoClique = d.ultimoClique || 0;
      const intervaloClique = 300; // milissegundos para considerar um duplo clique
      
      // Se for um duplo clique, não fazemos nada (prevenindo zoom acidental)
      if (agora - ultimoClique < intervaloClique) {
        event.preventDefault();
        return;
      }
      
      // Armazenamos o tempo deste clique
      d.ultimoClique = agora;
      
      toggleChildren(d);
      update(d);
    })
    .on('mouseover', (event, d) => {
      // Mostra tooltip com secretaria
      tooltip.transition().duration(200).style('opacity', 1);

      // Obtém a posição do nó no documento
      const nodeElement = event.currentTarget;
      const nodeRect = nodeElement.getBoundingClientRect();
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
      
      // Posicionamento melhorado do tooltip
      let tooltipX, tooltipY;
      
      // Posicionar o tooltip à direita do nó
      tooltipX = nodeRect.left + scrollLeft + nodeRect.width + 30; // 30px de distância do nó
      tooltipY = nodeRect.top + scrollTop - 150; // Um pouco acima do centro do nó
      
      // Assegurar que o tooltip não saia da tela
      const viewportWidth = window.innerWidth;
      const tooltipWidth = 300; // Estimativa da largura do tooltip
      
      if (tooltipX + tooltipWidth > viewportWidth) {
        // Se for sair pela direita, posicionar à esquerda do nó
        tooltipX = nodeRect.left + scrollLeft - tooltipWidth - 30;
      }
      
      // Garantir que não saia pelo topo
      if (tooltipY < 0) {
        tooltipY = 10;
      }
      
      // Formatar informações do cargo
      let cargoInfo = '';
      let pontosInfo = '';
      let valorInfo = '';
      let quantidadeInfo = '';
      let gastoTotalInfo = '';
      let denominacaoInfo = '';
      
      try {
        // Buscar a denominação da unidade na tabela core_unidade, se disponível
        if (originalData && originalData.core_unidade && d.data.codigo) {
          const unidade = originalData.core_unidade.find(
            u => u.codigo_unidade === d.data.codigo
          );
          
          if (unidade && unidade.denominacao) {
            denominacaoInfo = unidade.denominacao;
          }
        }
        
        // Buscar informações do cargo na tabela core_cargosiorg
        if (d.data.cargo) {
          cargoInfo = d.data.cargo;
          
          // Buscar informações diretas na tabela para esse cargo
          if (originalData && originalData.core_cargosiorg) {
            console.log(`Buscando valor para cargo: ${d.data.cargo}`);
            
            // Abordagem direta: buscar exatamente o texto do cargo
            for (const c of originalData.core_cargosiorg) {
              if (c.cargo === d.data.cargo) {
                console.log(`Correspondência EXATA encontrada: ${c.cargo} = ${c.valor}`);
                pontosInfo = c.nivel || '';
                valorInfo = parseFloat(c.valor) || 0;
                
                // Formatar valor como moeda
                valorInfo = new Intl.NumberFormat('pt-BR', { 
          style: 'currency', 
          currency: 'BRL' 
                }).format(valorInfo);
                
                // Calcular gasto total se tivermos quantidade
                if (d.data.quantidade) {
                  quantidadeInfo = d.data.quantidade;
                  // Extrair apenas o valor numérico do valorInfo
                  const valorLimpo = valorInfo
                    .replace('R$', '')
                    .replace(/\./g, '')
                    .replace(',', '.')
                    .trim();
                  const valorNumerico = parseFloat(valorLimpo);
                  
                  if (!isNaN(valorNumerico)) {
                    const gastoTotal = valorNumerico * quantidadeInfo;
                    gastoTotalInfo = new Intl.NumberFormat('pt-BR', { 
                      style: 'currency', 
                      currency: 'BRL' 
                    }).format(gastoTotal);
                    console.log(`Gasto total: ${valorNumerico} × ${quantidadeInfo} = ${gastoTotalInfo}`);
                  }
                }
                
                break;
              }
            }
            
            // Se não encontramos uma correspondência exata, defina o valor como zero
            if (!valorInfo) {
              valorInfo = 'R$ 0,00';
            }
          }
        }
      } catch (error) {
        console.error("Erro ao processar informações do cargo:", error);
        cargoInfo = d.data.cargo || 'Cargo não especificado';
      }
      
      tooltip
        .html(
          `
        <div class="tooltip-title">${d.data.nome}</div>
        ${denominacaoInfo ? 
          `<div class="tooltip-denominacao">${denominacaoInfo}</div>` : ''
        }
        <div class="tooltip-cargo">${d.data.cargo || 'Cargo não especificado'}</div>
        <div class="tooltip-field">
          <span class="tooltip-label">Sigla:</span>
          <span class="tooltip-value">${d.data.secretaria || d.data.sigla || 'Não especificada'}</span>
        </div>
        <div class="tooltip-field">
          <span class="tooltip-label">Tipo:</span>
          <span class="tooltip-value">${d.data.tipo_unidade || 'Não especificado'}</span>
        </div>
        <div class="tooltip-field">
            <span class="tooltip-label">Nível:</span>
          <span class="tooltip-value">${d.data.nivel || ''}</span>
        </div>
        ${calcularEExibirPontos(d.data)}
        ${calcularEExibirValor(d.data)}
        <div class="tooltip-field">
          <span class="tooltip-label">Quantidade:</span>
          <span class="tooltip-value">${d.data.quantidade || '1'}</span>
        </div>
        ${calcularEExibirGastoTotal(d.data)}
        <div class="tooltip-field">
            <span class="tooltip-label">Código:</span>
          <span class="tooltip-value">${d.data.codigo || ''}</span>
        </div>
        ${d.data.cargos && d.data.cargos.length > 0 ? 
          `<div style="border-top: 1px solid #e5e7eb; padding-top: 10px; margin-top: 10px;">
            <div style="font-size: 12px; font-weight: 600; color: #6b7280; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px;">
              Detalhes dos Cargos
            </div>
            <div style="display: flex; flex-direction: column; gap: 4px;">
              ${d.data.cargos.map(cargo => 
                `<div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0;">
                  <span style="background: #f3f4f6; color: #374151; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;">${cargo.tipo} ${cargo.nivel}</span>
                  <span style="background: #6b7280; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: 600; min-width: 20px; text-align: center;">${cargo.quantidade || 1}</span>
                </div>`
              ).join('')}
            </div>
          </div>` : ''
        }
      `
        )
        .style('left', tooltipX + 'px')
        .style('top', tooltipY + 'px');

      // Destaca o nó
      d3.select(event.currentTarget)
        .select('circle')
        .transition()
        .duration(200)
        .attr('r', d => d.depth === 0 ? 18 : 14);
    })
    .on('mouseout', (event, d) => {
      // Esconde tooltip
      tooltip.transition().duration(500).style('opacity', 0);

      // Remove destaque
      d3.select(event.currentTarget)
        .select('circle')
        .transition()
        .duration(200)
        .attr('r', d => d.depth === 0 ? 14 : 10);
    });

  // Adiciona círculos aos novos nós
  nodeEnter
    .append('circle')
    .attr('r', 0)
    .attr('fill', d => {
      // Estilo especial para o nó raiz (MPO)
      if (d.depth === 0) {
        return '#4e73df'; // Cor mais destacada para a raiz
      }
      return d._children ? '#a3bffa' : '#e9f0f9';
    })
    .attr('stroke', d => d.depth === 0 ? '#2c5282' : colors.node.stroke) // Borda destacada para a raiz
    .attr('stroke-width', d => d.depth === 0 ? 3 : 1.5); // Borda mais grossa para a raiz

  // Adiciona texto para o nome
  nodeEnter
    .append('text')
    .attr('class', 'label-nome')
    .attr('dy', -18)
    .attr('x', 0)
    .attr('text-anchor', 'middle')
    .text(d => d.data.secretaria || d.data.sigla || '') // Mostrar apenas a sigla
    .style('fill-opacity', 0)
    .style('font-weight', d => d.depth === 0 ? 'bold' : 'normal')
    .style('fill', d => d.depth === 0 ? '#ffffff' : '#333333');

  // Adiciona texto para o cargo
  nodeEnter
    .append('text')
    .attr('class', 'label-cargo')
    .attr('dy', 0)
    .attr('x', 0)
    .attr('text-anchor', 'middle')
    .text(d => d.data.cargo)
    .style('fill-opacity', 0)
    .style('font-size', '11px')
    .style('fill', d => d.depth === 0 ? '#e0e0e0' : '#666');

  // ATUALIZAÇÃO: Transição para novas posições
  const nodeUpdate = nodeEnter
    .merge(nodes)
    .transition()
    .duration(duration)
    .attr('transform', d => `translate(${d.x},${d.y})`)
    .style('opacity', 1);

  // Atualiza aparência dos nós
  nodeUpdate
    .select('circle')
    .transition()
    .duration(duration)
    .attr('r', d => d.depth === 0 ? 14 : 10) // Raiz maior
    .attr('fill', d => {
      if (d.depth === 0) {
        return '#4e73df'; // Cor destacada para a raiz
      }
      return d._children ? '#a3bffa' : '#e9f0f9';
    })
    .attr('stroke', d => d.depth === 0 ? '#2c5282' : colors.node.stroke)
    .attr('stroke-width', d => d.depth === 0 ? 3 : 1.5);

  // Atualiza texto
  nodeUpdate.selectAll('text').style('fill-opacity', 1);

  // SAÍDA: Remove nós que não são mais necessários
  const nodeExit = nodes
    .exit()
    .transition()
    .duration(duration)
    .attr('transform', d => `translate(${source.x},${source.y})`)
    .style('opacity', 0)
    .remove();

  // Reduz tamanho dos círculos na saída
  nodeExit.select('circle').attr('r', 0);

  // Desvanece texto na saída
  nodeExit.selectAll('text').style('fill-opacity', 0);

  // Atualiza os links (conexões entre nós)
  const links = g.selectAll('path.link').data(root.links(), d => d.target.id);

  // Função para gerar links horizontais tipo L
  function generateLink(d) {
    const sourceX = d.source.x;
    const sourceY = d.source.y;
    const targetX = d.target.x;
    const targetY = d.target.y;
    
    // Link tipo L para organograma horizontal com mais espaço
    // Voltamos para o formato anterior com melhores parâmetros
    return `M${sourceX},${sourceY}
            H${sourceX + (targetX - sourceX) * 0.7}
            V${targetY}
            H${targetX}`;
  }

  // ENTRADA: Adiciona novos links
  const linkEnter = links
    .enter()
    .append('path')
    .attr('class', 'link')
    .attr('d', d => {
      const o = { x: source.x0, y: source.y0 };
      return generateLink({
        source: o,
        target: o
      });
    })
    .attr('fill', 'none')
    .attr('stroke', d => d.target.depth === 1 ? '#4c7dd4' : colors.link)
    .attr('stroke-width', d => d.target.depth === 1 ? 2.5 : 2)
    .attr('stroke-opacity', 0.8);

  // ATUALIZAÇÃO: Transição para novas posições
  linkEnter.merge(links)
    .transition()
    .duration(duration)
    .attr('d', generateLink);

  // SAÍDA: Remove links que não são mais necessários
  links
    .exit()
    .transition()
    .duration(duration)
    .attr('d', d => {
      const o = { x: source.x, y: source.y };
      return generateLink({
        source: o,
        target: o
      });
    })
    .remove();

  // Armazena as posições atuais para a próxima transição
  root.descendants().forEach(d => {
    d.x0 = d.x;
    d.y0 = d.y;
  });
}

// Função para expandir um nó e carregar seus filhos a partir do grafo
function expandLoadChildren(d) {
  // Se já tem filhos, não precisa carregar
  if (d.children || !d.data || !d.data.codigo) return;
  
  // Carrega os filhos a partir do grafo usando originalData
  const codigo = d.data.codigo;
  
  try {
    if (!originalData || !originalData.core_unidadecargo) {
      console.error("Dados originais não disponíveis!");
      return;
    }
    
    console.log(`Carregando filhos para ${d.data.secretaria || d.data.sigla || 'Nó'} (${codigo}) - grafo: ${d.data.grafo}`);
    
    // Encontra todas as unidades que têm esse código como parte do grafo
    const filhos = [];
    
    originalData.core_unidadecargo.forEach(unit => {
      // Verifica apenas unidades com grafo e código
      if (!unit.grafo || !unit.codigo_unidade) return;
      
      // Não processar a própria unidade
      if (unit.codigo_unidade === codigo) return;
        
        // Verifica se o grafo contém o código do pai
        const codigosGrafo = unit.grafo.split('-');
        
      // Para ser um filho direto, o código do pai deve estar no grafo
        const indexPai = codigosGrafo.indexOf(codigo);
      
      if (indexPai >= 0) {
        // Verificamos se é filho direto - o pai deve ser o elemento imediatamente anterior
        const ehFilhoDireto = (indexPai === codigosGrafo.length - 2);
        
        if (ehFilhoDireto) {
          console.log(`Encontrado filho: ${unit.sigla || 'Sem sigla'} (${unit.codigo_unidade}) para pai: ${codigo}`);
          
          // Esta unidade é filha direta
          const node = {
            nome: unit.denominacao_unidade || "Unidade sem nome",
            codigo: unit.codigo_unidade,
            cargo: unit.tipo_cargo && unit.categoria && unit.nivel ? 
                   `${unit.tipo_cargo} ${unit.categoria} ${unit.nivel}` : "Sem cargo",
            secretaria: unit.sigla || "",
            sigla: unit.sigla || "",
            tipo_unidade: unit.tipo_unidade || "",
            nivel: unit.nivel || 0,
            grafo: unit.grafo || "",
            // Garantir que todos os nós tenham os campos necessários
            pontos: unit.pontos || 0,
            valor_unitario: unit.valor_unitario || 0,
            quantidade: unit.quantidade || 1,
            gasto_total: unit.gasto_total || 0,
            children: [] // Importante para permitir expansão futura
          };
          
          filhos.push(node);
        }
    }
    });
    
    console.log(`Filhos encontrados para ${d.data.secretaria || d.data.sigla || 'Nó'} (${codigo}): ${filhos.length}`);
    
    // Ordenar filhos com base no nível e sigla
    filhos.sort((a, b) => {
      // Primeiro ordena por nível
      const nivelDiff = (a.nivel || 0) - (b.nivel || 0);
      if (nivelDiff !== 0) return nivelDiff;
      
      // Se os níveis são iguais, ordena por sigla
      return (a.sigla || "").localeCompare(b.sigla || "");
    });
    
    // Se encontrou filhos, adiciona ao nó
    if (filhos.length > 0) {
      d.data.children = filhos;
      // Cria uma nova hierarquia para os filhos e associa ao nó pai
      const tempHierarchy = d3.hierarchy(d.data, node => node.children);
      d.children = tempHierarchy.children;
      
      // Atualizar a profundidade e propriedades pai para todos os filhos
      if (d.children) {
        d.children.forEach(child => {
          // Definir o pai explicitamente
          child.parent = d;
          
          // Atualizar a profundidade
          child.depth = d.depth + 1;
          
          // Verificar se este nó tem mais filhos (para indicar visualmente)
          const childHasChildren = originalData.core_unidadecargo.some(unit => {
            if (!unit.grafo || !unit.codigo_unidade || unit.codigo_unidade === child.data.codigo) return false;
            
            const grafoArr = unit.grafo.split('-');
            // Verificar se o código do filho está no grafo e se ele é o penúltimo código
            return grafoArr.includes(child.data.codigo) && 
                  grafoArr[grafoArr.length - 2] === child.data.codigo;
          });
          
          // Marca visualmente que este nó tem filhos potenciais
          if (childHasChildren) {
            child.data._hasChildren = true;
          }
        });
      }
    } else {
      console.log(`Nenhum filho encontrado para ${d.data.secretaria || d.data.sigla || 'Nó'} (${codigo})`);
    }
  } catch (error) {
    console.error("Erro ao carregar filhos:", error);
  }
}

// Função auxiliar para alternar filhos (expandir/colapsar)
function toggleChildren(d) {
  console.log(`Toggle node: ${d.data.sigla || d.data.nome} (${d.depth})`);
  
  // Primeiro colapsamos TODOS os outros nós em QUALQUER nível
  // Esta é a mudança mais importante - garantir que isso sempre ocorra
  colapsarTodosExceto(root, d);
  
  if (d.children) {
    // Se o nó já está expandido, apenas colapsa
    d._children = d.children;
    d.children = null;
    console.log("Nó colapsado");
  } else {
    // Agora expandimos o nó selecionado
    if (d._children) {
      // Já carregou filhos antes, restaura eles
      d.children = d._children;
      d._children = null;
      console.log("Nó expandido (filhos já carregados)");
    } else {
      // Nunca carregou filhos, tenta carregar do grafo
      expandLoadChildren(d);
      console.log("Nó expandido (carregando novos filhos)");
    }
  }
}

// Função mais robusta para colapsar TODOS exceto o nó selecionado e seus ancestrais
function colapsarTodosExceto(no, exceto) {
  if (!no) return;
  
  console.log(`Verificando colapso: ${no.data.sigla || no.data.nome}`);
  
  // Verificar se o nó atual é o próprio nó selecionado ou um ancestral
  const ehExceto = (no === exceto);
  const ehAncestral = isAncestor(no, exceto);
  
  // Se o nó não é o selecionado NEM ancestral, colapsamos ele
  if (no.children && !ehExceto && !ehAncestral) {
    console.log(`Colapsando: ${no.data.sigla || no.data.nome}`);
    no._children = no.children;
    no.children = null;
  }
  
  // Continua a verificação nos filhos (se existirem)
  if (no.children) {
    no.children.forEach(child => colapsarTodosExceto(child, exceto));
  }
}

// Função auxiliar para verificar se um nó é ancestral de outro
function isAncestor(possibleAncestor, node) {
  // Se o nó não existe, não é ancestral
  if (!node) return false;
  
  // Se o nó é igual ao possível ancestral, é considerado ancestral (ou seja, ele mesmo)
  if (node === possibleAncestor) return true;
  
  // Se o nó não tem pai, chegamos ao topo sem encontrar o ancestral
  if (!node.parent) return false;
  
  // Verificar recursivamente se o pai é o ancestral
  return isAncestor(possibleAncestor, node.parent);
}

// Função para expandir todos os nós
function expandAll(d) {
  if (d._children) {
    d.children = d._children;
    d._children = null;
  }
  
  if (d.children) {
    d.children.forEach(expandAll);
  } else {
    // Se não tem filhos carregados, tenta carregar
    expandLoadChildren(d);
    
    // Se agora tem filhos, expande-os recursivamente
    if (d.children) {
      d.children.forEach(expandAll);
    }
  }
}

// Função para colapsar nós a partir de um certo nível
function collapseAtLevel(d, level = 0) {
  // Se o nó tem filhos e não é o nó raiz (ou está abaixo do nível especificado)
  if (d.children && d.depth > level) {
    d._children = d.children
    d.children = null
  }
  // Se o nó tem filhos e está no nível especificado ou acima, colapsa seus filhos
  else if (d.children) {
    d.children.forEach(child => collapseAtLevel(child, level))
  }
}

// Função para obter a profundidade máxima visível na árvore
function getMaxVisibleDepth(node) {
  if (!node.children) {
    return node.depth;
  }
  
  let maxDepth = node.depth;
  if (node.children) {
    node.children.forEach(child => {
      const childDepth = getMaxVisibleDepth(child);
      if (childDepth > maxDepth) {
        maxDepth = childDepth;
      }
    });
  }
  
  return maxDepth;
}

// Função para colapsar todos os nós, mantendo apenas o nó raiz expandido
function collapseAll(d) {
  if (d.children) {
    // Para cada filho, primeiro colapsa todos os seus descendentes
    d.children.forEach(collapseAll);

    // Depois colapsa o próprio filho (exceto se for o nó raiz)
    if (d.depth > 0) {
      d._children = d.children;
      d.children = null;
    }
  }
}

// Função para aplicar filtros ao organograma
window.aplicarFiltrosOrganograma = function(filtros) {
  console.log("Aplicando filtros:", filtros);
  
  try {
    if (!originalData || !originalData.core_unidadecargo) {
      console.error("Dados originais não disponíveis para filtragem");
      alert("Não foi possível aplicar os filtros. Tente recarregar a página.");
      return;
    }
    
    // Mostrar indicador de carregamento
    const loadingIndicator = document.createElement('div');
    loadingIndicator.id = 'organogramaLoading';
    loadingIndicator.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 1000; text-align: center; background: rgba(255,255,255,0.8); padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1);';
    loadingIndicator.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div><div class="mt-2">Processando filtros...</div>';
    document.getElementById('organogramaContainer').appendChild(loadingIndicator);
    
    // Versão ultra simplificada que processa apenas uma quantidade limitada de unidades
    // MPO é sempre a raiz
    const mpoNode = originalData.core_unidadecargo.find(unit => unit.codigo_unidade === "308804");
    if (!mpoNode) {
      throw new Error("Não foi possível encontrar a unidade raiz (MPO)");
    }
    
    // Estrutura básica com a raiz
    const dadosFiltrados = {
      core_unidadecargo: [mpoNode]
    };
    
    // Limite máximo de unidades para evitar travamento do navegador
    const MAX_UNITS = 100;
    const allUnidades = originalData.core_unidadecargo || [];
    let contador = 0;
    
    // Filtragem simples por sigla, cargo e nível
    for (const unit of allUnidades) {
      if (!unit || unit.codigo_unidade === "308804" || contador >= MAX_UNITS) continue;
      
      let matchSigla = true, matchCargo = true, matchNivel = true;
      
      if (filtros.sigla) {
        const siglaUpper = filtros.sigla.toUpperCase();
        matchSigla = unit.sigla && unit.sigla.toUpperCase().includes(siglaUpper);
      }
      
      if (filtros.cargo) {
        matchCargo = unit.tipo_cargo && unit.tipo_cargo.toUpperCase().includes(filtros.cargo.toUpperCase());
      }
      
      if (filtros.nivel) {
        matchNivel = unit.nivel && unit.nivel.toString() === filtros.nivel;
      }
      
      if (matchSigla && matchCargo && matchNivel) {
        dadosFiltrados.core_unidadecargo.push(unit);
        contador++;
      }
    }
    
    console.log(`Total de unidades filtradas: ${dadosFiltrados.core_unidadecargo.length} (limitado a ${MAX_UNITS})`);
    
    // Reprocessar visualização com dados filtrados
    const hierarchicalData = transformData(dadosFiltrados);
    filteredData = hierarchicalData;
    
    // Resetar visualização
    g.selectAll('*').remove();
    
    // Criar nova hierarquia com os dados filtrados
    root = d3.hierarchy(hierarchicalData);
    
    // Preparar para animação
    root.x0 = 0;
    root.y0 = 0;
    
    // Expandir apenas o primeiro nível
    if (root.children) {
      root.children.forEach(child => {
        if (child.children) {
          child._children = child.children;
          child.children = null;
        }
      });
    }
    
    // Atualizar o organograma
    update(root);
    
    // Centralizar na visualização
    const initialTransform = d3.zoomIdentity
      .translate(width / 3.5, height / 3)
      .scale(0.75);
    svg.call(zoomBehavior.transform, initialTransform);
    
    // Atualizar informações de filtros na UI
    const filtrosAtivos = document.getElementById('filtrosAtivos');
    if (filtrosAtivos) {
      const semFiltros = document.getElementById('semFiltros');
      if (semFiltros) {
        if (filtros.sigla || filtros.cargo || filtros.nivel) {
          semFiltros.textContent = `Estrutura filtrada (${dadosFiltrados.core_unidadecargo.length} unidades)`;
        } else {
          semFiltros.textContent = "Nenhum filtro aplicado";
        }
      }
    }
  } catch (error) {
    console.error("Erro ao aplicar filtros:", error);
    alert("Ocorreu um erro ao aplicar os filtros: " + error.message);
  } finally {
    // Remover indicador de carregamento
    const loadingIndicator = document.getElementById('organogramaLoading');
    if (loadingIndicator) {
      loadingIndicator.remove();
    }
  }
};

// Função para limpar filtros e restaurar organograma original
window.limparFiltrosOrganograma = function() {
    if (!originalData) {
    console.error("Dados originais não disponíveis");
      return;
    }
    
  // Reprocessar visualização com dados originais
    const hierarchicalData = transformData(originalData);
  filteredData = hierarchicalData;
    
  // Resetar visualização
    g.selectAll('*').remove();
    
  // Criar nova hierarquia com os dados originais
    root = d3.hierarchy(hierarchicalData);
    
    // Preparar para animação
    root.x0 = 0;
    root.y0 = 0;
    
  // Expandir apenas o primeiro nível
    if (root.children) {
      root.children.forEach(child => {
        if (child.children) {
          child._children = child.children;
          child.children = null;
        }
      });
    }
    
  // Atualizar o organograma
    update(root);
    
    // Centralizar na visualização
    const initialTransform = d3.zoomIdentity
      .translate(width / 3.5, height / 3)
      .scale(0.75);
    svg.call(zoomBehavior.transform, initialTransform);
    
  console.log("Filtros limpos, organograma restaurado");
};

// Código para garantir compatibilidade entre diferentes versões do template
document.addEventListener('DOMContentLoaded', function() {
  // Tentar encontrar os elementos de filtro em ambas as versões do template
  const filtroSiglaId = document.getElementById('filtroSigla');
  const filtroCargoId = document.getElementById('filtroCargo');
  const filtroNivelId = document.getElementById('filtroNivel');
  const btnAplicarFiltrosId = document.getElementById('aplicarFiltros');
  const btnLimparFiltrosId = document.getElementById('limparFiltros');
  const filtrosAtivos = document.getElementById('filtrosAtivos');
  const semFiltros = document.getElementById('semFiltros');
  
  // Função para atualizar a exibição dos filtros ativos
  function atualizarFiltrosAtivos(filtros) {
    if (!filtrosAtivos || !semFiltros) return;
    
    // Limpa filtros anteriores
    while (filtrosAtivos.children.length > 1) {
      if (filtrosAtivos.lastChild !== semFiltros) {
        filtrosAtivos.removeChild(filtrosAtivos.lastChild);
      }
    }
    
    let temFiltroAtivo = false;
    
    // Adiciona badges para cada filtro ativo
    if (filtros.sigla) {
      adicionarBadgeFiltro('Sigla: ' + filtros.sigla);
      temFiltroAtivo = true;
    }
    if (filtros.cargo) {
      adicionarBadgeFiltro('Cargo: ' + filtros.cargo);
      temFiltroAtivo = true;
    }
    if (filtros.nivel) {
      adicionarBadgeFiltro('Nível: ' + filtros.nivel);
      temFiltroAtivo = true;
    }
    
    // Exibe ou oculta a mensagem "Nenhum filtro aplicado"
    semFiltros.style.display = temFiltroAtivo ? 'none' : 'inline';
  }
  
  // Função para adicionar badge de filtro
  function adicionarBadgeFiltro(texto) {
    const badge = document.createElement('span');
    badge.className = 'badge bg-primary filtro-badge';
    badge.textContent = texto;
    filtrosAtivos.appendChild(badge);
  }
  
  // Se os botões de filtros existirem, configurar os listeners
  if (btnAplicarFiltrosId) {
    console.log("Botão de aplicar filtros encontrado, configurando evento");
    
    btnAplicarFiltrosId.addEventListener('click', function() {
      // Coletar valores dos campos de filtro
      const sigla = filtroSiglaId ? filtroSiglaId.value.trim().toUpperCase() : '';
      const cargo = filtroCargoId ? filtroCargoId.value : '';
      const nivel = filtroNivelId ? filtroNivelId.value : '';
      
      // Construir objeto de filtros
      const filtros = {
        sigla: sigla,
        cargo: cargo,
        nivel: nivel,
        tipoUnidade: ""
      };
      
      // Aplicar filtros
      window.aplicarFiltrosOrganograma(filtros);
      
      // Atualizar badges de filtros ativos
      atualizarFiltrosAtivos(filtros);
    });
  }
  
  // Configurar o botão de limpar filtros
  if (btnLimparFiltrosId) {
    console.log("Botão de limpar filtros encontrado, configurando evento");
    
    btnLimparFiltrosId.addEventListener('click', function() {
      // Limpar os campos de filtro
      if (filtroSiglaId) filtroSiglaId.value = '';
      if (filtroCargoId) filtroCargoId.value = '';
      if (filtroNivelId) filtroNivelId.value = '';
      
      // Aplicar o reset do organograma
      window.limparFiltrosOrganograma();
      
      // Atualizar badges de filtros ativos - reset
      if (semFiltros) {
        semFiltros.style.display = 'inline';
      }
      if (filtrosAtivos) {
        while (filtrosAtivos.children.length > 1) {
          if (filtrosAtivos.lastChild !== semFiltros) {
            filtrosAtivos.removeChild(filtrosAtivos.lastChild);
          }
        }
      }
    });
  }
});

// Função para ajustar o tamanho do SVG quando a janela é redimensionada
function resizeOrganograma() {
  if (!container || !container.node()) return;
  
  // Obter o tamanho da área de visualização disponível
  const containerWidth = container.node().getBoundingClientRect().width;
  // Altura maior para o organograma
  const containerHeight = Math.max(700, window.innerHeight * 0.9);

  if (svg) {
    svg.attr('viewBox', `0 0 ${containerWidth} ${containerHeight}`)
       .attr('height', containerHeight + 'px');
    
    // Atualiza o container para garantir que o organograma seja visível
    container.style('height', containerHeight + 'px');
    
    // Reajusta o zoom para centralizar o organograma
  const initialTransform = d3.zoomIdentity
      .translate(width / 3, height / 3)
      .scale(0.8);
    svg.call(zoomBehavior.transform, initialTransform);
  }
}

// Adiciona evento de redimensionamento
window.addEventListener('resize', resizeOrganograma);

// Chama a função de redimensionamento quando a página carrega
window.addEventListener('load', resizeOrganograma);

// Adicionar CSS para melhorar o estilo do tooltip
document.addEventListener('DOMContentLoaded', function() {
  // Adicionar estilos específicos para o tooltip
  const style = document.createElement('style');
  style.innerHTML = `
    .organograma-tooltip {
      position: absolute;
      padding: 15px;
      background-color: white;
      border-radius: 8px;
      border: 1px solid #d1d9e6;
      box-shadow: 0 4px 8px rgba(0,0,0,0.15);
      pointer-events: none;
      min-width: 280px;
      max-width: 350px;
      z-index: 1000;
      font-size: 0.85rem;
    }
    .tooltip-title {
      font-weight: bold;
      font-size: 1rem;
      margin-bottom: 8px;
      color: #333;
      border-bottom: 1px solid #eee;
      padding-bottom: 5px;
    }
    .tooltip-denominacao {
      font-style: italic;
      margin-bottom: 8px;
      color: #444;
      font-size: 0.9rem;
    }
    .tooltip-cargo {
      font-style: italic;
      margin-bottom: 8px;
      color: #666;
    }
    .tooltip-field {
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
    }
    .tooltip-label {
      font-weight: 600;
      color: #555;
    }
    .tooltip-value {
      color: #0066cc;
    }
  `;
  document.head.appendChild(style);
});

// Forçar a regeneração do arquivo organograma.json
function forcarAtualizacaoJSON() {
  console.log("Forçando atualização do arquivo organograma.json...");
  fetch('/atualizar-organograma-json/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    }
  })
  .then(response => response.json())
  .then(data => {
    console.log("Resposta da atualização:", data);
    if (data.success) {
      console.log("JSON atualizado. Recarregando página...");
      location.reload();
    }
  })
  .catch(error => console.error("Erro ao atualizar JSON:", error));
}

// Adicionar botão para forçar atualização
document.addEventListener('DOMContentLoaded', function() {
  const botoesContainer = document.querySelector('.organograma-buttons');
  if (botoesContainer) {
    const botaoAtualizar = document.createElement('button');
    botaoAtualizar.className = 'btn btn-outline-primary me-2';
    botaoAtualizar.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar Dados';
    botaoAtualizar.addEventListener('click', forcarAtualizacaoJSON);
    botoesContainer.appendChild(botaoAtualizar);
  }
});

// Função para calcular e exibir os pontos do cargo
function calcularEExibirPontos(data) {
  if (!data.cargo) return '';
  
  let pontos = 0;
  
  // Mapear diretamente cada tipo de cargo para seus pontos
  if (data.cargo) {
    const cargo = data.cargo.trim();
    
    // Mapeamento direto - ignora formato e faz correspondência exata por tipo e nível
    // FCE
    if (cargo.includes('FCE') && cargo.includes('15')) pontos = 5.41;
    else if (cargo.includes('FCE') && cargo.includes('14')) pontos = 4.63;
    else if (cargo.includes('FCE') && cargo.includes('13')) pontos = 4.12;
    else if (cargo.includes('FCE') && cargo.includes('12')) pontos = 3.10;
    else if (cargo.includes('FCE') && cargo.includes('11')) pontos = 2.47;
    else if (cargo.includes('FCE') && cargo.includes('10')) pontos = 1.27;
    else if (cargo.includes('FCE') && cargo.includes('9')) pontos = 1.00;
    else if (cargo.includes('FCE') && cargo.includes('8')) pontos = 0.60;
    else if (cargo.includes('FCE') && cargo.includes('7')) pontos = 0.44;
    else if (cargo.includes('FCE') && cargo.includes('6')) pontos = 0.40;
    else if (cargo.includes('FCE') && cargo.includes('5')) pontos = 0.37;
    else if (cargo.includes('FCE') && cargo.includes('4')) pontos = 0.30;
    else if (cargo.includes('FCE') && cargo.includes('3')) pontos = 0.27;
    else if (cargo.includes('FCE') && cargo.includes('2')) pontos = 0.21;
    else if (cargo.includes('FCE') && cargo.includes('1')) pontos = 0.12;
    // CCE - adicionando níveis faltantes até 18
    else if (cargo.includes('CCE') && cargo.includes('18')) pontos = 6.41;
    else if (cargo.includes('CCE') && cargo.includes('17')) pontos = 6.00;
    else if (cargo.includes('CCE') && cargo.includes('16')) pontos = 5.60;
    else if (cargo.includes('CCE') && cargo.includes('15')) pontos = 5.41;
    else if (cargo.includes('CCE') && cargo.includes('14')) pontos = 4.63;
    else if (cargo.includes('CCE') && cargo.includes('13')) pontos = 4.12;
    else if (cargo.includes('CCE') && cargo.includes('12')) pontos = 3.10;
    else if (cargo.includes('CCE') && cargo.includes('11')) pontos = 2.47;
    else if (cargo.includes('CCE') && cargo.includes('10')) pontos = 1.27;
    
    console.log(`Cargo: ${cargo}, Pontos calculados: ${pontos}`);
  }
  
  return `
    <div class="tooltip-field">
      <span class="tooltip-label">Pontos:</span>
      <span class="tooltip-value">${pontos}</span>
    </div>
  `;
}

// Função para calcular e exibir o valor do cargo
function calcularEExibirValor(data) {
  if (!data.cargo) {
    return `
      <div class="tooltip-field">
        <span class="tooltip-label">Valor:</span>
        <span class="tooltip-value">R$ 0,00</span>
      </div>
    `;
  }
  
  let valor = 0;
  
  // Mapear diretamente cada tipo de cargo para seu valor
  if (data.cargo) {
    const cargo = data.cargo.trim();
    
    // Mapeamento direto - ignora formato e faz correspondência exata por tipo e nível
    // FCE
    if (cargo.includes('FCE') && cargo.includes('15')) valor = 17373.92;
    else if (cargo.includes('FCE') && cargo.includes('14')) valor = 14860.92;
    else if (cargo.includes('FCE') && cargo.includes('13')) valor = 13229.07;
    else if (cargo.includes('FCE') && cargo.includes('12')) valor = 9960.05;
    else if (cargo.includes('FCE') && cargo.includes('11')) valor = 7941.89;
    else if (cargo.includes('FCE') && cargo.includes('10')) valor = 4087.96;
    else if (cargo.includes('FCE') && cargo.includes('9')) valor = 3209.60;
    else if (cargo.includes('FCE') && cargo.includes('8')) valor = 1925.77;
    else if (cargo.includes('FCE') && cargo.includes('7')) valor = 1425.44;
    else if (cargo.includes('FCE') && cargo.includes('6')) valor = 1270.0;
    else if (cargo.includes('FCE') && cargo.includes('5')) valor = 1187.56;
    else if (cargo.includes('FCE') && cargo.includes('4')) valor = 962.4;
    else if (cargo.includes('FCE') && cargo.includes('3')) valor = 865.07;
    else if (cargo.includes('FCE') && cargo.includes('2')) valor = 664.2;
    else if (cargo.includes('FCE') && cargo.includes('1')) valor = 393.01;
    // CCE - adicionando níveis faltantes até 18
    else if (cargo.includes('CCE') && cargo.includes('18')) valor = 18690.18;
    else if (cargo.includes('CCE') && cargo.includes('17')) valor = 18100.00;
    else if (cargo.includes('CCE') && cargo.includes('16')) valor = 17600.00;
    else if (cargo.includes('CCE') && cargo.includes('15')) valor = 17373.92;
    else if (cargo.includes('CCE') && cargo.includes('14')) valor = 14860.92;
    else if (cargo.includes('CCE') && cargo.includes('13')) valor = 13229.07;
    else if (cargo.includes('CCE') && cargo.includes('12')) valor = 9960.05;
    else if (cargo.includes('CCE') && cargo.includes('11')) valor = 7941.89;
    else if (cargo.includes('CCE') && cargo.includes('10')) valor = 4087.96;
    
    console.log(`Cargo: ${cargo}, Valor calculado: ${valor}`);
  }
  
  // Formatar o valor como moeda brasileira
  const valorFormatado = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor);
  
  return `
    <div class="tooltip-field">
      <span class="tooltip-label">Valor:</span>
      <span class="tooltip-value">${valorFormatado}</span>
    </div>
  `;
}

// Função para calcular e exibir o gasto total
function calcularEExibirGastoTotal(data) {
  if (!data.cargo) {
    return `
      <div class="tooltip-field">
        <span class="tooltip-label">Gasto Total:</span>
        <span class="tooltip-value">R$ 0,00</span>
      </div>
    `;
  }
  
  let valor = 0;
  
  // Mapear diretamente cada tipo de cargo para seu valor
  if (data.cargo) {
    const cargo = data.cargo.trim();
    
    // Mapeamento direto - ignora formato e faz correspondência exata por tipo e nível
    // FCE
    if (cargo.includes('FCE') && cargo.includes('15')) valor = 17373.92;
    else if (cargo.includes('FCE') && cargo.includes('14')) valor = 14860.92;
    else if (cargo.includes('FCE') && cargo.includes('13')) valor = 13229.07;
    else if (cargo.includes('FCE') && cargo.includes('12')) valor = 9960.05;
    else if (cargo.includes('FCE') && cargo.includes('11')) valor = 7941.89;
    else if (cargo.includes('FCE') && cargo.includes('10')) valor = 4087.96;
    else if (cargo.includes('FCE') && cargo.includes('9')) valor = 3209.60;
    else if (cargo.includes('FCE') && cargo.includes('8')) valor = 1925.77;
    else if (cargo.includes('FCE') && cargo.includes('7')) valor = 1425.44;
    else if (cargo.includes('FCE') && cargo.includes('6')) valor = 1270.0;
    else if (cargo.includes('FCE') && cargo.includes('5')) valor = 1187.56;
    else if (cargo.includes('FCE') && cargo.includes('4')) valor = 962.4;
    else if (cargo.includes('FCE') && cargo.includes('3')) valor = 865.07;
    else if (cargo.includes('FCE') && cargo.includes('2')) valor = 664.2;
    else if (cargo.includes('FCE') && cargo.includes('1')) valor = 393.01;
    // CCE - adicionando níveis faltantes até 18
    else if (cargo.includes('CCE') && cargo.includes('18')) valor = 18690.18;
    else if (cargo.includes('CCE') && cargo.includes('17')) valor = 18100.00;
    else if (cargo.includes('CCE') && cargo.includes('16')) valor = 17600.00;
    else if (cargo.includes('CCE') && cargo.includes('15')) valor = 17373.92;
    else if (cargo.includes('CCE') && cargo.includes('14')) valor = 14860.92;
    else if (cargo.includes('CCE') && cargo.includes('13')) valor = 13229.07;
    else if (cargo.includes('CCE') && cargo.includes('12')) valor = 9960.05;
    else if (cargo.includes('CCE') && cargo.includes('11')) valor = 7941.89;
    else if (cargo.includes('CCE') && cargo.includes('10')) valor = 4087.96;
  }
  
  // Calcular o gasto total
  const quantidade = parseInt(data.quantidade) || 1;
  const gastoTotal = valor * quantidade;
  
  // Formatar o gasto total como moeda brasileira
  const gastoTotalFormatado = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(gastoTotal);
  
  console.log(`Cargo: ${data.cargo}, Valor: ${valor}, Quantidade: ${quantidade}, Gasto total: ${gastoTotal}`);
  
  return `
    <div class="tooltip-field">
      <span class="tooltip-label">Gasto Total:</span>
      <span class="tooltip-value">${gastoTotalFormatado}</span>
    </div>
  `;
}


