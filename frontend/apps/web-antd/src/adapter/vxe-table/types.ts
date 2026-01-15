/**
 * 声明式表格类型定义
 */
import type { Component } from 'vue';

import type { VbenFormSchema } from '#/adapter/form';
import type { Recordable } from '@vben/types';

// 从 vben 插件导出基础类型
export type { VxeTableGridOptions } from '@vben/plugins/vxe-table';

/**
 * 操作按钮点击参数
 */
export interface OnActionClickParams<T = Recordable<any>> {
  code: string;
  row: T;
}

/**
 * 操作按钮点击回调函数
 */
export type OnActionClickFn<T = Recordable<any>> = (
  params: OnActionClickParams<T>,
) => void;

/**
 * 基础行数据接口
 */
export interface BaseRow {
  id: number | string;
  isActive?: boolean;
  is_active?: boolean;
  name?: string;
  [key: string]: any;
}

/**
 * 表单操作模式
 */
export type FormMode = 'add' | 'copy' | 'edit' | 'view';

/**
 * 列定义函数类型
 * 返回 VxeTableGridOptions['columns'] 类型（可以是 undefined）
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars
export type ColumnsFactory<_T = any> = (...args: any[]) => any[] | undefined;

/**
 * API 配置
 */
export interface CrudApiConfig<T = any> {
  /** 列表查询 API（必填） */
  list: (params: Record<string, any>) => Promise<{ items: T[]; total: number }>;
  /** 删除 API */
  delete?: (id: any) => Promise<unknown>;
  /** 切换状态 API */
  toggleStatus?: (id: any, data: { is_active: boolean }) => Promise<unknown>;
}

/**
 * 工具栏配置
 */
export interface ToolbarConfig {
  custom?: boolean;
  export?: boolean;
  refresh?: boolean;
  search?: boolean;
  zoom?: boolean;
}

/**
 * useCrudPage 配置选项
 */
export interface UseCrudPageOptions<T extends BaseRow = BaseRow> {
  /** API 配置（必填） */
  api: CrudApiConfig<T>;

  /** 列定义函数（必填） */
  columns: ColumnsFactory<T>;

  /** 搜索表单 Schema */
  searchSchema?: VbenFormSchema[];

  /** 表单组件 */
  formComponent?: Component;

  /** 表单类型：drawer 或 modal，默认 drawer */
  formType?: 'drawer' | 'modal';

  /** i18n 前缀（必填） */
  i18nPrefix: string;

  /** 用于显示的名称字段，默认 'name' */
  nameField?: keyof T & string;

  /** 默认排序字段，默认 '-created_at' */
  defaultSort?: string;

  /** 行高，默认 64 */
  rowHeight?: number;

  /** 是否启用分页，默认 true */
  pager?: boolean;

  /** 工具栏配置 */
  toolbar?: ToolbarConfig;

  /** 自定义操作处理器（用于扩展非标准操作） */
  customActions?: Record<string, (row: T) => void>;
}

/**
 * 表格配置工厂函数参数
 */
export interface GridOptionsConfig {
  /** 列配置（必填） */
  columns: any[];
  /** 查询 API 函数（必填） */
  queryApi: (params: Record<string, any>) => Promise<any>;
  /** 默认排序字段，默认 '-created_at' */
  defaultSort?: string;
  /** 行高，默认 64 */
  rowHeight?: number;
  /** 是否启用分页，默认 true */
  pager?: boolean;
  /** 工具栏配置，默认显示全部 */
  toolbar?: ToolbarConfig;
  /** 其他自定义配置 */
  [key: string]: any;
}
