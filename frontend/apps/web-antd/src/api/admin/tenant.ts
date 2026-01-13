/**
 * 租户管理 API
 * 对接后端 /admin/tenants/* 接口
 */
import { requestClient } from '../request';

// ============================================================
// 类型定义
// ============================================================

/** 套餐类型 */
export type TenantPlan = 'free' | 'basic' | 'pro' | 'enterprise';

/** 租户列表查询参数 */
export interface TenantListParams {
  page?: number;
  page_size?: number;
  is_active?: boolean | null;
  plan?: TenantPlan | null;
}

/** 创建租户请求 */
export interface TenantCreateRequest {
  code: string;
  name: string;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  plan?: TenantPlan;
  quota?: Record<string, any> | null;
  expires_at?: string | null;
  remark?: string | null;
}

/** 更新租户请求 */
export interface TenantUpdateRequest {
  name?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  plan?: TenantPlan | null;
  quota?: Record<string, any> | null;
  expires_at?: string | null;
  remark?: string | null;
}

/** 切换状态请求 */
export interface TenantStatusRequest {
  is_active: boolean;
}

/** 租户信息（后端原始格式 snake_case） */
export interface TenantInfoRaw {
  id: number;
  code: string;
  name: string;
  contact_name?: string;
  contact_phone?: string;
  contact_email?: string;
  plan: TenantPlan;
  quota?: Record<string, any>;
  is_active: boolean;
  expires_at?: string;
  remark?: string;
  created_at: string;
  updated_at?: string;
}

/** 租户信息（前端格式 camelCase） */
export interface TenantInfo {
  id: number;
  code: string;
  name: string;
  contactName?: string;
  contactPhone?: string;
  contactEmail?: string;
  plan: TenantPlan;
  quota?: Record<string, any>;
  isActive: boolean;
  expiresAt?: string;
  remark?: string;
  createdAt: string;
  updatedAt?: string;
}

/** 分页列表响应 */
export interface TenantListResponse {
  items: TenantInfo[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================================
// 转换函数
// ============================================================

/** 将后端 snake_case 转换为前端 camelCase */
function transformTenantInfo(raw: TenantInfoRaw): TenantInfo {
  return {
    id: raw.id,
    code: raw.code,
    name: raw.name,
    contactName: raw.contact_name,
    contactPhone: raw.contact_phone,
    contactEmail: raw.contact_email,
    plan: raw.plan,
    quota: raw.quota,
    isActive: raw.is_active,
    expiresAt: raw.expires_at,
    remark: raw.remark,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  };
}

// ============================================================
// API 接口
// ============================================================

const API_PREFIX = '/admin/tenants';

/**
 * 获取租户列表
 * GET /admin/tenants
 */
export async function getTenantListApi(
  params?: TenantListParams,
): Promise<TenantListResponse> {
  const response = await requestClient.get<{
    items: TenantInfoRaw[];
    total: number;
    page: number;
    page_size: number;
  }>(API_PREFIX, { params });

  return {
    items: response.items.map(transformTenantInfo),
    total: response.total,
    page: response.page,
    page_size: response.page_size,
  };
}

/**
 * 获取租户详情
 * GET /admin/tenants/{tenant_id}
 */
export async function getTenantDetailApi(tenantId: number): Promise<TenantInfo> {
  const raw = await requestClient.get<TenantInfoRaw>(
    `${API_PREFIX}/${tenantId}`,
  );
  return transformTenantInfo(raw);
}

/**
 * 创建租户
 * POST /admin/tenants
 */
export async function createTenantApi(
  data: TenantCreateRequest,
): Promise<TenantInfo> {
  const raw = await requestClient.post<TenantInfoRaw>(API_PREFIX, data);
  return transformTenantInfo(raw);
}

/**
 * 更新租户
 * PUT /admin/tenants/{tenant_id}
 */
export async function updateTenantApi(
  tenantId: number,
  data: TenantUpdateRequest,
): Promise<TenantInfo> {
  const raw = await requestClient.put<TenantInfoRaw>(
    `${API_PREFIX}/${tenantId}`,
    data,
  );
  return transformTenantInfo(raw);
}

/**
 * 删除租户
 * DELETE /admin/tenants/{tenant_id}
 */
export async function deleteTenantApi(tenantId: number): Promise<void> {
  await requestClient.delete(`${API_PREFIX}/${tenantId}`);
}

/**
 * 切换租户状态
 * PUT /admin/tenants/{tenant_id}/status
 */
export async function toggleTenantStatusApi(
  tenantId: number,
  data: TenantStatusRequest,
): Promise<TenantInfo> {
  const raw = await requestClient.put<TenantInfoRaw>(
    `${API_PREFIX}/${tenantId}/status`,
    data,
  );
  return transformTenantInfo(raw);
}
