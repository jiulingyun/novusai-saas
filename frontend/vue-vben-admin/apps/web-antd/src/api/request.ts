/**
 * 该文件可自行根据业务逻辑进行调整
 * 支持多端（admin/tenant/user）Token 分离存储与刷新
 *
 * Token 获取策略：
 * - 根据请求 URL 判断端类型，从 TokenStorage 获取对应的 Token
 * - /admin/* -> admin Token
 * - /tenant/* -> tenant Token
 * - /api/v1/* -> user Token
 */
import type { RequestClientOptions } from '@vben/request';

import type { ApiEndpoint, RefreshTokenResultRaw } from './shared/types';

import { useAppConfig } from '@vben/hooks';
import { preferences } from '@vben/preferences';
import {
  authenticateResponseInterceptor,
  defaultResponseInterceptor,
  errorMessageResponseInterceptor,
  RequestClient,
} from '@vben/request';
import { useAccessStore } from '@vben/stores';

import { message } from 'ant-design-vue';

import { getApiEndpoint } from './shared/types';
import { LOGIN_PATHS, TokenStorage } from '#/store';

const { apiURL } = useAppConfig(import.meta.env, import.meta.env.PROD);

/**
 * 获取多端刷新 Token API URL
 * 避免循环依赖，直接返回 URL
 */
function getRefreshTokenUrl(endpoint: string): string {
  switch (endpoint) {
    case 'admin': {
      return '/admin/auth/refresh';
    }
    case 'tenant': {
      return '/tenant/auth/refresh';
    }
    default: {
      return '/api/v1/auth/refresh';
    }
  }
}

/**
 * 根据请求 URL 获取对应端的 Token
 * @param requestUrl 请求 URL
 */
function getTokenByRequestUrl(requestUrl: string): string | null {
  const endpoint = getEndpointByRequestUrl(requestUrl);
  return TokenStorage.getToken(endpoint);
}

/**
 * 根据请求 URL 判断端类型
 * @param requestUrl 请求 URL
 */
function getEndpointByRequestUrl(requestUrl: string): ApiEndpoint {
  if (requestUrl.startsWith('/admin')) {
    return 'admin';
  }
  if (requestUrl.startsWith('/tenant')) {
    return 'tenant';
  }
  // /api/v1/* 对应 user 端
  return 'user';
}

function createRequestClient(baseURL: string, options?: RequestClientOptions) {
  const client = new RequestClient({
    ...options,
    baseURL,
  });

  /**
   * 重新认证逻辑（多端支持）
   * Token 刷新失败或 refreshToken 过期时调用
   * 注意：不调用 multiAuthStore.logout() 避免循环调用
   */
  async function doReAuthenticate() {
    console.warn('Access token or refresh token is invalid or expired. ');
    const accessStore = useAccessStore();

    // 根据当前路由获取端类型
    const currentPath = window.location.pathname;
    const endpoint = getApiEndpoint(currentPath);

    // 仅清除当前端的 Token（不影响其他端）
    TokenStorage.clearToken(endpoint);

    // 清除 accessStore 中的 Token
    accessStore.setAccessToken(null);
    accessStore.setRefreshToken(null);

    if (
      preferences.app.loginExpiredMode === 'modal' &&
      accessStore.isAccessChecked
    ) {
      // 弹窗模式，设置登录过期状态
      accessStore.setLoginExpired(true);
    } else {
      // 重定向模式，直接跳转到对应端的登录页
      // 不调用 multiAuthStore.logout() 避免循环调用
      const loginPath = LOGIN_PATHS[endpoint];
      const currentFullPath =
        window.location.pathname + window.location.search;
      const redirect =
        currentFullPath !== loginPath
          ? `?redirect=${encodeURIComponent(currentFullPath)}`
          : '';
      window.location.href = loginPath + redirect;
    }
  }

  /**
   * 刷新 Token 逻辑（多端支持）
   * 根据当前路由判断调用哪个端的刷新接口
   */
  async function doRefreshToken() {
    const accessStore = useAccessStore();

    // 根据当前路由获取端类型
    const currentPath = window.location.pathname;
    const endpoint = getApiEndpoint(currentPath);

    // 从 TokenStorage 获取当前端的 Refresh Token
    const refreshToken = TokenStorage.getRefreshToken(endpoint);

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const refreshUrl = getRefreshTokenUrl(endpoint);

    // 使用新的 RequestClient 实例，避免循环依赖
    const baseClient = new RequestClient({ baseURL: apiURL });
    const result = await baseClient.post<RefreshTokenResultRaw>(refreshUrl, {
      refresh_token: refreshToken,
    });

    // 后端返回蛇形命名，转换为驼峰命名
    const newToken = result.access_token;

    // 更新 TokenStorage
    TokenStorage.setToken(endpoint, newToken);
    if (result.refresh_token) {
      TokenStorage.setRefreshToken(endpoint, result.refresh_token);
    }

    // 同时更新 accessStore（兼容 vben 框架）
    accessStore.setAccessToken(newToken);
    if (result.refresh_token) {
      accessStore.setRefreshToken(result.refresh_token);
    }

    return newToken;
  }

  function formatToken(token: null | string) {
    return token ? `Bearer ${token}` : null;
  }

  // 请求头处理（多端 Token 支持）
  client.addRequestInterceptor({
    fulfilled: async (config) => {
      // 根据请求 URL 获取对应端的 Token
      const requestUrl = config.url || '';
      const token = getTokenByRequestUrl(requestUrl);

      config.headers.Authorization = formatToken(token);
      config.headers['Accept-Language'] = preferences.app.locale;
      return config;
    },
  });

  // 处理返回的响应数据格式
  client.addResponseInterceptor(
    defaultResponseInterceptor({
      codeField: 'code',
      dataField: 'data',
      successCode: 0,
    }),
  );

  // token过期的处理
  client.addResponseInterceptor(
    authenticateResponseInterceptor({
      client,
      doReAuthenticate,
      doRefreshToken,
      enableRefreshToken: preferences.app.enableRefreshToken,
      formatToken,
    }),
  );

  // 通用的错误处理,如果没有进入上面的错误处理逻辑，就会进入这里
  client.addResponseInterceptor(
    errorMessageResponseInterceptor((msg: string, error) => {
      // 这里可以根据业务进行定制,你可以拿到 error 内的信息进行定制化处理，根据不同的 code 做不同的提示，而不是直接使用 message.error 提示 msg
      // 当前mock接口返回的错误字段是 error 或者 message
      const responseData = error?.response?.data ?? {};
      const errorMessage = responseData?.error ?? responseData?.message ?? '';
      // 如果没有错误信息，则会根据状态码进行提示
      message.error(errorMessage || msg);
    }),
  );

  return client;
}

export const requestClient = createRequestClient(apiURL, {
  responseReturn: 'data',
});

export const baseRequestClient = new RequestClient({ baseURL: apiURL });
