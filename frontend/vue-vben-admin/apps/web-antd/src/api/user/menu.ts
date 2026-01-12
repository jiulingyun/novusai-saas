/**
 * 租户用户端菜单 API
 * 对接后端 /api/v1/menus/* 接口
 */
import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '../request';

const API_PREFIX = '/api/v1';

/**
 * 获取用户菜单列表
 * 返回当前用户有权限的菜单
 */
export async function getUserMenusApi() {
  return requestClient.get<RouteRecordStringComponent[]>(`${API_PREFIX}/menus`);
}
