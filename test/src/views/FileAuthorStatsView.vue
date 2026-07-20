<template>
  <div>
    <h2>人员汇总统计（基于路径配置）</h2>

    <el-card shadow="hover">
      <el-form inline>
        <el-form-item label="仓库名称">
          <el-select v-model="filters.repo_name" placeholder="请选择仓库" style="width:200px">
            <el-option v-for="r in repoList" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="filters.start_time" type="datetime" placeholder="选择开始时间" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="filters.end_time" type="datetime" placeholder="选择结束时间" />
        </el-form-item>
        <el-form-item label="限制条数">
          <el-select v-model.number="filters.limit" style="width:100px">
            <el-option :value="50" label="50" /><el-option :value="100" label="100" /><el-option :value="200" label="200" /><el-option :value="500" label="500" />
          </el-select>
        </el-form-item>
        <el-form-item><el-button type="primary" @click="loadData" :disabled="!filters.repo_name">查询</el-button></el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="hover" style="margin-top:20px" v-if="data">
      <template #header><span>统计概览</span></template>
      <el-row :gutter="20">
        <el-col :span="8"><el-statistic title="汇总记录数" :value="data.total" /></el-col>
        <el-col :span="8"><el-statistic title="参与人员" :value="data.total" /></el-col>
      </el-row>
    </el-card>

    <el-card shadow="hover" style="margin-top:20px" v-if="data && pieChartData.labels.length > 0">
      <template #header><span>各人员修改总行数占比</span></template>
      <div style="height:350px"><Pie :data="pieChartData" :options="pieChartOptions" /></div>
    </el-card>

    <el-card shadow="hover" style="margin-top:20px" v-if="data">
      <template #header><span>人员汇总明细（共 {{ data.total }} 条）</span></template>
      <el-table :data="data.items" stripe>
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="author_name" label="姓名" width="140" />
        <el-table-column prop="author_email" label="邮箱" width="220" />
        <el-table-column prop="change_count" label="变更次数" width="100" align="center" />
        <el-table-column label="新增行数" width="110" align="center">
          <template #default="{ row }"><span style="color:#42b883">+{{ row.total_insertions }}</span></template>
        </el-table-column>
        <el-table-column label="删除行数" width="110" align="center">
          <template #default="{ row }"><span style="color:#e74c3c">-{{ row.total_deletions }}</span></template>
        </el-table-column>
        <el-table-column label="总行数" width="90" align="center">
          <template #default="{ row }"><span style="color:#666">{{ row.total_lines }}</span></template>
        </el-table-column>
      </el-table>
    </el-card>

    <p v-if="loading" style="text-align:center;color:#999;padding:20px">加载中...</p>
    <el-alert v-if="error" :title="error" type="error" show-icon style="margin-top:16px" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Pie } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement, CategoryScale } from 'chart.js'
import { api } from '@/api'
import { useRepoList } from '@/composables/useRepoList'

ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale)
const { repoList } = useRepoList()

const COLORS = ['#42b883','#3498db','#e74c3c','#f39c12','#9b59b6','#1abc9c','#e67e22','#2ecc71','#e91e63','#00bcd4','#ff5722','#607d8b','#795548','#8bc34a','#ff9800']

const filters = ref({ repo_name: '', start_time: '', end_time: '', limit: 100 })
const data = ref(null)
const loading = ref(false)
const error = ref('')

const pieChartData = computed(() => {
  if (!data.value?.items) return { labels: [], datasets: [] }
  const items = data.value.items
  return {
    labels: items.map(i => i.author_name),
    datasets: [{
      data: items.map(i => i.total_lines || 0),
      backgroundColor: items.map((_, idx) => COLORS[idx % COLORS.length]),
      borderWidth: 1,
    }],
  }
})

const pieChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right', labels: { padding: 12, font: { size: 12 } } },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const total = ctx.dataset.data.reduce((a, b) => a + b, 0)
          const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0
          return `${ctx.label}: ${ctx.parsed} 行 (${pct}%)`
        },
      },
    },
  },
}

const loadData = async () => {
  if (!filters.value.repo_name) return
  loading.value = true; error.value = ''; data.value = null
  try {
    const params = { repo_name: filters.value.repo_name, limit: filters.value.limit }
    if (filters.value.start_time) params.start_time = new Date(filters.value.start_time).toISOString()
    if (filters.value.end_time) params.end_time = new Date(filters.value.end_time).toISOString()
    data.value = await api.getAuthorSummary(params)
  } catch (e) { error.value = '查询失败: ' + e.message }
  finally { loading.value = false }
}
</script>
