
from svp_modules.db.nosql.minimongo import MiniMongo, MiniMongoCollection
from svp_modules.miniemr.classes.patient import Patient


class PatientCollection(MiniMongoCollection):
  
  def __init__(self):
    super().__init__(MiniMongo.db.patients, Patient)
    self.logged_on_patient = None

  #moved from main app
  def get_patient_info(self,id):
      patient = self.find_one({'id':int(id)})          
      return patient