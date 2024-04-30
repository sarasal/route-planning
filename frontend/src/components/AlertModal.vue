<script setup>
</script>

<template>
  <b-modal size="lg" centered :id="id" no-close-on-backdrop no-close-on-esc hide-header-close @ok="submit">
    <p>{{text}}</p>
    <template #modal-footer="{ ok }">
      <!-- Emulate built in modal footer ok and cancel button actions -->
      <b-button variant="success" @click="ok">
        {{btnTxt}}
      </b-button>
    </template>
  </b-modal>
</template>

<script>
export default {
  name: "QuestionModal",
  props: {
    btnTxt: {
      type: String,
      required: true
    },
    text: {
      type: String,
      required: true
    },
    id: {
      type: String,
      required: true
    },
  },
  methods: {
    submit: function (){
      this.$emit('submit');
    }
  }
}
</script>

<style scoped>

</style>