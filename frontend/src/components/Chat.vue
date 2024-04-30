<script setup>
  import QuestionModal from '../components/QuestionModal.vue'
  import AlertModal from '../components/AlertModal.vue'

</script>

<template>

  <div class="chat-container">
      <vue-advanced-chat
          :current-user-id="userId"
          :rooms="JSON.stringify(rooms)"
          :messages="JSON.stringify(messages)"
          :single-room="true"
          show-files="false"
          show-audio="false"
          show-emojis="false"
          show-new-messages-divider="false"
          emojis-suggestion-enabled="false"
          :messages-loaded="messagesLoaded"
          :message-actions="JSON.stringify(messageActions)"
          :templates-text="JSON.stringify(templatesText)"
          @send-message="sendMessage"

      />
    <QuestionModal id="initial-decision-modal" :questions="singleQuestion" :options="singleQuestionOptions" @submit="setInitialDecisionReport"></QuestionModal>
    <QuestionModal id="final-decision-modal" :questions="singleQuestion" :options="singleQuestionOptions" @submit="setFinalDecisionReport"></QuestionModal>
    <QuestionModal id="input-decision-modal" :questions="multipleQuestions" :options="multipleQuestionOptions" @submit="setInputDecisionReport"></QuestionModal>

    <AlertModal id="refresh-page-modal"  :text="refreshText" btnTxt="Refresh"></AlertModal>
    <AlertModal id="terminate-study-modal" :text="terminateText" btnTxt="End" @submit="terminateStudy"></AlertModal>
  </div>


</template>


<script>
import { register } from 'vue-advanced-chat'

register()

// const taskList = ["51", "52", "53"]
// taskList = list of task ids which are from get_group_task_instances API response


// *** confidence
// To what extent do you have confidence in your submitted decision?

// *** input effect
// To what extent was your final decision influenced by your input in the discussion?
// To what extent was your final decision influenced by your partner’s input in the discussion?
// To what extent was your final decision influenced by AI advice in the discussion?



export default {
  name: "ChatWindow",
  props: {
    demoSession: {
      type: Boolean,
      required: true
    },
    onBoarding: {
      type: Boolean,
      required: false,
      default: false
    },
    userId: {
      type: String,
      required: true
    },
    roomId: {
      type: String,
      required: true
    },
    taskIdList: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      singleQuestion: [
          'To what extent do you have confidence in your submitted decision?'
      ],
      singleQuestionOptions: [
          'Not at all confident', 'Slightly unconfident', 'Moderately unconfident', 'Neither confident nor unconfident', 'Moderately confident', 'Confident', 'Very confident'
      ],
      multipleQuestions: [
          'To what extent was your final decision influenced by your input in the discussion?',
          'To what extent was your final decision influenced by your partner’s input in the discussion?',
          'To what extent was your final decision influenced by AI advice in the discussion?',
      ],
      multipleQuestionOptions: [
        'Not at all influential', 'Slightly uninfluential', 'Moderately uninfluential', 'Neither influential nor uninfluential', 'Moderately influential', 'Influential', 'Highly influential'
      ],
      refreshText: "You seem to be disconnected. Please refresh the page to reestablish the connection.",
      terminateText: "It looks like your partner is experiencing difficulties with reconnecting. You have done a good job though, thank you for your participation. You can exit the task now by clicking the following button." ,
      currentTaskId: 0,
      connection: null,
      groupDisconnect: false,
      intervalId: 0,
      readyToSubmit: false,
      messagesLoaded: false,
      templatesText:[
        {
          tag: 'help',
          text: '/help'
        },
        {
          tag: 'initial-submit',
          text: '/initial-submit'
        },
        {
          tag: 'final-submit',
          text: '/final-submit'
        }
      ],
      selfReports:[],
      messageActions: [],
      rooms: [],
      messages: []
    }
  },
  methods :{

    sendMessage: function (arg) {
      if (this.onBoarding){
        return
      }

      let messageType = 'GROUP_MESSAGE';

      // error handling

      if (this.readyToSubmit === true){
        messageType = 'SUBMIT_DECISION';
      }

      const now_milisec = Date.now()
      const message = this.createGroupMessage(messageType, arg.detail[0].content, this.userId, this.roomId, now_milisec.toString(), this.taskIdList[this.currentTaskId ])

      this.connection.send(message);
    },
    getChatDate: function (){
      const current = new Date();
      const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
      return `${current.getDate()}`+ " " + monthNames[current.getMonth()];
    },

    getChatTime: function (messageTime){
      const current = new Date(parseInt(messageTime));
      return `${current.getHours()}` + ":" + `${current.getMinutes()}`;
    },

    createGroupMessage: function (messageType, messageContent, messageSenderId, messageRoomId, messageSenderTime, currentTaskId){
      if (this.onBoarding){
        return
      }

      const message = {
        type: messageType,
        content: messageContent,
        senderId: messageSenderId,
        roomId: messageRoomId,
        senderTime: messageSenderTime,
        taskId: currentTaskId
      }
      return JSON.stringify(message);
    },

    parseServerMessage: function (serverMessage, welcome){
      if (this.onBoarding){
        return
      }

      let message = "";
      if (welcome === true){
        message = {
          _id: '8888',
          content: serverMessage.content,
          senderId: '1',
          date: this.getChatDate(),
          timestamp: this.getChatTime(serverMessage.senderTime),
          system: true
        }
      }
      else {
        message = {
          _id: '8888',
          content: serverMessage.content,
          senderId: '1',
          system: true
        }
      }

      return message;
    },

    parseGroupMessage: function (serverMessage){
      if (this.onBoarding){
        return
      }

      return  {
        _id: '8888',
        content: serverMessage.content,
        senderId: serverMessage.senderId,
        timestamp: this.getChatTime(serverMessage.senderTime),
        disableActions: false,
        disableReactions: true
      }

    },

    parseReconnectMessage: function (serverMessage){
      if (this.onBoarding){
        return
      }

      let unsentMessages = [];
      let sentMessages = [];

      //  ****************** set unsent messages
      // check the type of the message
      for (let i = 0; i < serverMessage.unsentMessages.length; i++){
        if (serverMessage.unsentMessages[i].type === 'GROUP_CREATED'){
          continue;
        }
        if (serverMessage.unsentMessages[i].type === 'INITIAL_DECISION_SUBMITTED'){
          this.$bvModal.show('initial-decision-modal')
          continue;
        }

        // check the type of message whether it is group message or server message, then call the corresponding parsing function for that
        let oneMessage = {}
        if (serverMessage.unsentMessages[i]['senderId'] === '1'){
          oneMessage = this.parseServerMessage(serverMessage.unsentMessages[i], false)
        }
        else{
          oneMessage = this.parseGroupMessage(serverMessage.unsentMessages[i])
        }

        unsentMessages.push(oneMessage)
      }


      //  ******************** set sent messages
      // check the type of the message
      for (let i = 0; i < serverMessage.sentMessages.length; i++){
        if (serverMessage.sentMessages[i].type === 'GROUP_CREATED' || serverMessage.sentMessages[i].type === 'INITIAL_DECISION_SUBMITTED'){
          continue;
        }

        // check the type of message whether it is group message or server message, then call the corresponding parsing function for that
        let oneMessage = {}
        if (serverMessage.sentMessages[i]['senderId'] === '1'){
          let isWelcome = false;
          if (serverMessage.sentMessages[i].type === 'CHAT_JOINED'){
            isWelcome = true;
          }
          oneMessage = this.parseServerMessage(serverMessage.sentMessages[i], isWelcome)
        }
        else{
          oneMessage = this.parseGroupMessage(serverMessage.sentMessages[i])
        }

        sentMessages.push(oneMessage)
      }

      // console.log("before notification parsing")

      //  ********* notification server message
      let notificationMessage = this.parseServerMessage(serverMessage, false)


      return {
        notification: notificationMessage,
        unsent: unsentMessages,
        sent: sentMessages,
        status: serverMessage.status
      }

    },

    createNewRoom: function (serverMessage){
      if (this.onBoarding){
        return
      }

      const newRoom = []
      newRoom.push({
        roomId: serverMessage.roomId,
        roomName: 'Discussion Room',
        users: [{_id: serverMessage.member1, username: serverMessage.member1}, {_id: serverMessage.member2, username: serverMessage.member2}]
      });
      return newRoom
    },
    setInitialDecisionReport: function (val){
      this.selfReports[this.currentTaskId].initial_confidence = val[0];
      localStorage.setItem('self-reports', JSON.stringify(this.selfReports))
      localStorage.setItem("show-initial-modal", "false");
    },
    setFinalDecisionReport: function (val){
      this.selfReports[this.currentTaskId-1].final_confidence = val[0];
      localStorage.setItem('self-reports', JSON.stringify(this.selfReports))
      localStorage.setItem("show-final-modal", "false");
      setTimeout(()=> {
        localStorage.setItem("show-input-modal", "true");
        this.$bvModal.show('input-decision-modal')
      }, 200);
    },
    setInputDecisionReport: function (val){
      this.selfReports[this.currentTaskId-1].self_input = val[0];
      this.selfReports[this.currentTaskId-1].partner_input = val[1];
      this.selfReports[this.currentTaskId-1].ai_input = val[2];
      localStorage.setItem('self-reports', JSON.stringify(this.selfReports))
      localStorage.setItem("show-input-modal", "false");

      if(this.currentTaskId === this.taskIdList.length){
        const message = {
          type: 'ALL_COMPLETE',
          roomId: this.roomId,
          senderId: this.userId,
          selfReports: this.selfReports,
        }

        this.cancelKeepAlive();
        this.connection.send(JSON.stringify(message));
        this.$emit('finished');
      }
    },
    generateEmptySelfReports: function (){
      let reports = []
      for (let i = 0; i < this.taskIdList.length; i++) {
        reports.push({
          task_id: this.taskIdList[i],
          initial_confidence: -1,
          final_confidence: -1,
          self_input: -1,
          partner_input: -1,
          ai_input: -1,
        });
      }
      return reports;
    },
    terminateStudy: function (){
      window.location.href = String(import.meta.env.VITE_PROLIFIC_ACCEPT_LINK).toLowerCase();
    },
    generateDummyMessage: function (content, senderId){
      if (senderId === 1){
        return {
          _id: '8888',
          content: content,
          senderId: '1',
          system: true
        }
      }
      return {
        _id: '8888',
        content: content,
        senderId: senderId,
        timestamp: this.getChatTime(new Date().getTime()),
        disableActions: false,
        disableReactions: true
      }
    },
    // move it to mixin
    keepAlive: function (){
      if (this.connection.readyState === this.connection.OPEN) {
        this.connection.send(JSON.stringify({
          type : 'PING',
          senderId : this.userId,
        }));
      }
    },
    // move it to mixin
    cancelKeepAlive: function () {
      if (this.intervalId) {
        clearTimeout(this.intervalId);
      }
    }
  },
  created() {
    if (this.onBoarding){
      const newRoom = []
      newRoom.push({
        roomId: 10,
        roomName: 'Discussion Room',
        users: [
          {
            _id: "111",
            username: "111"
          },
          {
            _id: this.userId,
            username: this.userId
          }
        ]
      });

      this.rooms = newRoom;

      this.messages.push(this.generateDummyMessage("You have both made your initial choices. You have identified the best route to be route 2, and your partner has identified it to be route 5. The AI system is proposing route 6 as the best route. Please discuss this with your partner again and aim to reach a consensus on your final decision. You can run the \\final-submit command to finalize the decision once a consensus is reached.", 1));
      this.messages.push(this.generateDummyMessage("we didn't check route 6 together. Let's figure it out why route 6 is suggested", this.userId));
      this.messages.push(this.generateDummyMessage("the cost of route 6 is beyond the predefined budget", "111"));
      this.messages.push(this.generateDummyMessage("I still think route 5 is the best route", "111"));
      this.messages.push(this.generateDummyMessage("can you explain your rationale?", this.userId));



      setTimeout(() => {
        this.messagesLoaded = true;
      }, 100)

      return;
    }

    this.currentTaskId = parseInt(localStorage.current_task_index);
    this.selfReports =  JSON.parse(localStorage.getItem('self-reports' ));
    if(this.selfReports === null){
      this.selfReports = this.generateEmptySelfReports();
    }

    // init websocket with server
    console.log("Starting connection to websocket server");
    const origin = this;
    origin.connection = new WebSocket(`${window.location.origin}/ws`.replace('https','wss'));
    origin.intervalId = 0;

    this.intervalId = setInterval(origin.keepAlive, 20000);

    // open websocket connection with the server
    this.connection.onopen = function (event){
      console.log("WebSocket connection opened:", event);
      const user = {
        type: 'USER_CHAT',
        user_id: origin.userId,
        roomId: origin.roomId,
      }
      origin.connection.send(JSON.stringify(user))
      console.log("DONE and DONE and DONE!!!!!")
    };

    // when error occurs while trying to establish or maintain a connection
    this.connection.onerror = function (error){
      console.log("WebSocket error:", error);
    };


    // when close the connection
    this.connection.onclose = function (event){
      console.log("WebSocket connection closed:", event.code);
      if (origin.groupDisconnect === false){
        origin.$bvModal.show('refresh-page-modal')
      }
    };


    // different types of message will be received from the server
    this.connection.onmessage = function (event){
      console.log("WebSocket message received:", event.data)
      const serverMessage = JSON.parse(event.data);
      // const serverMessage = JSON.parse((event.data.replace(/'/g, '"')))


      if (serverMessage.type === 'GROUP_MESSAGE' ){
        const message = origin.parseGroupMessage(serverMessage);
        origin.messages.push(message);
      }
      else if (serverMessage.type === 'CHAT_JOINED'){
        origin.rooms = origin.createNewRoom(serverMessage)
        // origin.roomId = serverMessage.roomId;
        const message = origin.parseServerMessage(serverMessage, true)
        origin.messages.push(message);

        setTimeout(() => {
          origin.messagesLoaded = true;
        }, 100)
      }
      else if (serverMessage.type === 'SELF_RECONNECT'){
        origin.rooms = origin.createNewRoom(serverMessage);
        const messageObj = origin.parseReconnectMessage(serverMessage);

        for (let i = 0; i < messageObj.sent.length; i++){
          origin.messages.push(messageObj.sent[i]);
        }

        if (messageObj.status === 'READY_INITIAL_SUBMIT' || messageObj.status === 'READY_FINAL_SUBMIT'){
          origin.readyToSubmit = true;
        }


        setTimeout(() => {
          origin.messagesLoaded = true;
        }, 100)

        origin.messages.push(messageObj.notification);

        for (let i = 0; i < messageObj.unsent.length; i++){
          origin.messages.push(messageObj.unsent[i]);
        }

      }
      else if (serverMessage.type === 'DISCONNECT_LIMIT_EXCEED'){
        console.log("group member did not recover")
        origin.groupDisconnect = true;
        origin.$bvModal.show('terminate-study-modal');
      }
      else if (serverMessage.type === 'INITIAL_DECISION_SUBMITTED'){
        localStorage.setItem("show-initial-modal", "true");
        origin.$bvModal.show('initial-decision-modal')
      }
      else if (  serverMessage.type === 'GROUP_DISCONNECT' || serverMessage.type === 'GROUP_RECONNECT' || serverMessage.type === 'INSTRUCTION' || serverMessage.type === 'ICE_BREAKING' || serverMessage.type === 'WARNING' || serverMessage.type ==='READY_INITIAL_SUBMIT' || serverMessage.type ==='WAITING'|| serverMessage.type === 'SHOW_INITIAL_DECISION' || serverMessage.type ==='READY_FINAL_SUBMIT' || serverMessage.type ==='STATUS_CHANGE' || serverMessage.type === 'COMPLETED' || serverMessage.type === 'START_TASK'){
        const message = origin.parseServerMessage(serverMessage)
        origin.messages.push(message);

        if (serverMessage.type ==='READY_INITIAL_SUBMIT' || serverMessage.type ==='READY_FINAL_SUBMIT'){
          origin.readyToSubmit = true;
        }

        if (serverMessage.type === 'SHOW_INITIAL_DECISION' || serverMessage.type ==='STATUS_CHANGE' || serverMessage.type === 'COMPLETED'){
          origin.readyToSubmit = false;
        }

        // False comment, ignore it please: it should be done when the user click the next task button and then call the go-next-task api
        if(serverMessage.type === 'COMPLETED'){
          origin.currentTaskId = origin.currentTaskId + 1;
          if(origin.currentTaskId < origin.taskIdList.length){
            const message = {
              type: 'START_TASK',
              roomId: origin.roomId
            }
            origin.messages = [];
            origin.connection.send(JSON.stringify(message));
            origin.$emit('nextTask');
          }
          localStorage.setItem("show-final-modal", "true");
          origin.$bvModal.show('final-decision-modal')
        }

      }

    };
  },
  mounted: function (){
    if(localStorage.getItem("show-initial-modal") !== null && localStorage.getItem("show-initial-modal").toLowerCase() === "true"){
      this.$bvModal.show('initial-decision-modal');
    }
    if(localStorage.getItem("show-final-modal") !== null && localStorage.getItem("show-final-modal").toLowerCase() === "true"){
      this.$bvModal.show('final-decision-modal');
    }
    if(localStorage.getItem("show-input-modal") !== null && localStorage.getItem("show-input-modal").toLowerCase() === "true"){
      this.$bvModal.show('input-decision-modal');
    }
  }
}
</script>

<style scoped>

.chat-container {
  margin: 25px 50px;
}

.game {
  margin-top: 5rem;
  width: 100%;
  min-height: 30rem;
}

</style>