import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const AuthPageLayout = () => import('#/layouts/auth.vue');
const BasicLayout = () => import('#/layouts/basic.vue');

/** 租户后台路由 */
export const tenantRoutes: RouteRecordRaw[] = [
  // 租户后台认证路由
  {
    component: AuthPageLayout,
    meta: {
      hideInTab: true,
      title: 'Tenant Authentication',
    },
    name: 'TenantAuthentication',
    path: '/tenant/auth',
    redirect: '/tenant/login',
    children: [
      {
        name: 'TenantLogin',
        path: '/tenant/login',
        component: () => import('#/views/tenant/authentication/login.vue'),
        meta: {
          title: $t('page.auth.login'),
        },
      },
    ],
  },
  // 租户后台主布局
  {
    component: BasicLayout,
    meta: {
      hideInBreadcrumb: true,
      title: 'Tenant Root',
    },
    name: 'TenantRoot',
    path: '/tenant',
    redirect: '/tenant/dashboard',
    children: [
      {
        name: 'TenantDashboard',
        path: 'dashboard',
        component: () => import('#/views/tenant/dashboard/index.vue'),
        meta: {
          affixTab: true,
          icon: 'lucide:layout-dashboard',
          title: $t('page.dashboard.title'),
        },
      },
    ],
  },
];

/** 租户后台路由名称列表（不需要权限拦截） */
export const tenantCoreRouteNames = ['TenantAuthentication', 'TenantLogin'];
