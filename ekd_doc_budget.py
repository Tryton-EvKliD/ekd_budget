# -*- coding: utf-8 -*-

"Document Budget"
from trytond.model import ModelView, ModelSQL, fields
from trytond.tools import safe_eval
from decimal import Decimal, ROUND_HALF_EVEN
from trytond.pyson import In, If, Get, Eval, Not, Equal, Bool, Or, And
import datetime
import time
import logging

_MOVE_STATES = {
    'readonly': Equal(Eval('state'), 'posted'),
    }
_MOVE_DEPENDS = ['state']

_LINE_STATES = {
    'readonly': Equal(Eval('state'), 'posted'),
    }
_LINE_DEPENDS = ['state']

class DocumentCash(ModelSQL, ModelView):
    "Documents of cash"
    _name='ekd.document.head.cash'
    _description=__doc__
    _inherits = {'ekd.document': 'document'}

    def get_amount_field(self, ids, name):
        assert name in ('income', 'expense'), 'Invalid name - Set Amount'
        if not ids:
            return {}
        res={}.fromkeys(ids, Decimal('0.0'))
        for line in self.browse(ids):
            if line.template_cash.code == 'income' and name == 'income':
                res[line.id] = line.amount
            elif line.template_cash.code == 'expense' and name == 'expense':
                res[line.id] = line.amount
        return res

    def set_amount_field(self, id, name):
        assert name in ('income', 'expense'), 'Invalid name - Set Amount'
        if not value:
            return
        self.write(id, { 'amount': value, })

    def get_template(self, ids, name):
        assert name in ('template_cash'), 'Invalid name - Get Template'
        if not ids:
            return {}
        res={}
        for line in self.browse(ids):
            res[line.id] = line.template.id
        return res

    def get_template_select(self):
        template_obj = self.pool.get('ekd.document.template')
        template_ids = template_obj.search(['type_account','=','cash'])
        res=[]
        for template in template_obj.browse(template_ids):
            res.append([template.id,template.name])
        return res

    def set_template(self, id, name):
        assert name in ('template_cash'), 'Invalid name - Set Template'
        if not value:
            return
        self.write(id, { 'template': value, })


    document = fields.Many2One('ekd.document', 'Document', required=True,
            ondelete='CASCADE')

    template_cash = fields.Function('get_template', fnct_inv='set_template', type='many2one', relation='ekd.document.template', string='Document Name',
                                    help="Template documents", selection='get_template_select', domain=[('type_account','=','cash')])

    description = fields.Text('Note')
    type_line = fields.Selection([('income','Income'),('expense','expense')], 'Type Operation')
    cash_account = fields.Many2One('ekd.account', 'Cash Account',
                    domain=[('kind', '=', 'money'), ('type.code', '=', 'cash')],
                    select=1)
    document_base = fields.Many2One('ekd.document', 'Document Base')
    document_base_ref = fields.Reference('Document Base', selection='documents_get', select=1, translate=True)
    corr_account = fields.Many2One('ekd.account', 'Corr. Account',
                    domain=[('kind', '=', 'partner')],
                    select=1)

    from_to_party = fields.Function('get_party', fnct_inv='set_party', type='many2one', relation='party.party', string='From or To Party')

    corr2_account = fields.Many2One('ekd.account', 'Account expense',
                    domain=[('kind', '=', 'analytic'),('type.code', '=', 'expense')],
                    select=1)
    analytic = fields.Many2One('ekd.account.analytic', 'Analytic Account expense')
#    amount = fields.Numeric('Amount', digits="(16, currency_digits)")

    income = fields.Function('get_amount_field', fnct_inv='set_amount_field',
                            type='numeric', string='Income', digits=(16, Eval('currency_digits', 2)))

    expense = fields.Function('get_amount_field', fnct_inv='set_amount_field',
                            type='numeric', string='expense', digits=(16, Eval('currency_digits', 2)))

#    amount_currency = fields.Numeric('Amount in currency', digits="(16, second_currency_digits)")
    currency = fields.Many2One('currency.currency','Currency')
    currency_digits = fields.Function('get_currency_digits', type='integer',
                    string='Currency Digits')
#    second_currency_digits = fields.Function('get_currency_digits',
#                    type='integer', string='Second Currency Digits', on_change_with=['currency'])

    state = fields.Selection([('draft','Draft'), ('posted','Posted'), ('error','Error'), ('deleted','Deleted') ], 'State', required=True, readonly=True)
    balance = fields.Many2One('ekd.book.cash', 'Book Cash')

    move = fields.Function('get_move', fnct_inv='set_move', type='one2many', relation='ekd.account.move', string='Account Entry Lines',
                    states=_MOVE_STATES, depends=_MOVE_DEPENDS,
                    context="{'company':company, 'date_operation':date_account, 'from_party':from_party, 'to_party':to_party, 'note':note, 'name':name, 'state':state,}")
#                     'line':[('amount': amount, 'dt_account':cash_account, 'ct_account':corr_account, "\
#                    " 'dt_party':company, 'ct_party':from_to_party,), ('amount': amount, 'dt_account':cash_account, 'ct_account':corr_account, "\
#                    " 'dt_party':company, 'ct_party':from_to_party,)]}")
#  'document_ref': 'ekd.document.head.cash,%s'%(id),

    deleting = fields.Boolean('Flag deleting', readonly=True)

    def __init__(self):
        super(DocumentCash, self).__init__()
        self._rpc.update({
            'button_post': True,
            'button_draft': True,
            'button_restore': True,
            })

    def default_state(self):
        return 'draft'

    def default_type_line(self):
        return 'expense'

    def default_currency_digits(self):
        return 2

    def default_second_currency_digits(self):
        return 2

    def default_company(self):
        return Transaction().context.get('company') or False

    def get_rec_name(self, ids, name):
        res={}
        for document in self.browse(ids):
            if document.template.shortcut:
                if isinstance(document.template.shortcut, unicode):
                    TemplateName = document.template.shortcut.encode('UTF-8')
                else:
                    TemplateName = document.template.shortcut.decode('UTF-8')
            else:
                if isinstance(document.template.name, unicode):
                    TemplateName = document.template.name.encode('UTF-8')
                else:
                    TemplateName = document.template.shortcut.decode('UTF-8')

            if document.number_our:
                if isinstance(document.number_our, unicode):
                    DocumentNumber = document.number_our.encode('UTF-8')
                else:
                    DocumentNumber = document.number_our.decode('UTF-8')
            elif document.number_in:
                if isinstance(document.number_in, unicode):
                    DocumentNumber = document.number_in.encode('UTF-8')
                else:
                    DocumentNumber = document.number_in.decode('UTF-8')
            else:
                DocumentNumber = 'без номера'

            if document.date_account:
                DocumentDate = document.date_account.strftime('%d.%m.%Y')
            elif document.date_document:
                DocumentDate = document.date_document.strftime('%d.%m.%Y')
            else:
                DocumentDate = 'без даты'

            res[document.id] = "%s %s %s %s %s"%(TemplateName, u"№", DocumentNumber, u"от", DocumentDate)

        return res

    def documents_get(self):
        model_obj = self.pool.get('ir.model')
        res = []
        model = model_obj.search([
                    ('model', 'like', 'ekd.document%'),
                    ])
        for model in model_obj.browse(model):
            res.append([model.model, model.name])
        return res

    def get_currency_digits(self, ids, names):
        res = {}
        for line in self.browse(ids):
            for name in names:
                res.setdefault(name, {})
                res[name].setdefault(line.id, 2)
                if name == 'currency_digits':
                    if line.cash_account:
                        res[name][line.id] = line.cash_account.currency_digits
                    else:
                        res[name][line.id] = 2
                elif name == 'second_currency_digits':
                    if line.cash_account.second_currency:
                        res[name][line.id] = line.cash_account.second_currency.digits
                    else:
                        res[name][line.id] = 2
        return res

    def get_move(self, ids, name):
        assert name in ('move'), 'Invalid name'
        move_line = self.pool.get('ekd.account.move')
        res = {}
        for line in self.browse(ids):
            res[line.id] = move_line.search([('document_ref','=', 'ekd.document.head.cash,%s'%(line.id))])
        return res

    def set_move(self, ids, name):
        logger = logging.getLogger('import')
        logger.warning("name '%s' get_function " % (name))
        assert name in ('move'), 'Invalid name'
        if not value:
            return
        move_obj = self.pool.get('ekd.account.move')
        if isinstance(ids, list):
            logger.warning("ids '%s'  " % (ids))
            id = ids[0]
        else:
            id = ids
        logger.warning("id '%s'  " % (id))
        logger.warning("--CONTEXT-- '%s' " % (context))
        line = self.browse(id)
        if not line.template:
            return
        logger.warning("lines '%s' " % (line))
        logger.warning("lines '%s' " % (line.move))
        logger.warning("VALUE '%s' " % (value))
        for act in value:
                if act[0] == 'create':
                    act[1]['document_ref'] = 'ekd.document.head.cash,%s'%(id)
                    if line.template.code_call == 'income':
                        act[1]['from_party'] = line.from_to_party.id
                        act[1]['to_party'] = line.company.id
                    else:
                        act[1]['from_party'] = line.company.id
                        act[1]['to_party'] = line.from_to_party.id

                    move_obj.create(act[1])
                elif act[0] == 'write':
                    move_obj.write(act[1], act[2])
                elif act[0] == 'delete':
                    move_obj.delete(act[1])
                elif act[0] == 'add':
                    raise Exception('add--',name, 'act[1]-',act[1])
#               move_ids.append(act[1])
                elif act[0] == 'set':
                    raise Exception('set-',name, 'act[1]-',act[1])
#               move_ids.extend(act[1])

    def get_party(self, ids, name):
        assert name in ('from_to_party'), 'Invalid name'
        res = {}
        for balance in self.browse(ids):
            if balance.type_line == 'income':
                res[balance.id] = balance.from_party.id
            else:
                res[balance.id] = balance.to_party.id
        return res

    def set_party(self, id, name):
        assert name in ('from_to_party'), 'Invalid name SET PARTY'
        if not value:
            return
        balance = self.browse(id)
        if balance.type_line == 'income':
            self.write(id, {'from_party':value, })
        else:
            self.write(id, {'to_party':value, })

    def button_post(self, ids):
        return self.post(ids)

    def button_draft(self, ids):
        return self.draft(ids)

    def button_restore(self, ids):
        return self.draft(ids)

    def post(self, ids):
        sequence_obj = self.pool.get('ir.sequence')
        date_obj = self.pool.get('ir.date')
        if isinstance(ids, (int, long)):
            ids = [ids]
        DocumentCash_ids = self.browse(ids)
        for document in DocumentCash_ids:
            reference = sequence_obj.get_id(cursor, user,
            document.template.sequence.id)
            self.write(document.id, {
                    'number_our': reference,
                        'state': 'posted',
                    'post_date': date_obj.today(cursor, user),
                        })
        return

    def draft(self, ids):
        if isinstance(ids, (int, long)):
            ids = [ids]
        moves = self.browse(ids)
        for move in moves:
            for line in move.lines:
                if line.state == 'posted':
                    line.draft(line.id)
        self.write(move.id, {
                'state': 'draft',
                })
        return

DocumentCash()