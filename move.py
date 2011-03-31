# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009-today Dmitry klimanov
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
#NOTE: Операционный журнал
##############################################################################
'MoveRU'
from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pyson import Greater, Equal, Eval, Get, And, Or, Not, In, Bool, PYSONEncoder

class MoveLineBundgetLine(ModelSQL, ModelView):
    "Reference Move with Budget Line"
    _name="ekd.account.move.line.budget"
    _description=__doc__

    move_line = fields.Many2One('ekd.account.move.line', 'Move Line', required=True,
                ondelete="CASCADE", readonly=True)
    budget_line = fields.Many2One('ekd.account.budget.line', 'Budget Line', required=True,
                ondelete="RESTRICT", readonly=True)
    quantity = fields.Float('Quantity', digits=(16, 4))
    amount = fields.Numeric('Amount', digits=(16, 2))

MoveLineBundgetLine()

class MoveLine(ModelSQL, ModelView):
    _name="ekd.account.move.line"

    def post(self, ids):
        super(MoveLine, self).post(ids)
        line_budget_obj = self.pool.get('ekd.account.move.line.budget')
        line_analytic_dt_obj = self.pool.get('ekd.account.move.line.analytic_dt')
        line_analytic_ct_obj = self.pool.get('ekd.account.move.line.analytic_ct')
        for line in self.browse(ids):
            if line.dt_analytic_level:
                for analytic_account in line.dt_analytic_accounts:
                    model, model_id = analytic_account.analytic.split(',',1)
                    if model == 'ekd.account.budget.line': 
                        line_budget_obj.create({
                            'move_line': line.id,
                            'budget_line': model_id,
                            'quantity': line.quantity,
                            'amount': line.amount,
                        })
            if line.ct_analytic_level:
                for analytic_account in line.ct_analytic_accounts:
                    model, model_id = analytic_account.analytic.split(',',1)
                    if model == 'ekd.account.budget.line': 
                        line_budget_obj.create({
                            'move_line': line.id,
                            'budget_line': model_id,
                            'quantity': line.quantity,
                            'amount': line.amount,
                        })

    def post_cancel(self, ids):
        super(MoveLine, self).post_cancel(ids)
        line_budget_obj = self.pool.get('ekd.account.move.line.budget')
        line_analytic_dt_obj = self.pool.get('ekd.account.move.line.analytic_dt')
        line_analytic_ct_obj = self.pool.get('ekd.account.move.line.analytic_ct')
        for line in self.browse(ids):
            if line.dt_analytic_level:
                for analytic_account in line.dt_analytic_accounts:
                    model, model_id = analytic_account.analytic.split(',',1)
                    if model == 'ekd.account.budget.line':
                        budget_ids = line_budget_obj.search([
                            ('move_line','=', line.id),
                            ('budget_line','=', int(model_id))])
                        #raise Exception(str(budget_ids), line.id, model_id)
                        line_budget_obj.delete(budget_ids)
            if line.ct_analytic_level:
                for analytic_account in line.ct_analytic_accounts:
                    model, model_id = analytic_account.analytic.split(',',1)
                    if model == 'ekd.account.budget.line':
                        budget_ids = line_budget_obj.search([
                            ('move_line','=', line.id),
                            ('budget_line','=', int(model_id))])
                        line_budget_obj.delete(budget_ids)

MoveLine()