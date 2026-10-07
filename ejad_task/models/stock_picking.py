from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.constrains('scheduled_date', 'picking_type_id')
    def _check_outgoing_picking_date(self):
        for picking in self:

            if picking.picking_type_id.code != 'outgoing':
                continue

            if not picking.scheduled_date:
                continue
            print("scheduled_date", picking.scheduled_date)
            scheduled_date = fields.Datetime.context_timestamp(
                self,
                picking.scheduled_date
            ).date()
            print("scheduled_date123:", scheduled_date)

            today = fields.Date.context_today(self)
            print("today:", today)

            if scheduled_date < today:
                raise ValidationError(
                    'The scheduled date of an outgoing picking (Deliveries)'
                    'cannot be before today.'
                )