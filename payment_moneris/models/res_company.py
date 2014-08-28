# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class ResCompany(osv.Model):
    _inherit = "res.company"

    def _get_moneris_account(self, cr, uid, ids, name, arg, context=None):
        Acquirer = self.pool['payment.acquirer']
        company_id = self.pool['res.users'].browse(cr, uid, uid, context=context).company_id.id
        moneris_ids = Acquirer.search(cr, uid, [
            ('website_published', '=', True),
            ('name', 'ilike', 'moneris'),
            ('company_id', '=', company_id),
        ], limit=1, context=context)
        if moneris_ids:
            moneris = Acquirer.browse(cr, uid, moneris_ids[0], context=context)
            return dict.fromkeys(ids, moneris.moneris_email_account)
        return dict.fromkeys(ids, False)

    def _set_moneris_account(self, cr, uid, id, name, value, arg, context=None):
        Acquirer = self.pool['payment.acquirer']
        company_id = self.pool['res.users'].browse(cr, uid, uid, context=context).company_id.id
        moneris_account = self.browse(cr, uid, id, context=context).moneris_account
        moneris_ids = Acquirer.search(cr, uid, [
            ('website_published', '=', True),
            ('moneris_email_account', '=', moneris_account),
            ('company_id', '=', company_id),
        ], context=context)
        if moneris_ids:
            Acquirer.write(cr, uid, moneris_ids, {'moneris_email_account': value}, context=context)
        return True

    _columns = {
        'moneris_account': fields.function(
            _get_moneris_account,
            fnct_inv=_set_moneris_account,
            nodrop=True,
            type='char', string='Moneris Account',
            help="Moneris username (usually email) for receiving online payments."
        ),
    }
