<template>
  <div class="hello">
    <h2>{{ msg }}</h2>
    <p>编辑 <code>src/components/HelloWorld.vue</code> 来测试热更新。</p>
    <button @click="count++">计数: {{ count }}</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  msg: {
    type: String,
    default: 'Hello!'
  }
})

const count = ref(0)
</script>

<style scoped>
.hello {
  text-align: center;
  padding: 24px;
  background: #f0faf5;
  border-radius: 8px;
}
.hello h2 {
  color: #42b883;
}
code {
  background: #e8e8e8;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9rem;
}
button {
  margin-top: 16px;
  padding: 8px 20px;
  background: #42b883;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}
button:hover {
  background: #38a373;
}
</style>
