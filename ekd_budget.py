# -*- coding: utf-8 -*-
#
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
"Budget"
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard
from trytond.transaction import Transaction
from decimal import Decimal
from trytond.pyson import In, If, Get, Eval, Not, Equal, Bool, Or, And
import datetime

STATES = {
    'readonly': Equal(Eval('state'), 'close'),
}
DEPENDS = ['state']

_ICONS = {
    'open': 'tryton-open',
    'close': 'tryton-readonly',
}

# Бюджеты
class ConfigurationBudget(ModelSQL, ModelView):
    'Configuration Budget'
    _name = 'ekd.account.budget.configure'
    _description = __doc__

    company = fields.Many2One('company.company','Company')
    type_coding = fields.Selection([
                ('xxxxxx','XXXXXX'),
                ('[xxx][xxx]','[XXX][XXX]'),
                ('xxx.xxx','XXX.XXX')],'Type Coding Sections', required=True)
    code = fields.Char('Code', size=None, required=True)
    number_char_section = fields.Integer('Number of characters in the sectionb', required=True)
    number_char_article = fields.Integer('Number of characters per article', required=True)
    delimiter_section = fields.Char('Delimiter Section', size=1)
    delimiter_between = fields.Char('Delimiter Between Section and Article', size=1)
    delimiter_article = fields.Char('Delimiter Article', size=1)
    active = fields.Boolean('Active')

ConfigurationBudget()

# Бюджеты
class BudgetType(ModelSQL, ModelView):
    'Type Budget'
    _name = 'ekd.account.budget.type'
    _description = __doc__

    company = fields.Many2One('company.company','Company')
    direct_budget = fields.Selection([('income','Income'),('expense','expense')],'Direct Budget', required=True)
    code = fields.Char('Code', size=None, required=True)
    name = fields.Char('Name', size=None, required=True)
    parent = fields.Many2One('ekd.account.budget.type', 'Parent',
                ondelete="RESTRICT")
#, domain=[('direct_budget', '=', direct_budget)])
    childs = fields.One2Many('ekd.account.budget.type', 'parent', 'Children')
    active = fields.Boolean('Active')
    type = fields.Selection([
                    ('expense','expense'),
                    ('income','Running'),
                    ('project','Project'),
                    ], 'Type')

    def __init__(self):
        super(BudgetType, self).__init__()
        self._sql_constraints += [
            ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
        ]
        self._order.insert(0, ('code', 'ASC'))

BudgetType()


# Шаблоны бюджетов
class BudgetTemplate(ModelSQL, ModelView):
    'Budget Template'
    _name = 'ekd.account.budget.template'
    _description = __doc__

    code = fields.Char('Code', size=None, required=True)
    name = fields.Char('Name', size=None, required=True, translate=True)
    sequence = fields.Char('Sequence', size=None, required=True)
    lines = fields.One2Many('ekd.account.budget.template.line', 'template', 'Lines Budget Template')
    active = fields.Boolean('Active')

    def __init__(self):
        super(BudgetTemplate, self).__init__()
        self._sql_constraints += [
            ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
        ]
        self._order.insert(0, ('code', 'ASC'))
        self._order.insert(1, ('sequence', 'ASC'))

BudgetTemplate()

class BudgetTemplateLine(ModelSQL, ModelView):
    'Lines Budget Template'
    _name = 'ekd.account.budget.template.line'
    _description = __doc__

    template = fields.Many2One('ekd.account.budget.template', 'Template Budget',
                ondelete="RESTRICT")
    type_line = fields.Selection([('section','Section'),('line','Line')],'Type line')
    sequence = fields.Char('Sequence', size=None, required=True)
    code = fields.Char('Code', size=None, required=True)
    name = fields.Char('Name', size=None, required=True, translate=True)
    analytic = fields.Many2One('ekd.account.analytic', 'Analytic Account',
                ondelete="RESTRICT")
    parent = fields.Many2One('ekd.account.budget.template.line', 'Parent',
                ondelete="RESTRICT")
#                , domain=[('template', '=', template)])
    childs = fields.One2Many('ekd.account.budget.template.line', 'parent', 'Children')
#    quantity = fields.Float('Quantity', digits="(16, unit_digits)")
#    unit_digits = fields.Function('get_unit_digits', type='integer', string='Unit Digits', on_change_with=['product_uom'])
    product_uom = fields.Many2One('product.uom', 'Unit' )
#    amount = fields.Numeric('Amount', digits="(16, currency_digits)")
    currency = fields.Many2One('currency.currency','Currency')

    def __init__(self):
        super(BudgetTemplateLine, self).__init__()
        self._sql_constraints += [
            ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
        ]
        self._order.insert(0, ('code', 'ASC'))
        self._order.insert(1, ('sequence', 'ASC'))

BudgetTemplateLine()

# Бюджеты
class Budget(ModelSQL, ModelView):
    'General Budget'
    _name = 'ekd.account.budget'
    _description = __doc__
    _rec_name = 'name'

    company = fields.Many2One('company.company','Company', select=0)
    type_budget = fields.Many2One('ekd.account.budget.type','Type Budget')
    direct_budget = fields.Selection([('income','Income'),('expense','expense'), ('both','Income and expense')],'Direct Budget', required=True)
    code = fields.Char('Code', size=None, required=True,
                        states={'readonly': Not(Equal(Eval('state'), 'draft'))}, depends=['state'])
    name = fields.Char('Name', size=None, required=True, select=1,
                        states={'readonly': Not(Equal(Eval('state'), 'draft'))}, depends=['state'])
    parent = fields.Many2One('ekd.account.budget', 'Parent',
                        states={'readonly': Not(Equal(Eval('state'), 'draft'))}, depends=['state'])
    childs = fields.One2Many('ekd.account.budget', 'parent', 'Children',
                        states={'readonly': Not(Equal(Eval('state'), 'draft'))}, depends=['state'])
    start_date = fields.Date('Starting Date', select=2,
                        states={'readonly': Not(Equal(Eval('state'), 'draft'))}, depends=['state'])
    end_date = fields.Date('Expected End', select=2,
                        states={'readonly': Not(Equal(Eval('state'), 'draft'))}, depends=['state'])
    total_income = fields.Function(fields.Numeric('Total Income', digits=(16,2)), 'get_amount')
    total_budget = fields.Function(fields.Numeric('Total Budget', digits=(16,2)), 'get_amount')
    total_marga = fields.Function(fields.Numeric('Marga', digits=(16,2)), 'get_amount')
    move_income = fields.Function(fields.Numeric('Total Income', digits=(16,2)), 'get_amount')
    move_expense = fields.Function(fields.Numeric('Total Budget', digits=(16,2)), 'get_amount')
    currency = fields.Many2One('currency.currency','Currency')
    lines = fields.One2Many('ekd.account.budget.line', 'budget','Lines Budget')
    line_change = fields.One2Many('ekd.account.budget.line.change', 'budget', 'Budget Line Change', readonly=True)
    active = fields.Boolean('Active')
    state = fields.Selection([
                    ('draft','Draft'),
                    ('running','Performed'),
                    ('done','Completed'),
                    ('deleted','Deleted')
                    ], 'State', required=True, readonly=True)

    def __init__(self):
        super(Budget, self).__init__()
        self._sql_constraints += [
            ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
        ]
        self._order.insert(0, ('code', 'ASC'))
        self._order.insert(1, ('start_date', 'ASC'))
        self._order.insert(1, ('end_date', 'ASC'))

        self._rpc.update({
                'button_draft': True,
                'button_run': True,
                'button_done': True,
                'button_restore': True,
                'button_calculate': True,
                })

    def default_state(self):
        context = Transaction().context
        if context.get('state', False):
            return context.get('state')
        return 'draft'

    def default_active(self):
        context = Transaction().context
        if context.get('active', False):
            return context.get('active')
        return True

    def default_start_date(self):
        context = Transaction().context
        if context.get('start_date', False):
            return context.get('start_date')
        return datetime.datetime.now()

    def default_end_date(self):
        context = Transaction().context
        if context.get('end_date', False):
            return context.get('end_date')

    def default_company(self):
        return Transaction().context.get('company') or False

    def default_name(self):
        tmp_string=''
        context = Transaction().context
        if context.get('name', False):
            if isinstance(context.get('name'), unicode):
                tmp_string = "Проект: "+context.get('name').encode('UTF-8')
            else:
                tmp_string = "Проект: "+context.get('name')

        if context.get('code', False):
            if isinstance(context.get('code'), unicode):
                tmp_string += '- код: '+context.get('code').encode('UTF-8')
            else:
                tmp_string += '- код: '+context.get('code')

            return tmp_string
        return tmp_string

    def default_direct_budget(self):
        context = Transaction().context
        if context.get('direct_budget', False):
            return context.get('direct_budget')
        return 'both'

    def default_code(self):
        context = Transaction().context
        if context.get('code', False):
            return "%s%s"%("000-", context.get('code'))
        return '000-000.000.000'

    def get_unit_digits(self, ids, name):
        res = {}
        for line in self.browse(ids):
            if line.product_uom:
                res[line.id] = line.product_uom.digits
            else:
                res[line.id] = 2
        return res
    def get_amount(self, ids, names):
        res={}
#        amount = Decimal('0.0')
        for name in names:
            res.setdefault(name, {})

        for budget in self.browse(ids):
            for name in names:
                res.setdefault(name, {})
                res[name].setdefault(budget.id, Decimal('0.0'))
                for line in budget.lines:
                    if name == 'total_income' and line.type_line == 'line' and line.direct_line == 'income':
                        res[name][budget.id] += line.amount_change
                    elif name == 'total_budget' and line.type_line == 'line' and line.direct_line == 'expense':
                        res[name][budget.id] += line.amount_change
                    elif name == 'total_marga':
                        res[name][budget.id] = Decimal('0.0')
                    elif name == 'move_income' and line.type_line == 'line' and line.direct_line == 'income':
                        res[name][budget.id] += line.amount_move
                    elif name == 'move_expense' and line.type_line == 'line' and line.direct_line == 'expense':
                        res[name][budget.id] += line.amount_move
            if 'total_income' in names and 'total_marga' in names and 'total_budget' in names and len(budget.lines):
                res['total_marga'][budget.id] = res['total_income'][budget.id] - res['total_budget'][budget.id]

        return res


    def calculate(self, ids):
        stack_total = {}
        BudgetLineObj = self.pool.get('ekd.account.budget.line')
        amount = Decimal('0.0')
        amount_sec = Decimal('0.0')
        section_id = False
        for budget in self.browse(ids):
            for line in budget.lines:
                stack_total[line.sequence] = line.amount
            for line in budget.lines:
                if line.type_line == 'line':
                    if line.quantity and line.price_unit:
                        BudgetLineObj.write(line.id, {'amount': Decimal(str(line.quantity))*line.price_unit })
                    stack_total[line.sequence] = line.amount
                    amount += abs(line.amount)
                    amount_sec += abs(line.amount)
                elif line.type_line == 'subtotal':
                    if line.code:
                        str_tmp = ''
                        for val in line.code.split(' '):
                            if val in ('+','-','*','/','(',')'):
                                str_tmp += val
                            else:
                                if stack_total[val]:
                                    str_tmp += str(stack_total[val])
                                else:
                                    raise Exception('Error values in code', val, stack_total)

                        if line.direct_line == 'total_sum':
                            BudgetLineObj.write(line.id, {'amount': eval(str_tmp) })
                            stack_total[line.sequence] = line.amount
                        elif line.direct_line == 'total_per':
                            BudgetLineObj.write(line.id, {'amount': eval(str_tmp)*100 })
                            stack_total[line.sequence] = line.amount
                    else:
                        BudgetLineObj.write(line.id, {'amount': amount })
                        stack_total[line.sequence] = line.amount
                        amount = Decimal('0.0')
                elif line.type_line == 'section':
                    if amount_sec:
                        BudgetLineObj.write(section_id, {'amount': amount_sec })
                        stack_total[line.sequence] = line.amount
                        section_id = line.id
                        amount_sec = Decimal('0.0')
                        amount = Decimal('0.0')
                    else:
                        section_id = line.id
#                stack_total[line.sequence] = line.amount
            if amount_sec and section_id :
                BudgetLineObj.write(section_id, {'amount': amount_sec })

    def button_calculate(self, ids):
        return self.calculate(ids)

    def button_run(self, ids):
        return self.run(ids)

    def button_done(self, ids):
        return self.done(ids)

    def button_draft(self, ids):
        return self.draft(ids)

    def button_restore(self, ids):
        return self.draft(ids)

    def done(self, ids):
        line_obj = self.pool.get('ekd.account.budget.line')
        for budget in self.browse(ids):
            for line in budget.lines:
                if line.state == 'running':
                    line_obj.write(line.id, {'state':'done'})

        return self.write(ids, {
            'state': 'done',
            })

    def run(self, ids):
        line_obj = self.pool.get('ekd.account.budget.line')
        for budget in self.browse(ids):
            for line in budget.lines:
                if line.state == 'draft':
                    line_obj.write(line.id, {'state':'running'})
        return self.write(ids, {
            'state': 'running',
            })

    def draft(self, ids):
        line_obj = self.pool.get('ekd.account.budget.line')
        for budget in self.browse(ids):
            for line in budget.lines:
                line_obj.write(line.id, {'state':'draft'})
        return self.write(ids, {
            'state': 'draft',
            })

    def restore(self, ids):
        line_obj = self.pool.get('ekd.account.budget.line')
        for budget in self.browse(ids):
            for line in budget.lines:
                    line_obj.write(line.id, {'state':'draft'})
        return self.write(ids, {
            'state': 'draft',
            })

    def delete(self, ids):
        return super(Budget, self).delete(ids)

    def create(self, vals):
#        vals['code'] = "%s-%s"%('000',context.get('code', '000.000.000'))
        context = Transaction().context
        new_id = super(Budget, self).create(vals)
        budget = self.browse(new_id)
        if context.get('code', False):
            self.write(new_id, {
                                   'code': "%s-%s"%(new_id, context.get('code')),
                                    })
        else:
            self.write(new_id, {
                                   'code': "000-000.000",
                                    })
        return new_id

    def write(self, ids, vals):
#        if context.get('code', False):
#        vals['code'] = "%s-%s"%(new_id, context.get('code'))
#        budget = self.browse(new_id)
#        vals['code'] = "%s-%s"%(new_id, context.get('code')),

        return super(Budget, self).write(ids, vals)


Budget()

class BudgetLine(ModelSQL, ModelView):
    'General Budget Lines'
    _name = 'ekd.account.budget.line'
    _description = __doc__
    __sequence_line = 0

    budget = fields.Many2One('ekd.account.budget', 'Budget', ondelete="RESTRICT")
    direct_line = fields.Selection([
                        ('income','Income'),
                        ('expense','expense'),
                        ('total_sum','Total Summa'),
                        ('total_per','Total Percentage')
                        ],'Direct Budget', required=True)
    income = fields.Boolean('Income Budget')
    kind = fields.Selection([
                        ('quantity','Quantity'),
                        ('amount','Amount'),
                        ('quan_amount','Quantity and Amount'), 
                        ('percentage','Percentage')
                        ], 'Kind')
    type_line = fields.Selection([
                        ('section','Section'),
                        ('subtotal','Subtotal'),
                        ('line','Line')
                        ],'Type line')
    analytic = fields.Many2One('ekd.account.analytic', 'Analytic Account',
                domain=[('kind_analytic', '=', Eval('direct_line'))], ondelete="RESTRICT")
    code_section = fields.Char('Budget Section', size=None, help="Code Section")
    code = fields.Char('Budget Item', size=None, help="Code Item")
    name = fields.Char('Name', size=None, required=True, on_change_with=['analytic', 'name'])
    sequence = fields.Char('Code Line', size=None, required=True)
    parent = fields.Many2One('ekd.account.budget.line', 'Parent',
                ondelete="RESTRICT")
#            , domain=[('budget', '=', budget.id)])
    childs = fields.One2Many('ekd.account.budget.line', 'parent', 'Children')
    product = fields.Many2One('product.product', 'Product')
    quantity = fields.Float('Quantity', digits=(16, Eval('unit_digits', 2)), on_change=['quantity', 'price_unit'],
                states={'invisible':Or(Equal(Eval('kind'),'amount'), Not(Equal(Eval('type_line'),'line'))),
                        'tree_invisible':Or(Equal(Eval('kind'),'amount'), Not(Equal(Eval('type_line'),'line')))},
                depends=['kind', 'type_line'])
    uom = fields.Many2One('product.uom', 'Unit',
                states={'invisible':Or(Equal(Eval('kind'),'amount'), Not(Equal(Eval('type_line'),'line'))),
                        'tree_invisible':Or(Equal(Eval('kind'),'amount'), Not(Equal(Eval('type_line'),'line')))},
                depends=['kind', 'type_line'] )
    unit_digits = fields.Function(fields.Integer('Unit Digits', on_change_with=['uom']), 'get_unit_digits')
    price_unit = fields.Numeric('Price unit', digits=(16, 2),
                states={'invisible': Or(Equal(Eval('kind'),'amount'), Not(Equal(Eval('type_line'),'line'))),
                        'tree_invisible':Or(Equal(Eval('kind'), 'amount'), Equal(Eval('type_line'), 'line'))},
                depends=['kind', 'type_line'], on_change=['quantity', 'price_unit'])
    amount = fields.Numeric('Amount', digits=(16, 2), states={'readonly': Not(Equal(Eval('state'), 'draft'))})
    amount_change = fields.Function(fields.Numeric('Amount Change', digits=(16, 2),
                states={'invisible':Equal(Eval('state'), 'draft'),
                        'tree_invisible': Equal(Eval('state'), 'draft')}), 'get_amount_change')
    amount_move = fields.Function(fields.Numeric('Amount Accounting', digits=(16, 2),
                states={'invisible':Equal(Eval('state'), 'draft'),
                        'tree_invisible': Equal(Eval('state'), 'draft')}), 'get_amount_move')
    quantity_move = fields.Function(fields.Numeric('Quantity Accounting', digits=(16, 2),
                states={'invisible':Equal(Eval('state'), 'draft'),
                        'tree_invisible': Equal(Eval('state'), 'draft')}), 'get_amount_move')
    currency = fields.Many2One('currency.currency','Currency', states={'invisible':Equal(Eval('kind'), 'quantity')}, depends=['kind'])
    line_change = fields.One2Many('ekd.account.budget.line.change', 'budget_line', 'Budget Line Change',
                    states={'invisible': Equal(Eval('state'), 'draft'), 
                            'readonly': Equal(Eval('state'), 'draft'),},
                    context={'budget': Eval('budget'),'name': Eval('name'), 'uom': Eval('uom'), 
                            'analityc': Eval('analytic'), 'quantity': Eval('quantity'),
                            'unit_digits': Eval('unit_digits'), 'price_unit': Eval('price_unit'), 'amount': Eval('amount'),})
    move_line = fields.One2Many('ekd.account.move.line.budget', 'budget_line', 'Amount Accounting',
                    states={'invisible': Equal(Eval('state'), 'draft'), 
                            'readonly': Equal(Eval('state'), 'draft'),})
    state = fields.Selection([
                    ('draft','Draft'),
                    ('running','Performed'),
                    ('done','Completed'),
                    ('deleted','Deleted')
                    ], 'State', required=True, readonly=True)

    def __init__(self):
        super(BudgetLine, self).__init__()
        self._sql_constraints += [
            ('code_uniq', 'UNIQUE(budget,sequence)', 'The sequence in the budget must be unique!'),
        ]
        self._order.insert(0, ('budget', 'ASC'))
        self._order.insert(0, ('sequence', 'ASC'))
        self._order.insert(1, ('analytic', 'ASC'))

        self._rpc.update({
                'on_write': True,
                })

    def default_type_line(self):
        return 'line'

    def default_state(self):
        return 'draft'

    def default_sequence(self):
        self.__sequence_line = self.__sequence_line+10
        if self.__sequence_line < 100:
            return "00%s"%(self.__sequence_line)
        elif self.__sequence_line < 1000:
            return "0%s"%(self.__sequence_line)
        else:
            return str(self.__sequence_line)

    def default_kind(self):
        return 'quan_amount'

    def default_direct_line(self):
        return 'expense'

    def default_type_line(self):
        return 'line'

    def default_income(self):
        return False

    def get_unit_digits(self, ids, name):
        res = {}
        for line in self.browse(ids):
            if line.uom:
                res[line.id] = line.uom.digits
            else:
                res[line.id] = 2
        return res

    def get_amount_change(self, ids, name):
        res={}.fromkeys(ids, Decimal('0.0'))
        for line in self.browse(ids):
            if line.line_change:
                for line_change in line.line_change:
                    res[line.id] += line_change.amount
            res[line.id] += line.amount
        return res

    def get_amount_move(self, ids, names):
        res={}
        for name in names:
            res.setdefault(name, {})
        for line in self.browse(ids):
            if name == 'amount_move':
                res[name][line.id] = Decimal('0.0')
            if name == 'quantity_move':
                res[name][line.id] = 0.0
            if line.move_line:
                for move_line in line.move_line:
                    res[name][line.id] += move_line.amount
        return res

    def on_write(self, ids):
        lines = self.browse(ids)
        res = []
        for line in lines:
            res.extend([x.id for x in line.move.lines])
#        raise Exception(str(res), ids, str(context))
        return list({}.fromkeys(res))

    def on_change_with_name(self, vals):
        if not vals.get('analytic'):
            return
        analytic_obj = self.pool.get('ekd.account.analytic')
        if not vals.get('name'):
            return analytic_obj.browse(vals.get('analytic')).rec_name

    def on_change_with_unit_digits(self, vals):
        if not vals.get('uom'):
            return 2
        uom_obj = self.pool.get('product.uom')
        return uom_obj.browse(vals.get('uom')).digits

    def on_change_with_amount(self, vals):
        if not vals.get('quantity') or not vals.get('price_unit'):
            return vals
        return Decimal(str(vals.get('quantity'))) * Decimal(str(vals.get('price_unit')))

    def on_change_quantity(self, vals):
        if not vals.get('quantity') or not vals.get('price_unit'):
            return vals
        return { 'amount': Decimal(str(vals.get('quantity'))) * Decimal(str(vals.get('price_unit'))) }

    def on_change_price_unit(self, vals):
        if not vals.get('quantity') or not vals.get('price_unit'):
            return vals
        return { 'amount': Decimal(str(vals.get('quantity'))) * Decimal(str(vals.get('price_unit'))) }

    def delete(self, ids):
        return super(BudgetLine, self).delete(ids)

    def create(self, vals):
        return super(BudgetLine, self).create(vals)

    def write(self, ids, vals):
        return super(BudgetLine, self).write(ids, vals)

BudgetLine()

class BudgetLineChange(ModelSQL, ModelView):
    'General Budget Lines Changes'
    _name = 'ekd.account.budget.line.change'
    _description = __doc__

    budget_line = fields.Many2One('ekd.account.budget.line', 'Budget Line', ondelete="RESTRICT")
    budget = fields.Many2One('ekd.account.budget', 'Budget', ondelete="RESTRICT")
    date_change = fields.Date('Date Change', required=True)
    direct_line = fields.Function(fields.Char('Direct Budget'), 'get_fields')
    income = fields.Function(fields.Boolean('Income Budget'), 'get_fields')
    kind = fields.Function(fields.Char('Kind'), 'get_fields')
    type_line = fields.Function(fields.Char('Type Line'),'get_fields')
    analytic = fields.Function(fields.Many2One('ekd.account.analytic', 'Analytic Account'), 'get_fields')
    name = fields.Function(fields.Char('Name'),'get_fields')
    note = fields.Text('Note')
    product = fields.Many2One('product.product', 'Product')
    quantity = fields.Float('Quantity', digits=(16, Eval('unit_digits', 2)), on_change=['quantity', 'price_unit'],
                states={'invisible':Or(Equal(Eval('kind'), 'amount'), Not(Equal(Eval('type_line'), 'line'))),
                        'tree_invisible':Or(Equal(Eval('kind'), 'amount'), Equal(Eval('type_line'), 'line'))},
                depends=['kind', 'type_line'])
    uom = fields.Many2One('product.uom', 'Unit',
                states={'invisible': Equal(Eval('kind'), 'amount'), 
                        'tree_invisible': Equal(Eval('kind'), 'amount')},
                depends=['kind', 'type_line'] )
    unit_digits = fields.Function(fields.Integer('Unit Digits', on_change_with=['uom']), 'get_unit_digits')
    price_unit = fields.Numeric('Price unit', digits=(16, 2),
                states={'invisible':Or(Equal(Eval('kind'), 'amount'), Not(Equal(Eval('type_line'), 'line'))), 
                        'tree_invisible':Or(Equal(Eval('kind'), 'amount'), Not(Equal(Eval('type_line'), 'line')))},
                depends=['kind', 'type_line'], on_change=['quantity', 'price_unit'])
    amount = fields.Numeric('Amount', digits=(16, 2), states={'invisible': Equal(Eval('kind'), 'quantity')})
    state = fields.Selection([
                    ('draft','Draft'),
                    ('confirmed','Confirmed'),
                    ('deleted','Deleted')
                    ], 'State', required=True, readonly=True)
    employee_confirm = fields.Many2One('res.user', 'Employee Confirmed')

    def __init__(self):
        super(BudgetLineChange, self).__init__()
#        self._sql_constraints += [
#            ('code_uniq', 'UNIQUE(budget,sequence)', 'The sequence in the budget must be unique!'),
#        ]
        self._order.insert(0, ('budget_line', 'ASC'))

    def default_state(self):
        return 'draft'

    def default_budget(self):
        return Transaction().context.get('budget') or False
    def default_name(self):
        return Transaction().context.get('name') or False
    def default_uom(self): 
        return Transaction().context.get('uom') or False
    def default_quantity(self): 
        return Transaction().context.get('quantity') or False
    def default_price_unit(self): 
        return Transaction().context.get('price_unit') or False
    def default_amount(self): 
        return Transaction().context.get('amount') or False

    def get_unit_digits(self, ids, name):
        res = {}
        for line in self.browse(ids):
            if line.uom:
                res[line.id] = line.uom.digits
            else:
                res[line.id] = 2
        return res

    def get_fields(self, ids, names):
        res = {}
        for line in self.browse(ids):
            if line.budget_line:
                for name in names:
                    res.setdefault(name, {})
                    res[name].setdefault(line.id, False)
                    if name =='analytic':
                        res[name][line.id] = line.budget_line.analytic.id
                    elif name =='name':
                        res[name][line.id] = line.budget_line.name
                    elif name =='kind':
                        res[name][line.id] = line.budget_line.kind
                    elif name =='direct_line':
                        res[name][line.id] = line.budget_line.direct_line
                    elif name =='type_line':
                        res[name][line.id] = line.budget_line.type_line
        return res

    def on_change_with_name(self, vals):
        if not vals.get('analytic'):
            return
        analytic_obj = self.pool.get('ekd.account.analytic')
        if not vals.get('name'):
            return analytic_obj.browse(vals.get('analytic')).rec_name

    def on_change_with_unit_digits(self, vals):
        if not vals.get('uom'):
            return 2
        uom_obj = self.pool.get('product.uom')
        return uom_obj.browse(vals.get('uom')).digits

    def on_change_with_amount(self, vals):
        if not vals.get('quantity') or not vals.get('price_unit'):
            return vals
        return Decimal(str(vals.get('quantity'))) * Decimal(str(vals.get('price_unit')))

    def on_change_quantity(self, vals):
        if not vals.get('quantity') or not vals.get('price_unit'):
            return vals
        return { 'amount': Decimal(str(vals.get('quantity'))) * Decimal(str(vals.get('price_unit'))) }

    def on_change_price_unit(self, vals):
        if not vals.get('quantity') or not vals.get('price_unit'):
            return vals
        return { 'amount': Decimal(str(vals.get('quantity'))) * Decimal(str(vals.get('price_unit'))) }

    def delete(self, ids):
        return super(BudgetLineChange, self).delete(ids)

    def create(self, vals):
        return super(BudgetLineChange, self).create(vals)

    def write(self, ids, vals):
        return super(BudgetLineChange, self).write(ids, vals)

BudgetLineChange()

# Операции с бюджетами
class BudgetMove(ModelSQL, ModelView):
    'Budget Move'
    _name = 'ekd.account.budget.move'
    _description = __doc__

    name = fields.Char('Name', size=None, required=True)
    budget_reduce = fields.Many2One('ekd.account.budget', 'Budget Reduce', required=True)
    budget_enlarge = fields.Many2One('ekd.account.budget', 'Budget EnLarge', required=True)
    move_date = fields.Date('Move Date')
    post_date = fields.Date('Post Date')
#    document = fields.Reference('ekd.document.budget','Document Budget', translate=True)
#    amount = fields.Numeric('Amount', digits="(16, currency_digits)")
#    currency = fields.Many2One('currency.currency','Currency')
    lines = fields.One2Many('ekd.account.budget.move.line', 'move','Lines Budget Move')
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('validated','Validated')],'Type line')

    def __init__(self):
        super(BudgetMove, self).__init__()
#        self._sql_constraints += [
#            ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
#        ]
        self._order.insert(0, ('move_date', 'ASC'))

    def get_unit_digits(self, ids, name):
        res = {}
        for line in self.browse(ids):
            if line.product_uom:
                res[line.id] = line.uom.digits
            else:
                res[line.id] = 2
        return res

BudgetMove()

# Операции с бюджетами
class BudgetMoveLine(ModelSQL, ModelView):
    'Budget Move'
    _name = 'ekd.account.budget.move.line'
    _description = __doc__

    move = fields.Many2One('ekd.account.budget.move', 'Budget Move')
    description = fields.Char('Description', size=None)
    account_reduce = fields.Many2One('ekd.account.budget.line', 'Account Reduce')
    account_enlarge = fields.Many2One('ekd.account.budget.line', 'Account Enlarge')
#    account_reduce = fields.Many2One('ekd.account.budget.line', 'Account Reduce', domain=[('budget','=',move.budget_reduce.id)])
#    account_enlarge = fields.Many2One('ekd.account.budget.line', 'Account Enlarge', domain=[('budget','=',move.budget_enlarge.id)])
    quantity = fields.Float('Quantity', digits=(16, Eval('unit_digits', 2)))
    unit_digits = fields.Function(fields.Integer('Unit Digits', on_change_with=['product_uom']), 'get_unit_digits')
    uom = fields.Many2One('product.uom', 'Unit' )
    amount = fields.Numeric('Amount', digits=(16, 2))
    currency = fields.Many2One('currency.currency','Currency')

    def __init__(self):
        super(BudgetMoveLine, self).__init__()
#        self._sql_constraints += [
#            ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
#        ]
#        self._order.insert(0, ('code', 'ASC'))

    def get_unit_digits(self, ids, name):
        res = {}
        for line in self.browse(ids):
            if line.product_uom:
                res[line.id] = line.product_uom.digits
            else:
                res[line.id] = 2
        return res

BudgetMoveLine()
