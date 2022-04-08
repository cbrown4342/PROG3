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
APP_NAME=f'CVH Patient Formulary Admin ({APP_VERSION})'

import PySimpleGUI as sg
#import PySimpleGUIWeb as sg #for web UI
import os
from config import * 
from svp_modules.db.nosql.minimongo import MiniMongo
from svp_modules.miniemr.classes.patient import Patient
from svp_modules.miniemr.classes.patient_gui import PatientGUI
from svp_modules.miniemr.classes.patient_collection import PatientCollection
#from svp_modules.miniemr.classes.drug_collection import DrugCollection 
from svp_modules.miniemr.classes.employee_collection import EmployeeCollection #for login
from svp_modules.gui.pysimpleg_custom_ui import CustomWindow
from svp_modules.gui.pysimpleg_custom_ui_login import login_window_popup

#must open connection to database before creating layouts, in order to allow populating UI widgets with data
MiniMongo.connect(dbname=DATABASE_NAME)

#initializes the collection
if MiniMongo.connected():
    empl_collection=EmployeeCollection()
    #drug_collection=DrugCollection()    
    patient_collection = PatientCollection()
else:
    sg.PopupError('Cannot connect to MongoDb database.\nServer not available.\nApplication will close.',title=APP_NAME,location=APP_LOCATION)    
    exit()   

tab1_layout =PatientGUI.make_layout(do_not_show=[])

# tab2_layout = [     
#         [sg.Graph(canvas_size=(500, 50), graph_bottom_left=(0,50), graph_top_right=(500, 0), background_color='white', key='-LABEL_GRAPH-')],
#         [sg.Button('Print',key='-PRINT-')],
#     ]    

main_layout = [     
    [sg.Menu([['&File',['&New record...','&Logout','&Exit']],['&Help','&About']])],
    [
        sg.Column(
                [
                    [sg.T("Filter:"),sg.InputText(size=(37,1),enable_events=True, key='-FILTER-')],
                    [sg.Listbox(values=[],size =(42, 17),key ='-PATIENTS-',enable_events=True)],
                    #use https://en.wikipedia.org/wiki/List_of_Unicode_characters#Unicode_symbols
                    [sg.Button('⇤'),sg.Button('←'),sg.T('0-0 of 0',size=(15,1), key='-PG-'), sg.Button('→'),sg.Button('⇥'), sg.Button('↺')]
                ]),
        sg.Column(
                [[sg.TabGroup(
                    [[sg.Tab('Patient Info.', tab1_layout, tooltip='Edit View',key='-TAB_EDIT-')]])]])
    ]
]
# , sg.Tab('Label View', tab2_layout
window = CustomWindow(APP_NAME, layout=main_layout, enable_close_attempted_event=True)

def refresh_collection_page():
  if empl_collection.logged_on_employee:#only authorised employee can see collection
    record_list,start_idx,end_idx=patient_collection.get_page(sort=[("MRN",1)])
    window['-PATIENTS-'].Update(values=record_list)
    window['-PG-'].Update(value=f"{start_idx+1}-{end_idx+1} of {patient_collection.doc_count}")

def set_patient_focus(patient):
    #refreshes the collection and selects the drug in the listbox
    page_num,page_pos=patient_collection.get_doc_pos(patient.get('_id'),{},sort=[("MRN",1)])
    print(f'Updated Patient is on page:{page_num}, at index:{page_pos}')
    #clear filter
    window['-FILTER-'].update(value='')
    patient_collection.reset_filter()
    patient_collection.set_page(page_num)            
    refresh_collection_page()
    #scrolling and selecting the updated drug in the listbox
    window['-PATIENTS-'].update(set_to_index=[page_pos], scroll_to_index=page_pos)   
    PatientGUI.update(window,patient)
    PatientGUI.draw_labels(window['-LABEL_GRAPH-'],patient)

def clear_ui():#when logging out
    window.set_title(APP_NAME)
    window['-PATIENTS-'].update(set_to_index=[-1])
    window['-PATIENTS-'].update(values=[])
    window['-FILTER-'].update(value='')
    patient_collection.reset_filter()
    window['-PHOTO_GRAPH-'].erase()
    window['MRN'].update(value='')
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
            window.set_title(APP_NAME+', logged on as '+ empl_collection.logged_on_employee.get('full_name'))
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
            patient_collection.set_filter({'MRN':{'$regex':f'^{name_pattern}','$options':'i'}})
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
                    
        elif event =='-PATIENTS-':             
            patient = values['-PATIENTS-'][0]        
            print('Selected patient: ',patient)
            patient_collection.select(patient)
            PatientGUI.update(window,patient)
            PatientGUI.draw_label(window['-PHOTO_GRAPH-'],patient)

        elif event =='-dob_DATETIME-PICKER-':             
            sg.popup_ok('This will be replaced by a date time picker UI element','Date time picker here!')
            
        elif event =='-RECORD-UPDATE-':     
            patient = patient_collection.get_selected()
            if patient:
                print(f"updating record of {patient}")   
                #updates both the memory and database document for selected drug
                patient.update(values)
                set_patient_focus(patient)

        elif event =='New record...':        
            new_patient = Patient.new()
            patient_collection.select(new_patient)
            PatientGUI.update(window,new_patient)
            PatientGUI.draw_label(window['-LABEL_GRAPH-'],new_patient)        
            window['-TAB_EDIT-'].select()
            window['MRN'].SetFocus()
            
        elif event =='-IMG-UPLOAD-':                
            print('browsing and uploading image')
            patient = patient_collection.get_selected()
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
            patient = patient_collection.get_selected()
            if patient:            
                PatientGUI.print_label(window['-LABEL_GRAPH-'],patient)            
        

MiniMongo.disconnect()
window.close()

