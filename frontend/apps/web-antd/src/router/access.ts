import type {
  ComponentRecordType,
  GenerateMenuAndRoutesOptions,
} from '@vben/types';

import { generateAccessible } from '@vben/access';
import { preferences } from '@vben/preferences';

import { message } from 'ant-design-vue';

import {
  adminApi,
  type ApiEndpoint,
  getApiEndpoint,
  setExistingComponents,
  tenantApi,
  userApi,
} from '#/api';
import { BasicLayout, IFrameView } from '#/layouts';
import { $t } from '#/locales';

const forbiddenComponent = () => import('#/views/_core/fallback/forbidden.vue');

/**
 * 根据端类型获取对应的菜单 API
 */
function getMenuApi(endpoint: ApiEndpoint) {
  switch (endpoint) {
    case 'admin': {
      return adminApi.getAdminMenusApi;
    }
    case 'tenant': {
      return tenantApi.getTenantMenusApi;
    }
    default: {
      return userApi.getUserMenusApi;
    }
  }
}

/**
 * 生成路由和菜单
 * @param options 选项
 * @param endpoint 端类型（可选，不传则根据当前路由自动判断）
 */
async function generateAccess(
  options: GenerateMenuAndRoutesOptions,
  endpoint?: ApiEndpoint,
) {
  const pageMap: ComponentRecordType = import.meta.glob('../views/**/*.vue');

  // 设置已存在的组件映射，用于检测缺失的菜单组件
  setExistingComponents(pageMap);

  const layoutMap: ComponentRecordType = {
    BasicLayout,
    IFrameView,
  };

  // 如果未指定端类型，尝试从当前路由获取
  const currentEndpoint = endpoint || getCurrentEndpoint();
  const menuApi = getMenuApi(currentEndpoint);

  return await generateAccessible(preferences.app.accessMode, {
    ...options,
    fetchMenuListAsync: async () => {
      message.loading({
        content: `${$t('common.loadingMenu')}...`,
        duration: 1.5,
      });
      return await menuApi();
    },
    // 可以指定没有权限跳转403页面
    forbiddenComponent,
    // 如果 route.meta.menuVisibleWithForbidden = true
    layoutMap,
    pageMap,
  });
}

/**
 * 获取当前端类型
 * 从 window.location 获取，因为此时可能还没有路由实例
 */
function getCurrentEndpoint(): ApiEndpoint {
  const path = window.location.pathname;
  return getApiEndpoint(path);
}

export { generateAccess, getCurrentEndpoint, getMenuApi };
