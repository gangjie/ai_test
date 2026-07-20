<template>
  <div>
    <h2>文件统计</h2>

    <el-card shadow="hover">
      <el-form inline>
        <el-form-item label="仓库名称">
          <el-select v-model="repoName" placeholder="请选择仓库" style="width:200px">
            <el-option v-for="r in repoList" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="限制条数">
          <el-select v-model="limit" style="width:100px">
            <el-option :value="20" label="20" /><el-option :value="50" label="50" /><el-option :value="100" label="100" />
          </el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" @click="loadStats" :disabled="!repoName">查询</el-button></el-form-item>
      </el-form>
    </el-card>

    <template v-if="data">
      <el-card shadow="hover" style="margin-top:20px">
        <template #header><span>统计概览</span></template>
        <el-row :gutter="20">
          <el-col :span="6"><el-statistic title="变更文件数" :value="data.total_files" /></el-col>
        </el-row>
      </el-card>

      <el-card shadow="hover" style="margin-top:20px">
        <template #header><span>文件详情</span></template>
        <el-table :data="data.files" stripe>
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="file_path" label="文件路径" />
          <el-table-column prop="change_count" label="变更次数" width="100" align="center" />
          <el-table-column label="新增行数" width="110" align="center">
            <template #default="{ row }"><span style="color:#42b883">+{{ row.total_insertions }}</span></template>
          </el-table-column>
          <el-table-column label="删除行数" width="110" align="center">
            <template #default="{ row }"><span style="color:#e74c3c">-{{ row.total_deletions }}</span></template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <p v-if="loading" style="text-align:center;color:#999;padding:20px">加载中...</p>
    <el-alert v-if="error" :title="error" type="error" show-icon style="margin-top:16px" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/api'
import { useRepoList } from '@/composables/useRepoList'

const { repoList } = useRepoList()
const repoName = ref('')
const limit = ref(50)
const data = ref(null)
const loading = ref(false)
const error = ref('')

const loadStats = async () => {
  if (!repoName.value) return
  loading.value = true; error.value = ''
  try { data.value = await api.getFileStats(repoName.value, limit.value) }
  catch (e) { error.value = '查询失败: ' + e.message }
  finally { loading.value = false }
}
</script>
