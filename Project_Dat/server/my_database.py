from my_model import Base
from sqlalchemy import create_engine,text,event,DDL
from sqlalchemy.orm import sessionmaker

class my_database:
    def __init__(self,path_db):
        self.base=Base
        self.engine=create_engine(path_db)
        
    def cretate_database(self):
        self.base.metadata.create_all(self.engine)

    def create_trigger_auto_remove_data(self,model_class, ttl_seconds=604800):
        table = model_class.__table__
        trigger_name = f"delete_old_rows_{table.name}"
        ddl = f"""
        CREATE TRIGGER IF NOT EXISTS {trigger_name}
        AFTER INSERT ON {table.name}
        BEGIN
            DELETE FROM {table.name}
            WHERE strftime('%s', 'now') - strftime('%s', timestamp) > {ttl_seconds};
        END;
        """
        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            
    def create_session(self):
        return sessionmaker(bind=self.engine)  
