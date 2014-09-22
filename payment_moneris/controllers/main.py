# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json
import logging
import pprint
import urllib2
import werkzeug

def unescape(s):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    # this has to be last:
    s = s.replace("&amp;", "&")
    s = s.replace("&quot;", "\"")
    return s

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class MonerisController(http.Controller):
    _notify_url = '/payment/moneris/ipn/'
    _return_url = '/payment/moneris/dpn/'
    _cancel_url = '/payment/moneris/cancel/'

    def _get_return_url(self, **post):
        """ Extract the return URL from the data coming from moneris. """
        return_url = post.pop('return_url', '')
        if not return_url:
            t = unescape(post.pop('rvarret', '{}'))
            custom = json.loads(t)
            return_url = custom.get('return_url', '/')
        if not return_url:
            return_url = '/payment/shop/validate'
        return return_url

    def moneris_validate_data(self, **post):
        """ Moneris IPN: three steps validation to ensure data correctness

         - step 1: return an empty HTTP 200 response -> will be done at the end
           by returning ''
         - step 2: POST the complete, unaltered message back to Moneris (preceded
           by cmd=_notify-validate), with same encoding
         - step 3: moneris send either VERIFIED or INVALID (single word)

        Once data is validated, process it. """
        res = False
        cr, uid, context = request.cr, request.uid, request.context
        reference = post.get('rvaroid')
        tx = None
        if reference:
            tx_ids = request.registry['payment.transaction'].search(cr, uid, [('reference', '=', reference)], context=context)
            if tx_ids:
                tx = request.registry['payment.transaction'].browse(cr, uid, tx_ids[0], context=context)
        if tx:
            moneris_urls = request.registry['payment.acquirer']._get_moneris_urls(cr, uid, tx and tx.acquirer_id and tx.acquirer_id.env or 'prod', context=context)
            validate_url = moneris_urls['moneris_auth_url']
        else:
            _logger.warning('Moneris: No order found')
            return res
            
        new_post = dict(ps_store_id=post.get('rvarid'), hpp_key=post.get('rvarkey'), transactionKey=post.get('transactionKey'))
        
        urequest = urllib2.Request(validate_url, werkzeug.url_encode(new_post))
        uopen = urllib2.urlopen(urequest)
        resp = uopen.read()

        part = resp.split('<br>')
        new_response = dict([s.split(' = ') for s in part])
        _logger.info(new_response)

        success = post.get('response_code')
        if int(success) < 50 and post.get('result') == '1' and int(new_response.get('response_code')) < 50 and new_response.get('status') == 'Valid-Approved' and new_response.get('amount') == post.get('charge_total') and new_response.get('transactionKey') == post.get('transactionKey') and new_response.get('order_id') == post.get('response_order_id'):
            _logger.info('Moneris: validated data')
            res = request.registry['payment.transaction'].form_feedback(cr, SUPERUSER_ID, post, 'moneris', context=context)
        else:
            _logger.warning('Moneris: answered INVALID on data verification: ' + new_response.get('status'))
        return res

    @http.route('/payment/moneris/ipn/', type='http', auth='none', methods=['POST'])
    def moneris_ipn(self, **post):
        """ Moneris IPN. """
        _logger.info('Beginning Moneris IPN form_feedback with post data %s', pprint.pformat(post))  # debug
        self.moneris_validate_data(**post)
        return ''

    @http.route('/payment/moneris/dpn', type='http', auth="none", methods=['POST'])
    def moneris_dpn(self, **post):
        """ Moneris DPN """
        _logger.info('Beginning Moneris DPN form_feedback with post data %s', pprint.pformat(post))  # debug
        return_url = self._get_return_url(**post)
        if self.moneris_validate_data(**post):
            return werkzeug.utils.redirect(return_url)
        else:
            return werkzeug.utils.redirect(self._cancel_url)

    @http.route('/payment/moneris/cancel', type='http', auth="none")
    def moneris_cancel(self, **post):
        """ When the user cancels its Moneris payment: GET on this route """
        cr, uid, context = request.cr, SUPERUSER_ID, request.context
        _logger.info('Beginning Moneris cancel with post data %s', pprint.pformat(post))  # debug
        reference = post.get('rvaroid')
        if reference:
            return_url = '/shop/payment/get_status/' + reference
            sales_order_obj = request.registry['sale.order']
            tx_ids = sales_order_obj.search(cr, uid, [('name', '=', reference)], context=context)
            if tx_ids:
                tx = sales_order_obj.browse(cr, uid, tx_ids[0], context=context)
                if tx:
                    _logger.info('cancel')
                    tx.write({'state': 'cancel'})
                _logger.info('done')
        else:
            return_url = '/shop/payment/validate'
        return werkzeug.utils.redirect(return_url)
