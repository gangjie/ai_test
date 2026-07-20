const BASE_URL = 'http://127.0.0.1:8000/api/v1'

async function request(url, options = {}) {
  const { params, body, method = 'GET' } = options
  let fullUrl = `${BASE_URL}${url}`

  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value))
      }
    })
    const qs = searchParams.toString()
    if (qs) fullUrl += `?${qs}`
  }

  const fetchOptions = { method, headers: { 'Content-Type': 'application/json' } }
  if (body) fetchOptions.body = JSON.stringify(body)

  const res = await fetch(fullUrl, fetchOptions)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(JSON.stringify(err))
  }
  if (res.status === 204 || !res.body) return null
  return res.json()
}

// ========== Git 仓库管理 ==========
export const api = {
  // 克隆仓库
  cloneRepo: (data) => request('/git/clone', { method: 'POST', body: data }),
  // 仓库列表
  listRepos: () => request('/git/repos'),
  // 删除仓库
  deleteRepo: (repoName) => request(`/git/repos/${encodeURIComponent(repoName)}`, { method: 'DELETE' }),

  // ========== 提交记录分析 ==========
  // 查询分析状态
  getAnalysisStatus: (repoName) => request(`/commits/status/${encodeURIComponent(repoName)}`),
  // 提交记录列表
  listCommits: (params) => request('/commits', { params }),
  // 按人员统计
  getAuthorStats: (repoName) => request('/commits/authors', { params: { repo_name: repoName } }),
  // 按文件统计
  getFileStats: (repoName, limit) => request('/commits/files', { params: { repo_name: repoName, limit } }),
  // 按人员汇总统计（基于路径配置）
  getAuthorSummary: (params) => request('/commits/author-summary', { params }),
  // 触发分析
  triggerAnalysis: (repoName, repoPath) =>
    request(`/commits/analyze/${encodeURIComponent(repoName)}`, {
      method: 'POST',
      params: { repo_path: repoPath }
    }),

  // ========== 文件路径配置 ==========
  createPathConfig: (data) => request('/path-configs', { method: 'POST', body: data }),
  listPathConfigs: (repoName) => request('/path-configs', { params: { repo_name: repoName } }),
  updatePathConfig: (repoName, pathPattern, data) =>
    request(`/path-configs/${encodeURIComponent(pathPattern)}`, { method: 'PUT', body: data, params: { repo_name: repoName } }),
  deletePathConfig: (repoName, pathPattern) =>
    request(`/path-configs/${encodeURIComponent(pathPattern)}`, { method: 'DELETE', params: { repo_name: repoName } }),
  // 上传文件批量导入路径配置
  uploadPathConfig: (repoName, file) => {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE_URL}/path-configs/upload?repo_name=${encodeURIComponent(repoName)}`, {
      method: 'POST',
      body: form,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(JSON.stringify(err))
      }
      return res.json()
    })
  },
}
