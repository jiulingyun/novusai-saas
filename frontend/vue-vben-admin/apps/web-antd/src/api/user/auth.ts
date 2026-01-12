/**
 * 租户用户端认证 API
 * 对接后端 /api/v1/auth/* 接口
 */
import type {
  ChangePasswordParams,
  LoginParams,
  LoginResult,
  LoginResultRaw,
  RefreshTokenResult,
  RefreshTokenResultRaw,
  TenantUserInfo,
} from '../shared/types';

import { baseRequestClient, requestClient } from '../request';
import { useAccessStore } from '@vben/stores';

// Logout 使用 baseRequestClient 避免 401 时循环调用

const API_PREFIX = '/api/v1/auth';

/**
 * 用户登录 (JSON 格式)
 * 后端返回 snake_case，转换为 camelCase
 */
export async function userLoginApi(data: LoginParams): Promise<LoginResult> {
  const response = await requestClient.post<LoginResultRaw>(
    `${API_PREFIX}/login/json`,
    data,
  );
  return {
    accessToken: response.access_token,
    refreshToken: response.refresh_token,
  };
}

/**
 * 刷新 Token
 * 后端返回 snake_case，转换为 camelCase
 */
export async function userRefreshTokenApi(
  refreshToken: string,
): Promise<RefreshTokenResult> {
  const response = await baseRequestClient.post<{
    data: RefreshTokenResultRaw;
  }>(`${API_PREFIX}/refresh`, {
    refresh_token: refreshToken,
  });
  const raw = (response as any).data;
  return {
    accessToken: raw.access_token,
    refreshToken: raw.refresh_token,
  };
}

/**
 * 用户登出
 * 使用 baseRequestClient 避免 401 时触发循环调用
 */
export async function userLogoutApi() {
  try {
    const accessStore = useAccessStore();
    const token = accessStore?.accessToken;
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    return await baseRequestClient.post(`${API_PREFIX}/logout`, undefined, { headers });
  } catch {
    // 登出失败不影响主流程
  }
}

/**
 * 获取当前用户信息
 */
export async function getUserInfoApi() {
  return requestClient.get<TenantUserInfo>(`${API_PREFIX}/me`);
}

/**
 * 修改密码
 */
export async function userChangePasswordApi(data: ChangePasswordParams) {
  return requestClient.put(`${API_PREFIX}/password`, {
    old_password: data.oldPassword,
    new_password: data.newPassword,
    confirm_password: data.confirmPassword,
  });
}
