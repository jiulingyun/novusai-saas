/**
 * 平台角色管理 API
 * 对接后端 /admin/roles/* 接口
 */
import { requestClient } from '../request';

// ============================================================
// 类型定义
// ============================================================

/** 创建角色请求 */
export interface RoleCreateRequest {
  code: string;
  name: string;
  description?: string | null;
  is_active?: boolean;
  sort_order?: number;
  permission_ids?: number[];
}

/** 更新角色请求 */
export interface RoleUpdateRequest {
  name?: string | null;
  description?: string | null;
  is_active?: boolean | null;
  sort_order?: number | null;
  permission_ids?: number[] | null;
}

/** 分配权限请求 */
export interface RolePermissionsRequest {
  permission_ids: number[];
}

/** 权限基本信息 */
export interface PermissionBasicInfo {
  id: number;
  code: string;
  name: string;
  type: string;
}

/** 角色信息（后端原始格式 snake_case） */
export interface RoleInfoRaw {
  id: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  sort_order: number;
  permissions?: PermissionBasicInfo[];
  created_at: string;
  updated_at?: string;
}

/** 角色信息（前端格式 camelCase） */
export interface RoleInfo {
  id: number;
  code: string;
  name: string;
  description?: string;
  isActive: boolean;
  sortOrder: number;
  permissions?: PermissionBasicInfo[];
  createdAt: string;
  updatedAt?: string;
}

// ============================================================
// 转换函数
// ============================================================

/** 将后端 snake_case 转换为前端 camelCase */
function transformRoleInfo(raw: RoleInfoRaw): RoleInfo {
  return {
    id: raw.id,
    code: raw.code,
    name: raw.name,
    description: raw.description,
    isActive: raw.is_active,
    sortOrder: raw.sort_order,
    permissions: raw.permissions,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  };
}

// ============================================================
// API 接口
// ============================================================

const API_PREFIX = '/admin/roles';

/**
 * 获取角色列表
 * GET /admin/roles
 * 注意: 角色列表不分页，返回全部
 */
export async function getRoleListApi(): Promise<RoleInfo[]> {
  const response = await requestClient.get<RoleInfoRaw[]>(API_PREFIX);
  return response.map(transformRoleInfo);
}

/**
 * 获取角色详情（含权限列表）
 * GET /admin/roles/{role_id}
 */
export async function getRoleDetailApi(roleId: number): Promise<RoleInfo> {
  const raw = await requestClient.get<RoleInfoRaw>(`${API_PREFIX}/${roleId}`);
  return transformRoleInfo(raw);
}

/**
 * 创建角色
 * POST /admin/roles
 */
export async function createRoleApi(data: RoleCreateRequest): Promise<RoleInfo> {
  const raw = await requestClient.post<RoleInfoRaw>(API_PREFIX, data);
  return transformRoleInfo(raw);
}

/**
 * 更新角色
 * PUT /admin/roles/{role_id}
 */
export async function updateRoleApi(
  roleId: number,
  data: RoleUpdateRequest,
): Promise<RoleInfo> {
  const raw = await requestClient.put<RoleInfoRaw>(
    `${API_PREFIX}/${roleId}`,
    data,
  );
  return transformRoleInfo(raw);
}

/**
 * 删除角色
 * DELETE /admin/roles/{role_id}
 */
export async function deleteRoleApi(roleId: number): Promise<void> {
  await requestClient.delete(`${API_PREFIX}/${roleId}`);
}

/**
 * 分配角色权限
 * PUT /admin/roles/{role_id}/permissions
 */
export async function assignRolePermissionsApi(
  roleId: number,
  data: RolePermissionsRequest,
): Promise<RoleInfo> {
  const raw = await requestClient.put<RoleInfoRaw>(
    `${API_PREFIX}/${roleId}/permissions`,
    data,
  );
  return transformRoleInfo(raw);
}
