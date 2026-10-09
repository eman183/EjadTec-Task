from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_customer_id = fields.Many2one(
        'res.partner',
        string='Admin Customer',
        help='Default customer used by the Cash Now POS button.',
    )

    def _load_pos_data_fields(self, config_id):
        result = super()._load_pos_data_fields(config_id)

        if 'default_customer_id' not in result:
            result.append('default_customer_id')

        return result