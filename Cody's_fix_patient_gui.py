'''
    Copyright (C) 2022 Stefan V. Pantazi (svpantazi@gmail.com)    
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see http://www.gnu.org/licenses/.
'''

import json
import PySimpleGUI as psg
from apps.config import SML_FNT
from config import *
from svp_modules.miniemr.classes.patient import Patient
import svp_modules.automation.barcode_generator as bcode
import svp_modules.automation.qrcode_generator as qrcode
import svp_modules.gui.pysimpleg_custom_ui as cg
from svp_modules.gui.browser_view import browser_view
#from datetime module import datetime class, 
 #module and class happen to have the same name, no rule against it, just reads weird
from datetime import datetime,timedelta

def parse_datetime(datetime_str):
    try:
         return datetime.strptime(datetime_str,DB_DATE_TIME_FORMAT)
    except:
        return None

def calc_age(purchase_dt):
    age_years=(datetime.today()-purchase_dt) // timedelta(days=365.2425)
    return age_years

def render_purchase_date_and_age(purchase_date_str): 
    purchase_date_value=DateTime(purchase_date_str).Value    
    if  purchase_date_value:
        age_years=calc_age(purchase_date_value)
        return  purchase_date_value.strftime('%b %d, %Y') +' ('+str(age_years)+')'
    else:
        return 'N/A'

# Fix this!!!!
class PatientGUI(Patient):
    #field list inherited from the Patient class (MiniMongoDocument)
    field_defs={
        'id':{
            'label':'id',
            'desc':'Identification',
            'type':str,
            'ui':psg.InputText},
        'name':{
            'label':'Name',
            'desc':'Patient Name',
            'type':str,
            'ui':psg.InputText},
        'dob':{
            'label':'DOB',
            'desc':'Patient DOB',
            'type':str,
            'ui':psg.InputText},
        'gender':{
            'label':'Gender',
            'desc':'Gender',
            'type':str,
            'ui':psg.InputText},
        'Drug Associated':{
            'label':'Associated',
            'desc':'Drug Associated with Patient',
            'type':str,
            'ui':psg.InputText},
        # 'TYPE':{
        #     'label':'Drug type',
        #     'desc':'Drug type',
        #     'type':str,
        #     'ui':psg.InputText},
        # 'purchase_date':{
        #     'label':'Pruchase Date',
        #     'desc':'date of batch purchase',
        #     'type':datetime,
        #     'ui':psg.InputText,
        #     'ren_func':render_purchase_date_and_age},
        # 'photo':{
        #     'label':'Photo',
        #     'desc':'photo file',
        #     'type':str,
        #     'ui':psg.Text}
        #what about nested fields?, calculated fields?
    }

    @classmethod
    def make_layout(cls,do_not_show=[]):
        layout=[]
        layout.append([psg.T('Oid',size=(12,1)),psg.InputText(key='_id',size=(30,1),disabled=True)])
        for k in cls.field_list:
            if not k in do_not_show:
                if k in cls.field_defs:
                    label=cls.field_defs[k]['label']
                    ui_class=cls.field_defs[k]['ui']
                    data_type=cls.field_defs[k]['type']
                    if data_type==datetime: #special treatment
                        layout.append([psg.T(label,size=(12,1)),
                            ui_class(key=k,size=(30,1)),
                            psg.Button('...',key=f'-{k}_DATETIME-PICKER-')])                                                        
                    elif k=='photo':
                        layout.append([psg.T(label,size=(12,1)),
                            psg.Graph(canvas_size=(PHOTO_WIDTH,PHOTO_HEIGHT), graph_bottom_left=(0,PHOTO_HEIGHT-1), graph_top_right=(PHOTO_WIDTH-1,0), background_color='white', key='-PHOTO_GRAPH-'),
                            psg.Button('...',key='-IMG-UPLOAD-'),])
                        layout.append([psg.T(size=(12,1)),psg.InputText(key=k,size=(30,1),disabled=True)])
                    else:
                        if data_type in [float,int,str]:
                            layout.append([psg.T(label,size=(12,1)),
                                ui_class(key=k,size=(30,1))])        
                        else:
                            #disable UI for complex data types; add elipsis buttons, etc. 
                            layout.append([psg.T(label,size=(12,1)),
                                ui_class(key=k,size=(30,1),disabled=True)])        
                else:
                    #for undefined fields, default UI element is an readonly input text box
                    layout.append([psg.T(k,size=(12,1)),psg.InputText(key=k,size=(30,1),disabled=True)])        

        layout.append([psg.T(size=(12,1)),psg.Button('Update',key='-RECORD-UPDATE-')])
        return layout

    @classmethod
    def update(cls,window,patient):
        '''updates the UI elements of a window from the document dictionary using the field_list for keys
        Assumes that keys listed in the between the window and dictionary with the values are matching
        if a key does not exist the values dictionary, the UI element is just cleared
        so a call with an empty dictionary actually clears the UI'''
        values = patient.doc
        window['_id'].update(value=patient.get('_id'))
        for k in cls.field_defs:
            print(f'current doc value for key {k} is:{patient.get(k)}')
            if k in patient.doc:
                if k in cls.field_defs:
                    data_type=cls.field_defs[k]['type']                
                    current_value=patient.get(k)
                    render_func=cls.field_defs[k].get('ren_func',None)
                    if render_func:
                        window[k].update(value=render_func(current_value))
                    else:
                        if k in window.AllKeysDict:
                            window[k].update(value=current_value)
                    #photo fields need special processing to make the image appear
                    if k=='photo':
                        photo_graph=window['-PHOTO_GRAPH-']
                        photo_graph.erase()                    
                        file_oid_string=patient.doc[k]
                        img_data=cls.get_binary_data_from_oid(file_oid_string)                    
                        if img_data:
                            photo_graph.DrawImage(data=img_data,location=(0,0))
            else:
                #this field is undefined or a field that uses dot notation or a hidden field
                if k in window.AllKeysDict:
                    current_value=patient.get(k)
                    window[k].update(value=current_value)
                    if k=='photo':                
                        window['-LABEL_GRAPH-'].erase()

    @classmethod
    def draw_label(cls,graph,patient):
        graph.erase()
        rectangle = graph.DrawRectangle((0,0), (500,50), fill_color='white',line_color='black',line_width = 2  )   

        img_data=patient.get_photo_image_data()
        if img_data:
            graph.DrawImage(data=img_data,location=(10,10))

        #static text, images, logos, etc
        graph.DrawText("Conestoga Virtual Hospital",(10,4),font=SML_FNT,text_location =  psg.TEXT_LOCATION_TOP_LEFT)
            
        #resize image using tkinter methods?
        # graph.DrawText(patient.last_name+', '+patient.given_names,(10,16),font=SML_FNT,text_location = psg.TEXT_LOCATION_TOP_LEFT)
        graph.DrawText(patient.get("Last Name"),(10,16),font=SML_FNT,text_location = psg.TEXT_LOCATION_TOP_LEFT)
        graph.DrawText(patient.get("First Name"),(10,16),font=SML_FNT,text_location = psg.TEXT_LOCATION_TOP_LEFT)
        # graph.DrawText(drug.get('gender'),(10,26),font=SML_FNT,text_location =  psg.TEXT_LOCATION_TOP_LEFT)
        #graph.DrawText(patient.get('purchase_date'),(10,36),font=SML_FNT,text_location =  psg.TEXT_LOCATION_TOP_LEFT)
        # graph.DrawText(drug.get('allergies'),(150,16),font=SML_FNT,text_location =  psg.TEXT_LOCATION_TOP_LEFT)
        #barcode      
        barcode_data="id"+str(patient.get('id'))
        bcodeImg=bcode.GetBarcodeImage(data=barcode_data,bctype='code128')
        graph.DrawImage(data=bcodeImg,location=(250,-50))
        graph.DrawText(barcode_data,(160,36),font=SML_FNT,text_location =  psg.TEXT_LOCATION_TOP_LEFT)
        #qrcode
        qrcodeImg=qrcode.GetQRCodeImage(data=barcode_data,size=2)
        graph.DrawImage(data=qrcodeImg,location=(420,3))
        
    @classmethod
    def print_label(cls,graph,patient):
        print(f"printing wristband of {patient}")   
        #prints graphic to a pdf; file name will start with the string DIN and will include the actual DIN value
        pdf_file=cg.graph_to_pdf(graph,f"id{patient.get('id')}")
        browser_view(pdf_file)


