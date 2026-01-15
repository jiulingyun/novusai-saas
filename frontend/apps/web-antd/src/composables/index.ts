/**
 * Composables 统一导出
 */

// 声明式表格相关（从 vxe-table 模块重新导出）
export {
  useCrudPage,
  type BaseRow,
  type ColumnsFactory,
  type CrudApiConfig,
  type FormMode,
  type ToolbarConfig,
  type UseCrudPageOptions,
} from '#/adapter/vxe-table';

export {
  useRemoteSelect,
  type UseRemoteSelectOptions,
  type UseRemoteSelectReturn,
} from './use-remote-select';
