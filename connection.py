import os, mysql.connector
from dotenv import load_dotenv
load_dotenv()

class database_connection:

    def __init__(self):
        self.create_connection()


    def create_connection(self):
        try:
            username = os.getenv("DBUSER")
            host = os.getenv('DBHOST')
            password = os.getenv('DBPASSWORD')
            database_name = os.getenv('DBNAME')

            connection = mysql.connector.connect(host=host, database=database_name, user=username, password=password, port=3306 )

            if connection.is_connected():
                self.connection = connection
                self.db_info = connection.get_server_info()
                self.cursor = connection.cursor()

        except mysql.connector.Error as e:
            raise e


    def close(self):
        self.connection.close()
        self.cursor.close()

    
    def select(self, table, *args, **kwargs):
        columns = kwargs.get('columns', None)
        conditions = kwargs.get('conditions', None)
        if table is None:
            return
        else:
            try:
                if conditions is None and columns is None:
                    self.cursor.execute('select * from {}'.format(table))
                elif conditions is None:
                    if len(kwargs) == 1:
                        self.cursor.execute('select {} from {}'.format(columns, table))
                    else:
                        self.cursor.execute('select {} from {}'.format(', '.join(columns), table))
                elif columns is None:
                    self.cursor.execute('select * from {} where {}'.format(table, ', '.join(conditions)))
                else:
                    self.cursor.execute('select {} from {} where {}'.format(', '.join(columns), table, ', '.join(conditions)))
                return self.cursor.fetchall()
            except mysql.connector.Error as e:
                if e.errno == 2055:
                    self.create_connection()
                    return self.select(table, args, kwargs)
                raise e


    def select_max(self, table, column):
        if table is None:
            return
        else:
            try:
                self.cursor.execute('select * from {} where views=(select MAX({}) from {})'.format(table, column, table))
                return self.cursor.fetchall()
            except mysql.connector.Error as e:
                if e.errno == 2055:
                    self.create_connection()
                    return self.select_max(table, column)
                raise e


    def insert(self, table, *args, **kwargs):
        columns = kwargs.get('columns', None)
        url, broadcaster_name, video_id, game_id, title, views, created_at = kwargs.get('values', None)
        title = title.replace("'", "")
        if table is None or columns is None:
            print('Failed to inset data')
            return
        else:
            try:
                stmt = "INSERT INTO {}({}) VALUES('{}', '{}', '{}', '{}', '{}', {}, '{}');".format(table, ', '.join(columns), url, broadcaster_name, video_id, game_id, title, views, created_at)
                self.cursor.execute(stmt)
                self.connection.commit()
            except mysql.connector.Error as e:
                if e.errno == 2055:
                    self.create_connection()
                    try:
                        self.cursor.execute(stmt)
                    except mysql.connector.Error as e:
                        print(e)
                else:
                    print('failed to insert {} because of {}'.format(title, e))


    def delete(self, table, condition):
        try:
            stmt = "delete from {} where {};".format(table, condition)
            self.cursor.execute(stmt)
            self.connection.commit()
        except mysql.connector.Error as e:
            if e.errno == 2055:
                self.create_connection()
                self.delete(table, condition)
            else:
                print('failed to delete {} because {}'.format(condition, e))


    def prune_db(self):
        try:
            stmt = "DELETE FROM posted WHERE created_at < UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY));"
            self.cursor.execute(stmt)
            self.connection.commit()
        except mysql.connector.Error as e:
            if e.errno == 2055:
                self.create_connection()
                self.prune_db()
            else:
                print('failed prune because {}'.format(e))
