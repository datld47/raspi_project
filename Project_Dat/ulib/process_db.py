from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

def copy_attributes(source_obj, target_obj):   
    for (key, value) in source_obj.__dict__.items():
        if key.startswith('_'):
            continue
        target_obj.__setattr__(key, value)

class ProcessDB:
    def __init__(self,session_maker:sessionmaker) -> None:
        self.session=session_maker()
                 
    def _insert(self,obj):
        try:
            self.session.add(obj)
            self.session.commit()
        except Exception as error:
            print(error)
            self.session.rollback()
            return False
        else:
            print('successful')
            return True
     
    def insert(self,obj,model_class_pk=None,condition=None, model_class_2_pk=None,condition_2=None):
        
        if model_class_pk is not None and condition is not None:
            id=self.get_id(model_class_pk,condition)
            if id>0:
                if model_class_2_pk is not None and condition_2 is not None:
                    id=self.get_id(model_class_2_pk,condition_2)
                    if id>0:
                        return self._insert(obj)
                    else:
                        print('error key')
                        return False
                else:
                    return self._insert(obj)
            else:
                print('error key')
                return False
        else:
                return self._insert(obj)
   
    def insert_all(self,objs):
        try:
            self.session.add_all(objs)
            self.session.commit()
        except Exception as error:
            print(error)
            self.session.rollback()
            return False
        else:
            print('successful')
            return True
            
    def querry_all(self,model_class,condition=None):  
        try:
            if condition is None:
                obj=self.session.query(model_class).all()
            else:
                obj=self.session.query(model_class).filter(condition).all()
            self.session.commit()
        except:
            print('not successful')
            self.session.rollback()
            return None
        else:
            print('successful')
            return obj
     
    def querry_all_with_columns(self,model_class_columns,condition=None):
        try:
            if condition is None:
                obj=self.session.query(*model_class_columns).all()
            else:
                obj=self.session.query(*model_class_columns).filter(condition).all()
            self.session.commit()
        except:
            print('not successful')
            self.session.rollback()
            return None
        else:
            print('successful')
            return obj
    
    def querry_all_with_orderby(self,model_class_columns,orderby_clause):
        try:
            obj=self.session.query(*model_class_columns).order_by(orderby_clause).all()
            self.session.commit()
        except:
            print('not successful')
            self.session.rollback()
            return None
        else:
            print('successful')
            return obj
    
    def querry_distinct(self,model_class_column):
        try:
            obj=self.session.query(model_class_column).distinct().all()
            self.session.commit()
        except:
            print('not successful')
            self.session.rollback()
            return None
        else:
            print('successful')
            return obj
            
    def querry_lastest_with_timestamp(self,model_class,timestamp_desc_clause):
        try:
            obj=self.session.query(model_class).order_by(timestamp_desc_clause).first()
            self.session.commit()
        except:
            print('not successful')
            self.session.rollback()
            return None
        else:
            print('successful')
            return obj
      
    def querry_by_id(self,model_class,id):
        try:
            obj=self.session.query(model_class).filter(model_class.id==id).first()
            self.session.commit()
        except:
            print('not successful')
            self.session.rollback()
            return None
        else:
            print('successful')
            return obj
            
    def querry_by_condition(self,model_class,condition):
        try:
            obj=self.session.query(model_class).filter(condition).first()
            self.session.commit()
        except:
            print('not successful')
            self.session.rollback()
            return None
        else:
            print('successful')
            return obj

    def update_by_id(self,model_class,id,new_obj):
        try:
            obj=self.session.query(model_class).filter(model_class.id==id).first()
            copy_attributes(new_obj,obj)
            self.session.commit()
        except Exception as err:
            print(err)
            self.session.rollback()
            return False
        else:
            print('successful')
            return True
    
    def update(self,old_obj,new_obj):
        try:
            copy_attributes(new_obj,old_obj)
            self.session.commit()
        except Exception as err:
            print(err)
            self.session.rollback()
            return False
        else:
            print('successful')
            return True

    def delete_by_id(self,model_class,id):
        try:
            obj=self.session.query(model_class).filter(model_class.id==id).first()
            self.session.delete(obj)
            self.session.commit()
        except:
            print('not successful')
            self.session.rollback()
            return False
        else:
            print('successful')
            return True
    
    def delete(self,obj):
        try:
            self.session.delete(obj)
            self.session.commit()
        except:
            print('not successful')
            self.session.rollback()
            return False
        else:
            print('successful')
            return True
   
    def get_id(self,model_class,condition):      
        try:
            id=self.session.query(model_class.id).filter(condition).first()[0]
        except Exception as err:
            print(err)
            self.session.rollback()
            return 0
        else:
            print('successful')
            return id
      
    def save(self):
        try:
            self.session.commit()
        except Exception as err:
            print(err)
            self.session.rollback()
            return False
        else:
            print('successful')
            return True
    
    def new_session(self,session_maker:sessionmaker):
        self.close_session()
        self.session=session_maker()
         
    def close_session(self):
        self.session.close()
        
    def check_session(self):
        if not self.session.is_active:
            return 0
        else:
            return 1
        