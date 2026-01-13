/**
 * 权限控制工具
 * 扩展 @vben/access 的权限检查逻辑，支持超级管理员通配符
 */
import { computed } from 'vue';

import { useAccess as useVbenAccess } from '@vben/access';
import { useAccessStore } from '@vben/stores';

/**
 * 增强版权限检查 Hook
 * 支持超级管理员 '*' 通配符
 */
export function useAccess() {
  const vbenAccess = useVbenAccess();
  const accessStore = useAccessStore();

  /**
   * 检查是否为超级管理员（拥有 '*' 权限）
   */
  const isSuperAdmin = computed(() => {
    return accessStore.accessCodes.includes('*');
  });

  /**
   * 基于权限码判断是否有权限
   * 支持超级管理员 '*' 通配符
   * @param codes 需要检查的权限码列表
   */
  function hasAccessByCodes(codes: string[]): boolean {
    // 超级管理员拥有所有权限
    if (isSuperAdmin.value) {
      return true;
    }
    return vbenAccess.hasAccessByCodes(codes);
  }

  /**
   * 基于角色判断是否有权限
   */
  function hasAccessByRoles(roles: string[]): boolean {
    return vbenAccess.hasAccessByRoles(roles);
  }

  return {
    ...vbenAccess,
    hasAccessByCodes,
    hasAccessByRoles,
    isSuperAdmin,
  };
}

/**
 * 权限码常量 - 平台管理端
 */
export const ADMIN_PERMISSIONS = {
  // 管理员管理
  ADMIN_READ: 'admin:read',
  ADMIN_CREATE: 'admin:create',
  ADMIN_UPDATE: 'admin:update',
  ADMIN_DELETE: 'admin:delete',
  ADMIN_RESET_PASSWORD: 'admin:reset_password',
  ADMIN_TOGGLE_STATUS: 'admin:toggle_status',

  // 角色管理
  ROLE_READ: 'role:read',
  ROLE_CREATE: 'role:create',
  ROLE_UPDATE: 'role:update',
  ROLE_DELETE: 'role:delete',

  // 权限管理
  PERMISSION_READ: 'permission:read',

  // 租户管理
  TENANT_READ: 'tenant:read',
  TENANT_CREATE: 'tenant:create',
  TENANT_UPDATE: 'tenant:update',
  TENANT_DELETE: 'tenant:delete',
  TENANT_TOGGLE_STATUS: 'tenant:toggle_status',
} as const;

/**
 * 权限码常量 - 租户管理端
 */
export const TENANT_PERMISSIONS = {
  // 用户管理
  USER_READ: 'user:read',
  USER_CREATE: 'user:create',
  USER_UPDATE: 'user:update',
  USER_DELETE: 'user:delete',

  // 角色管理
  ROLE_READ: 'role:read',
  ROLE_CREATE: 'role:create',
  ROLE_UPDATE: 'role:update',
  ROLE_DELETE: 'role:delete',
} as const;
