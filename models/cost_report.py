# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CostReport(models.Model):
    _name = 'cost.report'
    _description = 'Relatório de Custo Detalhado'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Nome do Relatório', required=True, default='Relatório de Custo')
    bom_ids = fields.Many2many('mrp.bom', string='BOMs Analisados', readonly=True)
    max_display_levels = fields.Integer(string='Níveis de Hierarquia', readonly=True)
    include_operations = fields.Boolean(string='Inclui Operações', readonly=True)
    include_components = fields.Boolean(string='Inclui Componentes', readonly=True)
    include_taxes = fields.Boolean(string='Inclui Taxas', readonly=True)
    
    # Campos de resultado
    total_cost = fields.Float(string='Custo Total', compute='_compute_total_cost', store=True)
    total_operations = fields.Integer(string='Total de Operações', compute='_compute_counts', store=True)
    total_components = fields.Integer(string='Total de Componentes', compute='_compute_counts', store=True)
    total_products = fields.Integer(string='Total de Produtos', compute='_compute_counts', store=True)
    
    # Relacionamentos
    line_ids = fields.One2many('cost.report.line', 'report_id', string='Linhas do Relatório')
    
    # Campos de controle
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('generated', 'Gerado'),
        ('archived', 'Arquivado')
    ], string='Status', default='draft', tracking=True)
    
    company_id = fields.Many2one('res.company', string='Empresa', 
                                 default=lambda self: self.env.company)
    create_date = fields.Datetime(string='Data de Criação', readonly=True)
    create_uid = fields.Many2one('res.users', string='Criado por', readonly=True)
    
    @api.depends('line_ids.total_cost')
    def _compute_total_cost(self):
        """Calcula o custo total do relatório"""
        for record in self:
            record.total_cost = sum(record.line_ids.mapped('total_cost'))
    
    @api.depends('line_ids.line_type')
    def _compute_counts(self):
        """Calcula os totais de cada tipo de linha"""
        for record in self:
            lines = record.line_ids
            record.total_operations = len(lines.filtered(lambda l: l.line_type == 'operacao'))
            record.total_components = len(lines.filtered(lambda l: l.line_type == 'componente'))
            record.total_products = len(lines.filtered(lambda l: l.line_type in ['produto_principal', 'subconjunto']))
    
    def action_generate_report(self):
        """Gera o relatório de custo e armazena os dados"""
        if not self.bom_ids:
            raise UserError(_('Selecione pelo menos um BOM para gerar o relatório.'))
        
        # Limpa linhas existentes
        self.line_ids.unlink()
        
        # Gera o relatório usando o wizard
        wizard = self.env['cost.report.wizard'].create({
            'name': self.name,
            'bom_ids': [(6, 0, self.bom_ids.ids)],
            'max_display_levels': self.max_display_levels,
            'include_operations': self.include_operations,
            'include_components': self.include_components,
            'include_taxes': self.include_taxes,
        })
        
        # Gera os dados do relatório
        csv_data_rows = []
        wizard._generate_report_data_raw(csv_data_rows)
        
        # Converte os dados CSV para linhas do relatório
        self._create_report_lines(csv_data_rows)
        
        # Atualiza o status
        self.write({'state': 'generated'})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cost.report',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }
    
    def _create_report_lines(self, csv_data_rows):
        """Cria as linhas do relatório a partir dos dados CSV"""
        if not csv_data_rows or len(csv_data_rows) < 2:  # Pula o cabeçalho
            return
        
        # Pula o cabeçalho (primeira linha)
        data_rows = csv_data_rows[1:]
        
        for sequence, row in enumerate(data_rows, 1):
            if not row or all(not cell for cell in row):  # Pula linhas vazias
                continue
            
            # Mapeia os campos baseado na estrutura do CSV
            line_vals = {
                'report_id': self.id,
                'sequence': sequence,
                'bom_main_code': row[0] if len(row) > 0 else '',
                'item_code': row[1] if len(row) > 1 else '',
            }
            
            # Campos de hierarquia (posições 2 a 11)
            for i in range(10):
                if len(row) > 2 + i:
                    line_vals[f'level_{i+1}'] = row[2 + i] or ''
            
            # Campos de detalhes (posições 12 em diante)
            if len(row) > 12:
                line_vals.update({
                    'bom_reference': row[12] or '',
                    'item_qty': self._safe_float_convert(row[13]) if len(row) > 13 else 0.0,
                    'uom_name': row[14] if len(row) > 14 else '',
                    'unit_cost': self._safe_float_convert(row[15]) if len(row) > 15 else 0.0,
                    'total_cost': self._safe_float_convert(row[16]) if len(row) > 16 else 0.0,
                    'purchase_taxes': row[17] if len(row) > 17 else '',
                    'line_type': self._map_line_type(row[18]) if len(row) > 18 else 'componente',
                })
            
            # Campos específicos de operação
            if len(row) > 19:
                line_vals.update({
                    'operation_name': row[19] if len(row) > 19 else '',
                    'workcenter_name': row[20] if len(row) > 20 else '',
                    'operation_time': row[21] if len(row) > 21 else '',
                    'operation_cost': self._safe_float_convert(row[22]) if len(row) > 22 else 0.0,
                })
            
            # Cria a linha do relatório
            self.env['cost.report.line'].create(line_vals)
    
    def _safe_float_convert(self, value):
        """Converte valor para float de forma segura, tratando formatos brasileiros"""
        if not value:
            return 0.0
        
        try:
            # Remove espaços e substitui vírgula por ponto
            clean_value = str(value).strip().replace(',', '.')
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0
    
    def _map_line_type(self, type_str):
        """Mapeia o tipo de linha do CSV para o campo selection"""
        type_mapping = {
            'Produto Principal': 'produto_principal',
            'Subconjunto': 'subconjunto',
            'Operação': 'operacao',
            'Componente': 'componente'
        }
        return type_mapping.get(type_str, 'componente')
    
    def action_archive(self):
        """Arquiva o relatório"""
        self.write({'state': 'archived'})
    
    def action_draft(self):
        """Retorna para rascunho"""
        self.write({'state': 'draft'})
    
    def action_view_lines(self):
        """Abre a view das linhas do relatório"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Linhas do Relatório: {self.name}',
            'res_model': 'cost.report.line',
            'view_mode': 'tree,form',
            'domain': [('report_id', '=', self.id)],
            'context': {'default_report_id': self.id},
        }
