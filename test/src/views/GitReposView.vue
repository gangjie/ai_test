<template>
  <div>
    <h2>Git 仓库管理</h2>

    <el-card shadow="hover">
      <template #header><span>克隆仓库</span></template>
      <el-form :model="cloneForm" label-width="110px" style="max-width: 700px">
        <el-form-item label="仓库地址" required>
          <el-input v-model="cloneForm.url" placeholder="https://github.com/user/repo.git" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="分支"><el-input v-model="cloneForm.branch" placeholder="默认分支" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="目录名"><el-input v-model="cloneForm.directory" placeholder="自动解析" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="浅克隆深度"><el-input-number v-model="cloneForm.depth" :min="1" controls-position="right" style="width:100%" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Git 账号"><el-input v-model="cloneForm.username" placeholder="可选" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Git 密码/Token"><el-input v-model="cloneForm.password" type="password" show-password placeholder="可选" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-alert title="提示：GitHub 已禁用密码认证，请使用 Personal Access Token 作为密码。Token 创建路径：GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens" type="info" show-icon :closable="false" style="margin-bottom: 12px" />
          <el-button type="primary" @click="handleClone" :loading="cloning">克隆仓库</el-button>
        </el-form-item>
      </el-form>
      <el-alert v-if="cloneMsg" :title="cloneMsg" :type="cloneSuccess ? 'success' : 'error'" show-icon :closable="false" style="margin-top: 8px" />
    </el-card>

    <el-card shadow="hover" style="margin-top: 20px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>已克隆仓库</span>
          <el-button size="small" @click="loadRepos">刷新</el-button>
        </div>
      </template>
      <el-table :data="repos" v-loading="reposLoading" stripe>
        <el-table-column prop="name" label="仓库名称" />
        <el-table-column prop="path" label="本地路径" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-popconfirm :title="`确定删除仓库 &quot;${row.name}&quot; 吗？`" @confirm="handleDelete(row.name)">
              <template #reference><el-button type="danger" size="small">删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { ElMessage } from 'element-plus'

const cloneForm = ref({ url: '', branch: '', directory: '', depth: null, username: '', password: '' })
const cloning = ref(false)
const cloneMsg = ref('')
const cloneSuccess = ref(false)

const repos = ref([])
const reposLoading = ref(false)

const loadRepos = async () => {
  reposLoading.value = true
  try {
    const data = await api.listRepos()
    repos.value = data.repos || data.items || (Array.isArray(data) ? data : [])
  } catch (e) { console.error(e) } finally { reposLoading.value = false }
}

const handleClone = async () => {
  cloning.value = true; cloneMsg.value = ''
  try {
    const body = { url: cloneForm.value.url }
    if (cloneForm.value.branch) body.branch = cloneForm.value.branch
    if (cloneForm.value.directory) body.directory = cloneForm.value.directory
    if (cloneForm.value.depth) body.depth = cloneForm.value.depth
    if (cloneForm.value.username) body.username = cloneForm.value.username
    if (cloneForm.value.password) body.password = cloneForm.value.password
    const res = await api.cloneRepo(body)
    cloneSuccess.value = res.success; cloneMsg.value = res.message
    if (res.success) loadRepos()
  } catch (e) { cloneSuccess.value = false; cloneMsg.value = '克隆失败: ' + e.message }
  finally { cloning.value = false }
}

const handleDelete = async (name) => {
  try { await api.deleteRepo(name); loadRepos() }
  catch (e) { ElMessage.error('删除失败: ' + e.message) }
}

onMounted(loadRepos)
</script>
