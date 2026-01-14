/**
 * Store 统一导出
 * 按端分离的状态管理
 */

// 平台管理端状态
export * from './admin';

// 兼容旧代码，保留原auth导出
export * from './auth';

// 共享状态（多端通用）
export * from './shared';

// 租户管理端状态
export * from './tenant';

// 用户端状态
export * from './user';
