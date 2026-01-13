import type { Router } from 'vue-router';

import { preferences } from '@vben/preferences';
import { useAccessStore, useUserStore } from '@vben/stores';
import { startProgress, stopProgress } from '@vben/utils';

import { type ApiEndpoint, getApiEndpoint } from '#/api';
import { accessRoutes, coreRouteNames } from '#/router/routes';
import {
  HOME_PATHS,
  LOGIN_PATHS,
  TokenStorage,
  useMultiAuthStore,
} from '#/store';

import { generateAccess } from './access';

/** 根据路由路径获取对应端的登录路径 */
function getLoginPathByRoute(path: string): string {
  const endpoint = getApiEndpoint(path);
  return LOGIN_PATHS[endpoint];
}

/** 根据路由路径获取对应端的首页路径 */
function getHomePathByRoute(path: string): string {
  const endpoint = getApiEndpoint(path);
  return HOME_PATHS[endpoint];
}

/** 判断是否是登录页面 */
function isLoginPath(path: string): boolean {
  return Object.values(LOGIN_PATHS).includes(path);
}

/**
 * 通用守卫配置
 * @param router
 */
function setupCommonGuard(router: Router) {
  // 记录已经加载的页面
  const loadedPaths = new Set<string>();

  router.beforeEach((to) => {
    to.meta.loaded = loadedPaths.has(to.path);

    // 页面加载进度条
    if (!to.meta.loaded && preferences.transition.progress) {
      startProgress();
    }
    return true;
  });

  router.afterEach((to) => {
    // 记录页面是否加载,如果已经加载，后续的页面切换动画等效果不在重复执行

    loadedPaths.add(to.path);

    // 关闭页面加载进度条
    if (preferences.transition.progress) {
      stopProgress();
    }
  });
}

/**
 * 权限访问守卫配置
 * @param router
 */
function setupAccessGuard(router: Router) {
  router.beforeEach(async (to, from) => {
    const accessStore = useAccessStore();
    const userStore = useUserStore();
    const multiAuthStore = useMultiAuthStore();

    // 获取当前路由对应的端类型、登录路径和首页路径
    const currentEndpoint: ApiEndpoint = getApiEndpoint(to.path);
    const currentLoginPath = getLoginPathByRoute(to.path);
    const currentHomePath = getHomePathByRoute(to.path);

    // 从 TokenStorage 获取当前端的 Token（多端分离存储）
    const currentToken = TokenStorage.getToken(currentEndpoint);

    // 基本路由，这些路由不需要进入权限拦截
    if (coreRouteNames.includes(to.name as string)) {
      // 如果当前端已登录且访问登录页，重定向到对应端的首页
      if (isLoginPath(to.path) && currentToken) {
        return decodeURIComponent(
          (to.query?.redirect as string) ||
            userStore.userInfo?.homePath ||
            currentHomePath,
        );
      }
      return true;
    }

    // Token 检查（使用当前端的 Token）
    if (!currentToken) {
      // 明确声明忽略权限访问权限，则可以访问
      if (to.meta.ignoreAccess) {
        return true;
      }

      // 没有访问权限，跳转到对应端的登录页面
      if (!isLoginPath(to.path)) {
        return {
          path: currentLoginPath,
          query:
            to.fullPath === currentHomePath
              ? {}
              : { redirect: encodeURIComponent(to.fullPath) },
          replace: true,
        };
      }
      return to;
    }

    // 同步 Token 到 accessStore（兼容 vben 框架组件）
    if (accessStore.accessToken !== currentToken) {
      accessStore.setAccessToken(currentToken);
      const refreshToken = TokenStorage.getRefreshToken(currentEndpoint);
      if (refreshToken) {
        accessStore.setRefreshToken(refreshToken);
      }
    }

    // 是否已经生成过动态路由
    if (accessStore.isAccessChecked) {
      return true;
    }

    // 生成路由表
    // 当前登录用户拥有的角色标识列表
    // 注意：必须传入 endpoint 参数，因为 route.path 可能还是旧路由
    const userInfo =
      userStore.userInfo || (await multiAuthStore.fetchUserInfo(currentEndpoint));
    const userRoles = userInfo.roles ?? [];

    // 生成菜单和路由（根据端类型获取对应的菜单）
    const { accessibleMenus, accessibleRoutes } = await generateAccess(
      {
        roles: userRoles,
        router,
        routes: accessRoutes,
      },
      currentEndpoint,
    );

    // 保存菜单信息和路由信息
    accessStore.setAccessMenus(accessibleMenus);
    accessStore.setAccessRoutes(accessibleRoutes);
    accessStore.setIsAccessChecked(true);

    const redirectPath = (from.query.redirect ??
      (to.path === currentHomePath
        ? userInfo.homePath || currentHomePath
        : to.fullPath)) as string;

    return {
      ...router.resolve(decodeURIComponent(redirectPath)),
      replace: true,
    };
  });
}

/**
 * 项目守卫配置
 * @param router
 */
function createRouterGuard(router: Router) {
  /** 通用 */
  setupCommonGuard(router);
  /** 权限访问 */
  setupAccessGuard(router);
}

export { createRouterGuard };
