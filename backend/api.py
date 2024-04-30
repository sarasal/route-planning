from flask import Flask, jsonify, request 
from flask_cors import CORS
from flask_sock import Sock
import json
import uuid
import time
from threading import Lock
import sys
import ast

import service

n_instances = 2
n_participant_per_condition = 43
user_service = service.Service(n_instances, n_participant_per_condition)


app = Flask(__name__)
sock = Sock(app)
CORS(app)




# assign a study condition to the user & get the pre_test response
@app.route('/get_user_tutorial', methods = ['POST'])
def send_tutorial():
    
    try:
        user_data = request.json
        
        ### check if data format is correct
        if ("user_id" not in user_data) or ("pre_test" not in user_data):
            return "Bad Request -- TRIP-PLANNER", 400
        
        
        ### check if attention checks are answered correctly, otherwise reject the user instantly
        ### TODO uncomment for evaluating attention checks in the end
        # pre_test = user_data["pre_test"]
        pre_test = ast.literal_eval(str(user_data["pre_test"]))
        # attention_check = user_service.validate_pre_test_attention_checks(pre_test)
        # if attention_check == False:
        #     return { "status": "failed" }
        
        ### assign the study condition
        study_condition = "1"
        user_service.set_user_study_condition(user_data["user_id"], study_condition)
        
        ### set the tutorial based on study condition
        tutorial = user_service.set_user_tutorial(study_condition)
        
        ### save the pre_test
        user_service.save_user_pre_test_response(user_data["user_id"], pre_test)
        
        tutorial["status"] = "passed"

        ### convert the string to json
        tutorial_json = json.dumps(tutorial, sort_keys=False, indent=4)
        
        return tutorial_json
        
    except Exception as e:
        print(e)
        return "Internal Server Error -- TRIP-PLANNER", 500

    
    
# get the study condition from the user & send the training task
@app.route('/get_user_training_task', methods = ['POST'])
def send_training_task():
    
    try: 
        user_data = request.json
        
        ### check if data format is correct
        if "study_condition" not in user_data:
            return "Bad Request -- TRIP-PLANNER", 400

        ### set the training task
        training_task = user_service.set_user_training_task(user_data["study_condition"])

        ### convert the string to json
        training_task_json = json.dumps(training_task, sort_keys=False, indent=4)

        return training_task_json
    
    except Exception as e:
        print(e)
        return "Internal Server Error -- TRIP-PLANNER", 500

    
    
# get the study condition from the user & send the quiz
@app.route('/get_user_quiz', methods = ['POST'])
def send_quiz():
    
    try: 
        user_data = request.json
        
        ### check if data format is correct
        if "study_condition" not in user_data:
            return "Bad Request -- TRIP-PLANNER", 400

        ### set the quiz
        quiz_features = user_service.set_user_quiz_questions(user_data["study_condition"])

        ### convert the string to json
        quiz_features_json = json.dumps(quiz_features, sort_keys=False, indent=4)

        return quiz_features_json
    
    except Exception as e:
        print(e)
        return "Internal Server Error -- TRIP-PLANNER", 500
    
    
# determine the user score from the quiz    
@app.route('/check_user_qualification', methods = ['POST'])
def send_quiz_key_answers():
   
    try:
        user_data = request.json

        ### check if data format is correct
        if ("user_id" not in user_data) or ("study_condition" not in user_data) or ("quiz_response" not in user_data):
            return "Bad Request -- TRIP-PLANNER", 400

        ### check whether the user qualify to continiue, if so, send them the key answers for incorrect quiz response
        quiz_transcript = user_service.check_user_qualification(user_data["user_id"], user_data["study_condition"], user_data["quiz_response"])
        
        ### convert the string to json
        quiz_transcript_json = json.dumps(quiz_transcript, sort_keys=False, indent=4)
        print(" ############## quiz result #############")
        print(quiz_transcript_json)

        return quiz_transcript_json
    
    except Exception as e:
        print(e)
        return "Internal Server Error -- TRIP-PLANNER", 500
        
        
        
# if the user passed in the quiz and already joined a group, then send main study task instances
@app.route('/get_group_task_instances', methods = ['POST'])
def send_task_instances():
    
    try:
        user_data = request.json
        
        ### check if data format is correct
        if ("user_id" not in user_data) or ("group_id" not in user_data):
            return "Bad Request -- TRIP-PLANNER", 400

        ### get the main task instances for the group
        assigned_task_instances_json = user_service.retrieve_group_assigned_tasks_instances(user_data["group_id"])

        return assigned_task_instances_json
    
    except Exception as e:
        print(e)
        return "Internal Server Error -- TRIP-PLANNER", 500


# get group_responses
@app.route('/get_user_study_score', methods = ['POST'])
def save_group_study_responses():
    
    try:
        user_data = request.json
        
        ### check if data format is correct
        if "group_id" not in user_data:
            return "Bad Request -- TRIP-PLANNER", 400
        
        ### save group decisions for main task instances and return their score
        group_score = user_service.retrieve_group_score(user_data["group_id"])
        res = {"score": group_score}
        res_json = json.dumps(res, sort_keys=False, indent=4)
        
        return res_json
    
    except Exception as e:
        print(e)
        return "Internal Server Error -- TRIP-PLANNER", 500

    


# get post_test
@app.route('/submit_post_test', methods = ['POST'])
def save_post_test():
    
    try:
        user_data = request.json
        
        ### check if data format is correct
        if ("user_id" not in user_data) or ("post_test" not in user_data):
            return "Bad Request -- TRIP-PLANNER", 400
        
        ### save the post test and complete the study for the user 
        post_test = ast.literal_eval(str(user_data["post_test"]))
        # post_test = user_data["post_test"]
        user_service.complete_study(user_data["user_id"], post_test)

        return "OK -- TRIP-PLANNER", 200
    
    except Exception as e:
        print(e)
        return "Internal Server Error -- TRIP-PLANNER", 500



# get the event invoked by the user
@app.route('/submit_event', methods = ['POST'])
def save_event():
    
    try:
        user_data = request.json
        
        ### check if data format is correct
        if ("user_id" not in user_data) or ("task_id" not in user_data) or ("event_type" not in user_data) or ("timestamp" not in user_data) or ("event_value" not in user_data):
            return "Bad Request -- TRIP-PLANNER", 400

        ### save the event invoked by the user corresponding to a task id in the db
        user_service.save_user_event(user_data["user_id"], user_data["task_id"], user_data["event_type"], user_data["timestamp"], user_data["event_value"])
        

        return "OK -- TRIP-PLANNER", 200
    
    except Exception as e:
        print(e)
        return "Internal Server Error -- TRIP-PLANNER", 500


# websocket for chat
@sock.route('/ws',methods = ['GET'])
def chat(sock):
    while True:
        
        
        ### receive websocket data from clients
        data = user_service.chat.receive_websocket_data(sock)
        
        ### save websockets for the newly joined users
        user_service.chat.lock.acquire()
        user_service.chat.register_a_waiting_user(sock, data)
        user_service.chat.lock.release()


        ### create groups if there are waiting users
        user_service.chat.lock.acquire()
        
        
        group_id = user_service.chat.create_a_new_group(data)
        if group_id != '':
            
            user_service.set_group_main_task_instances(group_id, user_service.chat.groups[group_id]['member1'], user_service.chat.groups[group_id]['member2'])
            user_service.chat.lock.release()
            return
        
        user_service.chat.lock.release()

        
        ### register a websocket for chat and send ice-breaking message
        registered = user_service.chat.register_a_user_chat_websocket(sock, data)
        
        ### add some delay between the welcome message and ice-breaking instruction
        if registered == True:
            
            # print("two users are registered to join a chat")
            
            if 'status' in data and data['status'] == 'failed':
                break
            ### prepare for the ice-breaking step
            time.sleep(user_service.chat.ice_breaking_show_sec)
            print("ice-breaking delay ...")
           
            ### send ice-breaking samples after joining the group and see the instruction
            user_service.chat.send_ice_breaking_samples(data['roomId'])
            
            print("ice-breaking delay done.")
        
        
        
        ### handle if the user reconnect
        user_service.chat.reconnect_user(data, sock)
        
        ### receive messages from members and send them back to the group members
        user_service.chat.receive_message(data)

        ### receive initial or final decisions
        user_service.chat.submit_decision(data)
        
        ### terminate group if all tasks are completed
        if 'roomId' in data and data['type'] == 'ALL_COMPLETE':
            
            all_done = user_service.chat.update_user_self_reports(data['roomId'], data['senderId'], data['selfReports'])
            print("user self report data is received successfully.")
            
            ### after both members send this message
            if all_done > 0: 
                print("both members submitted their self repors, group score and their responses will be saved in db ...")
                decision_list = user_service.chat.retrieve_group_final_decisions(data['roomId'])
                group_score = user_service.save_group_main_study_response(data['roomId'], user_service.chat.groups[data['roomId']]['user_study'], decision_list , user_service.chat.groups[data['roomId']]['decision_times'])
                user_service.chat.terminate_group(data['roomId'], user_service.n_instances)
        


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='6000', debug=False)


    
    


