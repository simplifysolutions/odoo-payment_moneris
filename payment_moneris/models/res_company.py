# -*- coding: utf-8 -*-
# Copyright (C) 2015 xyenDev. All Rights Reserved
# Copyright (C) 2018 Simplify Solutions. All Rights Reserved
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_moneris_account(self):
        for company in self:
            acquirer_obj = self.env['payment.acquirer']
            moneris_ids = acquirer_obj.search([
                ('website_published', '=', True),
                ('name', 'ilike', 'moneris'),
                ('company_id', '=', self.env.user.company_id.id),
            ], limit=1)
            if moneris_ids:
                company.moneris_account = moneris_ids.moneris_email_account

    def _set_moneris_account(self):
        for company in self:
            return True

    moneris_account = fields.Char(
        compute='_get_moneris_account',
        inverse='_set_moneris_account',
        string='Moneris Account',
        store=True,
        help='Moneris username (usually email) for receiving online payments.'
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
