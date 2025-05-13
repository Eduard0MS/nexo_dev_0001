// Função para transformar os dados no formato hierárquico
function transformData(data) {
    console.log("Transformando dados para o organograma:", data);
    
    // Verificar se existe estrutura de dados esperada
    if (!data || !data.core_unidadecargo || !Array.isArray(data.core_unidadecargo)) {
        console.error("Dados inválidos para o organograma");
        return {
            nome: "Ministério do Planejamento e Orçamento - MPO",
            cargo: "Organograma Completo",
            secretaria: "MPO",
            codigo: "308804",
            tipo_unidade: "Ministério",
            cargos_detalhes: [],
            children: []
        };
    }
    
    // Disparar evento com os dados brutos para que a tabela possa acessá-los
    try {
        setTimeout(() => {
            console.log("Disparando evento dadosOrganogramaDisponivel");
            document.dispatchEvent(new CustomEvent('dadosOrganogramaDisponivel', { 
                detail: { dados: data.core_unidadecargo }
            }));
        }, 100);
    } catch (e) {
        console.error("Erro ao disparar evento dadosOrganogramaDisponivel:", e);
    }
    
    const unidades = data.core_unidadecargo;
    
    // Calcular total geral de todas as unidades no grafo (para a raiz MPO)
    let mpoTotalGasto = 0;
    let mpoTotalPontos = 0;
    
    // Primeiro passo: Somar todos os valores de todas as unidades para MPO
    unidades.forEach(unit => {
        mpoTotalGasto += parseFloat(unit.gasto_total || 0);
        mpoTotalPontos += parseFloat(unit.pontos_total || unit.pontos * unit.quantidade || 0);
    });
    
    // Exibir informações de depuração
    console.log(`MPO - Total geral calculado a partir de ${unidades.length} unidades:`);
    console.log(`Gasto Total: R$ ${mpoTotalGasto.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`);
    console.log(`Pontos Totais: ${mpoTotalPontos.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`);
    
    // Primeiro, vamos agrupar todas as unidades por código E grafo
    const unidadesPorCodigoEGrafo = {};
    unidades.forEach(unit => {
        // Criar uma chave única combinando código e grafo
        const chave = `${unit.codigo_unidade}|${unit.grafo || ''}`;
        
        if (!unidadesPorCodigoEGrafo[chave]) {
            unidadesPorCodigoEGrafo[chave] = {
                maiorNivel: -1,
                unidadePrincipal: null,
                quantidade: 0,
                pontos: 0,
                pontos_total: 0,
                gasto_total: 0,
                todas: [],
                cargos_detalhes: {} // Novo objeto para agrupar cargos
            };
        }
        
        const grupo = unidadesPorCodigoEGrafo[chave];
        grupo.todas.push(unit);
        
        // Atualizar quantidade e valores
        grupo.quantidade += (unit.quantidade || 0);
        grupo.pontos += (unit.pontos || 0);
        grupo.pontos_total += (unit.pontos_total || unit.pontos * unit.quantidade || 0);
        grupo.gasto_total += (unit.gasto_total || 0);
        
        // Agrupar cargos por tipo, categoria e nível
        if (unit.tipo_cargo && unit.categoria !== undefined && unit.nivel !== undefined) {
            const cargoKey = `${unit.tipo_cargo} ${unit.categoria} ${unit.nivel}`;
            if (!grupo.cargos_detalhes[cargoKey]) {
                grupo.cargos_detalhes[cargoKey] = 0;
            }
            grupo.cargos_detalhes[cargoKey] += (unit.quantidade || 0);
        }
        
        // Verificar se é o cargo de maior nível
        if (unit.nivel > grupo.maiorNivel) {
            grupo.maiorNivel = unit.nivel;
            grupo.unidadePrincipal = unit;
        }
    });
    
    // Função para criar um nó a partir de uma unidade agrupada
    function createNode(chave) {
        const grupo = unidadesPorCodigoEGrafo[chave];
        if (!grupo) return null;
        
        const unit = grupo.unidadePrincipal;
        
        // Converter o objeto de cargos_detalhes em um array para uso no tooltip
        const cargosArray = Object.entries(grupo.cargos_detalhes).map(([cargo, quantidade]) => {
            return { cargo, quantidade };
        }).sort((a, b) => a.cargo.localeCompare(b.cargo));
        
        return {
            nome: unit.denominacao_unidade || "Unidade sem nome",
            codigo: unit.codigo_unidade,
            cargo: unit.tipo_cargo ? `${unit.tipo_cargo} ${unit.nivel || ''}` : "Sem cargo",
            secretaria: unit.sigla || unit.sigla_unidade || "",
            tipo_unidade: unit.tipo_unidade || "",
            nivel: unit.nivel,
            grafo: unit.grafo || "",
            quantidade: grupo.quantidade,
            pontos: grupo.pontos,
            pontos_total: grupo.pontos_total,
            valor_unitario: unit.valor_unitario,
            gasto_total: grupo.gasto_total,
            cargos_detalhes: cargosArray,
            children: [],
            is_sibling: false
        };
    }
    
    // Criar a raiz do organograma
    const mpoChave = "308804|308804";
    const mpoNode = unidadesPorCodigoEGrafo[mpoChave]?.unidadePrincipal;
    let rootNode = {
        nome: "Ministério do Planejamento e Orçamento - MPO",
        cargo: "Organograma Completo",
        secretaria: "MPO",
        codigo: "308804",
        tipo_unidade: "Ministério",
        cargos_detalhes: [],
        children: []
    };
    
    // Se encontrarmos a unidade MPO, atualizar com seus dados
    if (mpoNode) {
        const grupo = unidadesPorCodigoEGrafo[mpoChave];
        
        // Converter o objeto de cargos_detalhes em um array para uso no tooltip
        const cargosArray = Object.entries(grupo.cargos_detalhes || {}).map(([cargo, quantidade]) => {
            return { cargo, quantidade };
        }).sort((a, b) => a.cargo.localeCompare(b.cargo));
        
        rootNode.nome = mpoNode.denominacao_unidade || rootNode.nome;
        rootNode.cargo = mpoNode.tipo_cargo ? `${mpoNode.tipo_cargo} ${mpoNode.nivel || ''}` : rootNode.cargo;
        rootNode.secretaria = mpoNode.sigla || "MPO";
        rootNode.tipo_unidade = mpoNode.tipo_unidade || rootNode.tipo_unidade;
        rootNode.nivel = mpoNode.nivel;
        rootNode.grafo = mpoNode.grafo || "308804";
        rootNode.quantidade = grupo.quantidade;
        rootNode.pontos = grupo.pontos;
        // Usar os totais calculados de todo o grafo para a raiz (MPO)
        rootNode.pontos_total = mpoTotalPontos;
        rootNode.valor_unitario = mpoNode.valor_unitario;
        rootNode.gasto_total = mpoTotalGasto;
        rootNode.cargos_detalhes = cargosArray;
    }
    
    // Mapa para armazenar todos os nós
    const nodesMap = { "308804": rootNode };
    
    // Criar estrutura hierárquica baseada no grafo
    Object.keys(unidadesPorCodigoEGrafo).forEach(chave => {
        if (chave === mpoChave) return;
        
        const unit = unidadesPorCodigoEGrafo[chave].unidadePrincipal;
        if (!unit.grafo) return;
        
        const grafoParts = unit.grafo.split('-');
        const parentCode = grafoParts[grafoParts.length - 2];
        const currentCode = unit.codigo_unidade;
        
        // Criar nó se ainda não existe
        if (!nodesMap[currentCode]) {
            nodesMap[currentCode] = createNode(chave);
        }
        
        // Adicionar ao pai apropriado
        if (parentCode && nodesMap[parentCode]) {
            const parentNode = nodesMap[parentCode];
            if (!parentNode.children.some(child => child.codigo === currentCode && child.grafo === unit.grafo)) {
                parentNode.children.push(nodesMap[currentCode]);
            }
        } else if (parentCode === "308804") {
            // Adicionar diretamente à raiz
            if (!rootNode.children.some(child => child.codigo === currentCode && child.grafo === unit.grafo)) {
                rootNode.children.push(nodesMap[currentCode]);
            }
        }
    });
    
    // Ordenar todos os níveis
    function sortChildren(node) {
        if (node.children && node.children.length > 0) {
            // Ordenar por nível do cargo (decrescente)
            node.children.sort((a, b) => (b.nivel || 0) - (a.nivel || 0));
            
            // Marcar irmãos
            if (node.children.length > 1) {
                node.children.forEach(child => {
                    child.is_sibling = true;
                });
            }
            
            node.children.forEach(sortChildren);
        }
    }
    
    sortChildren(rootNode);
    
    return rootNode;
} 