<template>
  <div class="page-container">
    <header class="page-header">
      <h1>{{ title }}</h1>
      <p class="subtitle">{{ subtitle }}</p>
    </header>

    <main class="page-content">
      <div class="card">
        <h2>欢迎使用 Vue 模板</h2>
        <p>这是一个基础的 Vue 页面模板，你可以在此基础上进行修改和扩展。</p>
        <button class="btn" @click="handleClick">
          {{ buttonText }}
        </button>
      </div>

      <div class="card">
        <h2>数据展示</h2>
        <ul>
          <li v-for="item in list" :key="item.id">
            {{ item.name }}
          </li>
        </ul>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const title = ref('Vue 模板页面')
const subtitle = ref('基于 Vue 3 Composition API')
const buttonText = ref('点击我')
const list = ref([
  { id: 1, name: '功能一' },
  { id: 2, name: '功能二' },
  { id: 3, name: '功能三' },
])

const handleClick = () => {
  alert('按钮被点击了！')
}
</script>

<style scoped>
.page-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 2rem;
  color: #333;
  margin-bottom: 8px;
}

.subtitle {
  color: #666;
  font-size: 1rem;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card h2 {
  margin-bottom: 12px;
  color: #333;
}

.btn {
  margin-top: 12px;
  padding: 8px 20px;
  background: #42b883;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.btn:hover {
  background: #38a373;
}

ul {
  list-style: none;
  padding: 0;
}

li {
  padding: 8px 0;
  border-bottom: 1px solid #eee;
  color: #555;
}
</style>
