/**
 * 声明式表格模块
 *
 * 统一导出所有表格相关功能
 */

// ============ 初始化（应用启动时调用） ============
export { setupVxeTable } from './setup';

// ============ 核心 Hook ============
// 推荐使用 useCrudPage，一行代码搞定列表页
export { useCrudPage } from './use-crud-page';

// 基础 Hook（useCrudPage 内部使用，也可单独使用）
export {
  useGridOptions,
  useGridSearchFormOptions,
  useVbenVxeGrid,
} from './use-vxe-grid';

// ============ 类型定义 ============
export type {
  BaseRow,
  ColumnsFactory,
  CrudApiConfig,
  FormMode,
  GridOptionsConfig,
  OnActionClickFn,
  OnActionClickParams,
  ToolbarConfig,
  UseCrudPageOptions,
  VxeTableGridOptions,
} from './types';

// ============ 扩展功能 ============
// 批量选择
export {
  checkboxColumn,
  clearSelection,
  getSelectedIds,
  getSelectedRows,
  seqColumn,
} from './extensions';

// Excel 导出
export {
  exportToExcel,
  type ExportColumn,
  type ExportOptions,
} from './extensions';

// 展开行
export {
  createExpandConfig,
  expandColumn,
  type ExpandConfig,
} from './extensions';

// 拖拽排序
export {
  dragColumn,
  type DragSortConfig,
  useTableDragSort,
} from './drag-sort';

// ============ 从 vben 插件导出基础类型 ============
export type * from '@vben/plugins/vxe-table';
