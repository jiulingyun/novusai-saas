/**
 * 平台管理端菜单 API
 * 对接后端 /admin/permissions/menus 接口
 */
import type { RouteRecordStringComponent } from '@vben/types';

import type { BackendMenuItemRaw } from '../shared/menu-transformer';

import { requestClient } from '../request';
import { needsTransform, transformMenuData } from '../shared/menu-transformer';

/**
 * 获取当前管理员菜单列表
 * 根据角色权限过滤，用于前端动态渲染菜单
 * 自动处理后端 snake_case 到前端 camelCase 的转换
 */
export async function getAdminMenusApi(): Promise<
  RouteRecordStringComponent[]
> {
  const menus = await requestClient.get<
    BackendMenuItemRaw[] | RouteRecordStringComponent[]
  >('/admin/permissions/menus');

  // 判断是否需要转换（后端可能返回不同格式）
  if (needsTransform(menus)) {
    return transformMenuData(menus as BackendMenuItemRaw[], 'admin');
  }

  return menus as RouteRecordStringComponent[];
}
