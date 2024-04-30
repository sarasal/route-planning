<script setup>

</script>

<template>
    <b-container style="min-width: 100%">

<!--      <b-row>-->
<!--        <b-alert style="width: 100%" v-if="groupCreated" show variant="info">You will join the group chat in 10 seconds</b-alert>-->
<!--      </b-row>-->

          <b-card-text style="margin-bottom: 2rem; font-size: 20px">
            Please wait patiently in the lobby for your partner to join you. You can engage in the breathing exercises or play the game 2048 while waiting.
            If your partner does not join you within 10 minutes, please refresh the page!
          </b-card-text>
      <b-row>
        <div style="width: 100%; border: 1px solid rgb(223,223,223); border-radius: 5px; margin-bottom: 2rem">
          <b-row>
            <b-col cols="2">
              <b-card-img :src="require('@/assets/2048.jpeg')" alt="2048 Game"></b-card-img>
            </b-col>
            <b-col cols="7" style="margin-top: 1rem">
              <b-row>
                <h1>2048 Game</h1>
              </b-row>
              <b-row>
                <b-card-text>
                  You can use the arrow keys to control the movement of the block and play the game.
                </b-card-text>
              </b-row>
            </b-col>
            <b-col cols="3">
              <a class="round-button" :style="`margin-top: 2rem;background:${(showGame) ? 'rgba(213,51,51,0.65)' : '#555777'}`" href="#" @click="switchToGame()">{{(showGame) ? "Stop" : "Start"}}</a>
            </b-col>
          </b-row>
        </div>
      </b-row>

      <b-collapse id="collapse-1" class="mt-2" style="margin-bottom: 2rem">
        <b-embed
            v-if="showGame"
            type="iframe"
            aspect="16by9"
            class="game"
            :src="gameURL"
            autofocus
            scrolling="no"
        ></b-embed>
        <b-row v-if="showGif" align-h="center">
          <b-col cols="2">
            <b-pagination
                v-model="currentGif"
                :total-rows="7"
                :per-page="1"
                size="sm"
                first-number
                last-number
            ></b-pagination>
            <p> {{(currentGif <= 4) ? "Please follow the instructions provided in the exercise. " : "Please synchronize your breathing with the animation." }} </p>
            <img  :src="gifItems[currentGif]" alt="this slowpoke moves"  width="250" id = "breathingGifs" />
          </b-col>

        </b-row>

      </b-collapse>

      <b-row>
        <div style="width: 100%; border: 1px solid rgb(223,223,223); border-radius: 5px;">
          <b-row>
            <b-col cols="2">
              <b-card-img :src="require('@/assets/breathing.jpeg')" alt="2048 Game"></b-card-img>
            </b-col>
            <b-col cols="7" style="margin-top: 1rem">
              <b-row>
                <h1>Breathing Exercise</h1>
              </b-row>
              <b-row>
                <b-card-text>
                  There are multiple breathing exercises you can try out to help reduce stress and promote relaxation.
                </b-card-text>
              </b-row>
            </b-col>
            <b-col cols="3">
              <a class="round-button" :style="`margin-top: 2rem;background:${(showGif) ? 'rgba(213,51,51,0.65)' : '#555777'}`" href="#" @click="switchToGif()">{{(showGif) ? "Stop" : "Start"}}</a>
            </b-col>
          </b-row>
        </div>
      </b-row>

      </b-container>
</template>


<script>
import { register } from 'vue-advanced-chat'

import two_circle from '../assets/two_circle.gif'
import multiple_circle from '../assets/multiple_circle.gif'
import multiple_layer from '../assets/multiple_layer.gif'
import gif_478 from '../assets/478.gif'
import sync_circle from '../assets/sync_circle.gif'
import sync_star from '../assets/sync_star.gif'
import sync_polygen from '../assets/sync_polygon.gif'

register()


const gifItems = ["", two_circle, multiple_circle, multiple_layer, gif_478, sync_circle, sync_star, sync_polygen]

export default {
  name: "ChatWindow",
  props: {
    demoSession: {
      type: Boolean,
      required: true
    },
    userId: {
      type: String,
      required: true
    },
  },
  data() {
    return {
      showGame: false,
      showGif: false,
      collapseOpened: false,
      currentGif: 1,
      connection: null,
      groupCreated: false,
      intervalId: 0,
      gifItems: gifItems,
      gameURL: `${window.location.origin}/game/`,
    }
  },
  methods :{
    openCollapsed: function (game){
      this.showGame = game;
      this.showGif = !game;
      this.collapseOpened = true;
      this.$root.$emit('bv::toggle::collapse', 'collapse-1')
    },
    switchToGame() {
      if(this.collapseOpened){
        this.$root.$emit('bv::toggle::collapse', 'collapse-1')
        this.collapseOpened = false;

        if(this.showGame){
          this.showGame = false;
          return
        }
        const origin = this;
        setTimeout(()=>{
          origin.openCollapsed(true);
        }, 500);
      } else {
        this.openCollapsed(true);
      }
    },
    switchToGif(){
      if(this.collapseOpened){
        this.$root.$emit('bv::toggle::collapse', 'collapse-1')
        this.collapseOpened = false;

        if(this.showGif){
          this.showGif = false;
          return
        }
        const origin = this;
        setTimeout(()=>{
          origin.openCollapsed(false);
        }, 500);
      } else{
        this.openCollapsed(false);
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
        clearInterval(this.intervalId);
      }
    }
  },
  created() {

    // init websocket with server
    console.log("Starting connection to websocket server");
    const origin = this;
    origin.connection = new WebSocket(`${window.location.origin}/ws`.replace('https','wss')); // todo HARD code alert!
    origin.intervalId = 0;

    this.intervalId = setInterval(origin.keepAlive, 20000);

    // open websocket connection with the server
    this.connection.onopen = function (event){
      console.log("WebSocket connection opened:", event);
      const user = {
        type: 'USER_JOIN',
        user_id: origin.userId
      }
      origin.connection.send(JSON.stringify(user))
    };

    // when error occurs while trying to establish or maintain a connection
    this.connection.onerror = function (error){
      console.log("WebSocket error:", error);
    };


    // when close the connection
    this.connection.onclose = function (event){
      console.log("WebSocket connection closed:", event.code);
    };


    // different types of message will be received from the server
    this.connection.onmessage = function (event){
      console.log("WebSocket message received:", event.data)
      const serverMessage = JSON.parse(event.data);
      // const serverMessage = JSON.parse((event.data.replace(/'/g, '"')))

      if (serverMessage.type === 'GROUP_CREATED') {
        origin.groupCreated = true;

        origin.$vs.notify({
          time:9000,
          title:'Partner Joined',
          text:'You\'ve joined a group and the main tasks are starting in 10 seconds.',
          color:'primary'}
        )
        origin.cancelKeepAlive();

        setTimeout(() => {
          console.log("Trigger an event to change the room!");
          console.log("Room ID is: " + serverMessage.roomId);
          origin.connection.close();
          origin.$emit('submit', serverMessage.roomId);
        },10000);
      }
    };
  }
}
</script>

<style scoped>

.game {
  //margin-top: 5rem;
  min-width: 100%;
  min-height: 100%;
  max-height: 100%;
  overflow: hidden;
  user-focus: true;
}

.round-button {
  display:flex;
  width:10rem;
  height:10rem;
  line-height:80px;
  border: 2px solid #f5f5f5;
  border-radius: 50%;
  color:#f5f5f5;
  text-align:center;
  text-decoration:none;
  background: #555777;
  box-shadow: 0 0 3px gray;
  font-size:20px;
  font-weight:bold;
  justify-content: center;
  align-items: center;
  text-decoration: none;
}
.round-button:hover {
  background: #777555;
}

</style>