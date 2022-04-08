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
from svp_modules.db.nosql.minimongo import MiniMongoDocument,Oid

class Patient(MiniMongoDocument):
    collection='Patient_formulary'
    #use dot dict like here? https://stackoverflow.com/questions/2352181/how-to-use-a-dot-to-access-members-of-dictionary
    
    field_list=['id','Name','DOB','Gender', 'Drug Associated']
    field_definitions={
        'id':{},
        'Name':{},
        'DOB':{},
        'Gender':{},
        'Drug Associated':{}
        }
        
    def __init__(self,doc):
        super().__init__(doc)
        #print('drug info:',self.doc)        
        #initializes names
        # self.last_name=''
        # self.given_names=''
        # self.split_full_name()        

    @classmethod
    def new(cls):
        new_doc=super().new()
        print('New patient doc:',str(new_doc))
        new_patient=Patient(new_doc)
        return new_patient

    # def split_full_name(self):
    #     #split full name       
    #     if 'name' in self.doc:
    #         names=self.doc['name'].split(',')
    #         self.last_name=names[0]
    #         if len(names)>1:
    #             self.given_names=names[1]
    #         else:
    #             self.given_names=''

    def update(self,values):
        super().update(values)
        self.split_full_name()

    def get_photo_image_data(self):
        return self.get_binary_data_from_field('photo')

    def __str__(self):
        return f"{self.get('id')} ({self.get('Name')}) ({self.get('DOB')}) ({self.get('Gender')})" 

