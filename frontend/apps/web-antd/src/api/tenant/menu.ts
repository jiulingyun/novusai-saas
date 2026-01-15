/**
 * 租户后台菜单 API
 * 对接后端 /tenant/permissions/menus 接口
 */
import type { RouteRecordStringComponent } from '@vben/types';

import type { BackendMenuItemRaw } from '../shared/menu-transformer';

import { requestClient } from '../request';
import {
  extractPermissionsFromMenus,
  needsTransform,
  transformMenuData,
} from '../shared/menu-transformer';

/** 菜单和权限码的返回结果 */
export interface MenusWithPermissions {
  menus: RouteRecordStringComponent[];
  permissions: string[];
}

/**
 * 获取当前租户管理员菜单列表（含权限码）
 * 根据角色权限过滤，用于前端动态渲染菜单
 * 自动处理后端 snake_case 到前端 camelCase 的转换
 * @returns 菜单列表和权限码
 */
export async function getTenantMenusWithPermissionsApi(): Promise<MenusWithPermissions> {
  const rawMenus = await requestClient.get<BackendMenuItemRaw[]>(
    '/tenant/permissions/menus',
  );

  // 提取权限码
  const permissions = extractPermissionsFromMenus(rawMenus);

  // 转换菜单格式
  const menus = needsTransform(rawMenus)
    ? transformMenuData(rawMenus, 'tenant')
    : (rawMenus as unknown as RouteRecordStringComponent[]);

  return { menus, permissions };
}

/**
 * 获取当前租户管理员菜单列表
 * @deprecated 请使用 getTenantMenusWithPermissionsApi 以同时获取权限码
 */
export async function getTenantMenusApi(): Promise<RouteRecordStringComponent[]> {
  const { menus } = await getTenantMenusWithPermissionsApi();
  return menus;
}
