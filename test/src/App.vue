<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="nav-brand">
        <router-link to="/">Git 分析平台</router-link>
      </div>
      <el-menu
        :default-active="route.path"
        mode="horizontal"
        background-color="#42b883"
        text-color="rgba(255,255,255,0.85)"
        active-text-color="#fff"
        router
      >
        <el-menu-item index="/">首页</el-menu-item>
        <el-menu-item index="/git-repos">仓库管理</el-menu-item>
        <el-menu-item index="/commits">提交记录</el-menu-item>
        <el-menu-item index="/author-stats">人员统计</el-menu-item>
        <el-menu-item index="/file-stats">文件统计</el-menu-item>
        <el-menu-item index="/file-author-stats">人员汇总</el-menu-item>
        <el-menu-item index="/path-config">路径配置</el-menu-item>
        <el-menu-item index="/about">关于</el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }
</style>

<style scoped>
.app-container { min-height: 100vh; }
.app-header {
  display: flex; align-items: center; padding: 0 24px;
  background: #42b883; height: 60px !important;
}
.nav-brand a {
  font-size: 1.2rem; font-weight: bold; color: #fff;
  text-decoration: none; margin-right: 32px; white-space: nowrap;
}
.app-header :deep(.el-menu) {
  border-bottom: none !important; background-color: transparent;
}
.app-header :deep(.el-menu-item) { border-bottom: none !important; }
.app-header :deep(.el-menu-item:hover) { background-color: rgba(255,255,255,0.15) !important; }
.app-header :deep(.el-menu-item.is-active) {
  background-color: rgba(255,255,255,0.25) !important;
  border-bottom: 2px solid #fff !important;
}
.app-main { background: #f5f7fa; min-height: calc(100vh - 60px); padding: 24px; }
</style>
