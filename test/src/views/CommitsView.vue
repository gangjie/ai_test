<template>
  <div>
    <h2>提交记录分析</h2>

    <el-card shadow="hover">
      <template #header><span>筛选条件</span></template>
      <el-form :model="filters" inline>
        <el-form-item label="仓库名称">
          <el-select v-model="filters.repo_name" placeholder="请选择仓库" style="width:200px" @change="loadCommits">
            <el-option v-for="r in repoList" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="提交者">
          <el-input v-model="filters.author" placeholder="按提交者筛选" clearable />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="filters.start_time" type="datetime" placeholder="选择开始时间" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="filters.end_time" type="datetime" placeholder="选择结束时间" />
        </el-form-item>
        <el-form-item label="每页条数">
          <el-select v-model="filters.limit" style="width:100px">
            <el-option :value="20" label="20" /><el-option :value="50" label="50" /><el-option :value="100" label="100" />
          </el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" @click="loadCommits">查询</el-button></el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="hover" style="margin-top:20px" v-if="filters.repo_name">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>分析状态</span>
          <div>
            <el-button size="small" @click="loadStatus">刷新状态</el-button>
            <el-button size="small" type="primary" @click="handleTrigger" :loading="triggering">触发分析</el-button>
          </div>
        </div>
      </template>
      <div v-if="status" style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">
        <el-tag :type="statusTagType">{{ status.status }}</el-tag>
        <span v-if="status.total_commits">总提交数: {{ status.total_commits }}</span>
        <span v-if="status.analyzed_at" style="color:#999;font-size:13px">分析时间: {{ formatTime(status.analyzed_at) }}</span>
        <span v-if="status.message" style="color:#999;font-size:13px">{{ status.message }}</span>
      </div>
      <el-input v-if="showTriggerInput" v-model="repoPath" placeholder="仓库本地路径" style="margin-top:12px;max-width:400px" />
    </el-card>

    <el-card shadow="hover" style="margin-top:20px">
      <template #header><span>提交记录 (共 {{ total }} 条)</span></template>
      <el-table :data="commits" v-loading="loading" stripe @row-click="toggleExpand">
        <el-table-column label="Hash" width="100">
          <template #default="{ row }"><code style="color:#42b883">{{ row.commit_hash?.substring(0, 8) }}</code></template>
        </el-table-column>
        <el-table-column prop="author_name" label="提交者" width="120" />
        <el-table-column prop="commit_message" label="提交信息" show-overflow-tooltip />
        <el-table-column label="时间" width="170">
          <template #default="{ row }"><span style="color:#888;font-size:13px">{{ formatTime(row.commit_time) }}</span></template>
        </el-table-column>
        <el-table-column prop="files_changed" label="文件数" width="80" align="center" />
        <el-table-column label="+/-" width="120">
          <template #default="{ row }"><span style="color:#42b883">+{{ row.insertions }}</span> <span style="color:#e74c3c">-{{ row.deletions }}</span></template>
        </el-table-column>
      </el-table>

      <div v-if="expandedRow" style="margin-top:16px">
        <h4 style="margin-bottom:8px;color:#555">{{ expandedRow.commit_hash?.substring(0,8) }} 文件变更</h4>
        <el-table :data="expandedRow.file_changes || []" size="small" stripe>
          <el-table-column prop="file_path" label="文件路径" />
          <el-table-column label="+" width="80"><template #default="{ row }"><span style="color:#42b883">+{{ row.insertions }}</span></template></el-table-column>
          <el-table-column label="-" width="80"><template #default="{ row }"><span style="color:#e74c3c">-{{ row.deletions }}</span></template></el-table-column>
          <el-table-column prop="total_lines" label="总行数" width="80" />
        </el-table>
      </div>

      <div v-if="total > filters.limit" style="display:flex;justify-content:center;margin-top:16px">
        <el-pagination v-model:current-page="currentPage" :page-size="filters.limit" :total="total" layout="prev, pager, next" @current-change="loadCommits" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api'
import { useRepoList } from '@/composables/useRepoList'
import { ElMessage } from 'element-plus'

const { repoList } = useRepoList()

const filters = ref({ repo_name: '', author: '', start_time: '', end_time: '', limit: 50 })
const commits = ref([])
const total = ref(0)
const loading = ref(false)
const currentPage = ref(1)
const expandedRow = ref(null)

const status = ref(null)
const triggering = ref(false)
const showTriggerInput = ref(false)
const repoPath = ref('')

const statusTagType = computed(() => {
  const map = { completed: 'success', running: 'warning', pending: 'info', failed: 'danger' }
  return map[status.value?.status] || 'info'
})

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const loadCommits = async () => {
  if (!filters.value.repo_name) return
  loading.value = true
  try {
    const params = {
      repo_name: filters.value.repo_name,
      skip: (currentPage.value - 1) * filters.value.limit,
      limit: filters.value.limit,
    }
    if (filters.value.author) params.author = filters.value.author
    if (filters.value.start_time) params.start_time = new Date(filters.value.start_time).toISOString()
    if (filters.value.end_time) params.end_time = new Date(filters.value.end_time).toISOString()
    const data = await api.listCommits(params)
    commits.value = data.items || []; total.value = data.total || 0
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const loadStatus = async () => {
  if (!filters.value.repo_name) return
  try { status.value = await api.getAnalysisStatus(filters.value.repo_name) } catch (e) { console.error(e) }
}

const handleTrigger = async () => {
  if (!repoPath.value) { showTriggerInput.value = true; return }
  triggering.value = true
  try { await api.triggerAnalysis(filters.value.repo_name, repoPath.value); loadStatus() }
  catch (e) { ElMessage.error('触发失败: ' + e.message) } finally { triggering.value = false }
}

const toggleExpand = (row) => { expandedRow.value = expandedRow.value?.id === row.id ? null : row }

onMounted(() => { if (filters.value.repo_name) { loadCommits(); loadStatus() } })
</script>
