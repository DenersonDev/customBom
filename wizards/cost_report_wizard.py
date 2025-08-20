# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import csv
from io import StringIO


class CostReportWizard(models.TransientModel):
    _name = 'cost.report.wizard'
    _description = 'Wizard para Relatório de Custo Detalhado'

    name = fields.Char(string='Nome do Relatório', default='Relatório de Custo Detalhado')
    bom_ids = fields.Many2many('mrp.bom', string='BOMs para Analisar', required=True)
    max_display_levels = fields.Integer(string='Níveis Máximos de Hierarquia', default=10)
    include_operations = fields.Boolean(string='Incluir Operações', default=True)
    include_components = fields.Boolean(string='Incluir Componentes', default=True)
    include_taxes = fields.Boolean(string='Incluir Taxas de Compra', default=True)
    filename = fields.Char(string='Nome do Arquivo', compute='_compute_filename')
    csv_data = fields.Binary(string='Arquivo CSV', readonly=True)
    
    @api.depends('bom_ids')
    def _compute_filename(self):
        for record in self:
            if record.bom_ids:
                bom_codes = [bom.code or bom.product_id.default_code or bom.product_id.name or 'BOM' for bom in record.bom_ids[:3]]
                record.filename = f'estrutura_custo_detalhada_{"_".join(bom_codes)}.csv'
            else:
                record.filename = 'estrutura_custo_detalhada.csv'

    def _format_float(self, value):
        """Formata valor numérico para string com 2 casas decimais usando vírgula"""
        if value is None:
            return '0,00'
        try:
            float_value = float(value)
            formatted_value = "{:.2f}".format(float_value)
            return formatted_value.replace('.', ',')
        except (ValueError, TypeError):
            return '0,00'

    def _format_duration(self, total_minutes_multiplied):
        """Converte minutos para formato HH:MM:SS"""
        if total_minutes_multiplied is None:
            return '00:00:00'
        try:
            total_minutes_float = float(total_minutes_multiplied)
            if total_minutes_float < 0:
                total_minutes_float = 0

            total_seconds_int = int(round(total_minutes_float * 60))
            hours = total_seconds_int // 3600
            remaining_seconds = total_seconds_int % 3600
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60
            
            return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
        except (ValueError, TypeError):
            return '00:00:00'

    def _get_string_value(self, value):
        """Converte valor para string de forma defensiva"""
        if value is None:
            return ''
        try:
            return str(value)
        except Exception:
            return ''

    def _generate_level_columns(self, parent_names_path, current_item_name, item_display_level_index):
        """Gera colunas de nível hierárquico"""
        level_columns = [''] * self.max_display_levels
        for i in range(len(parent_names_path)):
            if i < self.max_display_levels:
                level_columns[i] = parent_names_path[i]
        if item_display_level_index < self.max_display_levels:
            level_columns[item_display_level_index] = current_item_name
        else:
            if self.max_display_levels > 0:
                if level_columns[self.max_display_levels - 1]:
                    level_columns[self.max_display_levels - 1] += " > " + current_item_name
                else:
                    level_columns[self.max_display_levels - 1] = current_item_name
        return level_columns

    def _process_bom_recursively(self, top_level_main_product_code, parent_names_path_list, 
                                bom_to_process, current_item_level, effective_qty_multiplier, 
                                output_rows_list, use_formatting=True):
        """Processa BOM recursivamente calculando custos"""
        bom_product_record = bom_to_process.product_id if bom_to_process.product_id else bom_to_process.product_tmpl_id
        bom_product_name_formatted = self._get_string_value("[{}] {}".format(
            self._get_string_value(bom_product_record.default_code if bom_product_record else None),
            self._get_string_value(bom_product_record.name if bom_product_record else None)
        ))
        
        product_level_columns = self._generate_level_columns(parent_names_path_list, bom_product_name_formatted, current_item_level - 1)
        path_for_children = parent_names_path_list + [bom_product_name_formatted]
        children_display_level = current_item_level + 1

        rolled_up_cost_for_this_bom_level = 0.0
        tipo_linha_produto = 'Produto Principal' if current_item_level == 1 else 'Subconjunto'
        bom_product_uom_name = self._get_string_value(bom_to_process.product_uom_id.name if bom_to_process.product_uom_id else '')

        # Valores para formatação ou valores brutos
        qty_value = effective_qty_multiplier * bom_to_process.product_qty
        unit_cost_value = bom_product_record.standard_price if bom_product_record else 0.0
        
        if use_formatting:
            qty_display = self._format_float(qty_value)
            unit_cost_display = self._format_float(unit_cost_value)
        else:
            qty_display = qty_value
            unit_cost_display = unit_cost_value

        product_row_part1 = [
            self._get_string_value(top_level_main_product_code),
            self._get_string_value(bom_product_record.default_code if bom_product_record else None),
        ]
        product_row_part3_placeholder = [
            self._get_string_value("[{}] {}".format(
                self._get_string_value(bom_to_process.code),
                self._get_string_value(bom_product_record.name if bom_product_record else None)
            )),
            qty_display,
            bom_product_uom_name,
            unit_cost_display,
            "CALCULANDO...",
            '',
            tipo_linha_produto,
            '', '', '', ''
        ]
        product_row = product_row_part1 + product_level_columns + product_row_part3_placeholder
        output_rows_list.append(product_row)
        product_row_index_in_output = len(output_rows_list) - 1

        # Processa Operações se habilitado
        if self.include_operations and bom_to_process.operation_ids:
            for op_line in bom_to_process.operation_ids:
                op_name = self._get_string_value(op_line.name)
                op_workcenter_name = self._get_string_value(op_line.workcenter_id.name if op_line.workcenter_id else '')
                
                op_time_per_unit_of_parent = float(op_line.time_cycle_manual or op_line.time_cycle or 0.0)
                op_cost_per_unit_of_parent = 0.0
                if op_line.workcenter_id and op_line.workcenter_id.costs_hour > 0 and op_time_per_unit_of_parent > 0:
                    op_cost_per_unit_of_parent = (op_time_per_unit_of_parent / 60.0) * op_line.workcenter_id.costs_hour
                
                effective_total_op_time = op_time_per_unit_of_parent * effective_qty_multiplier
                effective_total_op_cost = op_cost_per_unit_of_parent * effective_qty_multiplier
                rolled_up_cost_for_this_bom_level += effective_total_op_cost
                
                op_level_columns = self._generate_level_columns(path_for_children, op_name, children_display_level - 1)

                op_row_part1 = [
                    self._get_string_value(top_level_main_product_code),
                    self._get_string_value(bom_product_record.default_code if bom_product_record else None),
                ]
                
                if use_formatting:
                    op_cost_display = self._format_float(effective_total_op_cost)
                    op_time_display = self._format_duration(effective_total_op_time)
                else:
                    op_cost_display = effective_total_op_cost
                    op_time_display = effective_total_op_cost  # Para dados brutos, usamos o custo

                op_row_part3 = [
                    '', '', '', '',
                    op_cost_display,
                    '',
                    'Operação',
                    op_name, op_workcenter_name,
                    op_time_display,
                    op_cost_display
                ]
                op_row = op_row_part1 + op_level_columns + op_row_part3
                output_rows_list.append(op_row)

        # Processa Componentes se habilitado
        if self.include_components:
            for comp_line in bom_to_process.bom_line_ids:
                component_product = comp_line.product_id
                qty_of_comp_in_this_bom = comp_line.product_qty
                next_level_effective_qty = qty_of_comp_in_this_bom * effective_qty_multiplier
                
                component_uom_name = self._get_string_value(comp_line.product_uom_id.name if comp_line.product_uom_id else '')

                actual_sub_bom = self.env['mrp.bom']._bom_find(
                    product=component_product,
                    company_id=bom_to_process.company_id.id,
                    bom_type=bom_to_process.type
                )
                
                if actual_sub_bom:
                    cost_from_sub_assembly = self._process_bom_recursively(
                        self._get_string_value(top_level_main_product_code),
                        path_for_children,
                        actual_sub_bom,
                        children_display_level,
                        next_level_effective_qty,
                        output_rows_list,
                        use_formatting
                    )
                    rolled_up_cost_for_this_bom_level += cost_from_sub_assembly
                else:
                    # É uma matéria-prima
                    last_purchase_taxes_str = ''
                    if self.include_taxes and component_product:
                        purchase_line_model = self.env['purchase.order.line']
                        last_purchase_lines = purchase_line_model.search([
                            ('product_id', '=', component_product.id),
                            ('state', 'in', ['purchase', 'done'])
                        ], order='id desc', limit=1)
                        
                        if last_purchase_lines:
                            last_purchase_line = last_purchase_lines[0]
                            if last_purchase_line.taxes_id:
                                tax_names = [tax.name or '' for tax in last_purchase_line.taxes_id]
                                last_purchase_taxes_str = ", ".join(filter(None, tax_names))
                    
                    comp_item_name_formatted = self._get_string_value("[{}] {}".format(
                        self._get_string_value(component_product.default_code if component_product else None),
                        self._get_string_value(component_product.name if component_product else None)
                    ))
                    comp_level_columns = self._generate_level_columns(path_for_children, comp_item_name_formatted, children_display_level - 1)
                    
                    effective_component_line_cost = next_level_effective_qty * (component_product.standard_price if component_product else 0.0)
                    rolled_up_cost_for_this_bom_level += effective_component_line_cost

                    raw_material_row_part1 = [
                        self._get_string_value(top_level_main_product_code),
                        self._get_string_value(component_product.default_code if component_product else None),
                    ]
                    
                    if use_formatting:
                        qty_display = self._format_float(next_level_effective_qty)
                        unit_cost_display = self._format_float(component_product.standard_price if component_product else 0.0)
                        total_cost_display = self._format_float(effective_component_line_cost)
                    else:
                        qty_display = next_level_effective_qty
                        unit_cost_display = component_product.standard_price if component_product else 0.0
                        total_cost_display = effective_component_line_cost

                    raw_material_row_part3 = [
                        '',
                        qty_display,
                        component_uom_name,
                        unit_cost_display,
                        total_cost_display,
                        last_purchase_taxes_str,
                        'Componente',
                        '', '', '', ''
                    ]
                    raw_material_row = raw_material_row_part1 + comp_level_columns + raw_material_row_part3
                    output_rows_list.append(raw_material_row)

        # Atualiza o custo total na linha do produto/subconjunto
        cost_column_index = 2 + self.max_display_levels + 4
        if product_row_index_in_output < len(output_rows_list) and len(output_rows_list[product_row_index_in_output]) > cost_column_index:
            if use_formatting:
                output_rows_list[product_row_index_in_output][cost_column_index] = self._format_float(rolled_up_cost_for_this_bom_level)
            else:
                output_rows_list[product_row_index_in_output][cost_column_index] = rolled_up_cost_for_this_bom_level
        
        return rolled_up_cost_for_this_bom_level

    def _generate_report_data_raw(self, output_rows_list):
        """Gera os dados do relatório sem formatação - usado pelo modelo CostReport"""
        if not self.bom_ids:
            return
        
        # Cabeçalho
        header_data_part1 = ['Código LdM Principal', 'Código Item']
        header_level_cols = []
        for i in range(1, self.max_display_levels + 1):
            header_level_cols.append(f'Nível {i}')
        
        header_data_part3 = [
            'Ref. LdM Item', 'Qtd Item', 'Unidade de Medida', 'Custo Unit. Item',
            'Custo Total Linha Item/LdM', 'Taxas Última Compra', 'Tipo de Linha',
            'Operação: Nome (Detalhe)', 'Operação: Centro Trabalho (Detalhe)',
            'Operação: Tempo (HH:MM:SS)', 'Operação: Custo (Detalhe)'
        ]
        header_data = header_data_part1 + header_level_cols + header_data_part3
        output_rows_list.append(header_data)

        # Processa cada BOM
        for bom_record_main in self.bom_ids:
            main_product_rec = bom_record_main.product_id if bom_record_main.product_id else bom_record_main.product_tmpl_id
            top_level_code = self._get_string_value(main_product_rec.default_code if main_product_rec else None)
            
            initial_multiplier = bom_record_main.product_qty if bom_record_main.product_qty > 0 else 1.0

            self._process_bom_recursively(
                top_level_code, [], bom_record_main, 1, initial_multiplier, output_rows_list, use_formatting=False
            )
            
            if len(self.bom_ids) > 1 and bom_record_main != self.bom_ids[-1]:
                output_rows_list.append([''] * len(header_data))

    def _generate_report_data(self, output_rows_list):
        """Gera os dados do relatório com formatação - usado para CSV"""
        if not self.bom_ids:
            return
        
        # Cabeçalho
        header_data_part1 = ['Código LdM Principal', 'Código Item']
        header_level_cols = []
        for i in range(1, self.max_display_levels + 1):
            header_level_cols.append(f'Nível {i}')
        
        header_data_part3 = [
            'Ref. LdM Item', 'Qtd Item', 'Unidade de Medida', 'Custo Unit. Item',
            'Custo Total Linha Item/LdM', 'Taxas Última Compra', 'Tipo de Linha',
            'Operação: Nome (Detalhe)', 'Operação: Centro Trabalho (Detalhe)',
            'Operação: Tempo (HH:MM:SS)', 'Operação: Custo (Detalhe)'
        ]
        header_data = header_data_part1 + header_level_cols + header_data_part3
        output_rows_list.append(header_data)

        # Processa cada BOM
        for bom_record_main in self.bom_ids:
            main_product_rec = bom_record_main.product_id if bom_record_main.product_id else bom_record_main.product_tmpl_id
            top_level_code = self._get_string_value(main_product_rec.default_code if main_product_rec else None)
            
            initial_multiplier = bom_record_main.product_qty if bom_record_main.product_qty > 0 else 1.0

            self._process_bom_recursively(
                top_level_code, [], bom_record_main, 1, initial_multiplier, output_rows_list, use_formatting=True
            )
            
            if len(self.bom_ids) > 1 and bom_record_main != self.bom_ids[-1]:
                output_rows_list.append([''] * len(header_data))

    def create_persistent_report(self):
        """Cria um relatório persistente que pode ser visualizado em tela"""
        if not self.bom_ids:
            raise UserError(_('Selecione pelo menos um BOM para criar o relatório.'))
        
        # Cria o relatório persistente
        cost_report = self.env['cost.report'].create({
            'name': self.name,
            'bom_ids': [(6, 0, self.bom_ids.ids)],
            'max_display_levels': self.max_display_levels,
            'include_operations': self.include_operations,
            'include_components': self.include_components,
            'include_taxes': self.include_taxes,
        })
        
        # Gera o relatório
        cost_report.action_generate_report()
        
        # Retorna para o relatório criado
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cost.report',
            'view_mode': 'form',
            'res_id': cost_report.id,
            'target': 'current',
        }

    def generate_cost_report(self):
        """Gera o relatório de custo detalhado"""
        if not self.bom_ids:
            raise UserError(_('Selecione pelo menos um BOM para gerar o relatório.'))

        csv_data_rows = []
        
        # Gera os dados do relatório
        self._generate_report_data(csv_data_rows)

        # Gera CSV
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
        for row in csv_data_rows:
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()

        # Codifica em base64 para download
        csv_data = base64.b64encode(csv_content.encode('utf-8-sig'))
        
        # Atualiza o wizard com os dados
        self.write({
            'csv_data': csv_data,
        })

        # Retorna ação para download
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cost.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
