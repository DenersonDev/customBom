from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CustomBOM(models.Model):
    _name = 'custom.bom'
    _description = 'Custom Bill of Materials'
    _rec_name = 'code'
    _order = 'code'

    code = fields.Char(string='Código', required=True, copy=False, readonly=True, 
                       default=lambda self: _('New'))
    product_id = fields.Many2one('product.product', string='Produto', required=True)
    product_tmpl_id = fields.Many2one('product.template', string='Modelo do Produto', 
                                      related='product_id.product_tmpl_id', store=True)
    bom_line_ids = fields.One2many('custom.bom.line', 'bom_id', string='Linhas BOM')
    active = fields.Boolean(default=True, string='Ativo')
    notes = fields.Text(string='Observações')
    company_id = fields.Many2one('res.company', string='Empresa', 
                                 default=lambda self: self.env.company)
    date_created = fields.Datetime(string='Data de Criação', default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('confirmed', 'Confirmado'),
        ('done', 'Concluído')
    ], string='Status', default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('custom.bom') or _('New')
        return super(CustomBOM, self).create(vals)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})


class CustomBOMLine(models.Model):
    _name = 'custom.bom.line'
    _description = 'Custom BOM Line'
    _order = 'sequence, id'

    bom_id = fields.Many2one('custom.bom', string='BOM', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Produto', required=True)
    product_tmpl_id = fields.Many2one('product.template', string='Modelo do Produto', 
                                      related='product_id.product_tmpl_id', store=True)
    product_qty = fields.Float(string='Quantidade', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Unidade de Medida', required=True)
    sequence = fields.Integer(string='Sequência', default=10)
    notes = fields.Text(string='Observações')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
