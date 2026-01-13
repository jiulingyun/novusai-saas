/**
 * 租户管理端认证 Store
 * 专用于租户管理员的登录、登出、用户信息管理
 */
import type { Recordable, UserInfo } from '@vben/types';

import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { useAccessStore, useUserStore } from '@vben/stores';

import { notification } from 'ant-design-vue';
import { defineStore } from 'pinia';

import { tenantApi, type TenantAdminInfo } from '#/api';
import { TENANT_HOME_PATH, TENANT_LOGIN_PATH } from '#/constants/endpoints';
import { $t } from '#/locales';
import { EndpointType } from '#/types/endpoint';
import { TokenStorage } from '../shared/token-storage';

export const useTenantAuthStore = defineStore('tenant-auth', () => {
  const accessStore = useAccessStore();
  const userStore = useUserStore();
  const router = useRouter();

  const loginLoading = ref(false);
  const tenantAdminInfo = ref<TenantAdminInfo | null>(null);

  /**
   * 租户管理员登录
   * @param params 登录参数
   * @param onSuccess 登录成功回调
   */
  async function login(
    params: Recordable<any>,
    onSuccess?: () => Promise<void> | void,
  ) {
    let userInfo: TenantAdminInfo | null = null;

    try {
      loginLoading.value = true;

      const { accessToken, refreshToken } = await tenantApi.tenantLoginApi({
        password: params.password,
        username: params.username,
      });

      if (accessToken) {
        // 存储Token到tenant端专用存储
        TokenStorage.setToken(EndpointType.TENANT, accessToken);
        if (refreshToken) {
          TokenStorage.setRefreshToken(EndpointType.TENANT, refreshToken);
        }

        // 同时设置到accessStore（兼容vben框架）
        accessStore.setAccessToken(accessToken);
        if (refreshToken) {
          accessStore.setRefreshToken(refreshToken);
        }

        // 获取用户信息
        userInfo = await fetchUserInfo();

        // 转换为vben UserInfo格式
        const vbenUserInfo: UserInfo = {
          avatar: userInfo?.avatar || '',
          desc: userInfo?.tenantName || '租户管理员',
          homePath: userInfo?.homePath || TENANT_HOME_PATH,
          realName: userInfo?.realName || '',
          roles: userInfo?.roles || [],
          token: accessToken,
          userId: String(userInfo?.id || ''),
          username: userInfo?.username || '',
        };

        userStore.setUserInfo(vbenUserInfo);

        if (accessStore.loginExpired) {
          accessStore.setLoginExpired(false);
        } else {
          onSuccess
            ? await onSuccess?.()
            : await router.push(vbenUserInfo.homePath || TENANT_HOME_PATH);
        }

        if (vbenUserInfo.realName) {
          notification.success({
            description: `${$t('authentication.loginSuccessDesc')}:${vbenUserInfo.realName}`,
            duration: 3,
            message: $t('authentication.loginSuccess'),
          });
        }
      }
    } finally {
      loginLoading.value = false;
    }

    return { userInfo };
  }

  /**
   * 租户管理员登出
   * @param redirect 是否重定向到登录页
   */
  async function logout(redirect: boolean = true) {
    try {
      await tenantApi.tenantLogoutApi();
    } catch {
      // 忽略错误
    }

    // 仅清除tenant端Token
    TokenStorage.clearToken(EndpointType.TENANT);

    // 清除accessStore
    accessStore.setAccessToken(null);
    accessStore.setRefreshToken(null);
    accessStore.setLoginExpired(false);
    accessStore.setAccessMenus([]);
    accessStore.setAccessRoutes([]);
    accessStore.setAccessCodes([]);
    accessStore.setIsAccessChecked(false);

    userStore.setUserInfo(null as unknown as UserInfo);
    tenantAdminInfo.value = null;

    await router.replace({
      path: TENANT_LOGIN_PATH,
      query: redirect
        ? { redirect: encodeURIComponent(router.currentRoute.value.fullPath) }
        : {},
    });
  }

  /**
   * 获取租户管理员信息
   */
  async function fetchUserInfo() {
    const info = await tenantApi.getTenantAdminInfoApi();
    tenantAdminInfo.value = info;

    // 设置权限码
    const permissions = info?.permissions || [];
    accessStore.setAccessCodes(permissions);

    return info;
  }

  /**
   * 检查是否已认证
   */
  function isAuthenticated(): boolean {
    return TokenStorage.hasToken(EndpointType.TENANT);
  }

  /**
   * 获取当前Token
   */
  function getToken(): string | null {
    return TokenStorage.getToken(EndpointType.TENANT);
  }

  /**
   * 获取当前租户ID
   */
  function getTenantId(): number | string | null {
    return tenantAdminInfo.value?.tenantId || null;
  }

  function $reset() {
    loginLoading.value = false;
    tenantAdminInfo.value = null;
  }

  return {
    $reset,
    fetchUserInfo,
    getToken,
    getTenantId,
    isAuthenticated,
    login,
    loginLoading,
    logout,
    tenantAdminInfo,
  };
});
