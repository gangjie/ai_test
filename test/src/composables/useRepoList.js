import { ref, onMounted } from 'vue'
import { api } from '@/api'

export function useRepoList() {
  const repoList = ref([])
  const repoLoading = ref(false)

  const loadRepos = async () => {
    repoLoading.value = true
    try {
      const data = await api.listRepos()
      const repos = data.repos || data.items || (Array.isArray(data) ? data : [])
      repoList.value = repos.map(r => r.name || r.repo_name || r)
    } catch (e) {
      console.error('加载仓库列表失败:', e)
    } finally {
      repoLoading.value = false
    }
  }

  onMounted(loadRepos)

  return { repoList, repoLoading, loadRepos }
}
