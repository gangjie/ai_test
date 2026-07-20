<template>
  <div>
    <el-row :gutter="20" style="margin-bottom:24px">
      <el-col :span="24" style="text-align:center;padding:40px 0">
        <h1 style="font-size:2rem;color:#333;margin-bottom:8px">欢迎使用 Git 分析平台</h1>
        <p style="color:#666">基于 Vue 3 + Vite + Element Plus + Vue Router 构建</p>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="8" v-for="f in features" :key="f.title">
        <el-card shadow="hover" style="text-align:center;margin-bottom:20px">
          <h3 style="color:#42b883;margin-bottom:8px">{{ f.title }}</h3>
          <p style="color:#666;font-size:14px">{{ f.desc }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" style="text-align:center">
      <h2 style="color:#42b883">Hello Vue 3!</h2>
      <p style="color:#666;margin-bottom:12px">编辑 <code>src/components/HelloWorld.vue</code> 来测试热更新。</p>
      <el-button type="primary" @click="count++">计数: {{ count }}</el-button>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const features = ref([
  { title: 'Vue 3', desc: '使用 Composition API 和最新特性' },
  { title: 'Vite', desc: '极速的开发构建工具' },
  { title: 'Element Plus', desc: '企业级 UI 组件库' },
])

const count = ref(0)
</script>
