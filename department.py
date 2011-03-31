# -*- coding: utf-8 -*-
#This file is part of Tryton.  The COPYRIGHT file at the top level of 
#this repository contains the full copyright notices and license terms. 
'Department'

from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pyson import Equal, Eval

_STATES = {
    'readonly': Equal(Eval('state'),'close'),
}

class Department(ModelSQL, ModelView):
    'Department'
    _name = 'ekd.company.department'
    _description = __doc__

    budget = fields.Many2One('ekd.account.budget', 'Department Budget',
                ondelete="RESTRICT")

Department()
