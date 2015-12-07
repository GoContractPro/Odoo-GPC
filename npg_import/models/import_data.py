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


from openerp.osv import fields, osv, orm
from openerp import tools
from openerp.tools.translate import _
import csv
import os
import cStringIO
import base64
import datetime 
import dateutil.parser
import time
#from  dbfread import DBF
#from dbfread import field_parser
import dbf
import logging 
import sys, traceback
import contextlib
from string import strip
from  types import *
from __builtin__ import False
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT 
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import pdb


_logger = logging.getLogger(__name__)

#log_msg = ''
def index_get(L, i, v=None):
    try: return L.index(i)
    except: return v
    

    
class import_m2o_substitutions(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = "import.m2o.substitutions"
    _description = "Create new value Substitutions functionality in Fields mapping"
    
    _columns = { 
                'header_map':fields.many2one('import.data.header', 'Header Map', required=True, ondelete='cascade'),
                'src_value':fields.char('Source field value', size=64,required=True),
                'odoo_value':fields.char('Corresponding odoo value', size=64,required=True),
                }
    
class import_m2o_values(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = "import.m2o.values"
    _description = "Create new value Substitutions functionality in Fields mapping"
    
    _columns = { 
                'header_map':fields.many2one('import.data.header', 'Header Map', required=True, ondelete='cascade'),
                'default_value':fields.char('Source Default value', size=64,required=True),
                'source_field':fields.many2one('import.data.header', 'Source Field', Domain="[('import_data_id','=', header_map)]"),
                'odoo_field':fields.many2one('ir.model.fields','Corresponding Odoo Field',Domain="[('model_id','=', header_map.model)]" ),
                }

class import_data_header(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = "import.data.header"
    _description = "Map Odoo Fields to Import Fields"
    
    _columns = { 'name':fields.char('Import Field Name', size=64),
                'import_data_id':fields.many2one('import.data.file','Import Data',required=True, ondelete='cascade',),
                'is_unique':fields.boolean('Is Unique', help ='Value for Field  Should be unique name or reference identifier and not Duplicated '),
                'model':fields.many2one('ir.model','Model'),
                'model_field':fields.many2one('ir.model.fields','Odoo Field', domain="[('model_id','=',model)]"),
                'model_field_type':fields.char('Odoo Data Type', size = 128),
                'model_field_name':fields.char('Odoo Field Name', size = 128),
                'relation': fields.char('Odoo Related Model', size = 128,
                    help="The tecnmical name of  Model this field is related to"),
                'relation_id': fields.many2one('ir.model','Odoo Related Field'),
                'relation_field': fields.char('Odoo Related Field', size = 128,
                    help="The  technical name of Field Relation field in one2many and many2many "),
                'search_filter':fields.char('Filter Source', size=256,
                      help="""Use to create Filter on incoming records Field value in source must match values in list or row is skipped on import, \n
                      Can use mulitple values for filter,  format as python type list for values example 'value1','value2','value3', 
		      """
		      ),           
                'create_related':fields.boolean('Create Related', help = "Will create the related records using system default values if missing" ),
                'field_label':fields.char('Description', size=32,),
                'field_type':fields.char('Data Type', size=32,),
                'field_val':fields.char('Record Value', size=128),
                'default_val':fields.char('Default Import Val', size = 256, help = 'The Default if no values for field in imported Source'),
                'substitutions':fields.one2many('import.m2o.substitutions','header_map', string="Source Value Substitutions"),
                'is_unique_external':fields.boolean('External ID Field', readonly=True ,
                                help ='Check if this field is Unique e.g. an Account Number or A vendor Number. Its value will be used in odoo external ID'),
                'm2o_values':fields.one2many('import.m2o.values','header_map', string="Default Values or source values to map to create related and parent records"),
                'm2o_create_external':fields.boolean('Create External on Related'),
                'search_related_external':fields.boolean('External ID Search'),
                'search_name' : fields.boolean('Name Search'),
                'search_other_field' : fields.many2one('ir.model.fields','Other Search Field', domain="[('model_id','=',relation_id)]", 
                                help='Select field  to match in related record othe than Name or External ID'),
                'related_source_table': fields.many2one('import.data.file','Related Source Table'),
            }
        
    def _get_model(self,cr,uid,context={}):
        return context.get('model',False)
    
    _defaults = {
                 'model':_get_model,
                 'search_name':True,
                 }
    
    
    def onchange_model_field(self, cr, uid, ids, model_field, context=None):
#         if not ids:
#             return {}
        fld = self.pool.get('ir.model.fields').browse(cr,uid,model_field)
        if fld:
       
            relation_id = self.pool.get('ir.model').search(cr,uid,[('model','=',fld.relation)])
            vals = {'model_field_type': fld.ttype,
                    'model_field_name': fld.name,
                    'relation_field': fld.relation_field,
                    'relation_id': relation_id and relation_id[0] or False,
                    'relation': fld.relation,
                    }
#             self.write(cr,uid,ids[0],vals)
            return {'value':vals}
            
        else:
            vals =  {'model_field_type': False,
                    'model_field_name': False,
                    'relation_field': False,
                    'relation_id': False,
                    'relation': False,}
#             self.write(cr,uid,ids[0],vals)
          
            return {'value':vals}
        
class import_data_file(osv.osv):
    
    _name = "import.data.file"
    _description = "Holds import Data file information"

   
    def _get_external_id_field(self, cr, uid, ids, fields, arg, context=None):
        
        header_fld_obj = self.pool.get('import.data.header')
        search = [('is_unique_external','=',True),('import_data_id','=',ids[0])]
        extern_fld = header_fld_obj.search(cr,uid, search)[0].name or None
        return extern_fld
        
         
    _columns = {
            'name':fields.char('Name',size=32,required = True ), 
            'description':fields.text('Description',), 
            'model_id': fields.many2one('ir.model', 'Model', ondelete='cascade', required= False,
                help="The model to import"),
            'start_time': fields.datetime('Start Time',  readonly=True),
            'end_time': fields.datetime('End Time',  readonly=True),
            'attachment': fields.many2many('ir.attachment',
                'data_import_ir_attachments_rel',
                'import_data_id', 'attachment_id', 'CSV File'),
            'error_log': fields.text('Status Log'),
            'test_sample_size': fields.integer('Test Sample Size'),
            'do_update': fields.boolean('Allow Update', 
                    help='If Set when  matching unique fields on records will update values for record, Otherwise will just log duplicate and skip this record '),
            'header_ids': fields.one2many('import.data.header','import_data_id','Fields Map',limit=300),
            'index':fields.integer("Index"),
            'dbf_path':fields.char('DBF Path',size=256),
            'record_num':fields.integer('Current Record'),
            'tot_record_num':fields.integer("Total Records"),
            'record_external':fields.boolean('Use External ID' , help = 'record number and File name to be used for External ID'),
            'has_errors':fields.boolean('Has Errors'),
            'rollback':fields.boolean('Roll Back Test Records'),
            'external_id_field':fields.many2one('import.data.header', string='External Id Field', domain="[('import_data_id','=',active_id)]"),
            'row_count':fields.integer("Rows Processed"),
            'count':fields.integer("Rows Imported"),
            'time_estimate':fields.float("Time Estimate"),
            'base_external_dbsource' : fields.many2one('base.external.dbsource', string="ODBC Connection", help="External Database connection to foreign databases using ODBC, MS-SQL, Postgres, Oracle Client or SQLAlchemy."),
            'src_table_name' : fields.char('Source Table Name',size=256),
            'src_type' : fields.selection([('csv', 'CSV'),('dbf', 'DBF File'),('odbc', 'ODBC Connection')], "Data Source Type", required=True),
            
            'sql_source': fields.text('SQL', help='Write a valid "SELECT" SQL query to fetch data from Source database'),
            #                 'state':fields.selection([(''),()]),
                'schedule_import': fields.many2one('ir.cron','Related Source Table'),
            }
    
    _defaults = {
        'test_sample_size':10,
        'record_num':1,
        'src_type':'csv'
        }

    
    def import_schedule(self, cr, uid, ids, context=None):
        cron_obj = self.pool.get('ir.cron')
        for imp in self.browse(cr, uid, ids, context):
            cron_id = False
            if not imp.schedule_import:
                new_create_id = cron_obj.create(cr, uid, {
                    'name': 'Import ODBC tables',
                    'interval_type': 'hours',
                    'interval_number': 1,
                    'numbercall': -1,
                    'model': 'import.data.file',
                    'function': 'action_import',
                    'doall': False,
                    'active': True
                })
                imp.write({'schedule_import':new_create_id})
                cron_id = new_create_id
            else:
                cron_id = imp.schedule_import.id
        return {
            'name': 'Import ODBC tables',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'ir.cron',
            'res_id': cron_id,
            'type': 'ir.actions.act_window',
        }
    
    
    

    def onchange_record_external(self,cr,uid, ids, record_external, context=None):
        
        if record_external:
            return {'value': {'external_id_field': False}}
        
    def onchange_external_id_field(self,cr,uid, ids, external_id_field,  context=None):
       
        if ids: 
            header_ids_vals = []
            header_ids = self.pool('import.data.header').search(cr,uid,[('import_data_id','=',ids[0])])
            for header_rec in self.pool('import.data.header').browse(cr,uid, header_ids, context = context):
            
                if header_rec.id == external_id_field:
                    value = True
                else:
                    value = False
                    
                vals = {  'is_unique_external': value}
                header_ids_vals.append((1,header_rec.id, vals))
                
            return{'value':{"header_ids":header_ids_vals}}
        else:
            return {}

    def action_get_headers(self, cr, uid, ids, context=None):
        
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.src_type == 'dbf':
                self.action_get_headers_dbf(cr, uid, ids, context)
                return
            elif rec.src_type == 'csv':
                self.action_get_headers_csv(cr, uid, ids, context)
                return
            elif rec.src_type == 'odbc':
                self.action_get_headers_odbc(cr, uid, ids, context)
                return
            
        raise osv.except_osv('Warning', 'No Data files to Import')
    
    def get_label_match_index(self, cr, uid, dbf_table ):
        
        
        dbf_path = dbf_table.filename
        dbf_directory = os.path.dirname(dbf_path)
        table_name = os.path.basename(dbf_path).split('.')[0]

        fldlabel_dbf_table = dbf.Table(dbf_directory + '/FLDLABEL.DBF')
        fldlabel_dbf_table.open()
        
        if not fldlabel_dbf_table:
            
            e = 'No Labels in DBF Import  %s:'  % (fldlabel_path, )
            _logger.error(_('Error %s' % (e,)))
              
        index = fldlabel_dbf_table.create_index(lambda rec: rec.table)
        
        return index.search(match=table_name.ljust(10))
                
 
    
    def action_get_headers_dbf(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        tot_records = 0
        for rec in self.browse(cr, uid, ids, context=context):
            rec.record_num = 1
            try:
         
                header_obj = self.pool.get('import.data.header')
                header_ids=header_obj.search(cr, uid,[('import_data_id','=',ids[0])])
                    
                if header_ids:
                    header_obj.unlink(cr,uid,header_ids,context=None)
               
                dbf_table = dbf.Table(rec.dbf_path)
                dbf_table.open()
                info = dbf.info(rec.dbf_path)
                
                structure = dbf.structure(rec.dbf_path)


                if not dbf_table:
                    
                    e = 'Error opening DBF Import  %s:'  % (rec.dbf_path, )
                    _logger.error(_('Error %s' % (e,)))
                    vals = {'error_log': e,
                            'has_errors':True}
                    self.write(cr,uid,ids[0],vals) 
                 
                tot_records = len(dbf_table)    
                if tot_records == 0:
                    e = 'Table has no data to Import  %s:'  % (rec.dbf_path, )
                    _logger.error(_('Error %s' % (e,)))
                    vals = {'error_log': e,
                            'has_errors':True}
                    self.write(cr,uid,ids[0],vals)
                    return
                    
                dbf_label_index = self.get_label_match_index(cr, uid, dbf_table)
                

                for field in structure:
           
                    field = field.split()

                    field_label =  self.vision_match_field_label(cr, uid, field[0], index = dbf_label_index)
        
                    fld_obj = self._match_import_header(cr, uid, rec.model_id.id, field[0], field_label)    
                        
                    vals = {'name':field[0], 'import_data_id':rec.id,
                            'model_field':fld_obj and fld_obj.id or False,
                            'model_field_name' :fld_obj and fld_obj.name or False,
                            'model_field_type' : fld_obj and fld_obj.ttype or False,
                            'model':rec.model_id and rec.model_id.id,
                            'relation': fld_obj and fld_obj.relation or False,
                            'relation_field' : fld_obj and fld_obj.relation_field or False,
                            'field_label': field_label or False,
                            'field_val':dbf_table[0][field[0]],
                            'field_type':field[1]
                            
                            
                            }
                    header_id = self.pool.get('import.data.header').create(cr,uid,vals,context=context)
                    
                vals = {'error_log':'Successful Header Import',
                    'has_errors':False,
                    'tot_record_num':tot_records, 
                    'description':info
                    }
                self.write(cr,uid,ids[0],vals)    
                
                return {'value': vals}
                
            except:
                sys_info = sys.exc_info()[1][1]
                e = 'Error opening DBF Import  %s: \n%s \n%s' % (rec.dbf_path, sys_info[1],sys_info) 
                print e
                _logger.error(_('Error:  %s ' % (e,)))
                vals = {'error_log': e,
                        'has_errors':True}
                self.write(cr,uid,ids[0],vals)  
 
        return {'value': vals}
    
    def action_get_headers_csv(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):

            for attach in rec.attachment:
                data_file = attach.datas
                continue
            str_data = base64.decodestring(data_file)
            
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                partner_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            
            header_csv_obj = self.pool.get('import.data.header')
            header_csv_ids=header_csv_obj.search(cr, uid,[('import_data_id','=',ids[0])])
            
            if header_csv_ids:
                header_csv_obj.unlink(cr,uid,header_csv_ids,context=None)
            
            headers_list = []
            for header in partner_data[0]:
                headers_list.append(header.strip())
            n=0
            row = 0
            for header in headers_list:
                row+= 1
                fids = self.pool.get('ir.model.fields').search(cr,uid,['|',('field_description','ilike',header),('name','ilike',header), ('model_id', '=', rec.model_id.id)])
                rid = self.pool.get('import.data.header').create(cr,uid,{'name':header,'index': row, 'csv_id':rec.id, 'model_field':fids and fids[0] or False, 'model':rec.model_id.id},context=context)
                
        return True
    
    def action_get_headers_odbc(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):
            src_table = str(rec.src_table_name).strip()
            if rec.sql_source:
                qry = str(rec.sql_source)
            else:
    #        qry = "select column_name, data_type, character_maximum_length from INFORMATION_SCHEMA.COLUMNS where table_name = %s;" % src_table
    #        qry = "select TOP 1 * from %(src_table)s"
    #        params = {'src_table':src_table}
    #                 result = rec.base_external_dbsource.execute(sqlquery=qry,sqlparams=params, metadata=True)
                qry = "select TOP 1 * from %s" % src_table
            result = rec.base_external_dbsource.execute(sqlquery=qry,metadata=True)
            if not result.has_key('cols'):
                continue
            has_row = result.has_key('rows')
            header_csv_obj = self.pool.get('import.data.header')
            header_csv_ids=header_csv_obj.search(cr, uid,[('import_data_id','=',ids[0])])
            
            if header_csv_ids:
                header_csv_obj.unlink(cr,uid,header_csv_ids,context=None)
            
#             headers_list = []
#             for header in result['cols']:
#                 headers_list.append(header[0].strip())
            headers_list = result['cols']
            row_data = result['rows']
            n=0
            for col in headers_list:
#                 fids = self.pool.get('ir.model.fields').search(cr,uid,[('field_description','ilike',header), ('model_id', '=', rec.model_id.id)])
#                 rid = self.pool.get('import.data.header').create(cr,uid,{'name':header,'index': row, 'csv_id':rec.id,
#                                                                           'model_field':fids and fids[0] or False, 
#                                                                           'model':rec.model_id.id},context=context)
                header = col[0]
#                fld_obj = self._match_import_header(cr, uid, rec.model_id.id, header, header)    
#		for c in col:
#			print c
#		pdb.set_trace()
                vals = {'name':header, 'import_data_id':rec.id,
                            'model_field':fld_obj and fld_obj.id or False,
                            'model_field_name' :fld_obj and fld_obj.name or False,
                            'model_field_type' : fld_obj and fld_obj.ttype or False,
                            'model':rec.model_id and rec.model_id.id,
                            'relation': fld_obj and fld_obj.relation or False,
                            'relation_field' : fld_obj and fld_obj.relation_field or False,
                            'field_label': header or False,
                            'field_type':col[1],
                            'field_val' : False,
                            }
                if has_row:
                    vals.update({'field_val' : row_data[n],})
                    n += 1
                header_id = self.pool.get('import.data.header').create(cr,uid,vals,context=context)
        return True
 
    def vision_match_field_label(self, cr ,uid,field_name, index ):         
        
        for fld_label in index:
            
            label_fld_name = fld_label.fldname.lower().strip()
                        
            if  label_fld_name == field_name:
                return fld_label.fldlabel.lower().strip()
        return None                                  
 
    def _match_import_header(self, cr,uid, model_id, field, field_label):
        """ Attempts to match a given header to a field of the
        imported model.

        :param str header: header name from the data file
        :param fields:
        :returns: False if the header couldn't be matched, or
                  the fields object
        :rtype: field object
        """
        #print field or '*' + '-' + field_label or '*'
        field = (field and field.strip().lower()) or '' 
        field_label = ( field_label and field_label.strip().lower()) or ''
        #print field + '-' + field_label
        
        search_domain =[('name','!=','display_name'), '&', ('model_id', '=', model_id),'|','|',('field_description','ilike',field),('field_description','ilike',field_label ),
                                                               '|',('name','ilike',field),('name','ilike',field_label)]
    
        #print search_domain   
        model_fields = self.pool.get('ir.model.fields')
        fields_odoo = model_fields.search(cr,uid,search_domain)
        fields_odoo = model_fields.browse(cr,uid,fields_odoo)
        if len(fields_odoo) == 1:
            return fields_odoo[0]
        
        for field_odoo in fields_odoo:
            
            field = field.strip().lower()
            odoo_description = field_odoo['field_description']
            odoo_description = (odoo_description and odoo_description.strip().lower()) or ''
            odoo_name =  field_odoo['name']
            odoo_name = (odoo_name and odoo_name.strip().lower()) or ''
        #    print field + ' == ' + odoo_name + ' or ' + odoo_description
            if field == odoo_description or field == odoo_name \
                    or field_label == odoo_description or field_label == odoo_name:
                return field_odoo

        return None            

    def search_record_exists(self, cr, uid, rec, data,header_dict, unique_fields=[]):
        if not unique_fields: return False
        ir_model_obj = self.pool.get('ir.model')
        ir_model_fields_obj = self.pool.get('ir.model.fields')
        
        dom = []
        for col in unique_fields:
            dom.append((col, '=', data[header_dict[col]]))
            
        obj = self.pool[rec.model_id.model]
        return obj.search(cr,uid,dom)
        
        #Todo Add Code here to  search on fields in header_dict which are flaged as Unique Record
        # for example a Name or Ref Field
        # if Found Return record ID (most also Consider is possible could be multiple records if search field not Truely unique Will update all these)
        # if not Found Return false
        
        return False  
    
    def action_import(self, cr, uid, ids, context=None):
        
        for rec in self.browse(cr, uid, ids, context=context):
        
            if rec.src_type == 'dbf':
                
                if context.get('test',False):
                    self.action_import_dbf(cr, uid, ids, context)
                    return True
        
                else:
                    vals={
                        'name': 'Import %s' % (rec.name),
                        'user_id': uid,
                        'model': 'import.data.file',
                        'function': 'action_import_dbf',
                        'args': repr([ids[0]])\
                        }
                    
                    self.pool.get('ir.cron').create(cr, uid, vals)
                    
                    stats_vals = {'start_time':False,
                    'end_time': False,
                    'error_log': False,
                    'time_estimate': False,
                    'row_count': False,
                    'count': False}   
                    return stats_vals

            elif rec.src_type == 'csv':
                self.action_import_csv(cr, uid, ids, context)
                return
            elif rec.src_type == 'odbc':
                self.action_import_odbc(cr, uid, ids, context)
                return
            
        raise osv.except_osv('Warning', 'No Data files to Import')
             
    def convert_backslash_string(self,s):
        
        if '//' in s:
            if isinstance(s, str):
                s = s.encode('string-escape')
            elif isinstance(s, unicode):
                s = s.encode('unicode-escape')
            return s
        else:
            return s
    
    def convert_raw_data_strings(self, field_raw):        
        
        if isinstance( field_raw, str):
            return field_raw.strip()

        elif isinstance(field_raw, unicode):
            return field_raw.strip()

        elif isinstance(field_raw, datetime.datetime):
            return field_raw.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        
        elif isinstance(field_raw , datetime.date):
            return field_raw.strftime(DEFAULT_SERVER_DATE_FORMAT)

        else: str(field_raw)
     
    def skip_current_row_filter(self, field_val, search_filter):
        
        if not  search_filter or search_filter == '[]':
            return False
        
        
        search_filter =  search_filter.replace('[','')
        search_filter =  search_filter.replace(']','')
        
        search_list = tuple(search_filter(split(',')))
        if not search_list:
            search_list.append(search_filter)
            
        if field_val in search_list:
            return False
            
        else:
            return True
    
    def do_substitution_mapping(self,field_val,substituions):
        
        substitutes = {}
        if substituions:
            for sub in substituions:
                substitutes.update({str(sub.src_value).strip() : str(sub.odoo_value).strip()})
                
        return substitutes.get(field_val, field_val)
                    
     
    def search_records(self, cr,uid, field_search_val, field, context=None ): 
            
        related_obj = self.pool.get(field.relation)
                  
            
        if related_obj:
    
            if field.search_related_external:
                search = [('name','=',field_search_val),('model','=', field.relation)]                     
                ext_ids =  self.pool.get('ir.model.data').search(cr,uid,search) or None
                if ext_ids:
                    res = self.pool.get('ir.model.data').browse(cr, uid, ext_ids[0])
                    return res and res.res_id or False
                
            if field.search_name:
                self.convert_backslash_string( field_search_val)
                res = related_obj.name_search(cr,uid,name=field_search_val )
                return res and res[0][0]
                    
            if field.search_other_field:    
                search = [(field.search_other_field.name,'=',field_search_val)]
                res = related_obj.search(cr, uid, search)
                return res and res[0]  or False
        
        return False
                
    def create_related_record(self, cr, uid, ids,rec, field, field_val, row = None, context= None ):
        
        try:
            vals = self.set_related_vals(cr, uid, field_val, field, context)
            res_id =  self.pool.get(field.relation).create(cr,uid, vals,context = context) or False
            
            if not res_id:
                log = _('Warning!: Related record for  value \'%s\' Not Created for relation \'%s\' row %s' % (res_id, field_val, field.relation, row )) 
                rec.error_log += '\n'+ log
                _logger.info( log)
                return   False 
            
            #if searching on related external IDs then create the related  external ID based on  field_val used to search 
            if res_id and field.search_related_external: 
                vals = {'name':field_val,
                    'model': field.relation,
                    'res_id':res_id,
                    'module':''
                    }

                self.pool.get('ir.model.data').create(cr,uid,vals, context=context)
            
            log = _('Related record ID %s : value \'%s\' Created for relation \'%s\' row %s' % (res_id, field_val, field.relation, row )) 
            rec.error_log += '\n'+ log
            _logger.info( log)    
            
            return res_id
            
        except:
            cr.rollback()
            rec.has_errors = True
            error_txt = _('Error  record \'%s\' not created for model \'%s\'' % (vals,relation))
            self.update_log_error(cr, uid, ids, rec, error_txt, context)
            
            return False
        
     
    def create_import_record(self, cr, uid, ids, rec, vals, external_id_name = False, row = None,context=None): 
        
        model_obj = self.pool.get(rec.model_id.model)
        res_id = False
        try:
            res_id = model_obj.create(cr,uid, vals, context)
              
            if external_id_name:                   
                external_vals = {'name':external_id_name,
                                 'model':rec.model_id.model,
                                 'res_id':res_id,
                                 'module':''
                                 }
                
                self.pool.get('ir.model.data').create(cr,uid,external_vals, context=context)
                
            _logger.info(_('Created record %s from Source row %s' % (vals,row)))
             
        except:
            cr.rollback()
            rec.has_errors = True
            error_txt = _('Error record %s not created for import row  %s' % (vals,row ))
            self.update_log_error(cr, uid, ids, rec, error_txt, context)
            
        return res_id
                      
    
    def search_external_id(self, cr, uid, external_id_name, model, context = None):
        
                
        search = [('name','=',external_id_name),('model','=', model)]                     
        ext_ids =  self.pool.get('ir.model.data').search(cr,uid,search) or None
        if ext_ids:
            res = self.pool.get('ir.model.data').browse(cr, uid, ext_ids[0])
            return res and res.res_id or False
        
        return False
    
    def update_log_error(self, cr, uid, ids,rec, error_txt = '', context = None):

        e = traceback.format_exc()
        _logger.error(error_txt + e)
        rec.error_log += error_txt +'\n' + e + '\n'
        log_vals = {'error_log': rec.error_log,
                'has_errors':rec.has_errors}
        self.write(cr,uid,ids,log_vals)
        return log_vals
    
    def check_external_id_name(self, cr, uid, row, rec, external_id_name = False):  
           
                                    
        #  When Using field for External ID 
        if external_id_name:
            return external_id_name 
        #  When using Record Row External ID and No field External ID            
        elif rec.record_external:         
            return ('%s_%s' % ( rec.name.split('.')[0], row,))
        else:
            return False  
                 
    
    def set_related_vals(self, cr, uid, field_val, field = None, context=None):
                                                   
            #TODO add functionality to build other Relate values defualts from list or other Tables
            return {'name': field_val}
        
    def convert_odoo_data_types(self, cr, uid, ids, rec, field, field_val, row=False, rec_val=None, context = None):
        
        if field.model_field_type == 'many2one' and field_val:
     
            res_id = self.search_records(cr, uid, field_search_val=field_val, field=field, context=context)
            
            if not res_id and field.create_related: 
                # If Success found the related record 
                res_id = self.create_related_record(cr, uid, ids,rec=rec, field=field, field_val=field_val, row=row, context=context)
                
            return res_id
        
        elif field.model_field_type == 'boolean' and  field_val:
            try:
                field_val = bool(field_val)
            except:
                cr.rollback()
                rec.has_errors = True
                field_val = False
                error_txt = ('Error: Row %s Field %s -- %s is not required Boolean type' %s (row,field.model_field.name,field_val,))
                self.update_log_error( cr, uid, ids, rec, error_txt, context)
                
            return field_val
        
        elif field.model_field_type == 'float' and  field_val:
                
            if field_val.lower() == 'false': field_val = '0.0'
            
            try:
                field_val = float(field_val)
            except:
                cr.rollback()
                rec.has_errors = True
                field_val = 0.0
                error_txt = _('Error: Row %s Field %s -- %s is not required  Floating Point type' %s ( row,field.model_field.name,field_val))
                self.update_log_error( cr, uid, ids, rec, error_txt, context)
                
            return field_val

        elif field.model_field_type == 'integer' and  field_val:
              
            if field_val.lower() == 'false': field_val = '0'
            try:
                field_val = int(field_val)
            except:
                cr.rollback()
                rec.has_errors = True
                field_val = 0
                error_txt = _('Error: Row %s Field %s -- not required Integer  type' %s (row,field.model_field.name,field_val))
                self.update_log_error( cr, uid, ids, rec, error_txt, context)
                
            return field_val
        
        elif field.model_field_type == 'selection' and  field_val:
            return field_val
        
        elif field.model_field_type in ['char', 'text','html'] and  field_val:
            return field_val
        elif field.model_field_type == 'binary' and  field_val: 
            return field_val
        elif field.model_field_type in ['one2many','many2many']:
                                
            
            
            res_id = self.search_records(cr, uid, field_search_val=field_val, field=field, context=context)
            m20 = self.get_o2m_m2m_vals(cr, uid, ids, field,field_val=field_val,res_id=res_id) 
            #TODO Add code here to handle finding related Records values in the Source Database and build Vals dict to pass to get_o2m_m2m_vals method        
            if rec_val:
                if m20:return rec_val.append(m20)
                else: rec_val
            else:
                if m20:return [m20]
                else:None
        else:
            return field_val
    
    def get_o2m_m2m_vals(self, cr, uid, ids,field, field_val, res_id = False, vals = None, context = None ): 
        
        if res_id:
            return (4,res_id)
        elif vals:
            return (0,0,{vals})
        else:
            related_obj = self.pool.get(field.relation)
            name = related_obj._rec_name or False
            model_id = self.pool.get('ir.model').search(cr,uid,[('model','=',field.relation)])
            field_id = self.pool.get('ir.model.fields').search(cr,uid,[('model_id','=',model_id and model_id[0] or False),('name','=',name)])
            field_obj = self.pool.get('ir.model.fields').browse(cr,uid,field_id and field_id[0] or False)
            if field_obj:
                if field_obj.ttype == 'many2one':
                    res_id = self.search_records(cr, uid, field_search_val=field_val, field=field, context=context)
                    if res_id:return (0,0,{name:res_id})
                    else: return None
                else:
                    return (0,0,{name:field_val})   
            else:
                return None
                 
       


    def update_statistics(self,cr,uid,ids,rec,processed_rows,count,remaining=True):   
        '''params:
        rec: The main record set for import File
        processed_rows: Current number of Rows processed from Data Source
        count: Total number of Rows actually imported without Skipped
        
        '''
        estimate_time = self.estimate_import_time(start_time=rec.start_time, processed_rows=processed_rows, tot_record_num=rec.tot_record_num, remaining=remaining)

        stats_vals = {'start_time':rec.start_time,
                    'end_time': False,
                    'error_log': rec.error_log,
                    'time_estimate': estimate_time,
                    'row_count': processed_rows,
                    'count': count}
                        
        self.write(cr,uid,ids,stats_vals) 
        
        return stats_vals
        
    def estimate_import_time(self, start_time, processed_rows, tot_record_num, remaining = True):
        '''params:
        start_time: Time in string format YYYY-MM-DD HH:MM:SS when import started
        processed_rows: Current number of Rows processed from Data Source
        tot_record_num: Total number of Rows in data Source
        remaining: Boolean if Tru return time left in import if false return total Estimated time
        '''
        t2 = datetime.datetime.now()
        time_delta = (t2 - datetime.datetime.strptime(start_time, DEFAULT_SERVER_DATETIME_FORMAT))
        time_each = time_delta / processed_rows
        time_each = time_each.total_seconds()
        
        if remaining:
            
            return (time_each * (tot_record_num - processed_rows)) / 3600 # return time in hours
                          
        else:
            return (time_each * tot_record_num) / 3600                
          
 
            
    def action_import_dbf(self, cr, uid, ids, context=None):
        
#        global log_msg
        
        if context is None:
            context = {}
        
        list_size =0 
        
        try:
            
            for rec in self.browse(cr, uid, ids, context=context):
                rec.has_errors = False
                rec.error_log = ''           
                dbf_table = dbf.Table(rec.dbf_path)
                dbf_table.open()
                rec.tot_record_num = len(dbf_table)
                rec.start_time = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                
                row = 0
                count = 0
                
                for import_record in dbf_table:
                    
                    vals = {}
                    search_unique =[]
                    external_id_name = False
                    skip_record = False
                   

                    
                    row+= 1
                    for field in rec.header_ids:
    
                        try:   # Buidling Vals DIctionary
                        
                            if not field.model_field: continue # Skip to next Field if no Odoo field set
                           
                            res_id = False
                            field_val = False
                            
                            field_raw =  field.name and import_record[field.name]  or False
                            # test  Clean and convert Rawincoming Data values to stings to allow comparing to search filters and substitutions         
                            field_val = self.convert_raw_data_strings(field_raw)
                            
                            if not field_val and field.default_val:
                                field_val = field.default_val

                            if field.is_unique_external:
                                external_id_name = field_val

                            # IF Field value not found in Filter Search list skip out to next import record row
                            if self.skip_current_row_filter(field_val,field.search_filter):
                                skip_record = True
                                break
                            
                            # Update Field value if Substitution Value Found. 
                            field_val = self.do_substitution_mapping(field_val,field.substitutions)
                            
                            #Convert to Odoo Data types and add field to Record Vals Dictionary

                            vals[field.model_field.name] = self.convert_odoo_data_types(cr, uid, ids, rec, field, field_val, row, vals.get(field.model_field.name,False), context)
                               
                            # If field is marked as Unique in mapping append to search on unique to use to confirm no duplicates before creating new record    
                            if field.is_unique and not field_val:
                                
                                error_txt = _('Error Required unique field value not set at line %s ' % (row))
                                self.update_log_error( cr, uid,ids,rec, error_txt, context)
                                skip_record = True
                                break 
                            elif field.is_unique:
                                search_unique.append((field.model_field.name,"=", field_val))
                                                                        
                        except: # Buidling Vals DIctionary
                            cr.rollback()
                            rec.has_errors = True
                            error_txt = _('Error Building Vals at row:  %s -Field: %s == %s \n Vals Dict: %s ' %(row,field.model_field.name, field_val, vals,))
                            self.update_log_error( cr, uid, ids,rec, error_txt, context)
                    
                    if skip_record : # this Record does not match filter skip to next Record in import Source
                        continue 
                    
                    try:  # Finding existing Records  
                        
                        if len(search_unique) > 0:      
                            search_ids = self.pool.get(rec.model_id.model).search(cr,uid,search_unique)
                        else:
                            search_ids = False
                            
                        external_id_name = self.check_external_id_name(cr, uid, row=row, rec=rec, external_id_name = external_id_name)

                        if external_id_name:
                        
                            res_id = self.search_external_id(cr, uid, external_id_name, rec.model_id.model, context)
                                
                            if rec.do_update and  search_ids and res_id and res_id != search_ids[0]:
                                error_txt = _('Error External Id and Unique not matching %s %s  Found at Row %s record skipped' % (search_unique,external_id_name,row,))
                                self.update_log_error( cr, uid, ids, rec, error_txt, context)
                                
                                continue

                        elif search_ids and not rec.do_update:
                                error_txt = _('Error Duplicate on Uniquie %s  Found at Row %s record skipped' % (search_unique,row,))
                                self.update_log_error( cr, uid, ids, rec, error_txt, context)
                                continue
                        elif search_ids:
                            res_id = search_ids[0] 
                        else:
                            res_id = False   
                            
                        
                    except: # Finding Existing Records
                        cr.rollback()
                        rec.has_errors = True
                        error_txt = _('Error Finding:  %s-%s-%s ' % (row,search_unique,external_id_name))
                        self.update_log_error(cr, uid, ids, rec, error_txt, context)                    

                    try: # Writing or Create Records     


                        if res_id and rec.do_update:
                            
                            self.pool.get(rec.model_id.model).write(cr,uid,res_id, vals,context=context)
                            _logger.info(_('Update row %s vals %s') % (row,vals,))
                        
                        elif res_id and not rec.do_update:
                            
                            error_txt = _('Error Duplicate External %s ID  Found at line %s record skipped') % (external_id_name,row,)
                            self.update_log_error( cr, uid, ids, rec, error_txt, context)
                            continue
                     
                        else: # no record Found So Create new record
                            
                            self.create_import_record(cr, uid, ids, rec=rec, vals=vals, external_id_name=external_id_name, row=row, context=context)
                    except: # Error Writing or Creating Records
                        cr.rollback()
                        rec.has_errors = True
                        error_txt = _('Writing or Creating row %s vals %s ' % (row,vals,))
                        self.update_log_error(cr, uid, ids, rec, error_txt, context)
                        

                    if row%10 == 0: # Update Statics every 10 records
                        self.update_statistics(cr,uid ,ids , rec, row, count)
                        
                    if rec.rollback and context.get('test',False): 
                        pass
                    else:
                        cr.commit() 

                    count += 1 
                    if  count >= rec.test_sample_size  and context.get('test',False):
                        
                        if rec.rollback: cr.rollback()
                        # Exit Import Records Loop  
                        return{'value':self.update_statistics(cr, uid, ids, rec=rec, processed_rows=row, count=count, remaining=False)}
        except:
            cr.rollback()
            rec.has_errors = True
            error_txt = _('Import Aborted')
            return self.update_log_error( cr, uid, ids, rec, error_txt, context)
        
        return 
    
    def action_import_odbc(self, cr, uid, ids, context=None):
        
#        global log_msg
        
        if context is None:
            context = {}
        
        list_size =0 
        
        try:
            
            for rec in self.browse(cr, uid, ids, context=context):
                rec.has_errors = False
                rec.error_log = ''  
                src_table = str(rec.src_table_name).strip()  
                if rec.sql_source:         
                    qry = str(rec.sql_source)
                elif context.get('test',False):
                    qry = "select TOP %s * from %s" % (rec.test_sample_size, src_table)
                else:
                    qry = "select * from %s" % src.table
#                 qry = "select TOP 10 * from %s" % src_table
#                 all_data = rec.base_external_dbsource.execute(sqlquery=qry)
                
#                 conn = rec.base_external_dbsource.conn_open()
                conn = self.pool.get('base.external.dbsource').conn_open(cr, uid, rec.base_external_dbsource.id)
#                 conn = self.conn_open(cr, uid, obj.id)
                cur = conn.cursor()
                
                cur.execute(qry)
                
#                 rec.tot_record_num = len(all_data)
                rec.write({'start_time' : datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
                cr.commit()
                row = 0
                count = 0
                all_data = True
                while all_data:
                    all_data = cur.fetchmany(500)
                    if not all_data:
                        break
                    for import_record in all_data:
                        
                        vals = {}
                        search_unique =[]
                        external_id_name = False
                        skip_record = False

                        row+= 1
                        for field in rec.header_ids:
        
                            try:   # Buidling Vals DIctionary
                            
                                if not field.model_field: continue # Skip to next Field if no Odoo field set
                               
                                res_id = False
                                field_val = False
                                
    #                             field_raw =  field.name and import_record[field.name]  or False
                                field_raw =  field.name and getattr(import_record, field.name)  or False
                                  
                                # test  Clean and convert Rawincoming Data values to stings to allow comparing to search filters and substitutions         
                                field_val = self.convert_raw_data_strings(field_raw)
                                
                                if not field_val and field.default_val:
                                    field_val = field.default_val
    
                                if field.is_unique_external:
                                    external_id_name = field_val
    
                                # IF Field value not found in Filter Search list skip out to next import record row
                                if self.skip_current_row_filter(field_val,field.search_filter):
                                    skip_record = True
                                    break
                                
                                # Update Field value if Substitution Value Found. 
                                field_val = self.do_substitution_mapping(field_val,field.substitutions)
                                
                                #Convert to Odoo Data types and add field to Record Vals Dictionary
    
                                vals[field.model_field.name] = self.convert_odoo_data_types(cr, uid, ids, rec, field, field_val, row, vals.get(field.model_field.name,False), context)
                                   
                                # If field is marked as Unique in mapping append to search on unique to use to confirm no duplicates before creating new record    
                                if field.is_unique and not field_val:
                                    
                                    error_txt = _('Error Required unique field value not set at line %s ' % (row))
                                    self.update_log_error( cr, uid,ids,rec, error_txt, context)
                                    skip_record = True
                                    break 
                                elif field.is_unique:
                                    search_unique.append((field.model_field.name,"=", field_val))
                                                                            
                            except: # Buidling Vals DIctionary
                                cr.rollback()
                                rec.has_errors = True
                                error_txt = _('Error Building Vals at row:  %s -Field: %s == %s \n Vals Dict: %s ' %(row,field.model_field.name, field_val, vals,))
                                self.update_log_error( cr, uid, ids,rec, error_txt, context)
                        
                        if skip_record : # this Record does not match filter skip to next Record in import Source
                            continue 
                        
                        try:  # Finding existing Records  
                            
                            if len(search_unique) > 0:      
                                search_ids = self.pool.get(rec.model_id.model).search(cr,uid,search_unique)
                            else:
                                search_ids = False
                                
                            external_id_name = self.check_external_id_name(cr, uid, row=row, rec=rec, external_id_name = external_id_name)
    
                            if external_id_name:
                            
                                res_id = self.search_external_id(cr, uid, external_id_name, rec.model_id.model, context)
                                    
                                if rec.do_update and  search_ids and res_id and res_id != search_ids[0]:
                                    error_txt = _('Error External Id and Unique not matching %s %s  Found at Row %s record skipped' % (search_unique,external_id_name,row,))
                                    self.update_log_error( cr, uid, ids, rec, error_txt, context)
                                    
                                    continue
    
                            elif search_ids and not rec.do_update:
                                    error_txt = _('Error Duplicate on Uniquie %s  Found at Row %s record skipped' % (search_unique,row,))
                                    self.update_log_error( cr, uid, ids, rec, error_txt, context)
                                    continue
                            elif search_ids:
                                res_id = search_ids[0] 
                            else:
                                res_id = False   
                                
                            
                        except: # Finding Existing Records
                            cr.rollback()
                            rec.has_errors = True
                            error_txt = _('Error Finding:  %s-%s-%s ' % (row,search_unique,external_id_name))
                            self.update_log_error(cr, uid, ids, rec, error_txt, context)                    
    
                        try: # Writing or Create Records     
    
    
                            if res_id and rec.do_update:
                                
                                self.pool.get(rec.model_id.model).write(cr,uid,res_id, vals,context=context)
                                _logger.info(_('Update row %s vals %s') % (row,vals,))
                            
                            elif res_id and not rec.do_update:
                                
                                error_txt = _('Error Duplicate External %s ID  Found at line %s record skipped') % (external_id_name,row,)
                                self.update_log_error( cr, uid, ids, rec, error_txt, context)
                                continue
                         
                            else: # no record Found So Create new record
                                
                                self.create_import_record(cr, uid, ids, rec=rec, vals=vals, external_id_name=external_id_name, row=row, context=context)
                        except: # Error Writing or Creating Records
                            cr.rollback()
                            rec.has_errors = True
                            error_txt = _('Writing or Creating row %s vals %s ' % (row,vals,))
                            self.update_log_error(cr, uid, ids, rec, error_txt, context)
                            
    
                        if row%10 == 0: # Update Statics every 10 records
                            self.update_statistics(cr,uid ,ids , rec, row, count)
    
                        count += 1 
                        if  count >= rec.test_sample_size  and context.get('test',False):
                            
                            if rec.rollback: cr.rollback()
                            # Exit Import Records Loop  
                            return{'value':self.update_statistics(cr, uid, ids, rec=rec, processed_rows=row, count=count, remaining=False)}
                            
                    if rec.rollback and context.get('test',False): 
                        pass
                    else:
                        cr.commit() 
                            
                conn.close()
        except:
            cr.rollback()
            conn.close()
            rec.has_errors = True
            error_txt = _('Import Aborted')
            return self.update_log_error( cr, uid, ids, rec, error_txt, context)
        
        return 
    
    def action_import_csv(self, cr, uid, ids, context=None):

        start = time.strftime('%Y-%m-%d %H:%M:%S')       
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):
            
            if not rec.header_ids:
                raise osv.except_osv('Warning', 'No Header selected in Header list')
            
            
            for attach in rec.attachment:
                data_file = attach.datas
                continue
            str_data = base64.decodestring(data_file)
            
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                csv_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            
            error_log = ''
            n = 1
            
            time_start = datetime.datetime.now()
            print "time_start",time_start
            headers_list = []
            for header in csv_data[0]:
                headers_list.append(header.strip())
            
            header_map = {}
            unique_fields = []
            for hd in rec.header_ids:
                if hd.model_field:
                    label = hd.model_field.field_description or ''
                    header_map.update({hd.model_field.name : hd.name})
                    if hd.is_unique:
                        unique_fields.append(hd.model_field.name)
                        
            if not header_map:
                raise osv.except_osv('Warning', 'No Header mapped with Model Field in Header line!')
                        
            headers_dict = {}
            for field, label in header_map.iteritems():  
                headers_dict[field] = index_get(headers_list,label)
                
            for data in csv_data[1:]:
#               Check if Uniques already exist in Data if so then if Do update is True then write Records else Skip
                # TODO add Code here to Search on Uniques
                n+= 1
                
                record_ids = self.search_record_exists(cr,uid,rec,data,headers_dict,unique_fields)
                print record_ids 
                if record_ids and not rec.do_update: 
                    
                    #TODO  need to add the Unique Record Field and Value Found to this Log
                    
                    _logger.info(_('Error Duplicate Name Found at line %s record skipped') % (n))
                    error_log += _('Error Duplicate Name Found at line %s record skipped\n') %(n)
                    
                    continue
                    
                # Create Vals Dict    
                vals ={}
                for hd in rec.header_ids:
                    model_field = hd.model_field
                    if not model_field or not headers_dict.has_key(model_field.name): continue
                    field_text = data[headers_dict[model_field.name]]
                    if model_field.ttype == 'many2one':
#                         Verts TODO: Generally many2one fields represented by "Name" Field. It can be any field from relation table. 
#                         Needs to change logic here according to appropriate fields
                        rel_id = self.pool[model_field.relation].search(cr,uid,[('name','=',field_text)])
                        if rel_id : 
                            vals.update({model_field.name : rel_id[0]})
                        else:
                            vals.update({model_field.name : False})
                            _logger.info(_('Value \'%s\' not found for the relation field \'%s\'') % (field_text, model_field.field_description))
                            error_log += _('Value \'%s\' not found for the relation field \'%s\'') % (field_text, model_field.field_description)
                    elif model_field.ttype == 'boolean':
#                         Verts: Check if the field type is boolean the eval corresponding cell string for this field
                        field_text = field_text.upper()
                        if field_text in ['TRUE','1','T']:
                            vals.update({model_field.name : True})
                        elif field_text in ['0','FALSE','F']:
                            vals.update({model_field.name : False})
                        else:
                            vals.update({model_field.name : False})
                    else:
                        vals.update({model_field.name : field_text})
                        
                try:
                    if record_ids:
                        self.pool.get(rec.model_id.model).write(cr, uid, record_ids, vals )
                        _logger.info('Update  Line Number %s  ' % n)

                    else:
                        self.pool.get(rec.model_id.model).create(cr, uid, vals, context=context)
                        _logger.info('Imported Line Number%s  ' % n)
                 
                except:
                    e = sys.exc_info()[1][1] + '\n' + traceback.format_exc()
                    _logger.info(_('Error  %s record not created for line Number %s') % (e,n,))
                    error_log += _('Error  %s at Record %s --\n') % (e,n, ) 
                  
                  
                # This is only a Test Roll Back Records exit loop and create POP UP With Info statistic about Import 
                                       
                
                if n== rec.test_sample_size  and context.get('test',False):
                    try:
                        t2 = datetime.datetime.now()
                        time_delta = (t2 - time_start)
                        time_each = time_delta / rec.test_sample_size
                        list_size = len(csv_data)
                          
                        estimate_time = (time_each * list_size)
                         
                        print "time_end,time_delta,estimate_time",t2,time_delta,estimate_time
                        msg = _('Time for %s records  is %s (hrs:min:sec) \n %s') % (list_size, estimate_time ,error_log)
                        cr.rollback()
                        vals = {'name':start,
                        'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'error_log':error_log}
                    
                        self.write(cr,uid,ids[0],vals)
                        return self.show_warning(cr, uid, msg , context = context)
                    except:
                        e = sys.exc_info()[1][1]
                        _logger.error(_('Error %s' % (e,)))
                        vals = {'error_log': e}
                        self.write(cr,uid,ids[0],vals)
                        return False

                    
	        vals = {'start_time':start,
                'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'error_log':error_log}
        if context.get('test',False):
            cr.rollback()
        self.write(cr,uid,ids[0],vals)
        result = {} 
        result['value'] = vals   
        return result
    
    def show_message(self, cr, uid, ids, context=None):
        
        return self.show_warning(cr,uid, "this is test")
        
    def show_warning(self,cr,uid,msg="None",context=None):
        
        warn_obj = self.pool.get( 'warning.warning')
        return warn_obj.info(cr, uid, title='Import Information',message = msg)
    
    def onchange_model(self, cr, uid, ids, model_id=False,  context=None):
        if not ids:
            return {}
        if model_id:
            header_ids_vals = []
            header_ids = self.pool('import.data.header').search(cr,uid,[('import_data_id','=',ids[0])])
            for rec in self.pool('import.data.header').browse(cr,uid, header_ids, context = context):
                  
                odoo_field_id = self._match_import_header(cr, uid, model_id, rec.name, rec.field_label)
                vals = { 'model_field':odoo_field_id,
                        'model': model_id,
                        }
                header_ids_vals.append((1,rec.id, vals))
                
            return{'value':{"header_ids":header_ids_vals}}
    
        else:
            return {}
    def record_forward(self,cr,uid,ids,context=None):
        
        rec= self.browse(cr,uid,ids[0],context)
        rec.record_num += 1
        self.onchange_record_num(cr, uid, ids, rec.record_num)

        
    def record_backward(self,cr,uid,ids,context=None):
        rec= self.browse(cr,uid,ids[0],context)
        if rec.record_num >1:
            rec.record_num -= 1
            self.onchange_record_num(cr, uid, ids, rec.record_num)
            return {"value":{"record_num":rec.record_num}}
        return
                
    def onchange_record_num(self,cr,uid,ids,record_num, context=None):
        
        if context is None:
            context = {}

	if record_num < 1:
		raise	osv.except_osv('Warning', "The Record Number must be positive value")
		return {}

	
	
        for rec in self.browse(cr, uid, ids, context=context):
	        header_ids_vals = []
		if rec.src_type == 'odbc':
	                raise   osv.except_osv('Warning', "Record set Values  is not available on CSV")
        	        return {}		

		elif rec.src_type == 'csv':
			raise   osv.except_osv('Warning', "Record set Values  is not available on CSV")
	                return {}

		elif rec.src_type == 'dbf':
		           
			dbf_table = dbf.Table(rec.dbf_path)
                	if not dbf_table:
                    
                    		e = 'Error opening DBF Import  %s:'  % (rec.dbf_path, )
	                    	_logger.error(_('Error %s' % (e,)))
        	            	raise osv.except_osv('Warning', e)
                    
	        	        dbf_table.open()
        	        	dbf_table_rec = dbf_table[record_num-1]   
                
	                	header_ids_vals = []
		                header_ids = self.pool('import.data.header').search(cr,uid,[('import_data_id','=',ids[0]),('name','!=',False)])
        		        for header_rec in self.pool('import.data.header').browse(cr,uid, header_ids, context = context):
                
                		    vals = {  'field_val':dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False}
		                    header_ids_vals.append((1,header_rec.id, vals))
        	        	header_rec.write({"field_val":dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False})
        	        
                    
        	else:
            		return {}    

		header_ids_vals = []
        	header_ids = self.pool('import.data.header').search(cr,uid,[('import_data_id','=',ids[0]),('name','!=',False)])
	        for header_rec in self.pool('import.data.header').browse(cr,uid, header_ids, context = context):

            		vals = {  'field_val':dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False}
			header_ids_vals.append((1,header_rec.id, vals))
	
		header_rec.write({"field_val":dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False})

	        return{'value':{'header_ids':header_ids_vals}}

     
class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'    

    _defaults = {
                 'model_id': lambda self,cr,uid,ctx=None: (ctx and ctx.get('default_model_id',False)),  
                 }        
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
