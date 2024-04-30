import json
import sqlite3
from datetime import datetime
import ast

class DatabaseManager():
    
    def __init__(self, db_path, total_task_instances, total_study_conditions, desc_file, route_file, static_file, training_desc_file, training_route_file, training_static_file, quiz_file, feature_file):
        self.db_path = db_path
        self.total_task_instances = total_task_instances
        self.total_study_conditions = total_study_conditions
        self.create_db()
        self.init_task_instances(desc_file, route_file, static_file, "main")
        self.init_task_instances(training_desc_file, training_route_file, training_static_file, "training")
        self.init_quizes(quiz_file)
        self.init_feature_explantions(feature_file)
        
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def create_connection_db(self):
        connection = None
        try:
            connection = sqlite3.connect(self.db_path +'.sqlite')
        except Error as e:
            print(e)

        if connection != None:
            connection.row_factory = self.dict_factory
            

        return connection


    def create_db(self):
        connection = None

        try:
            connection = sqlite3.connect(self.db_path +'.sqlite')
        except Error as e:
            print(e)

        ### responses
        ### "status" : in_progress, completed, failed
        ### "pre_test": [{"question_id": val, "answer": val}, ... ]
        ### "post_test": "[{"question_id": val, "answer": val}
        user_response_table =  """ CREATE TABLE IF NOT EXISTS user_responses (
                                            user_id TEXT PRIMARY KEY,
                                            study_condition TEXT,
                                            pre_test TEXT, 
                                            post_test TEXT,
                                            waiting_start TEXT,
                                            waiting_end TEXT,
                                            status TEXT
                                        ); """
        
        
        
    
        ### assigned_task_instances_json = [{"task_id": val, "study_condition": val, "scenario": val, "complexity": val, "task_type":val , "best_route_id": val, "best_time":val , "best_cost: val, "ai_route_id": val, "ai_time":val , "ai: val,  "route_transfer_mapping": val, "map_url_list":val, "route_info_list":val, "pickup_point": val, "n_transfer":val, "static_info":val, "chance_list":val, ""route_start_time": val}, ... ]
        ### "user_study" : [{"task_id": val, "initial_decision_1": val, "initial_decision_2": val, "final_decision": val}, ...]
        ### "decision_times": [{"task_id": val, "start_decision": val, "end_decision": val}, ...}]
        group_response_table =  """ CREATE TABLE IF NOT EXISTS group_responses (
                                            group_id TEXT PRIMARY KEY,
                                            user_id_1 TEXT,
                                            user_id_2 TEXT,
                                            study_condition TEXT,
                                            assigned_task_instances TEXT,
                                            user_study TEXT,
                                            decision_times TEXT,
                                            score TEXT
                                        ); """
        
        ### user messages
        ### "messages": [ { "content": val, "sender_id":val, "type": val, "timestamp": val}]
        user_messages_table = """ CREATE TABLE IF NOT EXISTS user_messages (
                                            user_id TEXT PRIMARY KEY,
                                            messages TEXT
                                        ); """
        
        
        ### group messages
        ### "messages": [ { "content": val, "sender_id":val, "type": val, "timestamp": val}]
        group_messages_table = """ CREATE TABLE IF NOT EXISTS group_messages (
                                            group_id TEXT PRIMARY KEY,
                                            user_id_1 TEXT,
                                            user_id_2 TEXT,
                                            messages TEXT
                                        ); """
        
        
        ### user_behaviour
        # CLICK => control buttons for routes
        # SUBMISSION => intial decision and final decision
        # HOVER_IN and HOVER_OUT => Map, Route Info, General Info
        user_behaviour_table = """ CREATE TABLE IF NOT EXISTS user_behaviour (
                                            user_id TEXT,
                                            task_id TEXT, 
                                            event_type TEXT,
                                            timestamp TEXT, 
                                            event_value TEXT
                                        ); """
        
        
        ### group_tasks
        ### "task_instances" = [ {"task_id": val, "best_route_id": val, "best_time": val, "best_cost": val, "ai_route_id": val, "ai_time": val, "ai_cost": val} ] 
        group_tasks_table = """ CREATE TABLE IF NOT EXISTS group_tasks (
                                            group_id TEXT,
                                            user_id_1 TEXT,
                                            user_id_2 TEXT,
                                            task_id TEXT,
                                            best_route_id TEXT,
                                            best_time TEXT,
                                            best_cost TEXT,
                                            ai_route_id TEXT,
                                            ai_time TEXT,
                                            ai_cost TEXT,
                                            PRIMARY KEY(group_id, task_id)
                                        ); """
       
        
    

        ### tasks
        task_table = """ CREATE TABLE IF NOT EXISTS tasks (
                                            task_id TEXT PRIMARY KEY,
                                            study_condition TEXT, 
                                            scenario TEXT,
                                            complexity TEXT,
                                            task_type TEXT,
                                            best_route_id TEXT,
                                            best_time TEXT,
                                            best_cost TEXT,
                                            route_transfer_mapping TEXT,
                                            route_info_list TEXT,
                                            pickup_point TEXT,
                                            n_transfer TEXT,
                                            static_info TEXT,
                                            route_start_time TEXT,
                                            chance_list TEXT
                                        ); """
        
        
        ### trainings
        training_table = """ CREATE TABLE IF NOT EXISTS trainings(
                                            task_id TEXT PRIMARY KEY,
                                            study_condition TEXT, 
                                            scenario TEXT,
                                            complexity TEXT,
                                            task_type TEXT,
                                            best_route_id TEXT,
                                            best_time TEXT,
                                            best_cost TEXT,
                                            route_transfer_mapping TEXT,
                                            route_info_list TEXT,
                                            pickup_point TEXT,
                                            n_transfer TEXT,
                                            static_info TEXT,
                                            route_start_time TEXT, 
                                            chance_list TEXT
                                        ); """
        
        

        
    
        
        ### quiz_questions 
        quiz_questions_table = """ CREATE TABLE IF NOT EXISTS quiz_questions (
                                            study_condition TEXT PRIMARY KEY,
                                            complexity TEXT,
                                            task_type TEXT,
                                            features_impact_score TEXT, 
                                            features_impact TEXT
                                        ); """
        
        ### feature_explanations
        feature_explanations_table = """ CREATE TABLE IF NOT EXISTS feature_explanations (
                                            study_condition TEXT PRIMARY KEY,
                                            complexity TEXT,
                                            task_type TEXT,
                                            features TEXT
                                        ); """
        
        


        ### create tables
        if connection != None:
            connection.row_factory = self.dict_factory
            conn = connection.cursor()
            
            conn.execute(user_response_table)
            conn.execute(group_response_table)
            conn.execute(group_messages_table)
            conn.execute(user_messages_table)
            conn.execute(user_behaviour_table)
            conn.execute(group_tasks_table)
            
            conn.execute(task_table)
            conn.execute(training_table)
            conn.execute(quiz_questions_table)
            conn.execute(feature_explanations_table)
            
            connection.commit()
        
        connection.close()

        return 




    def table_is_empty(self, table_name):
        try:
            connection = self.create_connection_db()
            sql = 'SELECT count(*) From '+ table_name
            cur = connection.cursor()
            cur.execute(sql)
            result = cur.fetchall()

            cur.close()
            connection.close()
            if result[0]['count(*)'] == 0:
                return True
            else:
                return False
        except:
            print("*********************** error counting the length of table ", table_name)
        
        return -1
        
    
    def get_table_length(self, table_name):
        try:
            connection = self.create_connection_db()
            sql = 'SELECT count(*) From '+ table_name
            cur = connection.cursor()
            cur.execute(sql)
            result = cur.fetchall()

            cur.close()
            connection.close()
            table_len = result[0]['count(*)']
            return table_len
        
        except:
            print("*********************** error counting the length of table ", table_name)
        return -1

    
    def find_task(self, study_json_list, task_id):
        for task in study_json_list:
            if task["task_id"] == task_id:
                return task
        return {}
    
    
    
    
    ############################################################### user_responses table ###############################################################
    
    
    ### insert
    def insert_user_response_entry(self, user_id, study_condition):
        status = "in_progress"
        
        try:
            connection = self.create_connection_db()
            sql = ''' INSERT INTO user_responses (user_id, study_condition, waiting_start, waiting_end , status)
                      VALUES(?,?,?,?,?) '''
            cur = connection.cursor()
            value = (user_id, study_condition, '' , '', status,)
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert user entry info with user with id ", user_id, " in user_responses table")

        return
    
    
    ### update
    def update_user_response_pre_test(self, user_id, pre_test):
        try:
            connection = self.create_connection_db()
            sql = ''' UPDATE user_responses SET pre_test = ? WHERE user_id = ? '''
            cur = connection.cursor()
            value = (pre_test, user_id,)
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert pretest of the user with id ", user_id, " in user_responses table")
        
        return
    
    
    ### update
    def update_user_response_post_test(self, user_id, post_test):
        status = "completed"
        try: 
            connection = self.create_connection_db()
            sql = ''' UPDATE user_responses SET post_test = ?, status = ? WHERE user_id = ? '''
            cur = connection.cursor()
            value = (post_test, status, user_id, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error update post-test of the user with id ", user_id, " in user_responses table")
                  
        return
    
    
    ### update
    def set_user_response_failed_user(self, user_id):
        status = "failed"
        try: 
            connection = self.create_connection_db()
            sql = ''' UPDATE user_responses SET status = ? WHERE user_id = ? '''
            cur = connection.cursor()
            value = (status, user_id, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error update status of the failed user with id ", user_id, " in user_responses table")
                  
        return
        
        
    ### update
    def set_user_response_waiting_user_start(self, user_id, start_time):
        try: 
            connection = self.create_connection_db()
            sql = ''' UPDATE user_responses SET waiting_start = ? WHERE user_id = ? '''
            cur = connection.cursor()
            value = (start_time, user_id, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error update the start time of the waiting user with id ", user_id, " in user_responses table")
                  
        return
    
    
    ### update
    def set_user_response_waiting_user_end(self, user_id, end_time):
        try: 
            connection = self.create_connection_db()
            sql = ''' UPDATE user_responses SET waiting_end = ? WHERE user_id = ? '''
            cur = connection.cursor()
            value = (end_time, user_id, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error update the end time of the waiting user with id ", user_id, " in user_responses table")
                  
        return
    
    
    ### retrieve
    def extract_user_study_condition(self, user_id):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT study_condition FROM user_responses WHERE user_id = ? '''
            value = (user_id,)
            cur.execute(sql, value)
            row = cur.fetchone()
            cur.close()
            connection.close()
            return row["study_condition"]
        except:
            print(" *********************** error retrieve the study condition of the user with id ", user_id, " in user_responses table")
            
        return -1 
    
    
    ############################################################## group_responses table ###############################################################
   

    ### insert
    def insert_group_repsonse_group_entry(self, group_id, user_id_1, user_id_2, study_condition, assigned_tasks_instances):
        try:
            connection = self.create_connection_db()
            sql = ''' INSERT INTO group_responses (group_id, user_id_1, user_id_2, study_condition, assigned_task_instances)
                      VALUES(?,?,?,?,?) '''
            cur = connection.cursor()
            value = (group_id, user_id_1, user_id_2, study_condition, assigned_tasks_instances, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert group entry info with group id ", group_id, " in group_responses table")
        
        return
    
    
    ### update
    def update_group_response_user_study(self, group_id, user_study, decision_times, score):
        try:
            connection = self.create_connection_db()
            sql = ''' UPDATE group_responses SET user_study = ?, decision_times = ?, score = ? WHERE group_id = ? '''
            cur = connection.cursor()
            value = (user_study, decision_times, score, group_id, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except: 
            print(" *********************** error update user study of the group with id ", group_id, " in group_responses table")
                  
        return
    
    
    ### retrieve
    def extract_group_task_instances(self, group_id):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT assigned_task_instances FROM group_responses WHERE group_id = ? '''
            value = (group_id,)
            cur.execute(sql, value)
            row = cur.fetchone()
            cur.close()
            connection.close()
            return row["assigned_task_instances"]
        except:
            print(" *********************** error retrieve assigned_tasks_instances of the group with id ", group_id, " in group_responses table")
        
        return -1
    
    ### retrive 
    def extract_group_score(self, group_id):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT score FROM group_responses WHERE group_id = ? '''
            value = (group_id,)
            cur.execute(sql, value)
            row = cur.fetchone()
            cur.close()
            connection.close()
            return row["score"]
        except:
            print(" *********************** error retrieve the score of the group with id ", group_id, " in group_responses table")
        
        return -1
        
    
    ### retrieve
    def extract_group_study_condition(self, group_id):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT study_condition FROM group_responses WHERE group_id = ? '''
            value = (group_id,)
            cur.execute(sql, value)
            row = cur.fetchone()
            cur.close()
            connection.close()
            return row["study_condition"]
        except:
            print(" *********************** error retrieve the study condition of the group with id ", group_id, " in group_responses table")
        
        return -1
    
    ############################################################### user_messages table ###############################################################
    
    
    ### insert
    def insert_user_messages_entry(self, user_id):
        messages = '[]'
        try:
            connection = self.create_connection_db()
            sql = ''' INSERT INTO user_messages (user_id, messages)
                      VALUES(?,?) '''
            cur = connection.cursor()
            value = (user_id, messages, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert user messages with user id ", user_id, " in user_messages table")
        
        return
    
    
    ### update
    def update_user_messages_one_message(self, user_id, message):
        try:
            # retrieve all messages and append new message to it's list
            all_messages = ast.literal_eval(self.extract_user_messages_all_messages(user_id))
            if all_messages == -1:
                return
                
            all_messages.append(message)
            all_messages = json.dumps(all_messages, sort_keys=False)
            
            connection = self.create_connection_db()
            sql = ''' UPDATE user_messages SET messages = ? WHERE user_id = ? '''
            cur = connection.cursor()
            value = (all_messages, user_id, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except: 
            print(" *********************** error update a new message of the user with id ", user_id, " in user_messages table")

        return
    
    
    ### retrieve
    def extract_user_messages_all_messages(self, user_id):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT messages FROM user_messages WHERE user_id = ? '''
            value = (user_id,)
            cur.execute(sql, value)
            row = cur.fetchone()
            cur.close()
            connection.close()
            return row["messages"]
        except:
            print(" *********************** error retrieve all messages of the user with id ", user_id, " in user_messages table")
        return -1
    
    ############################################################### group_messages table ###############################################################
    
    
    ### insert
    def insert_group_messages_entry(self, group_id, user_id_1, user_id_2):
        messages = '[]'
        try:
            connection = self.create_connection_db()
            sql = ''' INSERT INTO group_messages (group_id, user_id_1, user_id_2, messages)
                      VALUES(?,?,?,?) '''
            cur = connection.cursor()
            value = (group_id, user_id_1, user_id_2, messages, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert group messages with group id ", group_id, " in group_messages table")
        
        return
    
    
    ### update
    def update_group_messages_one_message(self, group_id, message):
        try:
            # retrieve all messages and append new message to it's list
            all_messages = ast.literal_eval(self.extract_group_messages_all_messages(group_id))
            if all_messages == -1:
                return
                
            all_messages.append(message)
            all_messages = json.dumps(all_messages, sort_keys=False)
            
            connection = self.create_connection_db()
            sql = ''' UPDATE group_messages SET messages = ? WHERE group_id = ? '''
            cur = connection.cursor()
            value = (all_messages, group_id, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except: 
            print(" *********************** error update a new message of the group with id ", group_id, " in group_messages table")

        return
    
    
    ### retrieve
    def extract_group_messages_all_messages(self, group_id):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT messages FROM group_messages WHERE group_id = ? '''
            value = (group_id,)
            cur.execute(sql, value)
            row = cur.fetchone()
            cur.close()
            connection.close()
            return row["messages"]
        except:
            print(" *********************** error retrieve all messages of the group with id ", group_id, " in group_messages table")
        return -1
    
    ############################################################### user_behaviuor table ###############################################################
    
    
    ### insert
    def insert_user_ui_interaction(self, user_id, task_id, event_type, timestamp, event_value):
        try:
            connection = self.create_connection_db()
            sql = ''' INSERT INTO user_behaviour (user_id, task_id, event_type, timestamp, event_value )
                      VALUES(?,?,?,?,?) '''
            cur = connection.cursor()
            value = (user_id, task_id, event_type, timestamp, event_value, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert event ", event_type, " with value of ", event_value, " for user with id ", user_id, " in user_behaviour table")
        
        return
    
    
    ################################################################## group_tasks table ###############################################################
    
    
    ### insert
    def insert_group_assigned_tasks(self, group_id, user_id_1, user_id_2 ,task_instances):
        
        try:
            connection = self.create_connection_db()
            # sql = ''' INSERT INTO group_tasks (group_id, user_id_1, user_id_2, task_id, best_route_id, best_time, best_cost, ai_route_id, ai_time, ai_cost)
            #           VALUES(?,?,?,?,?,?,?,?,?,?) '''
            sql = ''' INSERT INTO group_tasks (group_id, user_id_1, user_id_2, task_id, best_route_id, best_time, best_cost, ai_route_id, ai_time, ai_cost)
                      VALUES(?,?,?,?,?,?,?,?,?,?) '''
            cur = connection.cursor()
            
            for task_instance in task_instances:
                value = (group_id, user_id_1, user_id_2, task_instance["task_id"], task_instance["best_route_id"], task_instance["best_time"], task_instance["best_cost"], task_instance["ai_route_id"], task_instance["ai_time"], task_instance["ai_cost"], )
                cur.execute(sql, value)
                
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert group task instances for group with id ", group_id, " in group_tasks table")
        
        return
   

    ### retrive
    def extract_ai_suggestion_for_group_task(self, group_id, task_id):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT ai_route_id FROM group_tasks WHERE group_id = ? AND task_id = ? '''
            value = (group_id, task_id, )
            cur.execute(sql, value)
            row = cur.fetchone()
            cur.close()
            connection.close()
            return row["ai_route_id"]
        except:
            print(" *********************** error retrieve ai suggestion for group with id ", group_id, " and task with id ", task_id , " in group_tasks table")
        return -1
    
    
    ### retrieve
    def extract_group_assigned_tasks(self, group_id):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT * FROM group_tasks WHERE group_id = ? '''
            value = (group_id,)
            cur.execute(sql, value)
            rows = cur.fetchall()
            cur.close()
            connection.close()
            return rows
        except:
            print(" *********************** error retrieve group task instances for group with id ", group_id, " in group_tasks table")
        return -1
    
    ######################################################################## tasks table ###############################################################
    
    
    ### insert
    def insert_task_instance(self, task_id, study_condition, scenario, complexity, task_type, best_route_id, best_time, best_cost, route_transfer_mapping, route_info_list, pickup_point, n_transfer, static_info, route_start_time, chance_list):
        try: 
            tasks_len = self.get_table_length('tasks')
            if tasks_len >= self.total_task_instances:
                return

            connection = self.create_connection_db()
            sql = ''' INSERT INTO tasks (task_id, study_condition, scenario, complexity, task_type, best_route_id, best_time, best_cost, route_transfer_mapping, route_info_list, pickup_point, n_transfer, static_info, route_start_time, chance_list)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
            cur = connection.cursor()
            value = (task_id, study_condition, scenario, complexity, task_type, best_route_id, best_time, best_cost, route_transfer_mapping, route_info_list, pickup_point, n_transfer, static_info, route_start_time, chance_list, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert task with id ", task_id, " in tasks table")
            
        return

    
    ### retrieve
    def extract_task_instances(self, study_condition):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT * FROM tasks WHERE study_condition = ? '''
            value = (study_condition,)
            cur.execute(sql, value)
            rows = cur.fetchall()
            cur.close()
            connection.close()
            return rows
        except:
            print(" *********************** error retrieve tasks for study condition ", study_condition, " in tasks table")
        
        return -1
    
    
    #################################################################### trainings table ###############################################################
    
    ### insert
    def insert_training_task(self, task_id, study_condition, scenario, complexity, task_type, best_route_id, best_time, best_cost, route_transfer_mapping, route_info_list, pickup_point, n_transfer, static_info, route_start_time, chance_list):
        try: 
            tasks_len = self.get_table_length('trainings')
            if tasks_len >= (self.total_study_conditions):
                return

            connection = self.create_connection_db()
            sql = ''' INSERT INTO trainings (task_id, study_condition, scenario, complexity, task_type, best_route_id, best_time, best_cost, route_transfer_mapping, route_info_list, pickup_point, n_transfer, static_info, route_start_time, chance_list)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
            cur = connection.cursor()
            value = (task_id, study_condition, scenario, complexity, task_type, best_route_id, best_time,  best_cost, route_transfer_mapping, route_info_list, pickup_point, n_transfer, static_info, route_start_time, chance_list, )
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert training task with id ", task_id, " in trainings table")
            
        return

    ### retrieve
    def extract_training_task(self, study_condition):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT * FROM trainings WHERE study_condition = ? '''
            value = (study_condition,)
            cur.execute(sql, value)
            rows = cur.fetchall()
            cur.close()
            connection.close()
            return rows
        except:
            print(" *********************** error retrieve training task for study condition ", study_condition, " in trainings table")
        
        return -1
    
    ############################################################### quiz_questions table ###############################################################
    
    
    ### insert
    def insert_quiz_questions(self, study_condition, complexity, task_type, features_impact_score, features_impact):
        try:
            connection = self.create_connection_db()
            sql = ''' INSERT INTO quiz_questions (study_condition, complexity, task_type, features_impact_score, features_impact)
                      VALUES(?,?,?,?,?) '''
            cur = connection.cursor()
            value = (study_condition, complexity, task_type, features_impact_score, features_impact,)
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert questions into the quiz questions table ")
        
        return
    
    
    ### retrieve
    def extract_quiz_study_condition(self, study_condition):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT features_impact_score, features_impact FROM quiz_questions WHERE study_condition = ? '''
            value = (study_condition,)
            cur.execute(sql, value)
            row = cur.fetchone()
            cur.close()
            connection.close()
            return row
        except:
            print(" *********************** error retrieve quiz informatin for study condition ", study_condition, " in quiz_questions table")
        
        return -1
    
    
    ######################################################### feature_explanations table ###############################################################
    
    
    ### insert
    def insert_feature_explanations(self, study_condition, complexity, task_type, features):
        try:
            connection = self.create_connection_db()
            sql = ''' INSERT INTO feature_explanations (study_condition, complexity, task_type, features)
                      VALUES(?,?,?,?) '''
            cur = connection.cursor()
            value = (study_condition, complexity, task_type, features,)
            cur.execute(sql, value)
            connection.commit()
            cur.close()
            connection.close()
        except:
            print(" *********************** error insert into feature explantions table")
        
        return
    
    
    ### retrieve
    def extract_feature_explanations_study_condition(self, study_condition):
        try:
            connection = self.create_connection_db()
            cur = connection.cursor()
            sql = ''' SELECT * FROM feature_explanations WHERE study_condition = ? '''
            value = (study_condition,)
            cur.execute(sql, value)
            row = cur.fetchone()
            cur.close()
            connection.close()
            return row
        except:
            print(" *********************** error retrieve feature explanations for study condition ", study_condition, " in feature_explanations table")
        
        return -1
    
    
    ######################################################################## init tables ###############################################################
    
    ### quiz_questions table
    def init_quizes(self, quiz_file):
        f_quiz = open(quiz_file)
        quiz_data = json.load(f_quiz)
        
        for instance in quiz_data:
            self.insert_quiz_questions(instance["study_condition"], instance["complexity"], instance["task_type"], instance["features_impact_score"], str(instance["features_impact"]))
        
        return
    
    
    ### feature_explanations table
    def init_feature_explantions(self, feature_file):
        f_features = open(feature_file)
        exp_data = json.load(f_features)
        
        for instance in exp_data:
            self.insert_feature_explanations(instance["study_condition"], instance["complexity"], instance["task_type"], str(instance["features"]))
              
        return
    
    
    #### tasks/trainings table from file
    def init_task_instances(self, desc_file, route_file, static_file, training_or_main):
        
        study_condition_list = []
        
        ### desc_data is like [ {"task_id": taskid, "study_condition": sc_value, "scenario":s_vale, "complexity": low/medium/high, "task_type": diagnostic/prognostic}]
        f_desc = open(desc_file)
        desc_data = json.load(f_desc)
        
        ### route_data is like [{"task_id": taskid, "study_condition": sc_value, "best_index": best_route_id, "best_time": time, "best_cost": cost, "route_transfer_mapping": rt_value, "route_info_list": route_value,"pickup_point": [,], "n_transfer": n, "chance_list": c_value ]
        f_route = open(route_file)
        route_data = json.load(f_route)
        
        ### static file is like [ {"task_id": taskid, "study_condition": sc_value, "general_features": [{"train": n1, "taxi": n2, "bus": n3, "study_feature": sf_value, "attr": speed_kph/cost}] }
        f_static = open(static_file)
        static_data = json.load(f_static)
        
        
        ### init tasks/trainings table
        for instance in desc_data:
            route_dict = self.find_task(route_data, instance["task_id"])
            static_dict = self.find_task(static_data, instance["task_id"])
            
            ### insert task instance to tasks db or trainings db according to the file it reads from (identified with parameter training or main)
            if training_or_main == "main":
                self.insert_task_instance(instance["task_id"], instance["study_condition"], instance["scenario"], instance["complexity"], instance["task_type"], route_dict["best_index"], route_dict["best_time"], route_dict["best_cost"], route_dict["route_transfer_mapping"], route_dict["route_info_list"], route_dict["pickup_point"], route_dict["n_transfer"], static_dict["general_features"], route_dict["route_start_time"] , route_dict["chance_list"])
            elif training_or_main == "training":
                self.insert_training_task(instance["task_id"], instance["study_condition"], instance["scenario"], instance["complexity"], instance["task_type"], route_dict["best_index"], route_dict["best_time"], route_dict["best_cost"], route_dict["route_transfer_mapping"], route_dict["route_info_list"], route_dict["pickup_point"], route_dict["n_transfer"], static_dict["general_features"], route_dict["route_start_time"], route_dict["chance_list"])
        
            if instance["study_condition"] not in study_condition_list:
                study_condition_list.append(instance["study_condition"])
        
        
        return
    
    
    
    
################################################################################ start ###############################################################

    
    
total_task_instances = 18
total_study_conditions = 6

db_path = "/root/trip_planner/group/writing"
# db_path = "/root/trip_planner/group/medium-complexity"
# db_path = "/root/trip_planner/group/low-complexity"

description_path = '/root/trip_planner/config_files/description.json'
route_path = '/root/trip_planner/config_files/route.json'
static_path = '/root/trip_planner/config_files/static.json'

training_description_path = '/root/trip_planner/config_files/training_description.json'
training_route_path = '/root/trip_planner/config_files/training_route.json'
training_static_path = '/root/trip_planner/config_files/training_static.json'

quiz_path = '/root/trip_planner/config_files/quiz.json'
features_path = '/root/trip_planner/config_files/feature_explanations.json'


db = DatabaseManager(db_path, total_task_instances, total_study_conditions, description_path, route_path, static_path , training_description_path, training_route_path, training_static_path, quiz_path, features_path)



def get_instance():
    global db
    if db != None:
        return db
    
    db = DatabaseManager(db_path, total_task_instances, total_study_conditions, description_path, route_path, static_path, training_description_path, training_route_path, training_static_path,quiz_path, features_path)
