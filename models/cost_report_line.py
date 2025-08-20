# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class CostReportLine(models.Model):
    _name = 'cost.report.line'
    _description = 'Linha do Relatório de Custo'
    _order = 'sequence, id'
    _rec_name = 'item_code'

    # Campos de identificação
    report_id = fields.Many2one('cost.report', string='Relatório', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequência', default=10)
    
    # Campos principais
    bom_main_code = fields.Char(string='Código LdM Principal', readonly=True)
    item_code = fields.Char(string='Código Item', readonly=True)
    
    # Campos de hierarquia (Níveis 1-10)
    level_1 = fields.Char(string='Nível 1', readonly=True)
    level_2 = fields.Char(string='Nível 2', readonly=True)
    level_3 = fields.Char(string='Nível 3', readonly=True)
    level_4 = fields.Char(string='Nível 4', readonly=True)
    level_5 = fields.Char(string='Nível 5', readonly=True)
    level_6 = fields.Char(string='Nível 6', readonly=True)
    level_7 = fields.Char(string='Nível 7', readonly=True)
    level_8 = fields.Char(string='Nível 8', readonly=True)
    level_9 = fields.Char(string='Nível 9', readonly=True)
    level_10 = fields.Char(string='Nível 10', readonly=True)
    
    # Campos de detalhes
    bom_reference = fields.Char(string='Ref. LdM Item', readonly=True)
    item_qty = fields.Float(string='Qtd Item', readonly=True)
    uom_name = fields.Char(string='Unidade de Medida', readonly=True)
    unit_cost = fields.Float(string='Custo Unit. Item', readonly=True)
    total_cost = fields.Float(string='Custo Total Linha', readonly=True)
    purchase_taxes = fields.Char(string='Taxas Última Compra', readonly=True)
    line_type = fields.Selection([
        ('produto_principal', 'Produto Principal'),
        ('subconjunto', 'Subconjunto'),
        ('operacao', 'Operação'),
        ('componente', 'Componente')
    ], string='Tipo de Linha', readonly=True)
    
    # Campos específicos de operação
    operation_name = fields.Char(string='Nome da Operação', readonly=True)
    workcenter_name = fields.Char(string='Centro de Trabalho', readonly=True)
    operation_time = fields.Char(string='Tempo (HH:MM:SS)', readonly=True)
    operation_cost = fields.Float(string='Custo da Operação', readonly=True)
    
    # Campos computados para formatação
    unit_cost_formatted = fields.Char(string='Custo Unit. Formatado', compute='_compute_formatted_fields', store=True)
    total_cost_formatted = fields.Char(string='Custo Total Formatado', compute='_compute_formatted_fields', store=True)
    operation_cost_formatted = fields.Char(string='Custo Op. Formatado', compute='_compute_formatted_fields', store=True)
    
    @api.depends('unit_cost', 'total_cost', 'operation_cost')
    def _compute_formatted_fields(self):
        """Formata os campos de custo para exibição brasileira"""
        for record in self:
            record.unit_cost_formatted = self._format_currency(record.unit_cost)
            record.total_cost_formatted = self._format_currency(record.total_cost)
            record.operation_cost_formatted = self._format_currency(record.operation_cost)
    
    def _format_currency(self, value):
        """Formata valor monetário para exibição brasileira"""
        if value is None:
            return 'R$ 0,00'
        try:
            formatted_value = "{:.2f}".format(float(value))
            return f"R$ {formatted_value.replace('.', ',')}"
        except (ValueError, TypeError):
            return 'R$ 0,00'
    
    def get_level_display(self):
        """Retorna o nível hierárquico para exibição"""
        levels = [self.level_1, self.level_2, self.level_3, self.level_4, self.level_5,
                 self.level_6, self.level_7, self.level_8, self.level_9, self.level_10]
        
        # Encontra o primeiro nível não vazio
        for i, level in enumerate(levels, 1):
            if level:
                return f"Nível {i}: {level}"
        return "Nível Principal"
    
    def get_hierarchy_path(self):
        """Retorna o caminho hierárquico completo"""
        levels = [self.level_1, self.level_2, self.level_3, self.level_4, self.level_5,
                 self.level_6, self.level_7, self.level_8, self.level_9, self.level_10]
        
        # Filtra níveis vazios e junta com " > "
        non_empty_levels = [level for level in levels if level]
        if non_empty_levels:
            return " > ".join(non_empty_levels)
        return "Nível Principal"
