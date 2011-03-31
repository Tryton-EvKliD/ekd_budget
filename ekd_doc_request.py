# -*- coding: utf-8 -*-
"Document Request for money"
from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from decimal import Decimal, ROUND_HALF_EVEN
from trytond.pyson import In, If, Get, Eval, Not, Equal, Bool, Or, And

_RECEIVED_STATES = {
    'readonly': Equal(Eval('state_doc'), 'empty'),
        }

_RECEIVED_DEPENDS = ['state_doc']

class DocumentRequestCash(ModelSQL, ModelView):
    _name='ekd.document.head.request'

    budget_ref = fields.Function(fields.Many2One("ekd.account.budget", 'Budget'), 'get_budget_ref', setter='set_budget_ref')
    budget = fields.Many2One('ekd.account.budget', 'Budget', states=_RECEIVED_STATES, depends=_RECEIVED_DEPENDS)
    lines = fields.One2Many('ekd.document.line.request', 'requestcash', 'Lines Request',
                states=_RECEIVED_STATES, depends=_RECEIVED_DEPENDS,
                context={'document_ref':Eval('document_ref'), 
                         'budget_ref':Eval('budget_ref'),
                         'budget':Eval('budget'),
                         'currency_digits':Eval('currency_digits')})
    document_ref = fields.Reference('Base', selection='documents_get', select=1,
                states={'readonly': Not(In(Eval('state_doc'), ['empty', 'draft']))}, depends=['state_doc'], on_change=['document_ref'])

    def __init__(self):
        super(DocumentRequestCash, self).__init__()

    def get_budget_ref(self, ids, name):
        if not ids:
            return 
        res={}.fromkeys(ids, False)
        for line in self.browse(ids):
            if line.budget:
                res[line.id] = line.budget.id
            elif line.document_ref:
                model, model_id = line.document_ref.split(',')
                if model_id == '0':
                    continue 
                if model:
                    if model == 'ekd.account.budget':
                        res[line.id] = int(model_id)
                    elif model == 'ekd.project':
                        model_obj = self.pool.get(model)
                        model_brw = model_obj.browse(int(model_id))
                        if model_brw and model_brw.budget:
                            res[line.id] = model_brw.budget.id
                    else:
                        raise Exception('Error', 'Unknown-model: %s'%(model))
        return res

    def set_budget_ref(self, id, name, value):
        if not value:
            return
        self.write(id, { 'budget': value, })

    def on_change_document_ref(self, value):
        res={}
        if value.get('document_ref'):
            model, model_id = value.get('document_ref').split(',')
            if model_id == '0':
                return res
            if model == 'ekd.project':
                model_obj = self.pool.get(model)
                model_ids = model_obj.browse(int(model_id))
                if model_ids.manager:
                    res['manager'] = model_ids.manager.id
                if model_ids.employee:
                    res['employee'] = model_ids.employee.id
                if model_ids.budget:
                    res['budget_ref'] = model_ids.budget.id
                    res['budget'] = model_ids.budget.id
            elif model == 'ekd.account.budget':
                res['budget_ref'] = int(model_id)
                res['budget'] = int(model_id)
        return res

DocumentRequestCash()

class DocumentRequestCashLine(ModelSQL, ModelView):
    _name='ekd.document.line.request'

    budget_ref = fields.Function(fields.Many2One("ekd.account.budget", 'Budget'), 'get_budget_ref' )
    # Ошибка в домене ??????????????
    budget_line = fields.Many2One('ekd.account.budget.line', 'Budget Line', states={ 'readonly': Not(Bool(Eval('budget_ref')))},
                                domain=[
#                                "('budget','=', context.get('budget_ref',False))",
                                ('budget','=', Eval('budget_ref')),
                                ('direct_line','=','expense'),
                                ('type_line','=','line')
                                ], on_change=['budget_line'], depends=['budget_ref'])
    amount_budget = fields.Function(fields.Numeric('Amount in Budget', digits=(16, 2)), 'get_budget')
#    name = fields.Char('Description')
#    analytic = fields.Many2One('ekd.account.analytic', 'Analytic Account')

    def default_budget_ref(self):
        #raise Exception(str(Transaction().context))
        if Transaction().context.get('budget_ref'):
            return Transaction().context.get('budget_ref')
        elif Transaction().context.get('budget'):
            return Transaction().context.get('budget')
        return False

    def get_budget(self, ids, names):
        res={}
        for line in self.browse(ids):
            for name in names:
                res.setdefault(name, {}.fromkeys(ids, Decimal('0.0')))
                if name == 'amount_budget' and line.budget_line:
                    res[name][line.id] = line.budget_line.amount
        return res

    def get_budget_ref(self, ids, name):
        context = Transaction().context
        if context.get('budget_ref'):
            return {}.fromkeys(ids,context.get('budget_ref'))
        res={}.fromkeys(ids, False)
        for line in self.browse(ids):
            if line.requestcash.budget_ref:
                res[line.id] = line.requestcash.budget_ref.id
        #raise Exception(str(res))
        return res

    def on_change_budget_line(self, vals):
        if vals.get('budget_line'):
            budget_line_obj = self.pool.get('ekd.account.budget.line')
            budget_line = budget_line_obj.browse(vals.get('budget_line'))
            return {
                'name': budget_line.name,
                'analytic': budget_line.analytic.id,
                'amount_budget': budget_line.amount,
                'amount': budget_line.amount
                        }
        else:
            return {
                'analytic':  False,
                'amount_budget': Decimal('0.0'),
                'amount': Decimal('0.0')
                        }

    def on_change_analytic(self, vals):
        if vals.get('budget_line'):
            return {}
        elif vals.get('analytic'):
            analytic_obj = self.pool.get('ekd.account.analytic')
            analytic_id = analytic_obj.browse(vals.get('analytic'))
            if vals.get('name'):
                return { 'name': "%s - (%s)"%(vals.get('name'), analytic_id.name) }
            else:
                return { 'name': analytic_id.name }
        else:
            return {}

DocumentRequestCashLine()
