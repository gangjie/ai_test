<template>
  <div>
    <h2>文件路径配置</h2>

    <el-card shadow="hover">
      <el-form :model="createForm" inline>
        <el-form-item label="仓库名称">
          <el-select v-model="createForm.repo_name" placeholder="请选择仓库" style="width:200px">
            <el-option v-for="r in repoList" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="路径模式">
          <el-input v-model="createForm.path_pattern" placeholder="如 src/、modules/core/" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="createForm.is_enabled">启用</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleCreate">新增</el-button>
        </el-form-item>
        <el-form-item>
          <el-upload :show-file-list="false" :before-upload="handleUpload" :disabled="!createForm.repo_name || uploading">
            <el-button type="success" :loading="uploading">选择文件上传</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadConfigs" :disabled="!createForm.repo_name">查询</el-button>
        </el-form-item>
      </el-form>
      <el-alert v-if="createMsg" :title="createMsg" :type="createSuccess ? 'success' : 'error'" show-icon :closable="false" style="margin-top:8px" />
      <el-alert v-if="uploadMsg" :title="uploadMsg" :type="uploadSuccess ? 'success' : 'error'" show-icon :closable="true" style="margin-top:8px" />
    </el-card>

    <el-card shadow="hover" style="margin-top:20px" v-if="uploadResult">
      <template #header><span>导入结果</span></template>
      <el-row :gutter="20">
        <el-col :span="8"><el-statistic title="总条目数" :value="uploadResult.total" /></el-col>
        <el-col :span="8"><el-statistic title="成功创建" :value="uploadResult.created" /></el-col>
        <el-col :span="8"><el-statistic title="跳过" :value="uploadResult.skipped" /></el-col>
      </el-row>
      <el-table :data="uploadResult.items" stripe style="margin-top:12px">
        <el-table-column prop="pattern" label="路径模式" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'created' ? 'success' : row.status === 'skipped' ? 'warning' : 'danger'" size="small">{{ row.status === 'created' ? '创建' : row.status === 'skipped' ? '跳过' : '失败' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" />
      </el-table>
    </el-card>

    <el-card shadow="hover" style="margin-top:20px" v-if="configs.length > 0">
      <template #header><span>配置列表 (共 {{ total }} 条)</span></template>
      <el-table :data="configs" stripe>
        <el-table-column prop="path_pattern" label="路径模式" />
        <el-table-column prop="repo_name" label="仓库名称" width="150" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">{{ row.is_enabled ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }"><span style="color:#888;font-size:13px">{{ formatTime(row.created_at) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="startEdit(row)">编辑</el-button>
            <el-popconfirm :title="`确定删除路径配置 &quot;${row.path_pattern}&quot; 吗？`" @confirm="handleDelete(row.repo_name, row.path_pattern)">
              <template #reference><el-button type="danger" size="small">删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="编辑路径配置" width="420px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="路径模式"><el-input v-model="editForm.path_pattern" /></el-form-item>
        <el-form-item><el-checkbox v-model="editForm.is_enabled">启用</el-checkbox></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate">保存</el-button>
      </template>
    </el-dialog>

    <p v-if="loading" style="text-align:center;color:#999;padding:20px">加载中...</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/api'
import { useRepoList } from '@/composables/useRepoList'
import { ElMessage } from 'element-plus'

const { repoList } = useRepoList()

const createForm = ref({ repo_name: '', path_pattern: '', is_enabled: true })
const createMsg = ref('')
const createSuccess = ref(false)

const configs = ref([])
const total = ref(0)
const loading = ref(false)

const uploading = ref(false)
const uploadMsg = ref('')
const uploadSuccess = ref(false)
const uploadResult = ref(null)

const dialogVisible = ref(false)
const editingRepo = ref('')
const editingPattern = ref('')
const editForm = ref({ path_pattern: '', is_enabled: true })

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const loadConfigs = async () => {
  if (!createForm.value.repo_name) return
  loading.value = true
  try {
    const data = await api.listPathConfigs(createForm.value.repo_name)
    configs.value = data.items || []; total.value = data.total || 0
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const handleCreate = async () => {
  if (!createForm.value.repo_name) { createMsg.value = '请选择仓库名称'; return }
  if (!createForm.value.path_pattern) { createMsg.value = '请输入路径模式'; return }
  createMsg.value = ''
  try {
    await api.createPathConfig(createForm.value)
    createSuccess.value = true; createMsg.value = '创建成功'
    loadConfigs()
  } catch (e) { createSuccess.value = false; createMsg.value = '创建失败: ' + e.message }
}

const startEdit = (c) => {
  editingRepo.value = c.repo_name
  editingPattern.value = c.path_pattern
  editForm.value = { path_pattern: c.path_pattern, is_enabled: c.is_enabled }
  dialogVisible.value = true
}

const handleUpdate = async () => {
  if (!editForm.value.path_pattern) { ElMessage.error('路径模式不能为空'); return }
  try {
    await api.updatePathConfig(editingRepo.value, editingPattern.value, editForm.value)
    dialogVisible.value = false
    loadConfigs()
  } catch (e) { ElMessage.error('更新失败: ' + e.message) }
}

const handleDelete = async (repoName, pattern) => {
  try {
    await api.deletePathConfig(repoName, pattern)
    loadConfigs()
  } catch (e) { ElMessage.error('删除失败: ' + e.message) }
}

const handleUpload = async (file) => {
  if (!createForm.value.repo_name) { ElMessage.warning('请先选择仓库名称'); return false }
  uploading.value = true; uploadMsg.value = ''; uploadResult.value = null
  try {
    const res = await api.uploadPathConfig(createForm.value.repo_name, file)
    uploadSuccess.value = true; uploadMsg.value = `导入完成：成功 ${res.created} 条，跳过 ${res.skipped} 条`
    uploadResult.value = res
    loadConfigs()
  } catch (e) {
    uploadSuccess.value = false; uploadMsg.value = '上传失败: ' + e.message
  } finally { uploading.value = false }
  return false // 阻止自动上传
}
</script>
