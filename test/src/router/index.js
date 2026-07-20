import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/git-repos',
      name: 'git-repos',
      component: () => import('@/views/GitReposView.vue')
    },
    {
      path: '/commits',
      name: 'commits',
      component: () => import('@/views/CommitsView.vue')
    },
    {
      path: '/author-stats',
      name: 'author-stats',
      component: () => import('@/views/AuthorStatsView.vue')
    },
    {
      path: '/file-stats',
      name: 'file-stats',
      component: () => import('@/views/FileStatsView.vue')
    },
    {
      path: '/file-author-stats',
      name: 'file-author-stats',
      component: () => import('@/views/FileAuthorStatsView.vue')
    },
    {
      path: '/path-config',
      name: 'path-config',
      component: () => import('@/views/PathConfigView.vue')
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('@/views/AboutView.vue')
    }
  ]
})

export default router
