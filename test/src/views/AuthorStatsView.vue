<template>
  <div>
    <h2>人员统计</h2>

    <el-card shadow="hover">
      <el-form inline>
        <el-form-item label="仓库名称">
          <el-select v-model="repoName" placeholder="请选择仓库" style="width:200px">
            <el-option v-for="r in repoList" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" @click="loadStats" :disabled="!repoName">查询</el-button></el-form-item>
      </el-form>
    </el-card>

    <template v-if="data">
      <el-card shadow="hover" style="margin-top:20px">
        <template #header><span>统计概览</span></template>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="参与人员" :value="data.total_authors" />
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="hover" style="margin-top:20px">
        <template #header><span>人员详情</span></template>
        <el-table :data="data.authors" stripe>
          <el-table-column prop="author_name" label="姓名" />
          <el-table-column prop="author_email" label="邮箱" />
          <el-table-column prop="commit_count" label="提交次数" width="100" align="center" />
          <el-table-column label="新增行数" width="110" align="center">
            <template #default="{ row }"><span style="color:#42b883">+{{ row.total_insertions }}</span></template>
          </el-table-column>
          <el-table-column label="删除行数" width="110" align="center">
            <template #default="{ row }"><span style="color:#e74c3c">-{{ row.total_deletions }}</span></template>
          </el-table-column>
          <el-table-column prop="total_files_changed" label="变更文件数" width="120" align="center" />
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
const data = ref(null)
const loading = ref(false)
const error = ref('')

const loadStats = async () => {
  if (!repoName.value) return
  loading.value = true; error.value = ''
  try { data.value = await api.getAuthorStats(repoName.value) }
  catch (e) { error.value = '查询失败: ' + e.message }
  finally { loading.value = false }
}
</script>
