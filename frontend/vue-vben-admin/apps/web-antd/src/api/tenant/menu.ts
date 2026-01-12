/**
 * 租户后台菜单 API
 * 对接后端 /tenant/permissions/menus 接口
 */
import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '../request';
import {
  type BackendMenuItemRaw,
  needsTransform,
  transformMenuData,
} from '../shared/menu-transformer';

/**
 * 获取当前租户管理员菜单列表
 * 根据角色权限过滤，用于前端动态渲染菜单
 * 自动处理后端 snake_case 到前端 camelCase 的转换
 */
export async function getTenantMenusApi(): Promise<RouteRecordStringComponent[]> {
  const menus = await requestClient.get<BackendMenuItemRaw[] | RouteRecordStringComponent[]>(
    '/tenant/permissions/menus',
  );

  // 判断是否需要转换（后端可能返回不同格式）
  if (needsTransform(menus)) {
    return transformMenuData(menus as BackendMenuItemRaw[], 'tenant');
  }

  return menus as RouteRecordStringComponent[];
}
