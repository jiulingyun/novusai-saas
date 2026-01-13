/**
 * 平台权限管理 API
 * 对接后端 /admin/permissions/* 接口
 */
import { requestClient } from '../request';

// ============================================================
// 类型定义
// ============================================================

/** 权限类型 */
export type PermissionType = 'menu' | 'button' | 'api';

/** 权限节点（树形结构，后端原始格式） */
export interface PermissionNodeRaw {
  id: number;
  code: string;
  name: string;
  type: PermissionType;
  parent_id: number | null;
  sort_order: number;
  children?: PermissionNodeRaw[];
}

/** 权限节点（树形结构，前端格式） */
export interface PermissionNode {
  id: number;
  code: string;
  name: string;
  type: PermissionType;
  parentId: number | null;
  sortOrder: number;
  children?: PermissionNode[];
}

/** 权限项（平铺列表，后端原始格式） */
export interface PermissionItemRaw {
  id: number;
  code: string;
  name: string;
  type: PermissionType;
  parent_id: number | null;
}

/** 权限项（平铺列表，前端格式） */
export interface PermissionItem {
  id: number;
  code: string;
  name: string;
  type: PermissionType;
  parentId: number | null;
}

// ============================================================
// 转换函数
// ============================================================

/** 递归转换权限树节点 */
function transformPermissionNode(raw: PermissionNodeRaw): PermissionNode {
  return {
    id: raw.id,
    code: raw.code,
    name: raw.name,
    type: raw.type,
    parentId: raw.parent_id,
    sortOrder: raw.sort_order,
    children: raw.children?.map(transformPermissionNode),
  };
}

/** 转换权限项 */
function transformPermissionItem(raw: PermissionItemRaw): PermissionItem {
  return {
    id: raw.id,
    code: raw.code,
    name: raw.name,
    type: raw.type,
    parentId: raw.parent_id,
  };
}

// ============================================================
// API 接口
// ============================================================

const API_PREFIX = '/admin/permissions';

/**
 * 获取权限树
 * GET /admin/permissions
 * 返回树形结构，用于角色权限配置页面
 */
export async function getPermissionTreeApi(): Promise<PermissionNode[]> {
  const response = await requestClient.get<PermissionNodeRaw[]>(API_PREFIX);
  return response.map(transformPermissionNode);
}

/**
 * 获取权限列表（平铺）
 * GET /admin/permissions/list
 */
export async function getPermissionListApi(): Promise<PermissionItem[]> {
  const response = await requestClient.get<PermissionItemRaw[]>(
    `${API_PREFIX}/list`,
  );
  return response.map(transformPermissionItem);
}
