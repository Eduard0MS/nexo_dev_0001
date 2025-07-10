// organograma_fixed.js - Versão Integrada com Cálculo Único de Totais

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

// Cache para armazenar os valores totais calculados para cada nó DA ESTRUTURA ORIGINAL
let originalValoresCache = {};

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

// Variável global para armazenar o último nó expandido
let ultimoNoExpandido = null;

/* ============================================================
   Funções de Cálculo Único de Totais
   ============================================================
   Essa abordagem recursiva percorre um nó e todos os seus descendentes
   e acumula o custo (gasto_total) e os pontos (pontos_total) de forma que
   cada nó (identificado por "codigo") seja somado apenas uma vez.
================================================================ */
function computeUnionAndSum(node, union) {
  // Se o nó for nulo ou não tiver código, retorna zero.
  if (!node || !node.codigo) return { gasto: 0, pontos: 0 };
  
  // Se já contamos esse nó (pelo código), retorne zero para evitar duplicidade.
  if (union.has(node.codigo)) return { gasto: 0, pontos: 0 };
  
  union.add(node.codigo);

  // Converter os valores diretos (garantindo que sejam números)
  const gastoDireto = parseFloat(node.gasto_total) || 0;
  const pontosDiretos = parseFloat(node.pontos_total) || 0;

  let totalGasto = gastoDireto;
  let totalPontos = pontosDiretos;
  
  // Se há descendentes, soma os valores deles (evitando duplicatas)
  if (node.children && node.children.length > 0) {
    node.children.forEach(child => {
      const resultadoFilho = computeUnionAndSum(child, union);
      totalGasto += resultadoFilho.gasto;
      totalPontos += resultadoFilho.pontos;
    });
  }
  
  return { gasto: totalGasto, pontos: totalPontos };
}

function totalValoresParaNo(node) {
  const union = new Set();
  const resultado = computeUnionAndSum(node, union);
  return {
    gastoTotal: resultado.gasto,
    pontosTotal: resultado.pontos
  };
}

/* ============================================================
   Função para transformar os dados no formato hierárquico.
   Agrupa as unidades por código, define os relacionamentos (pai–filho)
   e gera a estrutura que o D3 usará para renderização.
================================================================ */
function transformData(data, codigoPrincipal = null) {
    console.log("Transformando dados para o organograma:", data);
    
    // Verifica se os dados estão no formato esperado
    if (!data || !data.core_unidadecargo || !Array.isArray(data.core_unidadecargo)) {
        console.error("Dados inválidos para o organograma");
        return {
            nome: "Organograma Completo",
            cargo: "",
            secretaria: "",
            codigo: "0000",
            tipo_unidade: "",
            cargos_detalhes: [],
            children: []
        };
    }
    
    // Se temos um código principal, vamos filtrar para mostrar apenas essa unidade e suas subordinadas diretas
    let unidades = data.core_unidadecargo;
    
    // Função para verificar se uma unidade é subordinada direta de outra (baseado no grafo)
    function isSubordinadaDireta(grafoPai, grafoFilho) {
        if (!grafoPai || !grafoFilho) return false;
        
        // Formato típico do grafo: "308804-308804-308805"
        const partesFilho = grafoFilho.split('-');
        const partesPai = grafoPai.split('-');
        
        // O filho deve ter o grafo do pai + uma parte adicional
        return partesFilho.length === partesPai.length + 1 && 
               grafoFilho.startsWith(grafoPai);
    }
    
    // Se temos um código principal, vamos aplicar filtragem adicional
    if (codigoPrincipal) {
        // Primeiro encontrar o grafo da unidade principal
        const unidadePrincipal = unidades.find(u => u.codigo_unidade === codigoPrincipal);
        if (unidadePrincipal && unidadePrincipal.grafo) {
            const grafoPrincipal = unidadePrincipal.grafo;
            console.log(`Filtrando para unidade principal: ${codigoPrincipal} com grafo ${grafoPrincipal}`);
            
            // Filtrar para incluir a unidade principal e TODAS as suas descendentes (qualquer profundidade)
            unidades = unidades.filter(u => {
                // Incluir a própria unidade principal
                if (u.codigo_unidade === codigoPrincipal) return true;
                // Incluir qualquer descendente cujo grafo comece com o grafo da principal
                if (u.grafo && u.grafo.startsWith(grafoPrincipal) && u.grafo.length > grafoPrincipal.length) {
                    return true;
                }
                return false;
            });
            
            console.log(`Após filtragem, ${unidades.length} unidades serão exibidas no organograma (incluindo descendentes).`);
        }
    }
    
    const unidadesPorCodigo = {};
    
    // Agrupamento por código
    unidades.forEach(unit => {
        const codigo = unit.codigo_unidade;
        if (!unidadesPorCodigo[codigo]) {
            unidadesPorCodigo[codigo] = {
                unidades: [],
                principal: null,
                maiorNivel: -1,
                nivel_hierarquico: -1,
                valores_diretos: { pontos_total: 0, gasto_total: 0 },
                cargos_detalhes: {}
            };
        }
        
        const grupo = unidadesPorCodigo[codigo];
        grupo.unidades.push(unit);
        
        // Determina o nível hierárquico a partir do campo "grafo"
        const grafo = unit.grafo || '';
        const partes = grafo.split('-');
        const nivel_hierarquico = partes.length - 1;
        if (nivel_hierarquico > grupo.nivel_hierarquico) {
            grupo.nivel_hierarquico = nivel_hierarquico;
        }
        
        // Seleciona a unidade principal com maior "nivel"
        const nivel = parseInt(unit.nivel || 0);
        if (nivel > grupo.maiorNivel) {
            grupo.maiorNivel = nivel;
            grupo.principal = unit;
        }
        
        // Acumula os valores diretos
        grupo.valores_diretos.pontos_total += parseFloat(unit.pontos_total || (unit.pontos * unit.quantidade) || 0);
        grupo.valores_diretos.gasto_total += parseFloat(unit.gasto_total || 0);
        
        // Agrupa detalhes de cargos para uso no tooltip
        if (unit.tipo_cargo && unit.categoria !== undefined && unit.nivel !== undefined) {
            const cargoKey = `${unit.tipo_cargo} ${unit.categoria} ${unit.nivel}`;
            if (!grupo.cargos_detalhes[cargoKey]) grupo.cargos_detalhes[cargoKey] = 0;
            grupo.cargos_detalhes[cargoKey] += parseInt(unit.quantidade || 0);
        }
    });
    console.log(`Agrupados ${Object.keys(unidadesPorCodigo).length} códigos únicos.`);
    
    // Estabelece relações pai-filho com base no campo "grafo"
    const filhosPorCodigo = {};
    const paiPorCodigo = {};
    Object.keys(unidadesPorCodigo).forEach(codigo => { filhosPorCodigo[codigo] = []; });
    
    Object.keys(unidadesPorCodigo).forEach(codigo => {
        const principal = unidadesPorCodigo[codigo].principal;
        if (!principal || !principal.grafo) return;
        const grafo = principal.grafo;
        const partes = grafo.split('-');
        if (partes.length > 1) {
            const codigoPai = partes[partes.length - 2];
            if (codigoPai && unidadesPorCodigo[codigoPai] && codigo !== codigoPai) {
                paiPorCodigo[codigo] = codigoPai;
                if (!filhosPorCodigo[codigoPai].includes(codigo)) {
                    filhosPorCodigo[codigoPai].push(codigo);
                }
            }
        }
    });
    
    // Constrói os nós para visualização
    const nodesMap = {};
    function createNode(codigo) {
        if (!codigo || !unidadesPorCodigo[codigo] || !unidadesPorCodigo[codigo].principal) return null;
        const grupo = unidadesPorCodigo[codigo];
        const principal = grupo.principal;
        const valores = grupo.valores_diretos;
        const cargosArray = Object.entries(grupo.cargos_detalhes).map(([cargo, quantidade]) => ({ cargo, quantidade }));
        return {
            nome: principal.denominacao_unidade || "Unidade sem nome",
            codigo: codigo,
            cargo: principal.tipo_cargo ? `${principal.tipo_cargo} ${principal.nivel || ''}` : "Sem cargo",
            secretaria: principal.sigla || principal.sigla_unidade || "",
            tipo_unidade: principal.tipo_unidade || "",
            tipo_cargo: principal.tipo_cargo || "",
            denominacao: principal.denominacao || principal.denominacao_unidade || "",
            categoria: principal.categoria,
            nivel: principal.nivel,
            grafo: principal.grafo || "",
            quantidade: parseInt(principal.quantidade || 0),
            pontos: parseFloat(principal.pontos || 0),
            pontos_total: valores.pontos_total,
            gasto_total: valores.gasto_total,
            nivel_hierarquico: grupo.nivel_hierarquico,
            cargos_detalhes: cargosArray,
            children: [],
            is_sibling: false
        };
    }
    
    // Define o nó raiz (geralmente com código "308804" ou outro identificado)
    const rootNode = createNode("308804") || {
        nome: "Organograma Completo",
        cargo: "",
        secretaria: "",
        codigo: "0000",
        tipo_unidade: "",
        pontos_total: 0,
        gasto_total: 0,
        cargos_detalhes: [],
        children: []
    };
    nodesMap["308804"] = rootNode;
    Object.keys(unidadesPorCodigo).forEach(codigo => { if (codigo !== "308804") nodesMap[codigo] = createNode(codigo); });
    
    // Relaciona pai-filho
    Object.keys(nodesMap).forEach(codigo => {
        if (codigo === "308804") return;
        if (!nodesMap[codigo]) return;
        const codigoPai = paiPorCodigo[codigo];
        if (codigoPai && nodesMap[codigoPai]) {
            nodesMap[codigoPai].children.push(nodesMap[codigo]);
        } else {
            rootNode.children.push(nodesMap[codigo]);
        }
    });
    
    // Ordena e marca irmãos (opcional)
    function sortChildren(node) {
        if (node.children && node.children.length > 0) {
            node.children.sort((a, b) => (b.nivel || 0) - (a.nivel || 0));
            if (node.children.length > 1) node.children.forEach(child => { child.is_sibling = true; });
            node.children.forEach(sortChildren);
        }
    }
    sortChildren(rootNode);
    
    console.log("Estrutura hierárquica construída.");
    return rootNode;
}

/* ============================================================
   Funções para exibição no Tooltip
================================================================ */
function calcularEExibirPontos(data) {
    if (!data || !data.pontos) return '';
    return `<div class="tooltip-field"><span class="tooltip-label">Pontos:</span><span class="tooltip-value">${data.pontos}</span></div>`;
}

function calcularEExibirValor(data) {
    if (!data || !data.valor_unitario) return '';
    return `<div class="tooltip-field"><span class="tooltip-label">Valor:</span><span class="tooltip-value">R$ ${data.valor_unitario.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span></div>`;
}

function calcularEExibirGastoTotal(data) {
    if (!data || !data.gasto_total) return '';
    return `<div class="tooltip-field"><span class="tooltip-label">Gasto Total:</span><span class="tooltip-value">R$ ${data.gasto_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span></div>`;
}

/* ============================================================
   Função para processar dados e atualizar a visualização
================================================================ */
function processarDados(data) {
    console.log("Processando dados iniciais para o organograma");
    try {
        originalData = data;
        originalValoresCache = {}; // Limpar/Inicializar o cache original

        const hierarchicalData = transformData(data);

        console.log("Calculando valores totais originais para todos os nós...");
        preCalcularTotais(hierarchicalData, originalValoresCache); // Calcular e popular o cache ORIGINAL
        console.log("Cálculo de valores originais concluído. Cache:", originalValoresCache);

        root = d3.hierarchy(hierarchicalData);
        root.x0 = 0;
        root.y0 = 0;

        if (root.children) {
            root.children.forEach(child => collapseAtLevel(child, 0));
        }

        update(root); // Renderizar

        setTimeout(function() {
            const initialTransform = d3.zoomIdentity.translate(width / 10, height / 2).scale(0.55);
            svg.call(zoomBehavior.transform, initialTransform);
            document.dispatchEvent(new CustomEvent('organogramaCarregado', {
                detail: {
                    root: root,
                    dataLength: data.core_unidadecargo ? data.core_unidadecargo.length : 0
                }
            }));
        }, 100);

        // Inicializar o dropdown de unidades após processar os dados
        initializeUnits();
    } catch (error) {
        console.error("Erro ao processar dados para o organograma:", error);
        
        // Mostrar mensagem de erro
        const errorMessage = document.createElement('div');
        errorMessage.className = 'alert alert-danger m-3';
        errorMessage.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i> Erro ao processar dados: ${error.message}`;
        container.node().appendChild(errorMessage);
    }
}

// Função para pré-calcular e armazenar os valores totais na estrutura HIERÁRQUICA fornecida
function preCalcularTotais(node, cacheToPopulate) {
    if (!node || !node.codigo) return;
    if (!cacheToPopulate) {
        console.error("Cache deve ser fornecido para preCalcularTotais");
        return;
    }

    // Calcular valores totais para este nó usando a estrutura passada
    const totais = totalValoresParaNo(node); 

    // Armazenar no cache fornecido
    cacheToPopulate[node.codigo] = {
        gastoTotal: totais.gastoTotal,
        pontosTotal: totais.pontosTotal
    };

    // Processar filhos recursivamente
    if (node.children && node.children.length > 0) {
        node.children.forEach(child => preCalcularTotais(child, cacheToPopulate));
    }
}

/* ============================================================
   Funções de manipulação de nós: toggle, expandir, colapsar, etc.
================================================================ */
function toggleChildren(d) {
    if (d.children) {
        // Colapsa o nó atual
        d._children = d.children;
        d.children = null;
    } else if (d._children) {
        // Expande o nó atual
        d.children = d._children;
        d._children = null;
    }
}

function collapseAtLevel(d, currentLevel, maxLevel = 0) {
    if (d.children) {
        if (currentLevel >= maxLevel) { 
            d._children = d.children; 
            d.children = null; 
        } else {
            d.children.forEach(child => collapseAtLevel(child, currentLevel + 1, maxLevel));
        }
    }
}

function expandAll(d) {
    if (d._children) { d.children = d._children; d._children = null; }
    if (d.children) { d.children.forEach(expandAll); }
}

function collapseAll(d) {
    if (d.children) { d._children = d.children; d.children = null; }
    if (d._children) { d._children.forEach(collapseAll); }
}

function getMaxVisibleDepth(node) {
    let maxDepth = 0;
    function traverse(n, depth) {
        if (depth > maxDepth) maxDepth = depth;
        if (n.children) n.children.forEach(child => traverse(child, depth + 1));
    }
    traverse(node, 0);
    return maxDepth;
}

/* ============================================================
   Inicialização da visualização e dos controles
================================================================ */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Inicializando organograma...");
    container = d3.select('#organogramaContainer');
    
    const controls = container.append('div').attr('class', 'organograma-controls d-flex justify-content-end mb-2');
    
    // Botões existentes
    const expandAllBtn = controls.append('button')
      .attr('id', 'expandAllBtn')
      .attr('class', 'btn btn-sm btn-outline-primary me-2')
      .on('click', function() {
        if (root) {
          expandAll(root);
          update(root);
          setTimeout(() => {
            const maxDepth = getMaxVisibleDepth(root);
            const scale = Math.max(0.3, 0.9 - (maxDepth * 0.1));
            const initialTransform = d3.zoomIdentity.translate(50, height / 2).scale(scale);
            svg.call(zoomBehavior.transform, initialTransform);
          }, 600);
        }
      });
    expandAllBtn.append('i').attr('class', 'fas fa-expand-arrows-alt me-1');
    expandAllBtn.append('span').text('Expandir Todos');
    
    const collapseBtn = controls.append('button')
      .attr('id', 'collapseBtn')
      .attr('class', 'btn btn-sm btn-outline-primary me-2')
      .on('click', function() { if (root) { collapseAll(root); update(root); } });
    collapseBtn.append('i').attr('class', 'fas fa-compress-arrows-alt me-1');
    collapseBtn.append('span').text('Recolher Todos');
    
    const resetBtn = controls.append('button')
      .attr('id', 'resetBtn')
      .attr('class', 'btn btn-sm btn-outline-primary me-2')
      .on('click', function() { 
        if (svg) {
          svg.transition().duration(750)
             .call(zoomBehavior.transform, d3.zoomIdentity.translate(width / 10, height / 2).scale(0.55));
        }
      });
    resetBtn.append('i').attr('class', 'fas fa-sync me-1');
    resetBtn.append('span').text('Resetar Zoom');
    
    // Novos botões de Zoom
    const zoomInBtn = controls.append('button')
      .attr('id', 'zoomInBtn')
      .attr('class', 'btn btn-sm btn-outline-secondary me-1')
      .attr('title', 'Aumentar Zoom')
      .on('click', function() {
        if (svg) {
          svg.transition().duration(250).call(zoomBehavior.scaleBy, 1.2);
        }
      });
    zoomInBtn.append('i').attr('class', 'fas fa-search-plus');

    const zoomOutBtn = controls.append('button')
      .attr('id', 'zoomOutBtn')
      .attr('class', 'btn btn-sm btn-outline-secondary')
      .attr('title', 'Diminuir Zoom')
      .on('click', function() {
        if (svg) {
          svg.transition().duration(250).call(zoomBehavior.scaleBy, 0.8);
        }
      });
    zoomOutBtn.append('i').attr('class', 'fas fa-search-minus');

    // Criar o tooltip ANTES de tudo
    tooltip = container.append('div')
        .attr('class', 'organograma-tooltip')
        .style('opacity', 0)
        .style('position', 'fixed')
        .style('pointer-events', 'none')
        .style('z-index', 1000);
    
    console.log("Tooltip criado:", tooltip.node()); // Log para debug
    // Criar o tooltip ANTES de tudo
    tooltip = container.append('div')
        .attr('class', 'organograma-tooltip')
        .style('opacity', 0)
        .style('position', 'fixed')
        .style('pointer-events', 'none')
        .style('z-index', 1000);
    
    console.log("Tooltip criado:", tooltip.node()); // Log para debug
    
    svg = container.append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet');
    
    g = svg.append('g').attr('class', 'organograma-group');
    
    zoomBehavior = d3.zoom()
      .scaleExtent([0.2, 2])
      .on('zoom', (event) => { g.attr('transform', event.transform); });
    svg.call(zoomBehavior);
  
    const treeLayout = d3.tree().nodeSize([60, 200]).separation((a, b) => (a.parent === b.parent ? 1.2 : 1.8));
    window.treeLayout = treeLayout;
  
    try {
      if (window.organogramaData) {
        console.log("Usando dados embutidos no HTML");
        const data = window.organogramaData;
        processarDados(data);
      } else {
        console.error("Dados do organograma não encontrados no template!");
        exibirErro("Não foi possível carregar os dados do organograma. Tente atualizar a página.");
      }
    } catch (err) {
      console.error('Erro ao processar dados do organograma:', err);
      exibirErro("Ocorreu um erro ao processar os dados: " + err.message);
    }
});

/* ============================================================
   Função para atualizar a visualização (update)
================================================================ */
function update(source) {
  const duration = 500;
  window.treeLayout(root);
  
  // Inverte coordenadas para layout horizontal
  root.each(d => {
    const oldX = d.x, oldY = d.y;
    d.x = oldY; d.y = oldX;
  });
  
  // CRIAR LINKS PRIMEIRO (para ficarem por baixo dos nós)
  const links = g.selectAll('path.link')
      .data(root.links(), d => d.target.id);
  
  const linkEnter = links.enter().append('path')
      .attr('class', 'link')
      .attr('d', d => {
          const o = { x: source.x0, y: source.y0 };
          return diagonal({ source: o, target: o });
      })
      .attr('fill', 'none')
      .attr('stroke', colors.link)
      .attr('stroke-width', 1.5)
      .style('opacity', 0);
  
  linkEnter.merge(links)
      .transition().duration(duration)
      .attr('d', diagonal)
      .style('opacity', 1);
  
  links.exit()
      .transition().duration(duration)
      .attr('d', d => {
          const o = { x: source.x, y: source.y };
          return diagonal({ source: o, target: o });
      })
      .style('opacity', 0)
      .remove();
  
  // AGORA CRIAR NÓS (por cima das linhas)
  // CRIAR LINKS PRIMEIRO (para ficarem por baixo dos nós)
  const links = g.selectAll('path.link')
      .data(root.links(), d => d.target.id);
  
  const linkEnter = links.enter().append('path')
      .attr('class', 'link')
      .attr('d', d => {
          const o = { x: source.x0, y: source.y0 };
          return diagonal({ source: o, target: o });
      })
      .attr('fill', 'none')
      .attr('stroke', colors.link)
      .attr('stroke-width', 1.5)
      .style('opacity', 0);
  
  linkEnter.merge(links)
      .transition().duration(duration)
      .attr('d', diagonal)
      .style('opacity', 1);
  
  links.exit()
      .transition().duration(duration)
      .attr('d', d => {
          const o = { x: source.x, y: source.y };
          return diagonal({ source: o, target: o });
      })
      .style('opacity', 0)
      .remove();
  
  // AGORA CRIAR NÓS (por cima das linhas)
  const nodes = g.selectAll('g.node').data(root.descendants(), d => d.id || (d.id = ++i));
  
  const nodeEnter = nodes.enter().append('g')
    .attr('class', d => {
      let classes = `node`;
      classes += (d.children || d._children) ? ` node--internal` : ` node--leaf`;
      if (d._children) classes += ` collapsed`;
      if (d.data.is_sibling) classes += ` sibling`;
      return classes;
    })
    .attr('transform', d => `translate(${source.x0},${source.y0})`)
    .style('opacity', 0)
    .on('click', (event, d) => { event.stopPropagation(); toggleChildren(d); update(d); })
    .on('mouseover', (event, d) => {
      console.log("Mouseover detectado no nó:", d.data.secretaria); // Log para debug
      
      console.log("Mouseover detectado no nó:", d.data.secretaria); // Log para debug
      
      const nodeElement = event.currentTarget;
      const { x, y, position } = calcularPosicaoTooltip(event, nodeElement);
      
      console.log("Posição calculada:", { x, y, position }); // Log para debug
      
      console.log("Posição calculada:", { x, y, position }); // Log para debug
      
      // Buscar valores do cache ORIGINAL ou usar zeros como fallback
      let totaisCalculados = originalValoresCache[d.data.codigo];
      if (!totaisCalculados) {
          console.warn(`Valores não encontrados no cache para ${d.data.codigo}, usando fallback.`);
          totaisCalculados = { gastoTotal: 0, pontosTotal: 0 };
      }
      console.debug(`Exibindo valores para nó ${d.data.codigo}:`, totaisCalculados);

      // Calcular porcentagem em relação ao pai para mostrar junto das unidades vinculadas
      let porcentagemTexto = '';
      if (d.parent && d.parent.data && d.parent.data.codigo) {
        const totaisPai = originalValoresCache[d.parent.data.codigo];
        if (totaisPai && totaisPai.pontosTotal > 0) {
          // Calcular pontos totais de todos os irmãos (filhos do mesmo pai)
          let pontosFilhos = 0;
          if (d.parent.children) {
            d.parent.children.forEach(irmao => {
              const totaisIrmao = originalValoresCache[irmao.data.codigo];
              if (totaisIrmao) {
                pontosFilhos += totaisIrmao.pontosTotal;
              }
            });
          } else if (d.parent._children) {
            d.parent._children.forEach(irmao => {
              const totaisIrmao = originalValoresCache[irmao.data.codigo];
              if (totaisIrmao) {
                pontosFilhos += totaisIrmao.pontosTotal;
              }
            });
          }
          
          // Se temos pontos dos filhos, calcular porcentagem em relação aos filhos
          if (pontosFilhos > 0) {
            const percentual = ((totaisCalculados.pontosTotal / pontosFilhos) * 100).toFixed(1);
            porcentagemTexto = ` (${percentual}%)`;
          }
        }
      }

      // Calcular porcentagem em relação ao pai para mostrar junto das unidades vinculadas
      let porcentagemTexto = '';
      if (d.parent && d.parent.data && d.parent.data.codigo) {
        const totaisPai = originalValoresCache[d.parent.data.codigo];
        if (totaisPai && totaisPai.pontosTotal > 0) {
          // Calcular pontos totais de todos os irmãos (filhos do mesmo pai)
          let pontosFilhos = 0;
          if (d.parent.children) {
            d.parent.children.forEach(irmao => {
              const totaisIrmao = originalValoresCache[irmao.data.codigo];
              if (totaisIrmao) {
                pontosFilhos += totaisIrmao.pontosTotal;
              }
            });
          } else if (d.parent._children) {
            d.parent._children.forEach(irmao => {
              const totaisIrmao = originalValoresCache[irmao.data.codigo];
              if (totaisIrmao) {
                pontosFilhos += totaisIrmao.pontosTotal;
              }
            });
          }
          
          // Se temos pontos dos filhos, calcular porcentagem em relação aos filhos
          if (pontosFilhos > 0) {
            const percentual = ((totaisCalculados.pontosTotal / pontosFilhos) * 100).toFixed(1);
            porcentagemTexto = ` (${percentual}%)`;
          }
        }
      }

      // Gerar a seção de cargos e servidores
      let cargosHtml = '';
      let totalServidores = 0;
      
      if (d.data.cargos_detalhes && d.data.cargos_detalhes.length > 0) {
        // Calcular total de servidores
        totalServidores = d.data.cargos_detalhes.reduce((total, cargo) => total + cargo.quantidade, 0);
        
        // Gerar HTML para cada cargo
        const cargosListaHtml = d.data.cargos_detalhes
          .map(cargo => `<div class="cargo-item">${cargo.cargo}: ${cargo.quantidade} servidor${cargo.quantidade !== 1 ? 'es' : ''}</div>`)
          .join('');
        
        cargosHtml = `
          <div class="tooltip-subtitle">Servidores (${totalServidores} total)</div>
          <div class="cargos-lista">
            ${cargosListaHtml}
          </div>
        `;
      }

      const formatMoeda = valor => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
      const formatPontos = valor => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 }).format(valor);
      
      // Primeiro definir o conteúdo do tooltip
      // Primeiro definir o conteúdo do tooltip
      tooltip.html(`
        <div class="tooltip-title">${d.data.nome} ${ (d.children || d._children) ? `<span class="badge">${(d.children ? d.children.length : d._children.length)} unidade(s) vinculada(s)${porcentagemTexto}</span>` : '' }</div>
        <div class="tooltip-title">${d.data.nome} ${ (d.children || d._children) ? `<span class="badge">${(d.children ? d.children.length : d._children.length)} unidade(s) vinculada(s)${porcentagemTexto}</span>` : '' }</div>
        <div class="tooltip-subtitle">Informações da Estrutura</div>
        <div class="tooltip-field">
          <span class="tooltip-label">Sigla:</span>
          <span class="tooltip-value">${d.data.secretaria || d.data.sigla || 'Não especificada'}</span>
        </div>
        <div class="tooltip-field">
          <span class="tooltip-label">Custo Total da Estrutura:</span>
          <span class="tooltip-value">${formatMoeda(totaisCalculados.gastoTotal)}</span>
        </div>
        <div class="tooltip-field">
          <span class="tooltip-label">Pontos Totais da Estrutura:</span>
          <span class="tooltip-value">${formatPontos(totaisCalculados.pontosTotal)}</span>
        </div>
        <div class="tooltip-field">
          <span class="tooltip-label">Código:</span>
          <span class="tooltip-value">${d.data.codigo || ''}</span>
        </div>
        ${cargosHtml}
      `);
      
      console.log("Tooltip HTML definido, aplicando posição..."); // Log para debug
      
      // Depois posicionar e mostrar o tooltip
      tooltip.attr('class', `organograma-tooltip ${position}`)
             .style('left', x + 'px')
             .style('top', y + 'px')
             .style('opacity', 0)
             .style('transform', 'translateX(0)')
             .transition()
             .duration(200)
             .style('opacity', 1);
      
      console.log("Tooltip exibido"); // Log para debug
      
      console.log("Tooltip HTML definido, aplicando posição..."); // Log para debug
      
      // Depois posicionar e mostrar o tooltip
      tooltip.attr('class', `organograma-tooltip ${position}`)
             .style('left', x + 'px')
             .style('top', y + 'px')
             .style('opacity', 0)
             .style('transform', 'translateX(0)')
             .transition()
             .duration(200)
             .style('opacity', 1);
      
      console.log("Tooltip exibido"); // Log para debug
      
      d3.select(event.currentTarget).select('circle')
        .transition().duration(200).attr('r', d => d.depth === 0 ? 18 : 14);
    })
    .on('mouseout', (event, d) => {
      console.log("Mouseout detectado no nó:", d.data.secretaria); // Log para debug
      
      tooltip.transition()
             .duration(150)
             .style('opacity', 0);
             
      console.log("Mouseout detectado no nó:", d.data.secretaria); // Log para debug
      
      tooltip.transition()
             .duration(150)
             .style('opacity', 0);
             
      d3.select(event.currentTarget).select('circle')
        .transition().duration(200).attr('r', d => d.depth === 0 ? 14 : 10);
    });
  
  nodeEnter.append('circle')
    .attr('r', 0)
    .attr('fill', d => {
      // Forçar cor azul céu para nós pais
      if (d.children || d._children) {
        return '#87ceeb'; // Azul céu para pais
      }
      return '#ffffff'; // Branco para folhas
    })
    .attr('fill', d => {
      // Forçar cor azul céu para nós pais
      if (d.children || d._children) {
        return '#87ceeb'; // Azul céu para pais
      }
      return '#ffffff'; // Branco para folhas
    })
    .attr('stroke', '#2c5282')
    .attr('stroke-width', d => d.depth === 0 ? 2 : 1.5)
    .attr('stroke-dasharray', 'none');
  
  nodeEnter.append('text')
    .attr('dy', '-1.5em')
    .attr('text-anchor', 'middle')
    .text(d => d.data.secretaria)
    .attr('data-sigla', d => d.data.secretaria)
    .style('fill', colors.text)
    .style('font-weight', 'bold')
    .style('font-size', '12px')
    .style('fill-opacity', 0);
  
  nodeEnter.append('text')
    .attr('dy', '1.5em')
    .attr('text-anchor', 'middle')
    .text(d => d.data.cargo)
    .style('fill', colors.text)
    .style('font-size', '10px')
    .style('fill-opacity', 0);
  
  const nodeUpdate = nodeEnter.merge(nodes)
      .transition().duration(duration)
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .style('opacity', 1);
  
  nodeUpdate.select('circle')
      .attr('r', d => d.depth === 0 ? 14 : 10)
      .attr('fill', d => {
        // Forçar cor azul céu para nós pais sempre
        if (d.children || d._children) {
          return '#87ceeb'; // Azul céu para pais
        }
        return '#ffffff'; // Branco para folhas
      })
      .attr('fill', d => {
        // Forçar cor azul céu para nós pais sempre
        if (d.children || d._children) {
          return '#87ceeb'; // Azul céu para pais
        }
        return '#ffffff'; // Branco para folhas
      })
      .attr('stroke', '#2c5282')
      .attr('stroke-width', d => d.depth === 0 ? 2 : 1.5)
      .attr('stroke-dasharray', 'none');
  
  nodeUpdate.select('text').style('fill-opacity', 1);
  
  const nodeExit = nodes.exit()
      .transition().duration(duration)
      .attr('transform', d => `translate(${source.x},${source.y})`)
      .style('opacity', 0)
      .remove();
  
  nodeExit.select('circle').attr('r', 0);
  nodeExit.select('text').style('fill-opacity', 0);
  
  root.eachBefore(d => { d.x0 = d.x; d.y0 = d.y; });
  
  function diagonal(d) {
      const path = `
        M ${d.source.x} ${d.source.y}
        C ${d.source.x + (d.target.x - d.source.x) / 3} ${d.source.y},
          ${d.source.x + 2 * (d.target.x - d.source.x) / 3} ${d.target.y},
          ${d.target.x} ${d.target.y}
      `;
      return path;
  }
  
  document.dispatchEvent(new CustomEvent('organogramaAtualizado', { detail: { root: root } }));
}

/* ============================================================
   Função para calcular a posição ideal do tooltip
================================================================ */
function calcularPosicaoTooltip(event, nodeElement) {
  const nodeRect = nodeElement.getBoundingClientRect();
  const tooltipWidth = 320;
  const tooltipHeight = 280;
  const spacing = 15; // Aumentar um pouco o espaçamento
  const spacing = 15; // Aumentar um pouco o espaçamento
  const container = document.getElementById('organogramaContainer');
  const containerRect = container.getBoundingClientRect();
  const nodeCenterX = nodeRect.left + (nodeRect.width / 2);
  const nodeCenterY = nodeRect.top + (nodeRect.height / 2);
  
  let tooltipX, tooltipY, position = 'right';
  
  // PRIORIDADE 1: Tentar sempre à direita primeiro
  const rightX = nodeRect.right + spacing;
  const rightY = nodeCenterY - (tooltipHeight / 2);
  
  // Verificar se cabe à direita (com mais tolerância)
  if (rightX + tooltipWidth <= window.innerWidth - 20) { // 20px de margem da janela
    tooltipX = rightX;
    tooltipY = rightY;
    position = 'right';
    
    // Ajustar Y para não sair da tela
    if (tooltipY < 10) {
      tooltipY = 10;
    } else if (tooltipY + tooltipHeight > window.innerHeight - 10) {
      tooltipY = window.innerHeight - tooltipHeight - 10;
    }
  }
  // PRIORIDADE 2: Se não couber à direita, tentar à esquerda
  else {
    const leftX = nodeRect.left - tooltipWidth - spacing;
    
    if (leftX >= 20) { // 20px de margem da janela
      tooltipX = leftX;
  
  // PRIORIDADE 1: Tentar sempre à direita primeiro
  const rightX = nodeRect.right + spacing;
  const rightY = nodeCenterY - (tooltipHeight / 2);
  
  // Verificar se cabe à direita (com mais tolerância)
  if (rightX + tooltipWidth <= window.innerWidth - 20) { // 20px de margem da janela
    tooltipX = rightX;
    tooltipY = rightY;
    position = 'right';
    
    // Ajustar Y para não sair da tela
    if (tooltipY < 10) {
      tooltipY = 10;
    } else if (tooltipY + tooltipHeight > window.innerHeight - 10) {
      tooltipY = window.innerHeight - tooltipHeight - 10;
    }
  }
  // PRIORIDADE 2: Se não couber à direita, tentar à esquerda
  else {
    const leftX = nodeRect.left - tooltipWidth - spacing;
    
    if (leftX >= 20) { // 20px de margem da janela
      tooltipX = leftX;
      tooltipY = nodeCenterY - (tooltipHeight / 2);
      position = 'left';
      
      // Ajustar Y para não sair da tela
      if (tooltipY < 10) {
        tooltipY = 10;
      } else if (tooltipY + tooltipHeight > window.innerHeight - 10) {
        tooltipY = window.innerHeight - tooltipHeight - 10;
      }
    }
    // PRIORIDADE 3: Como último recurso, posicionar acima ou abaixo
    else {
      tooltipX = Math.max(20, Math.min(nodeCenterX - (tooltipWidth / 2), window.innerWidth - tooltipWidth - 20));
      
      // Tentar posicionar acima
      if (nodeRect.top - tooltipHeight - spacing >= 10) {
        tooltipY = nodeRect.top - tooltipHeight - spacing;
        position = 'top';
      }
      // Caso contrário, posicionar abaixo
      else {
        tooltipY = nodeRect.bottom + spacing;
        position = 'bottom';
        
        // Se não couber abaixo, forçar para caber na tela
        if (tooltipY + tooltipHeight > window.innerHeight - 10) {
          tooltipY = window.innerHeight - tooltipHeight - 10;
        }
      }
    }
  }
  
  // Garantir que o tooltip nunca saia completamente da tela
  tooltipX = Math.max(10, Math.min(tooltipX, window.innerWidth - tooltipWidth - 10));
  tooltipY = Math.max(10, Math.min(tooltipY, window.innerHeight - tooltipHeight - 10));
      
      // Ajustar Y para não sair da tela
      if (tooltipY < 10) {
        tooltipY = 10;
      } else if (tooltipY + tooltipHeight > window.innerHeight - 10) {
        tooltipY = window.innerHeight - tooltipHeight - 10;
      }
    }
    // PRIORIDADE 3: Como último recurso, posicionar acima ou abaixo
    else {
      tooltipX = Math.max(20, Math.min(nodeCenterX - (tooltipWidth / 2), window.innerWidth - tooltipWidth - 20));
      
      // Tentar posicionar acima
      if (nodeRect.top - tooltipHeight - spacing >= 10) {
        tooltipY = nodeRect.top - tooltipHeight - spacing;
        position = 'top';
      }
      // Caso contrário, posicionar abaixo
      else {
        tooltipY = nodeRect.bottom + spacing;
        position = 'bottom';
        
        // Se não couber abaixo, forçar para caber na tela
        if (tooltipY + tooltipHeight > window.innerHeight - 10) {
          tooltipY = window.innerHeight - tooltipHeight - 10;
        }
      }
    }
  }
  
  // Garantir que o tooltip nunca saia completamente da tela
  tooltipX = Math.max(10, Math.min(tooltipX, window.innerWidth - tooltipWidth - 10));
  tooltipY = Math.max(10, Math.min(tooltipY, window.innerHeight - tooltipHeight - 10));
  
  return { x: tooltipX, y: tooltipY, position };
}

/* ============================================================
   Funções para aplicar e limpar filtros
================================================================ */
const aplicarFiltros = () => {
    let siglaFiltro = '';
    // Verificar se estamos usando Select2
    if (typeof $ !== 'undefined' && $.fn.select2) {
        siglaFiltro = $('#filtroSigla').val() || '';
        // Também obtém o texto da opção selecionada se necessário
        if (siglaFiltro) {
            const selectedText = $('#filtroSigla').select2('data')[0].text;
            siglaFiltro = selectedText.split(' - ')[0]; // Extrai a sigla da parte inicial (ex: "SAGE - ...")
        }
    } else {
        siglaFiltro = document.getElementById('filtroSigla').value.trim();
    }

    console.log(`Aplicando filtros: Sigla=${siglaFiltro}`);
    const temFiltros = siglaFiltro;
    if (!temFiltros) { limparFiltros(); return; }
    const loadingEl = container.append('div')
        .attr('class', 'alert alert-info m-3')
        .html('<i class="fas fa-spinner fa-spin me-2"></i> Carregando dados filtrados...');
    
    // Filtro específico e preciso para a sigla usando modo Exact
    let url = `/api/organograma-filter/?sigla=${encodeURIComponent(siglaFiltro)}&modo=exact`;
    
    console.log("URL da API de filtro:", url);
    
    // 1. Primeiro, filtrar o organograma
    fetch(url)
        .then(response => { if (!response.ok) throw new Error('Erro ao filtrar dados'); return response.json(); })
        .then(data => {
            // Verificar se o resultado contém unidades
            if (!data.core_unidadecargo || data.core_unidadecargo.length === 0) {
                throw new Error(`Nenhuma unidade encontrada para a sigla ${siglaFiltro}`);
            }
            
            loadingEl.remove();
            if (!originalData) originalData = data; // Manter dados originais
            g.selectAll('*').remove();
            console.log(`Dados filtrados recebidos: ${data.core_unidadecargo.length} unidades`);
            filteredData = data;
            
            // Filtrar os dados para incluir apenas a unidade selecionada e suas subordinadas diretas
            const unidadePrincipal = data.core_unidadecargo.find(u => 
                u.sigla === siglaFiltro || u.sigla_unidade === siglaFiltro
            );
            
            if (unidadePrincipal) {
                console.log(`Unidade principal encontrada: ${unidadePrincipal.denominacao_unidade}`);
                
                // Se encontrou a unidade principal, filtrar os dados para mostrar apenas ela e suas subordinadas diretas
                const codigoPrincipal = unidadePrincipal.codigo_unidade;
                
                // Transformar os dados com filtragem adicional
                const hierarchicalData = transformData(data, codigoPrincipal);
                
                root = d3.hierarchy(hierarchicalData);
                root.x0 = 0; root.y0 = 0;
                
                // Manter o comportamento padrão de colapso inicial (apenas primeiro nível visível)
                if (root.children) {
                    root.children.forEach(child => collapseAtLevel(child, 0));
                }
                
                update(root);
                
                // Ajustar o zoom para mostrar toda a estrutura
                setTimeout(() => {
                    const maxDepth = getMaxVisibleDepth(root);
                    const scale = Math.max(0.3, 0.9 - (maxDepth * 0.1));
                    const initialTransform = d3.zoomIdentity.translate(50, height / 2).scale(scale);
                    svg.call(zoomBehavior.transform, initialTransform);
                }, 100);
            } else {
                console.log("Unidade principal não encontrada nos dados retornados. Mostrando todos os dados.");
                const hierarchicalData = transformData(data);
                root = d3.hierarchy(hierarchicalData);
                root.x0 = 0; root.y0 = 0;
                if (root.children) { 
                    // Colapsar todos os nós quando não temos unidade principal
                    root.children.forEach(child => collapseAtLevel(child, 0)); 
                }
                update(root);
            }
            
            const filtrosAtivos = document.getElementById('filtrosAtivos');
            const semFiltros = document.getElementById('semFiltros');
            if (filtrosAtivos) {
                const filtros = [];
                if (siglaFiltro) filtros.push(`Sigla: ${siglaFiltro}`);
                if (filtros.length > 0) {
                    if (semFiltros) semFiltros.style.display = 'none';
                    
                    // Verificar quantas unidades realmente estão sendo exibidas no organograma filtrado
                    let unidadesExibidas = 0;
                    if (unidadePrincipal) {
                        // Contar unidade principal + subordinadas diretas
                        const unidadesFiltradas = data.core_unidadecargo.filter(u => {
                            if (u.codigo_unidade === unidadePrincipal.codigo_unidade) return true;
                            // Verificar se é subordinada direta usando o grafo
                            if (u.grafo && unidadePrincipal.grafo) {
                                const partesPai = unidadePrincipal.grafo.split('-');
                                const partesFilho = u.grafo.split('-');
                                return partesFilho.length === partesPai.length + 1 && u.grafo.startsWith(unidadePrincipal.grafo);
                            }
                            return false;
                        });
                        unidadesExibidas = unidadesFiltradas.length;
                    }
                    
                    filtrosAtivos.innerHTML = `<strong>Filtros ativos:</strong> ${filtros.join(', ')} <span class="badge bg-primary">${unidadesExibidas} unidade(s)</span>`;
                } else {
                    if (semFiltros) semFiltros.style.display = 'inline';
                    filtrosAtivos.innerHTML = `<strong>Filtros ativos:</strong> <span id="semFiltros">Nenhum filtro aplicado</span>`;
                }
            }
            
            // 2. Agora, buscar dados dos cargos para a tabela
            console.log("Buscando dados de cargos com a sigla/código:", siglaFiltro);
            buscarDadosCargos(siglaFiltro, '', '');
        })
        .catch(error => {
            console.error('Erro ao aplicar filtros:', error);
            loadingEl.attr('class', 'alert alert-danger m-3')
                .html(`<i class="fas fa-exclamation-circle me-2"></i> Erro ao filtrar dados: ${error.message}. Tente novamente.`);
            setTimeout(() => { loadingEl.transition().duration(500).style('opacity', 0).remove(); }, 5000);
        });
};

// Função para buscar dados dos cargos para a tabela
function buscarDadosCargos(sigla = '', tipoCargo = '', nivel = '', pagina = 1, tamanhoPagina = 20) {
    console.log(`Buscando cargos: sigla=${sigla}, tipoCargo=${tipoCargo}, nivel=${nivel}, página=${pagina}, tamanho=${tamanhoPagina}`);
    
    // Mostrar indicador de carregamento
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
    
    // Desabilitar botões de paginação durante o carregamento
    const btnAnterior = document.getElementById('btn-pagina-anterior');
    const btnProximo = document.getElementById('btn-pagina-proxima');
    if (btnAnterior) btnAnterior.disabled = true;
    if (btnProximo) btnProximo.disabled = true;
    
    // Construir URL com parâmetros de filtro e paginação
    let url = `/api/cargos_diretos/?pagina=${pagina}&tamanho=${tamanhoPagina}`;
    if (sigla) url += `&sigla=${encodeURIComponent(sigla)}`;
    if (tipoCargo && tipoCargo !== 'Todos os cargos') url += `&tipo_cargo=${encodeURIComponent(tipoCargo)}`;
    if (nivel) url += `&nivel=${encodeURIComponent(nivel)}`;
    
    console.log('URL da API:', url);
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Dados recebidos da API:', data);
            
            if (!data.cargos) {
                throw new Error('Resposta da API não contém o campo "cargos"');
            }
            
            // Ocultar indicador de carregamento
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            // Atualizar tabela com os cargos recebidos
            const tbody = document.getElementById('tabelaCargosBody');
            if (!tbody) {
                console.error('Elemento tabelaCargosBody não encontrado');
                return;
            }
            
            tbody.innerHTML = '';
            
            const cargos = data.cargos;
            console.log(`Processando ${cargos.length} cargos para exibição`);
            
            if (cargos.length === 0) {
                const tr = document.createElement('tr');
                tr.innerHTML = '<td colspan="9" class="text-center">Nenhum cargo encontrado com os filtros aplicados</td>';
                tbody.appendChild(tr);
            } else {
                cargos.forEach((cargo, index) => {
                    try {
                        console.log('Cargo:', cargo); // Para depuração
                        
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${cargo.area || cargo.sigla_unidade || '-'}</td>
                            <td>${cargo.categoria_unidade || cargo.tipo_unidade || '-'}</td>
                            <td>${cargo.tipo_cargo || '-'}</td>
                            <td>${cargo.denominacao || '-'}</td>
                            <td>${cargo.categoria || '-'}</td>
                            <td>${cargo.nivel || '-'}</td>
                            <td>${cargo.quantidade || '0'}</td>
                            <td>${cargo.pontos ? Number(cargo.pontos).toFixed(2) : '0.00'}</td>
                            <td>R$ ${cargo.valor_unitario ? Number(cargo.valor_unitario).toFixed(2) : '0.00'}</td>
                        `;
                        tbody.appendChild(tr);
                    } catch (err) {
                        console.error(`Erro ao processar cargo ${index}:`, err, cargo);
                    }
                });
            }
            
            // Atualizar informações de paginação
            const totalItens = data.total_itens || 0;
            const totalPaginas = data.total_paginas || 1;
            const paginaAtual = data.pagina_atual || pagina;
            
            // Atualizar texto de informação da paginação
            const paginacaoInfo = document.getElementById('paginacao-info');
            if (paginacaoInfo) {
                paginacaoInfo.textContent = `Página ${paginaAtual} de ${totalPaginas} (${totalItens} itens)`;
            }
            
            // Habilitar/desabilitar botões de paginação conforme necessário
            if (btnAnterior) btnAnterior.disabled = paginaAtual <= 1;
            if (btnProximo) btnProximo.disabled = paginaAtual >= totalPaginas;
            
            // Atualizar contagem de resultados
            const resultCount = document.getElementById('resultCount');
            if (resultCount) {
                resultCount.textContent = `Mostrando ${cargos.length} de ${totalItens} cargos`;
            }
            
            // Disparar evento para notificar que os dados estão disponíveis
            document.dispatchEvent(new CustomEvent('dadosCargoDisponivel', { 
                detail: { 
                    cargos: cargos 
                } 
            }));
        })
        .catch(error => {
            console.error('Erro ao buscar dados:', error);
            
            // Ocultar indicador de carregamento
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            
            // Mostrar mensagem de erro na tabela
            const tbody = document.getElementById('tabelaCargosBody');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">Erro ao carregar dados: ${error.message}</td></tr>`;
            }
            
            // Manter botões de paginação desabilitados
            if (btnAnterior) btnAnterior.disabled = true;
            if (btnProximo) btnProximo.disabled = true;
            
            // Atualizar mensagem de paginação para indicar erro
            const paginacaoInfo = document.getElementById('paginacao-info');
            if (paginacaoInfo) {
                paginacaoInfo.textContent = 'Erro ao carregar dados';
            }
        });
}

// Função para atualizar o estado dos botões de paginação
function atualizarBotoesPaginacao() {
    const btnAnterior = document.getElementById('btn-pagina-anterior');
    const btnProximo = document.getElementById('btn-pagina-proxima');
    const paginacaoInfo = document.getElementById('paginacao-info');
    
    if (!paginacaoInfo || !btnAnterior || !btnProximo) {
        console.error('Elementos de paginação não encontrados');
        return;
    }
    
    const match = paginacaoInfo.textContent.match(/Página (\d+) de (\d+)/);
    
    if (match && match[1] && match[2]) {
        const paginaAtual = parseInt(match[1]);
        const totalPaginas = parseInt(match[2]);
        
        btnAnterior.disabled = paginaAtual <= 1;
        btnProximo.disabled = paginaAtual >= totalPaginas;
        
        btnAnterior.style.cursor = btnAnterior.disabled ? 'default' : 'pointer';
        btnProximo.style.cursor = btnProximo.disabled ? 'default' : 'pointer';
    } else {
        btnAnterior.disabled = true;
        btnProximo.disabled = true;
    }
}

const limparFiltros = () => {
    // Limpar seleção de unidade
    if (typeof $ !== 'undefined' && $.fn.select2) {
        $('#filtroSigla').val(null).trigger('change');
    } else {
        document.getElementById('filtroSigla').value = '';
    }
    
    const loadingEl = container.append('div')
        .attr('class', 'alert alert-info m-3')
        .html('<i class="fas fa-spinner fa-spin me-2"></i> Carregando dados originais...');
    if (originalData) {
        loadingEl.remove();
        g.selectAll('*').remove();
        console.log("Restaurando visualização original dos dados em memória");
        
        const hierarchicalData = transformData(originalData);
        root = d3.hierarchy(hierarchicalData);
        root.x0 = 0;
        root.y0 = 0;
        if (root.children) {
            root.children.forEach(child => collapseAtLevel(child, 0));
        }
        
        update(root);
        
        // Buscar dados padrão para a tabela (por exemplo, SE)
        buscarDadosCargos('SE', '', '');
        
        // Aplicar zoom adequado
        setTimeout(() => {
            const initialTransform = d3.zoomIdentity.translate(width / 10, height / 2).scale(0.55);
            svg.call(zoomBehavior.transform, initialTransform);
        }, 100);
        
        
        const filtrosAtivos = document.getElementById('filtrosAtivos');
        const semFiltros = document.getElementById('semFiltros');
        if (filtrosAtivos) {
            if (semFiltros) semFiltros.style.display = 'inline';
            filtrosAtivos.innerHTML = '<strong>Filtros ativos:</strong> <span id="semFiltros">Nenhum filtro aplicado</span>';
        }
        return;
    }
    fetch('/api/organograma-filter/')
        .then(response => { if (!response.ok) throw new Error('Erro ao carregar dados originais'); return response.json(); })
        .then(data => {
            loadingEl.remove();
            originalData = data;
            g.selectAll('*').remove();
            
            // Processar dados, que também preencherá o cache
            processarDados(data);
            
            // Buscar dados padrão para a tabela (por exemplo, SE)
            buscarDadosCargos('SE', '', '');
            
            const filtrosAtivos = document.getElementById('filtrosAtivos');
            const semFiltros = document.getElementById('semFiltros');
            if (filtrosAtivos) {
                if (semFiltros) semFiltros.style.display = 'inline';
                filtrosAtivos.innerHTML = '<strong>Filtros ativos:</strong> <span id="semFiltros">Nenhum filtro aplicado</span>';
            }
        })
        .catch(error => {
            console.error('Erro ao limpar filtros:', error);
            loadingEl.attr('class', 'alert alert-danger m-3')
                .html(`<i class="fas fa-exclamation-circle me-2"></i> Erro ao limpar filtros: ${error.message}. Tente novamente.`);
            setTimeout(() => { loadingEl.transition().duration(500).style('opacity', 0).remove(); }, 5000);
        });
};

document.addEventListener('DOMContentLoaded', function() {
    const btnAplicarFiltros = document.getElementById('aplicarFiltros');
    if (btnAplicarFiltros) btnAplicarFiltros.addEventListener('click', aplicarFiltros);
    const btnLimparFiltros = document.getElementById('limparFiltros');
    if (btnLimparFiltros) btnLimparFiltros.addEventListener('click', limparFiltros);
});

/* ============================================================
   Estilização do Tooltip via CSS
================================================================ */
const style = document.createElement('style');
style.textContent = `
  .organograma-tooltip {
    position: fixed;
    background: white;
    border-radius: 8px;
    padding: 12px;
    font-size: 12px;
    width: 320px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.15), 0 2px 8px rgba(0,0,0,0.1);
    box-shadow: 0 8px 16px rgba(0,0,0,0.15), 0 2px 8px rgba(0,0,0,0.1);
    border: 1px solid rgba(0,0,0,0.1);
    pointer-events: none;
    z-index: 1000;
    max-height: 300px;
    overflow-y: auto;
    max-height: 300px;
    overflow-y: auto;
  }
  
  /* Setinhas do tooltip */
  
  /* Setinhas do tooltip */
  .organograma-tooltip::after {
    content: '';
    position: absolute;
    width: 10px;
    height: 10px;
    width: 10px;
    height: 10px;
    background: white;
    transform: rotate(45deg);
    border: 1px solid rgba(0,0,0,0.1);
  }
  
  /* Posição direita (padrão) - setinha à esquerda do tooltip */
  .organograma-tooltip.right::after { 
    left: -5px; 
    top: 50%; 
    margin-top: -5px; 
    border-right: none; 
    border-bottom: none; 
  }
  
  /* Posição esquerda - setinha à direita do tooltip */
  .organograma-tooltip.left::after { 
    right: -5px; 
    top: 50%; 
    margin-top: -5px; 
    border-left: none; 
    border-top: none; 
  }
  
  /* Posição superior - setinha embaixo do tooltip */
  .organograma-tooltip.top::after { 
    bottom: -5px; 
    left: 50%; 
    margin-left: -5px; 
    border-top: none; 
    border-right: none; 
  }
  
  /* Posição inferior - setinha em cima do tooltip */
  .organograma-tooltip.bottom::after { 
    top: -5px; 
    left: 50%; 
    margin-left: -5px; 
    border-bottom: none; 
    border-left: none; 
  }
  
  .tooltip-title { 
    font-size: 14px; 
    font-weight: 600; 
    color: #2c5282; 
    margin-bottom: 8px; 
    border-bottom: 1px solid #e2e8f0; 
    padding-bottom: 8px; 
    line-height: 1.3;
  }
  
  
  /* Posição direita (padrão) - setinha à esquerda do tooltip */
  .organograma-tooltip.right::after { 
    left: -5px; 
    top: 50%; 
    margin-top: -5px; 
    border-right: none; 
    border-bottom: none; 
  }
  
  /* Posição esquerda - setinha à direita do tooltip */
  .organograma-tooltip.left::after { 
    right: -5px; 
    top: 50%; 
    margin-top: -5px; 
    border-left: none; 
    border-top: none; 
  }
  
  /* Posição superior - setinha embaixo do tooltip */
  .organograma-tooltip.top::after { 
    bottom: -5px; 
    left: 50%; 
    margin-left: -5px; 
    border-top: none; 
    border-right: none; 
  }
  
  /* Posição inferior - setinha em cima do tooltip */
  .organograma-tooltip.bottom::after { 
    top: -5px; 
    left: 50%; 
    margin-left: -5px; 
    border-bottom: none; 
    border-left: none; 
  }
  
  .tooltip-title { 
    font-size: 14px; 
    font-weight: 600; 
    color: #2c5282; 
    margin-bottom: 8px; 
    border-bottom: 1px solid #e2e8f0; 
    padding-bottom: 8px; 
    line-height: 1.3;
  }
  
  .tooltip-cargo { font-size: 12px; color: #4a5568; margin-bottom: 8px; }
  .tooltip-field { display: flex; justify-content: space-between; margin-bottom: 4px; align-items: flex-start; }
  .tooltip-label { color: #718096; font-weight: 500; }
  .tooltip-value { color: #0ea5e9; font-weight: 500; text-align: right; }
  .tooltip-percentage { color: #dc2626; font-weight: bold; background-color: #fef2f2; padding: 2px 6px; border-radius: 4px; }
  .tooltip-value { color: #0ea5e9; font-weight: 500; text-align: right; }
  .tooltip-percentage { color: #dc2626; font-weight: bold; background-color: #fef2f2; padding: 2px 6px; border-radius: 4px; }
  .cargos-detalhes { border-top: 1px dashed #e2e8f0; padding-top: 6px; margin-top: 6px; }
  .detalhes-lista { display: flex; flex-direction: column; align-items: flex-end; }
  .detalhe-item { margin-bottom: 2px; white-space: nowrap; }
  .tooltip-subtitle { font-size: 13px; font-weight: 600; color: #4a5568; margin: 8px 0; }
  .badge { 
    font-size: 11px; 
    padding: 3px 8px; 
    border-radius: 12px; 
    background: #0ea5e9; 
    color: white; 
    font-weight: 500; 
    margin-left: 8px;
    display: inline-block;
    white-space: nowrap;
  }
  
  /* Forçar cores dos nós */
  .node--internal circle,
  .node.collapsed circle {
    fill: #87ceeb !important; /* Azul céu para nós pais */
  }
  
  .node--leaf circle {
    fill: #ffffff !important; /* Branco para nós folhas */
  }
  .badge { 
    font-size: 11px; 
    padding: 3px 8px; 
    border-radius: 12px; 
    background: #0ea5e9; 
    color: white; 
    font-weight: 500; 
    margin-left: 8px;
    display: inline-block;
    white-space: nowrap;
  }
  
  /* Forçar cores dos nós */
  .node--internal circle,
  .node.collapsed circle {
    fill: #87ceeb !important; /* Azul céu para nós pais */
  }
  
  .node--leaf circle {
    fill: #ffffff !important; /* Branco para nós folhas */
  }
`;
document.head.appendChild(style);

/**
 * Inicializa o dropdown de unidades
 */
function initializeUnits() {
    const filtroSigla = document.getElementById('filtroSigla');
    if (!filtroSigla) return;
    
    // Popular o dropdown de unidades a partir dos dados
    if (window.organogramaData && Array.isArray(window.organogramaData.core_unidadecargo)) {
        console.log("Inicializando dropdown de unidades...");
        
        // Agrupar por código de unidade para evitar duplicações
        const unidades = {};
        window.organogramaData.core_unidadecargo.forEach(item => {
            const codigo = item.codigo_unidade;
            if (!unidades[codigo]) {
                unidades[codigo] = {
                    codigo: codigo,
                    nome: item.denominacao_unidade,
                    sigla: item.sigla || item.sigla_unidade
                };
            }
        });
        
        // Limpar o select, mantendo apenas a opção padrão
        while (filtroSigla.options.length > 1) {
            filtroSigla.remove(1);
        }
        
        // Primeiro, adicionar a opção SE (Secretaria Executiva) no topo se existir nos dados
        const secretariaExecutiva = Object.values(unidades).find(u => u.sigla === 'SE');
        if (secretariaExecutiva) {
            const seOption = document.createElement('option');
            seOption.value = secretariaExecutiva.sigla;
            seOption.textContent = `${secretariaExecutiva.sigla} - ${secretariaExecutiva.nome}`;
            filtroSigla.appendChild(seOption);
        }
        
        // Depois adicionar todas as outras unidades
        Object.values(unidades)
            .filter(unidade => unidade.sigla) // Filtrar apenas unidades com sigla
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
                option.value = unidade.sigla;
                option.textContent = `${unidade.sigla} - ${unidade.nome}`;
                filtroSigla.appendChild(option);
            });
        
        // Verificar se estamos usando Select2 e reinicializar
        if (typeof $ !== 'undefined' && $.fn.select2) {
            try {
                $(filtroSigla).select2('destroy');
            } catch (e) {
                // Ignorar erro se o Select2 ainda não foi inicializado
            }
            
            $(filtroSigla).select2({
                placeholder: "Digite para pesquisar uma unidade...",
                allowClear: true,
                width: '100%',
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
                        // Não mostrar mensagem "Digite mais X caracteres"
                        return "";
                    }
                }
            });
        }
    }
}

// Função para exibir mensagens de erro
function exibirErro(mensagem) {
    console.error("Erro no organograma:", mensagem);
    if (container && container.node) {
        const errorDiv = container.append('div')
            .attr('class', 'alert alert-danger m-3')
            .html(`<i class="fas fa-exclamation-circle me-2"></i>${mensagem}`);
    }
}

// Função para exibir mensagens de erro
function exibirErro(mensagem) {
    console.error("Erro no organograma:", mensagem);
    if (container && container.node) {
        const errorDiv = container.append('div')
            .attr('class', 'alert alert-danger m-3')
            .html(`<i class="fas fa-exclamation-circle me-2"></i>${mensagem}`);
    }
}
