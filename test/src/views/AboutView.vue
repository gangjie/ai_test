<template>
  <div>
    <h2>关于</h2>
    <el-card shadow="hover">
      <p>这是一个基于 Vue 3 + Vite + Element Plus 的模板工程，用于快速启动 Vue 项目开发。</p>
      <h3 style="margin-top:20px">项目结构</h3>
      <el-text tag="pre" style="display:block;background:#f5f7fa;padding:16px;border-radius:6px;margin-top:12px;font-size:14px">{{ projectStructure }}</el-text>
    </el-card>
  </div>
</template>

<script setup>
const projectStructure = `├── public/              # 静态资源
├── src/
│   ├── api/             # API 请求封装
│   ├── assets/          # 样式和图片资源
│   ├── components/      # 公共组件
│   ├── composables/     # 组合式函数
│   ├── views/           # 页面视图
│   ├── router/          # 路由配置
│   ├── App.vue          # 根组件
│   └── main.js          # 应用入口
├── index.html           # HTML 入口
├── package.json         # 依赖配置
└── vite.config.js       # Vite 配置`
</script>
