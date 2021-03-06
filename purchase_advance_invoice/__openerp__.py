# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    'name':'Purchase Advance Invoice',
    'description': ''' This module adds advance invoicing facility to purchase order''',
    'category':'Sales & Purchases',
    'version':'2.0',
    'author':'Novapoint Group LLC',
    'website':'http://www.novapointgroup.com',
    'depends':['purchase'],
    'data':[
            'wizard/purchase_advance_invoice_view.xml',
            'purchase_view.xml',
            'account_invoice_view.xml'],
    'demo':[],
    'test':[],
    'auto_install': False,
    'installable':True,
}
