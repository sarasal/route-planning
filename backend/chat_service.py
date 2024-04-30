import json
import uuid
import time
from threading import Lock, Timer
import db_utils
import ast
import copy


class ChatService():
    # time to join the group after GROUP_CREATED message is sent is 10000 milisec, set in the client waiting room
    # def __init__(self, ice_breaking_show_sec = 10, discussion_limit_milisec = 120000, disconnect_limit_sec = 180, num_routes = 10):
    def __init__(self, ice_breaking_show_sec = 1, discussion_limit_milisec = 5000, disconnect_limit_sec = 5, num_routes = 10):
        self.user_socket_list = {}
        self.user_status_list = {}
        self.user_unsent_list = {}
        self.groups = {}
        self.waiting_user = ''
        self.lock = Lock()
        self.db = db_utils.get_instance()
        self.ice_breaking_show_sec = ice_breaking_show_sec
        self.discussion_limit_milisec = discussion_limit_milisec
        self.disconnect_limit_sec = disconnect_limit_sec
        self.num_routes = num_routes
    
    ################################################################# db access  ###############################################################
    
    def save_message_db(self, group_id, m_type, m_content, m_sender_id, m_sender_time):
        current_time_millis = int(round(time.time() * 1000))
        if m_sender_time == '':
            m_sender_time = current_time_millis

        new_message = {
                    'type': m_type,
                    'content': m_content,
                    'sender_id': m_sender_id,
                    'sender_time': m_sender_time,
                    'server_time': current_time_millis
                }
        
        self.db.update_group_messages_one_message(group_id, new_message)
        return
    
    
    def save_message_user_db(self, user_id, one_message):
        
        sender_time_millis = 0
        m_sender_id = '1'
        
        one_message_json = json.loads(one_message)
        if 'senderId' in one_message_json:
            m_sender_id = one_message_json['senderId']
            sender_time_millis = one_message_json['senderTime']
            
            
        new_message = {
                    'type': one_message_json['type'],
                    'content': one_message_json['content'],
                    'senderId': m_sender_id,
                    'senderTime': sender_time_millis
                }
        
        self.db.update_user_messages_one_message(user_id, new_message)
        return
    
    
    def retrieve_ai_suggestion(self, group_id, task_id):
        
        ai_suggestion = self.db.extract_ai_suggestion_for_group_task(group_id, task_id)
        
        ### add +1 since routes are started from 0-9
        ai_suggestion = str(int(ai_suggestion) + 1)
        
        return ai_suggestion
      
    ############################################################### create_message  ##########################################################
    
    def create_group_join_message(self, new_group_id, new_group):
        new_message = {
                        'type':'GROUP_CREATED',
                        'roomId': new_group_id,
                        'member1': new_group['member1'],
                        'member2': new_group['member2'],
                        'content': ''
                    }
        # m_content = new_message['content']
        new_message = json.dumps(new_message, sort_keys=False)
        return new_message
    
    
    def recreate_group_join_message(self, group_id, member1, member2):
        new_message = {
                        'type':'GROUP_CREATED',
                        'roomId': group_id,
                        'member1': member1,
                        'member2': member2,
                        'content': ''
                    }
        
        new_message = json.dumps(new_message, sort_keys=False)
        return new_message
        


    def create_chat_join_message(self, m_content, group_id):
        new_message = {
                        'type': 'CHAT_JOINED',
                        'content': m_content,
                        'roomId': group_id,
                        'member1': self.groups[group_id]['member1'],
                        'member2': self.groups[group_id]['member2']
                    }
        new_message = json.dumps(new_message, sort_keys=False)
        return new_message
    
    
    def create_server_message(self, m_type, m_content):
        new_message = {
                        'type': m_type,
                        'content': m_content
                    }
        new_message = json.dumps(new_message, sort_keys=False)
        return new_message



    def create_group_message(self, m_content, user_id, sender_time):
        new_message = {
                    'type': 'GROUP_MESSAGE',
                    'content': m_content,
                    'senderId': user_id,
                    'senderTime': sender_time
                }
        new_message = json.dumps(new_message, sort_keys=False)
        return new_message
    
    
    def create_reconnect_messages(self, group_id, user_id, member1, member2, m_content, sent_messages, unsent_messages):
        last_status = self.user_status_list[user_id]
        if len(self.user_unsent_list[user_id]['status']) > 0:
            last_status = self.user_unsent_list[user_id]['status'][-1]
        new_message = {
                    'type': 'SELF_RECONNECT',
                    'roomId': group_id,
                    'member1': member1,
                    'member2': member2,
                    'status': last_status,
                    'content': m_content,
                    'sentMessages' : sent_messages,
                    'unsentMessages': unsent_messages
                }
        new_message = json.dumps(new_message, sort_keys=False)
        return new_message
    
    
    def create_ping_message(self):
        new_message = {
                    'type': 'PING'
                    }
        new_message = json.dumps(new_message, sort_keys=False)
        return new_message
    
    
    
    ############################################################### send_message  ###############################################################

    def send_server_member_message(self, group_id, user_id, new_message, updated_status = ''):
        
        new_message_json = json.loads(new_message)
        
        ### send message to user and update the user status if required, add the message in db
        try:
            
            ### send the message into the user websocket
            self.user_socket_list[user_id].send(new_message)
            
            ### update the status of the user
            if updated_status != '':
                self.user_status_list[user_id] = updated_status
                
            ### save the sent message in the user message db
            self.save_message_user_db(user_id, new_message)
        
        ### in case of error in sending, add unsent message and status to send it after reconnect
        except Exception as e:
            
            print("************** the message is adding to unsent messages")
            
            ### add the message to unset list
            self.user_unsent_list[user_id]['messages'].append(new_message_json)
            
            ### add the status to unsent list
            if updated_status != '':
                self.user_unsent_list[user_id]['status'] = updated_status
            
            ### notify the other teammate that this user is disconnected
            print("************** start notifying the teammate that this member is disconnected..")
            self.notify_user_disconnect(group_id, user_id)
            
            
            print("************** timer has started to check the disconnection time of the user ", user_id)
            ### activate this timer to track the disconnection time
            timer = Timer(self.disconnect_limit_sec, self.check_disconnect_limit_exceed, [group_id])
            timer.start()
                
            # error_message = "failed sending message " + new_message + " in group" + group_id + " to user " + user_id
            # print(error_message)

        return
    
    
    def send_server_group_message(self, group_id, new_message, updated_status = ''):
        
        self.send_server_member_message(group_id, self.groups[group_id]['member1'], new_message, updated_status = '')
        self.send_server_member_message(group_id, self.groups[group_id]['member2'], new_message, updated_status = '')
        
        return
    
    
    def send_ping(self, user_id):
        try:
            ping = self.create_ping_message()
            self.user_socket_list[user_id].send(ping)
            return 1
        except:
            print("the user is disconnected", user_id)
            return -1
    
    ############################################################### close connection  ###############################################
    
    def close_group_connection(self, group_id):

        ### close connection for each member of the group
        try:

            if group_id not in self.groups:
                print("group is already removed from the list")
                return
            
            ### close connection of member 1
            member1 = self.groups[group_id]['member1']
            
            is_connected = self.send_ping(member1)
            if is_connected > 0:
                self.user_socket_list[member1].close()
            
            if member1 in self.user_socket_list:
                del self.user_socket_list[member1]
                
            if member1 in self.user_status_list:
                del self.user_status_list[member1]
            
            if member1 in self.user_unsent_list:
                del self.user_unsent_list[member1]
            

            ### close connection of member 2
            member2 = self.groups[group_id]['member2']
            
            is_connected = self.send_ping(member2)
            if is_connected > 0:
                self.user_socket_list[member2].close()
            
            
            if member2 in self.user_socket_list:
                del self.user_socket_list[member2]
            
            if member2 in self.user_status_list:
                del self.user_status_list[member2]
                
            if member2 in self.user_unsent_list:
                del self.user_unsent_list[member2]
            
            
            
            ### remove group from the groups dictionary
            del self.groups[group_id]
            
            print("group data entry is removed")

        except Exception as e:
            
            error_message = "failed to close connection for members of group " + group_id 
            print(error_message)

        return
    
    
    def close_member_connection(self, group_id, user_id):
        
        try:

            if group_id not in self.groups:
                print("group is already removed from the list")
                return
            
            ### online member
            
            is_connected = self.send_ping(user_id)
            if is_connected > 0:
                self.user_socket_list[user_id].close()
            
            if user_id in self.user_socket_list:
                del self.user_socket_list[user_id]
            
            if user_id in self.user_status_list:
                del self.user_status_list[user_id]
            
            if user_id in self.user_unsent_list:
                del self.user_unsent_list[user_id]
            
            
            ### disconnected member
            disconnected_id = self.groups[group_id]['member2']
            if self.groups[group_id]['member2'] == user_id:
                disconnected_id = self.groups[group_id]['member1']
            
            
            if disconnected_id in self.user_socket_list:
                del self.user_socket_list[disconnected_id]
            
            if disconnected_id in self.user_status_list:
                del self.user_status_list[disconnected_id]
            
            if disconnected_id in self.user_unsent_list:
                del self.user_unsent_list[disconnected_id]
                
            
            
            ### remove group from the groups dictionary
            del self.groups[group_id]
            
            print("group data entry is removed")

        except Exception as e:
            
            error_message = "failed to close connection for members of group " + group_id + user_id
            print(error_message)
        
        
        return
                
    
    
    ############################################################### disconnect & reconnect  #######################################
    
    def retrieve_group_information(self, user_id):
        for key, value in self.groups.items():
            if value['member1'] == user_id or value['member2'] == user_id:
                print("*********** the group id is found which is:", key)
                return key, value['member1'], value['member2']
        return '', '', ''
    
    
    def filter_messages_current_task(self, sent_messages):
        filtered_messages = []
        for message in sent_messages:
            if message['type'] == 'START_TASK':
                filtered_messages = []
            filtered_messages.append(message)
        return filtered_messages
    
    
    def notify_user_disconnect(self, group_id, disconnected_user_id):
        
        ### find the user id of the online teammate and start the timer for the disconnected member
        if self.groups[group_id]['member1'] == disconnected_user_id:
            online_user_id = self.groups[group_id]['member2']
            
            if self.groups[group_id]['disconnect_time_1'] == 0:
                self.groups[group_id]['disconnect_time_1'] = int(round(time.time() * 1000))
        else:
            online_user_id = self.groups[group_id]['member1']
            
            if self.groups[group_id]['disconnect_time_2'] == 0:
                self.groups[group_id]['disconnect_time_2'] = int(round(time.time() * 1000))
        
        ### if group is ready to submit the decision or if the group is in the middle of submitting the decision
        if (self.groups[group_id]['status'] == 'READY_INITIAL_SUBMIT') or (self.groups[group_id]['status'] == 'READY_FINAL_SUBMIT'):
            
            ### message for the online user
            m_content = 'Your partner has just lost connection to the chat. Please go ahead with your decision if you haven\'t already, and then await their reconnection.'

        else:
            
            ### message for the online user
            m_content = 'Your partner has just lost connection to the chat, please wait for them to reconnect.'
            
        new_message = self.create_server_message('GROUP_DISCONNECT', m_content)
        self.send_server_member_message(group_id, online_user_id, new_message)
        
        
        
        
        return
    
    
    def check_disconnect_limit_exceed(self, group_id):
        
        ### check if disconnection have been already started
        if (self.groups[group_id]['disconnect_time_1'] == 0) and (self.groups[group_id]['disconnect_time_2'] == 0):
            return
        
        ### calculate disconnect time to check if exceed
        current_time_millis = int(round(time.time() * 1000))
        disconnect_time_1 =  current_time_millis - self.groups[group_id]['disconnect_time_1'] 
        disconnect_time_2 =  current_time_millis - self.groups[group_id]['disconnect_time_2'] 
        
        online_user_id = ""
        if disconnect_time_1 >=  (self.disconnect_limit_sec * 1000):
            online_user_id = self.groups[group_id]['member2']
        elif disconnect_time_2 >= (self.disconnect_limit_sec * 1000):
            online_user_id = self.groups[group_id]['member1']
            
        if online_user_id != "":
            print('********* disconnection exceed message to user is sent', online_user_id)
            m_content = 'It looks like your partner is experiencing difficulties with reconnecting. You have done a good job though, thank you for your participation. You can now exit the task.'
            new_message = self.create_server_message('DISCONNECT_LIMIT_EXCEED', m_content)
            self.send_server_member_message(group_id, online_user_id, new_message)
            
            

            ### close connections
            self.close_member_connection(group_id, online_user_id)
        
        return
    
    
    def reconnect_user(self, data, sock):
        
        ### if there is an error
        if data['status'] == 'failed':
            return
        
        ### user id should be sent for reconnection
        if 'user_id' not in data:
            return
        
        ### check if user or group exists
        if ('user_id' in data and data['user_id'] not in self.user_socket_list) or ('roomId' in data and data['roomId'] not in self.groups):
            return
    
        
        ### check if the already existed user open a new websocket (disconnet then reconnect or reconnect)
        if self.user_socket_list[data['user_id']] != sock and self.user_status_list[data['user_id']] != 'GROUP_CREATED':
            
            print("************** start reconnecting user ...")
            
            ### update reconnected user websocket
            self.user_socket_list[data['user_id']] = sock
            
            print("************** websocket for reconnected user is updated")
            
            ### retrieve past sent messages and filter them ones for the current task
            sent_messages = ast.literal_eval(self.db.extract_user_messages_all_messages(data['user_id']))
            sent_messages = self.filter_messages_current_task(sent_messages)
            
            ### retrieve unsent messages
            unsent_messages = self.user_unsent_list[data['user_id']]['messages']
            
            print("************** messages for the reconnected user is retrieved")
            
            ### send all messages and update the status of the user, and notify that the user reconnected
            m_content = 'You have just rejoined the chat. You can proceed with the task.'
            group_id, member1, member2 = self.retrieve_group_information(data['user_id'])
            
            if group_id == '':
                print("*************** group id is empty")
            
                
            new_message = self.create_reconnect_messages(group_id, data['user_id'], member1, member2, m_content, sent_messages, unsent_messages)
            self.send_server_member_message(group_id, data['user_id'], new_message, self.user_unsent_list[data['user_id']]['status'])
            
            print("************** all messages (sent and unsent) and rejoin notification is sent to the reconnected user")
            
            ### notify online user that the teammate reconnected
            if self.groups[group_id]['member1'] == data['user_id']:
                online_user_id = self.groups[group_id]['member2']
                
                ### stop the disconnect timer for the reconnected user
                self.groups[group_id]['disconnect_time_1'] = 0
            else:
                online_user_id = self.groups[group_id]['member1']
                
                ### stop the disconnect timer for the reconnected user
                self.groups[group_id]['disconnect_time_2'] = 0
                
            m_content = 'Your partner has just rejoined the chat. You can proceed with the task.'
            new_message = self.create_server_message('GROUP_RECONNECT', m_content)
            self.send_server_member_message(group_id, online_user_id, new_message)
            
            print("************** other teammate get the notification about reconnection")
            
        return

    ############################################################### group construction and update ###############################################################


    def register_a_waiting_user(self, sock, data):

        ### check if data received 
        if data['status'] == 'failed':
            return

        ### if user is in waiting room
        if (data['type']== 'USER_JOIN') and ('user_id' in data):
            
            ### initiate websocket for a new user arrives in the waiting room
            if data['user_id'] not in self.user_socket_list:
                self.user_socket_list[data['user_id']] = sock
                self.user_status_list[data['user_id']] = 'WAITING'
                self.user_unsent_list[data['user_id']] = {'status': '', 'messages': []}
                print("new user id is registered in waiting room", data['user_id'])
            
            ### update websocket for a user in waiting phase who reconnected
            elif (data['user_id'] in self.user_socket_list) and (self.user_status_list[data['user_id']] == 'WAITING'):
                self.user_socket_list[data['user_id']] = sock
                print("waiting user is reconnected",data['user_id'])
            
            ### if user reconnect just after joining the group and before entering the user_chat status
            elif (data['user_id'] in self.user_socket_list) and (self.user_status_list[data['user_id']] == 'GROUP_CREATED'):
                self.user_socket_list[data['user_id']] = sock
                group_id, member1, member2 = self.retrieve_group_information(data['user_id'])
                new_message = self.recreate_group_join_message(group_id, member1, member2)
                self.send_server_member_message(group_id, data['user_id'], new_message, 'GROUP_CREATED')
                print("user will join chat after disconnecting after joining the group", data['user_id'])
                
            
            
            if self.waiting_user == '':
                self.waiting_user = data['user_id']
            else:
                is_connected = self.send_ping(self.waiting_user)
                if is_connected < 0:
                    print("teammate is reconnected", self.waiting_user)
                    self.waiting_user = data['user_id']
                    
                
            
            ### set the waiting_start time for the user
            current_time_millis = int(round(time.time() * 1000))
            self.db.set_user_response_waiting_user_start(data['user_id'], str(current_time_millis))
            
            print("************** user ", data['user_id'], " is in the waiting room")

        return


    def create_a_group_obj(self, user_id):

        new_group_id = str(uuid.uuid4())
        new_group = {
                        'member1': self.waiting_user,
                        'member2': user_id,
                        'status': 'GROUP_CREATED',
                        'start_time': 0,
                        'ready': [],
                        'submitted': [],
                        'decisions': [],
                        'initial_decision': False,
                        'final_decision': False,
                        'user_study': {self.waiting_user: [], user_id: []},
                        'self_reports': {},
                        'decision_times': [],
                        'disconnect_time_1': 0,
                        'disconnect_time_2': 0
                    }


        self.groups[new_group_id] = new_group
        self.waiting_user = ''
        
        ### update each user status
        self.user_status_list[new_group['member1']] = 'GROUP_CREATED'
        self.user_status_list[new_group['member2']] = 'GROUP_CREATED'
        
        print("************** new group just created\n", new_group)

        return new_group_id, new_group

    
    def check_user_already_in_group(self, user_id):
        for group_id in self.groups:
            if self.groups[group_id]['member1'] == user_id or self.groups[group_id]['member2'] == user_id:
                return True
        return False
    
    def create_a_new_group(self, data):

        new_group_id = ''
        
        ### if the user already exists and reconnected 
        if 'user_id' in data and self.check_user_already_in_group(data['user_id']):
            return new_group_id

        ### create a group when new a user arrives
        if ('user_id' in data) and (self.waiting_user!= data['user_id']) and (self.waiting_user != ''):
            
            print("enter creating a new group...")
            
            
            ### check if two members are still connected
            is_connected_1 = self.send_ping(self.waiting_user)
            is_connected_2 = self.send_ping(data['user_id'])
            if is_connected_1 < 0:
                print("team member is already disconnected", self.waiting_user)
                self.waiting_user = data['user_id']
                return new_group_id
            if is_connected_2 < 0:
                print("team member is already disconnected", data['user_id'])
                return new_group_id
            

            ### create new group with the waiting user and update waiting user variable
            new_group_id, new_group = self.create_a_group_obj(data['user_id'])
            
            
            ### set the waiting_end time for both members
            current_time_millis = int(round(time.time() * 1000))
            self.db.set_user_response_waiting_user_end(self.groups[new_group_id]['member1'], str(current_time_millis))
            self.db.set_user_response_waiting_user_end(self.groups[new_group_id]['member2'], str(current_time_millis))
            
            
            ### set the group entry in the database for the newly-created group
            self.db.insert_group_messages_entry(new_group_id, self.groups[new_group_id]['member1'], self.groups[new_group_id]['member2'])

            ### set the user entry in the database for each member of the newly-created group
            self.db.insert_user_messages_entry(self.groups[new_group_id]['member1'])
            self.db.insert_user_messages_entry(self.groups[new_group_id]['member2'])
            
            print("************** group and members are added to database successfully.")
            
            ### send group join message to newly created group
            new_message = self.create_group_join_message(new_group_id, new_group)
            self.send_server_group_message(new_group_id, new_message, 'GROUP_CREATED')
            
            print("************** group created message is sent")
            
        return new_group_id

    
    def register_a_user_chat_websocket(self, sock, data):
        
        # print("************** inside user chat ws registration")
        # print(data)
        
        ### if there is an error
        if ('type' in data and data['type'] != 'USER_CHAT') or (data['status'] == 'failed'):
            return False
            
        ### check if user or group exists
        if (data['user_id'] not in self.user_socket_list) or (data['roomId'] not in self.groups):
            return False
        
        ### check if the user is not a already existing user with reconnection
        if self.user_status_list[data['user_id']] != 'GROUP_CREATED':
            return False
        
        
        
        ### update chat websocket for the user and the status
        self.user_socket_list[data['user_id']] = sock
        self.user_status_list[data['user_id']] = 'USER_CHAT'
        

        # print("************** user chat socket is updated sucessfully.")

        ### check if the other member have updated the chat websocket
        if (self.user_status_list[self.groups[data['roomId']]['member1']] != 'USER_CHAT') or (self.user_status_list[self.groups[data['roomId']]['member2']] != 'USER_CHAT'):
            return False
        
        ### check ws socket of both members are still connected
        is_connected_1 = self.send_ping(self.groups[data['roomId']]['member1'])
        is_connected_2 = self.send_ping(self.groups[data['roomId']]['member2'])
        
        if is_connected_1 < 0 or is_connected_2 < 0:
            return False

        ### send welcome message to newly created group when register their chat websocket
        m_content = 'Welcome to the Discussion Room; please follow these instructions to complete the task successfully:' + "<br>" +  '1. Please use the next 2 minutes to introduce yourselves and get to know each other further. Feel free to use the suggested questions below or devise your own.' + "<br>" +  '2. Once introductions are complete, you can talk about the task.' + "<br>" +  '3. When making a decision, use the command /initial-submit (with no additional character) to get a blue message inside the chat asking for your initial decision. Both participants should execute this command to receive the question for the initial decision.' + "<br>" + '4. After making the initial decision, discuss and evaluate the available options and their potential outcomes.' + "<br>" + '5. On reaching a consensus, use the command /final-submit (with no additional character) to get a blue message inside the chat asking for your final decision. Both participants should execute this command to receive the question for the final decision.' + "<br>" + '6. Upon finishing the present task, you will move on to the next one. There are a total of three tasks. Follow steps 2 to 5 for each of the following tasks.'
        new_message = self.create_chat_join_message(m_content, data['roomId'])
        self.send_server_group_message(data['roomId'], new_message, 'CHAT_JOINED')

        ### update the group status
        self.groups[data['roomId']]['status'] = 'CHAT_JOINED'

        ### save the message in the db
        self.save_message_db(data['roomId'], 'CHAT_JOINED', m_content, '1', '')
        
        print("************** one user chat socket is updated sucessfully.")
            
        return True
    


    def update_group_user_study(self, group_id, submit_type, task_id):
        
        ### initial submission
        ### -1 the decision to convert into 0-9 range
        if submit_type == 'INITIAL_DECISION':
            task_dict_temp = {'task_id': task_id, 'initial_decision': '', 'final_decision': '', 'initial_confidence': '', 'final_confidence': '', 'self_input': '', 'partner_input': '', 'ai_input':''} 
            
            ### member 1
            member_1_task = copy.deepcopy(task_dict_temp)
            member_1_task['initial_decision'] = str(int(self.groups[group_id]['decisions'][0]) - 1)
            self.groups[group_id]['user_study'][self.groups[group_id]['submitted'][0]].append(member_1_task)
            
            ### member 2
            member_2_task = copy.deepcopy(task_dict_temp)
            member_2_task['initial_decision'] = str(int(self.groups[group_id]['decisions'][1]) - 1)
            self.groups[group_id]['user_study'][self.groups[group_id]['submitted'][1]].append(member_2_task)
            
        
        ### final submission
        elif submit_type == 'FINAL_DECISION':
            
            ### member 1
            for task_dict in self.groups[group_id]['user_study'][self.groups[group_id]['submitted'][0]]:
                if task_dict['task_id'] == task_id:
                    task_dict['final_decision'] = str(int(self.groups[group_id]['decisions'][0]) - 1)
            
            ### member 2
            for task_dict in self.groups[group_id]['user_study'][self.groups[group_id]['submitted'][1]]:
                if task_dict['task_id'] == task_id:
                    task_dict['final_decision'] = str(int(self.groups[group_id]['decisions'][1]) - 1)
        return
    
    
    def update_group_decision_times(self, group_id, submit_type, task_id):
        
        task_dict = {'task_id': task_id, 'start_decision': 0, 'end_decision': 0}
        current_time_millis = int(round(time.time() * 1000))
        
        if submit_type == 'INITIAL_DECISION':
            task_dict['start_decision'] = current_time_millis
            self.groups[group_id]['decision_times'].append(task_dict)
            
        elif submit_type == 'FINAL_DECISION':
            for task in self.groups[group_id]['decision_times'] :
                if task['task_id'] == task_id:
                    task['end_decision'] = current_time_millis
                    break
        return
    
    
    def update_user_self_reports(self, group_id, user_id, self_reports):
        
        for report in self_reports:
            for task in self.groups[group_id]['user_study'][user_id]:
                if  report['task_id'] == task['task_id']:
                    task['initial_confidence'] = report['initial_confidence']
                    task['final_confidence'] = report['final_confidence']
                    task['self_input'] = report['self_input']
                    task['partner_input'] = report['partner_input']
                    task['ai_input'] = report['ai_input']
                    

        self.user_status_list[user_id] = 'STUDY_DONE'
        if self.user_status_list[self.groups[group_id]['member1']] == 'STUDY_DONE' and self.user_status_list[self.groups[group_id]['member2']] == 'STUDY_DONE':
            return 1
        else:
            return -1
    
    
    def retrieve_group_final_decisions(self, group_id):
        
        decision_list = []
        member1 = self.groups[group_id]['member1']
        for task in self.groups[group_id]['user_study'][member1]:
            task_dict = { 'task_id': task['task_id'], 'final_decision': task['final_decision']}
            decision_list.append(task_dict)
        
        return decision_list


    def check_all_tasks_complete(self, group_id, num_task_instances):

            if len(self.groups[group_id]['user_study'][self.groups[group_id]['member1']]) != num_task_instances:
                return False
            
            if len(self.groups[group_id]['user_study'][self.groups[group_id]['member2']]) != num_task_instances:
                return False

            for task in self.groups[group_id]['user_study'][self.groups[group_id]['member1']]:
                if (task['initial_decision'] == '') or (task['final_decision'] == '' ):
                    return False
                
            for task in self.groups[group_id]['user_study'][self.groups[group_id]['member2']]:
                if (task['initial_decision'] == '') or (task['final_decision'] == '' ):
                    return False

            return True
    
    
    def check_one_task_complete(self, group_id, task_id):
        
        if len(self.groups[group_id]['user_study'][self.groups[group_id]['member1']]) == 0:
            return False
        
        if len(self.groups[group_id]['user_study'][self.groups[group_id]['member2']]) == 0:
            return False
        
        for task in self.groups[group_id]['user_study'][self.groups[group_id]['member1']]:
            if task['task_id'] == task_id:
                if (task['initial_decision'] == '') or (task['final_decision'] == '' ):
                    return False
        
        for task in self.groups[group_id]['user_study'][self.groups[group_id]['member2']]:
            if task['task_id'] == task_id:
                if (task['initial_decision'] == '') or (task['final_decision'] == '' ):
                    return False
        
        return True
    
    
    def terminate_group(self, group_id, n_instances):
        
        ### save the entire responses for user study and decision_times if initial and final decisions are complete 
        is_complete = self.check_all_tasks_complete(group_id, n_instances)
            
        ### check if all tasks are completed
        if is_complete:
            print("group finished all tasks")
            self.close_group_connection(group_id)
        
        return
        
    ############################################################### ice-breaking  ###############################################################

    def calculate_ice_breaking_time(self, group):
        current_time_millis = int(round(time.time() * 1000))
        duration = current_time_millis - group['start_time']
        return duration

    
    def send_ice_breaking_samples(self, group_id):
        
        ### check if the chat window is just created and no further message is communicated between members or members and the server
        if group_id == '':
            return
        
        if self.groups[group_id]['status'] != 'CHAT_JOINED':
            return

        ### send a sample of ice-breaking questions and set the status of the group to ice-breaking
        m_content = 'To begin, take the time to introduce yourselves within 2 minutes. Here are some examples of ice-breaker questions. You can choose one or come up with your own.' +  "<br>" + 'What do you like to eat on your pizza?' + "<br>" + 'If you could live in any perioid of history, when would it be?' + "<br>" + 'What is the best present you ever received?'
        new_message = self.create_server_message('ICE_BREAKING', m_content)
        self.send_server_group_message(group_id, new_message, 'ICE_BREAKING')
        
        self.groups[group_id]['status'] = 'ICE_BREAKING'

        ### set the time of starting ice_breaking step
        current_time_millis = int(round(time.time() * 1000))
        self.groups[group_id]['start_time'] = current_time_millis
        
        ### save the message in the db
        self.save_message_db(group_id, 'ICE_BREAKING', m_content, '1', '')
        
        print("************** message in ice breaking is sent")

        return

    ############################################################### start-discussion  ############################################################

    def start_discussion(self, duration, group_id, data):

        ### check if the group is in ice-breaking step and no further message is communicated between members or members and the server when the timer starts for this function
        if group_id == '':
            return
        
        if self.groups[group_id]['status'] != 'ICE_BREAKING':
            return

        ### after the time limit, ask members to start discussing about the task and they will be redirected to start_discussion status
        if duration > self.discussion_limit_milisec :
            m_content = 'Please begin discussing the task and the best route to take. When prepared, use the command /initial-submit (with no additional character) to get a blue message inside the chat asking for your initial decision. Both participants should execute this command to receive the question for the initial decision.' 
            new_message = self.create_server_message('WARNING', m_content)
            self.send_server_group_message(group_id, new_message, 'START_DISCUSSION')
            self.groups[group_id]['status'] = 'START_DISCUSSION' 
            
            ### save message in db
            self.save_message_db(group_id, 'START_DISCUSSION', m_content, '1', '')

        return

    ############################################################### initial-submit & final-submit  #################################################

    def validate_pass_group_message(self, group_id, user_id):
        ### check if a message could be sent to both members 
        if (self.groups[group_id]['status'] == 'READY_INITIAL_SUBMIT') or (self.groups[group_id]['status'] == 'READY_FINAL_SUBMIT'):
            return -1
        return 1
    
    
    def validate_ready_sumbit(self, group_id, submit_type):
        
        ### check whether this step is activated in the correct step
        warning = False

        ### if group members are not currently in start_discussion step, they get the warning message
        if (self.groups[group_id]['status'] != 'START_DISCUSSION') and (self.groups[group_id]['initial_decision'] == False):
            if submit_type == 'READY_INITIAL_SUBMIT': 
                m_content = 'You cannot initiate this stage until you have completed the steps for the short introduction and discussion.'
            elif submit_type == 'READY_FINAL_SUBMIT': 
                m_content = 'You cannot initiate this stage until you have completed the steps for the short introduction, discussion, and initial decision submission.'
            warning = True

        ### if group members activate final_submit before the initial_submit step 
        elif (self.groups[group_id]['initial_decision'] == False) and (submit_type == 'READY_FINAL_SUBMIT'):
            m_content = 'You have not yet submitted your initial decision. You can proceed with this step after making your initial decision.'
            warning = True

        ### if group members activate initial decision more than once
        elif (self.groups[group_id]['initial_decision'] == True) and (submit_type == 'READY_INITIAL_SUBMIT'):
            m_content = 'You have already submitted your initial decision. You cannot to do so again. The next step is to make a final decision.'
            warning = True

        ### if group members activate final decision more than once
        elif (self.groups[group_id]['final_decision'] == True) and (submit_type == 'READY_FINAL_SUBMIT'):
            m_content = 'You have already submitted your final decision. You cannot to do so again.'
            warning = True

        if warning:
            new_message = self.create_server_message('WARNING', m_content)
            self.send_server_group_message(group_id, new_message)
            
            ### save the message in db
            self.save_message_db(group_id, 'WARNING', m_content, '1', '')
      
        return warning
    
    
    def ready_sumbit_two_members(self, group_id, submit_type, task_id):
        
        m_content = 'You should choose the routes that minimize both time and cost. You cannot view your partner’s response until you submit your own. Please enter the route number you have selected from 1 to 10, and wait for your partner to submit their initial decision as well.'
        new_message = self.create_server_message(submit_type, m_content)
        self.send_server_group_message(group_id, new_message)
        
        self.groups[group_id]['status'] = submit_type
        self.groups[group_id]['ready'] = []

        ### save the message in db
        self.save_message_db(group_id, submit_type, m_content, '1', '')

        ### update the group that initial or final decision is submitted to avoid activating it again
        if submit_type == 'READY_INITIAL_SUBMIT':
            self.groups[group_id]['initial_decision'] = True
            decision_type = 'INITIAL_DECISION'

        elif submit_type == 'READY_FINAL_SUBMIT':
            self.groups[group_id]['final_decision'] = True
            decision_type = 'FINAL_DECISION'

        ### update decision times for the group
        self.update_group_decision_times(group_id, decision_type, task_id)
        
        return
    
    
    def ready_submit_one_member(self, group_id, submit_type):
        
        if submit_type == 'READY_INITIAL_SUBMIT':
            m_content = 'Both participants need to enter /initial-submit in order to proceed to this stage.'
        elif submit_type == 'READY_FINAL_SUBMIT':
            m_content = 'Both participants need to enter /final-submit in order to proceed to this stage.'

        new_message = self.create_server_message('WAITING',m_content)
        self.send_server_group_message(group_id, new_message)

        ### save the message in db
        self.save_message_db(group_id, 'WAITING', m_content, '1', '')
        
        return
    
    
    # submit_type = 'READY_INITIAL_SUBMIT' or 'READY_FINAL_SUBMIT'
    def ready_submit(self, group_id, user_id, submit_type, task_id):
        
        ### check whether this step is activated in the right order
        warning = self.validate_ready_sumbit(group_id, submit_type)
        if warning:
            return
        
        ### add the group member to ready to submit phase
        if user_id not in self.groups[group_id]['ready']:
            self.groups[group_id]['ready'].append(user_id)
            self.user_status_list[user_id] = submit_type

        ### if both group members activate initial_submit or final_submit, then they enter this step seperately to type their decision
        if len(self.groups[group_id]['ready']) == 2:
            self.ready_sumbit_two_members(group_id, submit_type, task_id)

        ### if only one group member activates the inital_submit or final_submit, they get a warning to be activated by the other as well
        elif len(self.groups[group_id]['ready']) == 1:
            self.ready_submit_one_member(group_id, submit_type)
        
        return
    

    def validate_decision_format(self, group_id , user_id, decision, sender_time):
        warning = False
        
        ### check the format of data a user submitted as her decision
        if (decision.isdigit() == False) or (decision.isdigit() == True and ( (int(decision) < 1) or (int(decision)> self.num_routes))):

            ### send back the user input
            new_message = self.create_group_message(str(decision), user_id, sender_time)
            self.send_server_member_message(group_id, user_id, new_message)

            ### save the message in db
            self.save_message_db(group_id, 'ERROR_SUBMISSION', str(decision), user_id, sender_time)

            ### send the warning message to the user 
            m_content = 'You entered the incorrect format. Please enter only the number corresponding to the selected route from 1 to 10.'
            new_message = self.create_server_message('WARNING', m_content)
            self.send_server_member_message(group_id, user_id, new_message)

            ### save the message in db
            self.save_message_db(group_id, 'ERROR_SUBMISSION_WARNING', m_content, '1', '')
            
            warning = True
        
        return warning
   
    
    def submit_decision_one_member(self, group_id, user_id, decision, sender_time):
        
        ### add the member and decision in the group object
        if user_id not in self.groups[group_id]['submitted']:
            self.groups[group_id]['submitted'].append(user_id)
            self.groups[group_id]['decisions'].append(str(decision))

            new_message = self.create_group_message(str(decision),user_id, sender_time)
            updated_stat = 'COMPLETE_' + self.groups[group_id]['status'][6:]
            self.send_server_member_message(group_id, user_id, new_message, updated_stat)

            ### save the message in ddb
            self.save_message_db(group_id, self.groups[group_id]['status'][6:], str(decision), user_id, sender_time)
            
            
            ### inform the user that the initial decision submitted successfully
            if self.groups[group_id]['status'][6:13] == 'INITIAL':

                new_message = self.create_server_message('INITIAL_DECISION_SUBMITTED', '')
                self.send_server_member_message(group_id, user_id, new_message)
            
                ### save the message in db
                self.save_message_db(group_id, 'INITIAL_DECISION_SUBMITTED', '', '1', '')
            
            
            
            print("$$$$$$$$$$$$$$$$$$$$$$")
            print("user ", user_id, " submitted decision ", decision, " with status ", updated_stat)
            print("$$$$$$$$$$$$$$$$$$$$$$")
        
        return
    
    
    def validate_initial_submit_two_members(self, group_id, task_id):
        
        if self.groups[group_id]['status']== 'READY_INITIAL_SUBMIT':
            
            ### retrive ai_best_route for the task_id
            ai_best_route = self.retrieve_ai_suggestion(group_id, task_id)
            
            m_content = 'You have both made your initial choices. Your team have identified the best route to be route ' + str(self.groups[group_id]['decisions'][0]+ ' and route '+ self.groups[group_id]['decisions'][1]) + '. The AI system is proposing route ' + str(ai_best_route)+ ' as the best route. Please discuss this with your partner again and aim to reach a consensus on your final decision. You can run the command /final-submit (with no additional character) to get a blue message inside the chat asking for your final decision. Both participants should execute this command to receive the question for the final decision.' 
            new_message = self.create_server_message('SHOW_INITIAL_DECISION', m_content)

            ### send server message
            self.send_server_group_message(group_id, new_message, 'START_DISCUSSION')

            ### update group status
            self.groups[group_id]['status'] = 'SUBMITTED_INITIAL_DECISION'

            ### update group initial decision
            self.update_group_user_study(group_id, 'INITIAL_DECISION', task_id)
            

            ### save the message in db
            self.save_message_db(group_id, 'SHOW_INITIAL_DECISION', m_content, '1', '')
        
        return
    
    
    def identical_final_submit(self, group_id, task_id):
        
        m_content = 'You have completed this task successfully.'
        new_message = self.create_server_message('COMPLETED',m_content)

        ### send server message
        self.send_server_group_message(group_id, new_message, 'TASK_COMPLETED')

        ### update group status
        self.groups[group_id]['status']= 'COMPLETED'

        ### update group final decision
        self.update_group_user_study(group_id, 'FINAL_DECISION', task_id)
        print("################## final decisions are updated ####################")
        print(self.groups[group_id]['user_study'])
        print("#####################################")

        ### save the message in db
        self.save_message_db(group_id, 'COMPLETED', m_content, '1', '')

        ### update group data in groups dictionary after finishing one task
        self.groups[group_id]['start_time'] = 0
        self.groups[group_id]['initial_decision'] = False
        self.groups[group_id]['final_decision'] = False
        
        return
    
    
    def non_identical_final_submit(self, group_id):
        
        m_content = 'Each partner submitted a different route. You should reach an agreement for the final decision. Please  discuss this further to reach a consensus on the route, and then try submitting again.'
        new_message = self.create_server_message('STATUS_CHANGE', m_content)

        ### send server message
        self.send_server_group_message(group_id, new_message, 'START_DISCUSSION')
        
        ### update group status
        self.groups[group_id]['status']= 'START_DISCUSSION'
        self.groups[group_id]['final_decision'] = False

        print("************** change the status of the group to discussion")

        ### save the message in db
        self.save_message_db(group_id, 'STATUS_CHANGE', m_content, '1', '')
        
        return
                                     
                        
    def validate_final_submit_two_members(self, group_id, task_id):
        
        if self.groups[group_id]['status']=='READY_FINAL_SUBMIT':

            ### if the final decisions of both members are identical, then they complete the task
            if self.groups[group_id]['decisions'][0] == self.groups[group_id]['decisions'][1]:
                self.identical_final_submit(group_id, task_id)
            else:
                self.non_identical_final_submit(group_id)
                
        return
    
    
    def submit_decision(self, data):
        
        ### check if data received 
        if data['status'] == 'failed':
            return

        ### check if the client in submit_decision status
        if data['type'] != 'SUBMIT_DECISION':
            return
        
        group_id = data['roomId']
        user_id = data['senderId']
        decision = data['content']
        sender_time = data['senderTime']
        task_id = data['taskId']

        ### check whether users are ready submit initial or final decision
        if  self.groups[group_id]['status']== 'READY_INITIAL_SUBMIT' or self.groups[group_id]['status']=='READY_FINAL_SUBMIT':
            
            ### check the format of data a user submitted as her decision
            warning = self.validate_decision_format(group_id , user_id, decision, sender_time)
            if warning:
                return
            
            ### add the member and decision in the group object
            self.submit_decision_one_member(group_id, user_id, decision, sender_time)
            
            ### verify both members submit their decision
            if len(self.groups[group_id]['decisions']) == 2:

                ### when both group members submitted their inital decision, their decision and AI suggestion will be sent to the group
                self.validate_initial_submit_two_members(group_id, task_id)
                
                ### when both group members submitted their final decision
                self.validate_final_submit_two_members(group_id, task_id)
                
                ### empty the two fields of the group object used for decision making
                self.groups[group_id]['submitted'] = []
                self.groups[group_id]['decisions'] = []
        
        return

    
    ############################################################### help  ###############################################################

    def help_group(self, group_id):
        m_content = 'Please follow these instructions to complete the task successfully:' + "<br>" +  '1. Please use the next 2 minutes to introduce yourselves and get to know each other further. Feel free to use the suggested questions below or devise your own.' + "<br>" +  '2. Once introductions are complete, you can talk about the task.' + "<br>" +  '3. When making a decision, use the command /initial-submit (with no additional character) to get a blue message inside the chat asking for your initial decision. Both participants should execute this command to receive the question for the initial decision.' + "<br>" + '4. After making the initial decision, discuss and evaluate the available options and their potential outcomes.' + "<br>" + '5. On reaching a consensus, use the command /final-submit (with no additional character) to get a blue message inside the chat asking for your final decision. Both participants should execute this command to receive the question for the final decision.' + "<br>" + '6. Upon finishing the present task, you will move on to the next one. There are a total of three tasks. Follow steps 2 to 5 for each of the following tasks.'
        new_message = self.create_server_message('INSTRUCTION', m_content)
        self.send_server_group_message(group_id, new_message)
        
        ### save the message in db
        self.save_message_db(group_id, 'INSTRUCTION', m_content, '1', '')
        
        return
    
    ############################################################### next task  ###############################################
    
    def ready_next_task(self, user_id, group_id):
        if (self.groups[group_id]['status'] == 'COMPLETED') and ( user_id not in self.groups[group_id]['ready']):
            self.groups[group_id]['ready'].append(user_id)
        return 
    
    def start_next_task(self, group_id):
        
        ### update the status of group to start the next task if the previous one is completed
        if (self.groups[group_id]['status'] == 'COMPLETED'):
            self.groups[group_id]['status'] = 'START_DISCUSSION'
        
            ### send the message to inform group members to start the new task
            m_content = 'You can start the next task. The same procedure should be followed, beginning with a discussion and then proceeding to the initial and final decisions.'
            new_message = self.create_server_message('START_TASK', m_content)

            self.send_server_group_message(group_id, new_message,'START_TASK')
            
            ### save the message in db
            self.save_message_db(group_id, 'START_TASK', m_content, '1', '')

            ### empty ready
            self.groups[group_id]['ready'] = []
        
        return

    ############################################################### receive data and message  ###############################################

    def receive_websocket_data(self, sock):

        ### check the data received without error from the client
        try:
            data = json.loads(sock.receive())
            data['status'] = 'received'
            print(data['type'])
            return data

        except Exception as e:
            error_message = "failed receiving message from the client"
            # print(error_message)

        return {'status': 'failed'}


    def receive_message(self, data):

        ### check if data received 
        if data['status'] == 'failed':
            return
        
        ### check if the group enters next task
        if data['type'] == 'START_TASK':
            self.start_next_task(data['roomId'])
            
        
        ### send back ping message
        if data['type'] == 'PING':
            self.send_ping(data['senderId'])

        ### echo group disucssion to bothe members, and activate the steps based on their message /initial-submit, /final-submit, /help
        if data['type']=='GROUP_MESSAGE':
            
            ### validate the group message can be broadcasted to both group members
            is_valid = self.validate_pass_group_message(data['roomId'], data['senderId'])
            if is_valid < 0:
                return

            ### echo the message to group members
            new_message = self.create_group_message(data['content'], data['senderId'], data['senderTime'])
            self.send_server_group_message(data['roomId'], new_message)

            ### save the message in db
            self.save_message_db(data['roomId'], 'GROUP_MESSAGE', data['content'], data['senderId'], data['senderTime'])

            ### redirect members to start-discussion status after the time limit in the ice-breaking 
            duration = self.calculate_ice_breaking_time(self.groups[data['roomId']])
            self.start_discussion(duration, data['roomId'], data)

            ### check if messages are commands from this list: /initial-submit, /final-submit, /help
            if data['content'] == r'/initial-submit':
                self.ready_submit(data['roomId'], data['senderId'], 'READY_INITIAL_SUBMIT', data['taskId'])

            elif data['content'] == r'/final-submit':
                self.ready_submit(data['roomId'], data['senderId'], 'READY_FINAL_SUBMIT', data['taskId'])

            elif data['content'] == r'/help':
                self.help_group(data['roomId'])

        return




    
    