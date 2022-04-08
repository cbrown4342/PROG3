
from svp_modules.db.nosql.minimongo import MiniMongo, MiniMongoCollection
from svp_modules.miniemr.classes.drug import Drug


class DrugCollection(MiniMongoCollection):
  
  def __init__(self):
    super().__init__(MiniMongo.db[Drug.collection], Drug)
    self.selected_drug=None

  #moved from main app
  def get_drug_info(self,DIN):
      drug=self.find_one({'DIN':int(DIN)})          
      return drug
      