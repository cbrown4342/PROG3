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
APP_VERSION='v1'
APP_NAME=f'CVH Patient Admin ({APP_VERSION})'

import PySimpleGUI as sg
#import PySimpleGUIWeb as sg #for web UI
import os
from config import * 
from svp_modules.db.nosql.minimongo import MiniMongo
from svp_modules.miniemr.classes.patient import Patient
from svp_modules.miniemr.classes.patient_gui import PatientGUI
from svp_modules.miniemr.classes.patient_collection import PatientCollection
from svp_modules.miniemr.classes.employee_collection import EmployeeCollection #for login
from svp_modules.miniemr.classes.drug_collection import DrugCollection
from svp_modules.miniemr.classes.drug_gui import DrugGUI
from svp_modules.miniemr.classes.drug import Drug
from svp_modules.gui.pysimpleg_custom_ui import CustomWindow
from svp_modules.gui.pysimpleg_custom_ui_login_no_crypto import login_window_popup
from svp_modules.miniemr.emr_automation import BarcodeScanner
from datetime import date

#must open connection to database before creating layouts, in order to allow populating UI widgets with data
MiniMongo.connect(dbname=DATABASE_NAME)

#initializes the collection
if MiniMongo.connected():
    empl_collection=EmployeeCollection()
    patient_collection=PatientCollection()
    drug_collection = DrugCollection()
else:
    sg.PopupError('Cannot connect to MongoDb database.\nServer not available.\nApplication will close.',title=APP_NAME,location=APP_LOCATION)    
    exit()   

tab1_layout =PatientGUI.make_layout(do_not_show=['vitals'])

tab2_layout = [     
        [sg.Text('Medications')],
        [sg.Listbox(values=[],key='DrugList', size=(45,20))],
        [sg.Text('Quantity:')],
        [sg.InputText(key='doseBox')],
        [sg.Button('Prescribe Button')]
    ]    

main_layout = [     
    [sg.Menu([['&File',['&New record...','&Logout','&Exit']],['&Help','&About']])],
    [sg.Text('Date: ' + str(date.today()), text_color='white')],
    [sg.Column(
                [
                    [sg.T("Filter:"),sg.InputText(size=(10,1),enable_events=True, key='-FILTER-')],
                    [sg.Listbox(values=[],size =(42, 17),key ='-PATIENTS-',enable_events=True)],
                    #use https://en.wikipedia.org/wiki/List_of_Unicode_characters#Unicode_symbols
                    [sg.Button('⇤'),sg.Button('←'),sg.T('0-0 of 0',size=(15,1), key='-PG-'), sg.Button('→'),sg.Button('⇥'), sg.Button('↺')]
                ]),
        sg.Column(
            [
                [sg.TabGroup(
                        [[sg.Tab('Record Edit', tab1_layout, tooltip='Edit View',key='-TAB_EDIT-'), sg.Tab('Medications', tab2_layout)]])]])
    ]
]


window = CustomWindow(APP_NAME, layout=main_layout, enable_close_attempted_event=True)

#Confirmation window to add drug to patient
def openConfirmWindw(drug, patient):
    confirm_layout = [[sg.Text('Confirmation to prescribe ' + str(drug) + ' to '+ str(patient)+'?')],
                        [sg.Submit(button_color='green'), sg.Cancel(button_color='red')]]

    windowConfirm = sg.Window("Confirmation Popup",confirm_layout, modal=True)
    event, values = windowConfirm.read()
    windowConfirm.close()
    return event

def refresh_collection_page():
  if empl_collection.logged_on_employee:#only authorised employee can see collection
    record_list,start_idx,end_idx=patient_collection.get_page(sort=[("name",1)])
    window['-PATIENTS-'].Update(values=record_list)

    #Refreshes medication list from DB
    record_list,start_idx,end_idx=drug_collection.get_page()
    window['DrugList'].Update(values=record_list)

    window['-PG-'].Update(value=f"{start_idx+1}-{end_idx+1} of {patient_collection.doc_count}")

def set_patient_focus(patient):
    #refreshes the collection and selects the patient in the listbox
    page_num,page_pos=patient_collection.get_doc_pos(patient.get('_id'),{},sort=[("name",1)])
    print(f'Updated patient is on page:{page_num}, at index:{page_pos}')
    #clear filter
    window['-FILTER-'].update(value='')
    patient_collection.reset_filter()
    patient_collection.set_page(page_num)            
    refresh_collection_page()
    #scrolling and selecting the updated patient in the listbox
    window['-PATIENTS-'].update(set_to_index=[page_pos], scroll_to_index=page_pos)   
    PatientGUI.update(window,patient)

def clear_ui():#when logging out
    window.set_title(APP_NAME)
    window['-PATIENTS-'].update(set_to_index=[-1])
    window['-PATIENTS-'].update(values=[])
    window['-FILTER-'].update(value='')
    patient_collection.reset_filter()
    window['_id'].update(value='')
    window['-PHOTO_GRAPH-'].erase()
    for f in PatientGUI.field_list:
        if f in window.AllKeysDict:
            window[f].update(value='')

def login():
    if SILENT_LOGIN_USER:
        empl_collection.logged_on_employee=empl_collection.get_employee_record_by_username(SILENT_LOGIN_USER)
    else:
        empl_collection.logged_on_employee=login_window_popup(empl_collection.get_employee_record_by_username,parent_window=window)

def logout():
    clear_ui()
    empl_collection.logged_on_employee=None
    refresh_collection_page()


while True:    
    if not empl_collection.logged_on_employee:
        login()
        if empl_collection.logged_on_employee:
            window.finalize()
            window.set_title(APP_NAME+', logged on as '+empl_collection.logged_on_employee.get('full_name'))
            #update ui after successful login
            refresh_collection_page()
        else:
            break
    else:
        event, values = window.read()      
        print('Main window event: ',event)
        if event=='Exit' or event ==sg.WIN_CLOSED:
            break      

        elif event == 'Logout' or event ==sg.WIN_X_EVENT:
            logout()
            if SILENT_LOGIN_USER:
                quit()

        elif event =='About':
            sg.PopupOK(f'{APP_AUTHOR}\n (c) 2022  \n {APP_VERSION} application prototype',title=APP_NAME,location=APP_LOCATION)

        elif event =='-FILTER-':   
            name_pattern=values['-FILTER-']                 
            patient_collection.set_filter({'name':{'$regex':f'^{name_pattern}','$options':'i'}})
            patient_collection.first_page()
            refresh_collection_page()

        elif event in ['⇤','←','→','⇥','↺']:
            if event=='⇤':
                do_update=patient_collection.first_page()
            if event=='←':
                do_update=patient_collection.prev_page()
            elif event=='→':
                do_update=patient_collection.next_page()
            elif event=='⇥':
                do_update=patient_collection.last_page()
            elif event=='↺':
                #resets the filter pattern
                window['-FILTER-'].update(value='')
                window['-FILTER-'].SetFocus()
                patient_collection.reset_filter()
                do_update=True
            if do_update:
                refresh_collection_page()
                    
        # Patient Listbox selecting patient
        elif event =='-PATIENTS-':             
            patient= values['-PATIENTS-'][0] 
            print('Selected patient: ',patient)

            patient_collection.select(patient)
            PatientGUI.update(window,patient)

        elif event =='-dob_DATETIME-PICKER-':             
            sg.popup_ok('This will be replaced by a date time picker UI element','Date time picker here!')
            
        elif event =='-RECORD-UPDATE-':     
            patient=patient_collection.get_selected()
            if patient:
                print(f"updating record of {patient}")   
                #updates both the memory and database document for selected patient
                patient.update(values)
                set_patient_focus(patient)

        elif event =='New record...':        
            new_patient=Patient.new()
            patient_collection.select(new_patient)
            PatientGUI.update(window,new_patient)  
            window['-TAB_EDIT-'].select()
            window['id'].SetFocus()
            
        elif event =='-IMG-UPLOAD-':                
            print('browsing and uploading image')
            patient=patient_collection.get_selected()
            if patient:
                sg.set_options(auto_size_buttons=True)
                filename = sg.popup_get_file('Open image file(png)', no_window=True, file_types=(("png file","*.png"),))            
                print("File selected:",filename)        
                if filename!='':
                    oid=MiniMongo.uploadGridFSFile(filename,tag="patient_photo")
                    if oid:                
                        #note the the oid is an ObjectId type
                        values['photo']=oid #adds the photo to the values
                        patient.update(values)                    
                        set_patient_focus(patient)

        elif event == '-PRINT-':                    
            patient=patient_collection.get_selected()

        #When user pressues Update
        elif event == 'Prescribe Button':
            #Make sure user has clicked on drug and patient
            if window['DrugList'].get() and window['-PATIENTS-'].get:
               
                event = openConfirmWindw(values['DrugList'][0].get("TRADENAME").strip(), values['-PATIENTS-'][0])
                if event == "Submit":
                    try:
                        values['-PATIENTS-'][0].get('orders.medications').append({'drug': values['DrugList'][0].get("TRADENAME").strip()})
                        values['-PATIENTS-'][0].get('orders.medications').append({'dose': values['doseBox']})

                        print("Prescribed drug: " + str(values['DrugList'][0].get("TRADENAME") + " " + values['doseBox']))
                        patient.update(values)
                    except:
                        pass
                    

        

MiniMongo.disconnect()
window.close()



