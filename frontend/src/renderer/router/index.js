import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/accounts/list',
    component: () => import('../components/Layout/MainLayout.vue'),
    children: [
      {
        path: '/accounts',
        redirect: '/accounts/list',
        meta: { title: '账号管理', icon: 'User' },
      },
      {
        path: '/accounts/list',
        name: 'AccountList',
        component: () => import('../views/Accounts/List.vue'),
        meta: { title: '账号列表', icon: 'User' },
      },
      {
        path: '/accounts/import',
        name: 'AccountImport',
        component: () => import('../views/Accounts/Import.vue'),
        meta: { title: '批量导入', icon: 'Upload' },
      },
      {
        path: '/proxies',
        name: 'Proxies',
        component: () => import('../views/Proxies.vue'),
        meta: { title: '代理管理', icon: 'Connection' },
      },
      {
        path: '/bulk-message',
        name: 'BulkMessage',
        component: () => import('../views/BulkMessage.vue'),
        meta: { title: '群发消息', icon: 'ChatDotSquare' },
      },
      {
        path: '/direct-message',
        name: 'DirectMessage',
        component: () => import('../views/DirectMessage.vue'),
        meta: { title: '批量私信', icon: 'ChatLineSquare' },
      },
      {
        path: '/invite',
        name: 'Invite',
        component: () => import('../views/Invite.vue'),
        meta: { title: '批量拉人', icon: 'UserFilled' },
      },
      {
        path: '/checker',
        name: 'Checker',
        component: () => import('../views/Checker.vue'),
        meta: { title: '账户检查', icon: 'CircleCheck' },
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { title: '资料管理', icon: 'Edit' },
      },
      {
        path: '/stats',
        name: 'Stats',
        component: () => import('../views/Stats.vue'),
        meta: { title: '数据统计', icon: 'TrendCharts' },
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
