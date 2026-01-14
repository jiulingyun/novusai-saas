/**
 * 租户管理端路由模块
 */
import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const AuthPageLayout = () => import('#/layouts/auth.vue');
const BasicLayout = () => import('#/layouts/basic.vue');

/** 租户管理端认证路由 */
const authRoutes: RouteRecordRaw = {
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
    {
      name: 'TenantImpersonate',
      path: '/tenant/impersonate',
      component: () => import('#/views/tenant/authentication/impersonate.vue'),
      meta: {
        title: $t('page.auth.impersonate'),
      },
    },
  ],
};

/** 租户管理端主布局路由 */
const mainRoutes: RouteRecordRaw = {
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
    // 系统管理
    {
      name: 'TenantSystem',
      path: 'system',
      meta: {
        icon: 'lucide:settings',
        title: $t('tenant.system.title'),
      },
      children: [
        {
          name: 'TenantSystemRole',
          path: 'role',
          component: () => import('#/views/tenant/system/role/list.vue'),
          meta: {
            icon: 'lucide:shield',
            title: $t('tenant.system.role.title'),
          },
        },
      ],
    },
  ],
};

/** 租户管理端路由 */
export const tenantRoutes: RouteRecordRaw[] = [authRoutes, mainRoutes];

/** 租户管理端路由名称列表（不需要权限拦截） */
export const tenantCoreRouteNames = [
  'TenantAuthentication',
  'TenantLogin',
  'TenantImpersonate',
];
