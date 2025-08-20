# Custom BOM - Relatórios de Custo - Módulo Odoo 14

## Descrição
Módulo personalizado para gerenciamento de Bill of Materials (BOM) no Odoo 14, com funcionalidades customizadas para atender necessidades específicas de fabricação e **relatórios detalhados de custos**.

## Funcionalidades

### 🏭 Gerenciamento de BOMs
- Criação e gerenciamento de BOMs personalizados
- Controle de status (Rascunho, Confirmado, Concluído)
- Linhas de BOM com produtos, quantidades e unidades de medida
- Numeração automática com prefixo CBOM/
- Suporte a múltiplas empresas
- Interface intuitiva com visualizações tree, form e search

### 📊 Relatórios de Custo Detalhados
- **Análise hierárquica completa** de produtos e subconjuntos
- **Cálculos de custos** de fabricação com operações
- **Tempos de operação** em formato HH:MM:SS
- **Custos de centros de trabalho** por operação
- **Taxas de compra** das últimas aquisições
- **Exportação para CSV** com formatação brasileira (vírgula decimal)
- **Configurações flexíveis** para incluir/excluir elementos

## Instalação
1. Copie a pasta `customBom` para o diretório de addons do Odoo
2. Atualize a lista de aplicações no Odoo
3. Instale o módulo "Custom BOM - Relatórios de Custo"
4. O módulo estará disponível no menu principal

## Dependências
- Odoo 14.0
- Módulo base
- Módulo mrp (Manufacturing)
- Módulo purchase (para taxas de compra)

## Estrutura do Módulo
```
customBom/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── custom_bom.py
├── wizards/
│   ├── __init__.py
│   └── cost_report_wizard.py
├── views/
│   ├── custom_bom_views.xml
│   └── cost_report_wizard_views.xml
├── security/
│   └── ir.model.access.csv
├── data/
│   └── custom_bom_data.xml
└── README.md
```

## Uso

### Gerenciamento de BOMs
1. Acesse o menu "Custom BOM" > "Custom BOMs"
2. Clique em "Criar" para adicionar um novo BOM
3. Preencha as informações básicas (produto, empresa)
4. Adicione as linhas do BOM com produtos e quantidades
5. Use os botões de ação para alterar o status

### Relatórios de Custo
1. **Via Menu**: Custom BOM > Relatório de Custo
2. **Via BOM**: Clique no botão "Relatório de Custo" em qualquer BOM
3. **Selecione os BOMs** que deseja analisar
4. **Configure as opções**:
   - Níveis máximos de hierarquia
   - Incluir operações
   - Incluir componentes
   - Incluir taxas de compra
5. **Clique em "Gerar Relatório"**
6. **Faça o download** do arquivo CSV

## Colunas do Relatório CSV
- **Código LdM Principal**: Código do produto principal
- **Código Item**: Código do item/componente
- **Níveis 1-10**: Hierarquia de produtos e subconjuntos
- **Ref. LdM Item**: Referência da lista de materiais
- **Qtd Item**: Quantidade necessária
- **Unidade de Medida**: UoM do item
- **Custo Unit. Item**: Custo unitário padrão
- **Custo Total Linha**: Custo total calculado
- **Taxas Última Compra**: Impostos da última compra
- **Tipo de Linha**: Produto Principal, Subconjunto, Operação, Componente
- **Operação: Nome**: Nome da operação de fabricação
- **Operação: Centro Trabalho**: Centro de trabalho da operação
- **Operação: Tempo**: Tempo total em HH:MM:SS
- **Operação: Custo**: Custo total da operação

## Permissões
- **Usuários**: Podem criar, editar e visualizar BOMs e relatórios
- **Administradores**: Podem criar, editar, visualizar e excluir BOMs

## Personalização
O módulo pode ser facilmente personalizado para adicionar:
- Campos adicionais nos BOMs
- Validações customizadas
- Relatórios específicos
- Integrações com outros módulos
- Novas opções de configuração nos relatórios

## Características Técnicas
- **Formatação brasileira**: Decimais com vírgula
- **Encoding UTF-8**: Suporte completo a caracteres especiais
- **Delimitador CSV**: Ponto e vírgula (;) para compatibilidade com Excel
- **Cálculos recursivos**: Análise completa de estruturas complexas
- **Performance otimizada**: Processamento eficiente de BOMs grandes

## Suporte
Para dúvidas ou sugestões, entre em contato com a equipe de desenvolvimento.

---

## 🎯 Casos de Uso

### Para Engenheiros de Produção
- Análise detalhada de custos de fabricação
- Comparação de custos entre diferentes BOMs
- Identificação de gargalos de custo
- Planejamento de preços de venda

### Para Contadores
- Análise de custos para fechamento contábil
- Relatórios para auditoria
- Controle de custos por produto
- Análise de rentabilidade

### Para Compras
- Identificação de componentes de maior custo
- Análise de fornecedores por custo
- Planejamento de negociações
- Controle de variações de preço
