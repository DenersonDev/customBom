{
    'name': 'Custom BOM - Relatórios de Custo',
    'version': '14.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Módulo personalizado para gerenciamento de BOM e relatórios de custo detalhados',
    'description': """
        Módulo personalizado para gerenciamento de Bill of Materials (BOM) 
        com funcionalidades customizadas para o Odoo 14.
        
        Inclui:
        - Gerenciamento de BOMs personalizados
        - Relatórios detalhados de custos com operações
        - Análise hierárquica de produtos e subconjuntos
        - Cálculos de custos de fabricação
        - Exportação para CSV com formatação brasileira
    """,
    'author': 'Seu Nome',
    'website': 'https://www.seusite.com',
    'depends': ['base', 'mrp', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_bom_views.xml',
        'views/cost_report_wizard_views.xml',
        'data/custom_bom_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 1,
}
