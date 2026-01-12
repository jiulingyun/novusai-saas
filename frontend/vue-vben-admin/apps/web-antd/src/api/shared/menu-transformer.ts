/**
 * 菜单数据转换器
 * 将后端返回的菜单数据格式转换为 vben-admin 框架需要的 RouteRecordStringComponent 格式
 */
import type { RouteRecordStringComponent } from '@vben/types';

import type { ApiEndpoint } from './types';

/**
 * 后端返回的菜单项原始格式（snake_case）
 * 根据 RBAC 权限管理开发规范定义
 */
export interface BackendMenuItemRaw {
  id?: number | string;
  code?: string;
  name: string;
  path: string;
  component?: string;
  redirect?: string;
  parent_id?: number | string | null;
  sort_order?: number;
  icon?: string;
  title?: string;
  hidden?: boolean;
  // meta 字段可能是嵌套对象或扁平字段
  meta?: {
    title?: string;
    icon?: string;
    order?: number;
    hide_in_menu?: boolean;
    hide_in_tab?: boolean;
    hide_in_breadcrumb?: boolean;
    affix_tab?: boolean;
    keep_alive?: boolean;
    badge?: string;
    badge_type?: string;
    badge_variants?: string;
    authority?: string[];
    iframe_src?: string;
    link?: string;
  };
  children?: BackendMenuItemRaw[];
}

/**
 * 转换组件路径
 * 将后端返回的组件路径转换为前端 views 目录下的实际路径
 * @param component 后端组件路径，如 /dashboard/Index.vue
 * @param endpoint 端类型
 * @returns 前端组件路径，如 /admin/dashboard/index.vue
 */
function transformComponentPath(
  component: string | undefined,
  endpoint: ApiEndpoint,
): string {
  if (!component) return '';

  // 如果是 layout 组件，不做转换
  if (component === 'BasicLayout' || component === 'IFrameView') {
    return component;
  }

  // 标准化路径：确保以 / 开头
  let path = component.startsWith('/') ? component : `/${component}`;

  // 处理文件扩展名和大小写
  // 后端可能返回 Index.vue，但前端文件通常是 index.vue
  if (path.endsWith('.vue')) {
    // 将文件名转为小写（如 Index.vue -> index.vue）
    const lastSlash = path.lastIndexOf('/');
    const fileName = path.slice(lastSlash + 1);
    path = path.slice(0, lastSlash + 1) + fileName.toLowerCase();
  } else {
    // 没有扩展名的，添加 .vue 并确保小写
    path = `${path.toLowerCase()}.vue`;
  }

  // 根据端类型添加前缀
  // 前端 views 目录结构：views/admin/xxx, views/tenant/xxx
  // 后端返回：/dashboard/index.vue
  // 需要转换为：/admin/dashboard/index.vue 或 /tenant/dashboard/index.vue
  if (endpoint === 'admin' && !path.startsWith('/admin/')) {
    path = `/admin${path}`;
  } else if (endpoint === 'tenant' && !path.startsWith('/tenant/')) {
    path = `/tenant${path}`;
  }
  // user 端暂不添加前缀，可根据实际目录结构调整

  return path;
}

/**
 * 转换单个菜单项
 * @param item 后端菜单项
 * @param endpoint 端类型
 * @returns vben-admin 格式的菜单项
 */
function transformMenuItem(
  item: BackendMenuItemRaw,
  endpoint: ApiEndpoint,
): RouteRecordStringComponent {
  // 构建 meta 对象
  // 后端的 name 字段是菜单显示名称，应作为 meta.title
  // 这是最重要的字段，必须设置，否则框架的 $t() 函数会报错
  const meta: Record<string, any> & { title: string } = {
    title: item.name,
  };

  // 处理 meta 字段（可能来自嵌套对象或扁平字段）
  if (item.meta) {
    // 后端返回的 meta 对象（如果有显式的 title，覆盖默认值）
    if (item.meta.title) meta.title = item.meta.title;
    if (item.meta.icon) meta.icon = item.meta.icon;
    if (item.meta.order !== undefined) meta.order = item.meta.order;
    if (item.meta.hide_in_menu) meta.hideInMenu = item.meta.hide_in_menu;
    if (item.meta.hide_in_tab) meta.hideInTab = item.meta.hide_in_tab;
    if (item.meta.hide_in_breadcrumb)
      meta.hideInBreadcrumb = item.meta.hide_in_breadcrumb;
    if (item.meta.affix_tab) meta.affixTab = item.meta.affix_tab;
    if (item.meta.keep_alive) meta.keepAlive = item.meta.keep_alive;
    if (item.meta.badge) meta.badge = item.meta.badge;
    if (item.meta.badge_type) meta.badgeType = item.meta.badge_type;
    if (item.meta.badge_variants) meta.badgeVariants = item.meta.badge_variants;
    if (item.meta.authority) meta.authority = item.meta.authority;
    if (item.meta.iframe_src) meta.iframeSrc = item.meta.iframe_src;
    if (item.meta.link) meta.link = item.meta.link;
  }

  // 处理扁平字段（兼容不同后端格式）
  if (item.title && item.title !== meta.title) meta.title = item.title;
  if (item.icon && !meta.icon) meta.icon = item.icon;
  if (item.sort_order !== undefined && meta.order === undefined)
    meta.order = item.sort_order;
  if (item.hidden) meta.hideInMenu = item.hidden;

  // 生成路由名称（使用 code 字段或根据 path 生成）
  // 路由名称应该是唯一标识符，不能使用中文
  const routeName = item.code || generateRouteName(item.path, endpoint);

  // 构建路由项
  const route: RouteRecordStringComponent = {
    name: routeName,
    path: item.path,
    component: transformComponentPath(item.component, endpoint),
    meta,
  };

  // 添加可选字段
  if (item.redirect) {
    route.redirect = item.redirect;
  }

  // 递归处理子菜单
  if (item.children && item.children.length > 0) {
    route.children = item.children.map((child) =>
      transformMenuItem(child, endpoint),
    );
  }

  return route;
}

/** 用于收集缺失组件的提示信息 */
interface MissingComponentInfo {
  menuName: string;
  componentPath: string;
  expectedFile: string;
}

/** 组件映射表类型 */
type ComponentMap = Record<string, unknown>;

/** 缓存已存在的组件路径（从 pageMap 解析） */
let cachedExistingPaths: Set<string> | null = null;

/**
 * 设置已存在的组件映射表
 * 这个函数应该在应用启动时调用，传入 import.meta.glob 的结果
 * @param pageMap 组件映射表
 */
export function setExistingComponents(pageMap: ComponentMap): void {
  cachedExistingPaths = new Set<string>();
  for (const key of Object.keys(pageMap)) {
    // 解析路径：../views/admin/dashboard/index.vue -> /admin/dashboard/index.vue
    const normalizedPath = key.replace(/^\.\.?\/views/, '').toLowerCase();
    cachedExistingPaths.add(normalizedPath);
  }
}

/**
 * 检查组件是否存在
 * @param componentPath 组件路径，如 /admin/dashboard/index.vue
 */
function componentExists(componentPath: string): boolean {
  if (!cachedExistingPaths) {
    // 如果没有设置 pageMap，无法检查，默认认为不存在
    return false;
  }
  return cachedExistingPaths.has(componentPath.toLowerCase());
}

/**
 * 转换菜单列表
 * 将后端返回的菜单数据转换为 vben-admin 框架格式
 * @param menus 后端菜单列表
 * @param endpoint 端类型，用于确定组件路径前缀
 * @returns vben-admin 格式的菜单列表
 */
/** 日志前缀 */
const LOG_TAG = '[动态菜单]';

export function transformMenuData(
  menus: BackendMenuItemRaw[],
  endpoint: ApiEndpoint = 'admin',
): RouteRecordStringComponent[] {
  if (!Array.isArray(menus)) {
    console.warn(`${LOG_TAG} 无效的菜单数据:`, menus);
    return [];
  }

  // 收集缺失的组件信息
  const missingComponents: MissingComponentInfo[] = [];

  const result = menus.map((item) =>
    transformMenuItemWithCheck(item, endpoint, missingComponents),
  );

  // 输出友好的警告信息
  if (missingComponents.length > 0) {
    printMissingComponentsWarning(missingComponents, endpoint);
  }

  return result;
}

/**
 * 转换单个菜单项并检查组件
 */
function transformMenuItemWithCheck(
  item: BackendMenuItemRaw,
  endpoint: ApiEndpoint,
  missingComponents: MissingComponentInfo[],
): RouteRecordStringComponent {
  const route = transformMenuItem(item, endpoint);

  // 检查是否有组件路径（排除父级菜单和 layout 组件）
  if (
    route.component &&
    route.component !== 'BasicLayout' &&
    route.component !== 'IFrameView' &&
    route.component !== ''
  ) {
    // 只记录真正缺失的组件
    if (!componentExists(route.component)) {
      missingComponents.push({
        menuName: item.name,
        componentPath: route.component,
        expectedFile: `src/views${route.component}`,
      });
    }
  }

  // 递归处理子菜单
  if (item.children && item.children.length > 0) {
    route.children = item.children.map((child) =>
      transformMenuItemWithCheck(child, endpoint, missingComponents),
    );
  }

  return route;
}

/**
 * 输出缺失组件的警告信息
 */
function printMissingComponentsWarning(
  missingComponents: MissingComponentInfo[],
  endpoint: ApiEndpoint,
): void {
  const endpointName =
    endpoint === 'admin'
      ? '平台管理端'
      : endpoint === 'tenant'
        ? '租户端'
        : '用户端';

  // 使用 console.groupCollapsed 组织输出，美化显示
  console.groupCollapsed(
    `%c${LOG_TAG} 📦 ${endpointName}有 ${missingComponents.length} 个菜单页面组件尚未创建`,
    'color: #faad14; font-weight: bold;',
  );
  console.log('%c请在以下路径创建对应的 Vue 组件文件:', 'color: #1890ff;');

  missingComponents.forEach(({ menuName, expectedFile }) => {
    console.log(`  • 「${menuName}」 → %c${expectedFile}`, 'color: #52c41a;');
  });

  console.log('%c提示: 这些菜单将显示为 404 页面，直到创建对应组件', 'color: #999;');
  console.groupEnd();
}

/**
 * 根据路径生成路由名称
 * @param path 路由路径
 * @param endpoint 端类型
 * @returns 路由名称
 */
function generateRouteName(path: string, endpoint: ApiEndpoint): string {
  // 将路径转换为路由名称，如 /system/admins -> admin.system.admins
  const cleanPath = path.replace(/^\//,  '').replace(/\//g, '.');
  return `${endpoint}.${cleanPath || 'index'}`;
}

/**
 * 判断后端返回的菜单是否需要转换
 * 如果后端返回的数据已经是 camelCase 格式，则不需要转换
 * @param menus 菜单数据
 * @returns 是否需要转换
 */
export function needsTransform(menus: any[]): boolean {
  if (!Array.isArray(menus) || menus.length === 0) {
    return false;
  }

  const firstItem = menus[0];

  // 检查是否有 snake_case 字段
  return (
    'parent_id' in firstItem ||
    'sort_order' in firstItem ||
    (firstItem.meta &&
      ('hide_in_menu' in firstItem.meta ||
        'hide_in_tab' in firstItem.meta ||
        'affix_tab' in firstItem.meta))
  );
}
