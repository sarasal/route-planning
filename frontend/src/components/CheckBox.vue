<template>
  <div>
    <b-form-group v-if="options.length !==0"
        class="bigger-txt"
        label="When I make an important decision, it is essential to ..."
    >
      <p class="smaller-txt">Please choose any relevant items that apply to you.</p>
      <b-form-checkbox
          class="normal-txt"
          v-for="(option, index) in options"
          v-model="selected[index]"
          :key="option.value"
          :value="option.value"
          name="flavour-3a"
      >
        {{ option.text }}
      </b-form-checkbox>
    </b-form-group>

  </div>
</template>

<script>
export default {
  name: "CheckBox",
  props:{
    questions: {
      type: Array,
      required: true
    },
  },
  data() {
    return {
      options: [],
      selected: [],
    }
  },
  watch:{
    selected: function (val){
      this.$emit('selectedArrayChanged', val);
    }
  },
  created: function (){
    const options = [];
    for (let i = 0; i < this.questions.length; i++) {
      if(this.questions[i].likert_scale === 1){
        options.push({
          key: this.questions[i].question_id,
          text: this.questions[i].question,
        })
      }
    }
    this.options = options;
    this.selected = new Array(options.length).fill(-1)
  }
}
</script>

<style scoped>
.bigger-txt {
  font-size: 28px;
}
.smaller-txt {
  font-size: 20px;
}
.normal-txt {
  font-size: 16px;
}
</style>