/**
 * 通用 CRUD 操作 Composable
 *
 * 封装列表页面常用的增删改查操作，减少重复代码
 *
 * @module composables/use-crud-actions
 *
 * @example 简单用法（推荐）
 * ```ts
 * const crud = useCrudActions({
 *   gridApi,
 *   formDrawerApi,
 *   deleteApi: api.deleteAdminApi,
 *   i18nPrefix: 'admin.system.admin',
 * });
 * ```
 *
 * @example 完整配置
 * ```ts
 * const { onDelete, onToggleStatus, onEdit, onCreate, onRefresh } = useCrudActions({
 *   gridApi,
 *   formDrawerApi,
 *   deleteApi: api.deleteAdminApi,
 *   toggleStatusApi: api.toggleAdminStatusApi,
 *   i18nPrefix: 'admin.system.admin',
 *   nameField: 'username',  // 默认 'name'
 * });
 * ```
 */

import { message, Modal } from 'ant-design-vue';

import { $t } from '#/locales';

/**
 * 表单抽屉/弹窗 API 接口
 * 兼容 ExtendedDrawerApi 和 ExtendedModalApi
 */
interface FormPopupApi {
  setData: (data: Record<string, unknown>) => FormPopupApi;
  open: () => void;
}

/**
 * Grid API 接口
 */
interface GridApi {
  query: () => void;
}

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
 * - add: 新建
 * - edit: 编辑
 * - copy: 复制（预留扩展）
 * - view: 查看（预留扩展）
 */
export type FormMode = 'add' | 'copy' | 'edit' | 'view';

/**
 * useCrudActions 配置选项
 */
export interface UseCrudActionsOptions<T extends BaseRow = BaseRow> {
  /** vxe-grid API 实例（必填） */
  gridApi: GridApi;

  /** 表单抽屉 API（与 formModalApi 二选一） */
  formDrawerApi?: FormPopupApi;

  /** 表单弹窗 API（与 formDrawerApi 二选一） */
  formModalApi?: FormPopupApi;

  /** 删除 API 函数 */
  deleteApi?: (id: number | string) => Promise<unknown>;

  /** 切换状态 API 函数 */
  toggleStatusApi?: (
    id: number | string,
    data: { is_active: boolean },
  ) => Promise<unknown>;

  /** i18n 前缀（必填） */
  i18nPrefix: string;

  /** 用于显示的名称字段，默认 'name' */
  nameField?: keyof T & string;
}

/**
 * useCrudActions 返回值
 */
export interface UseCrudActionsReturn<T extends BaseRow> {
  /** 删除操作 */
  onDelete: (row: T) => void;
  /** 切换状态操作 */
  onToggleStatus: (newStatus: boolean, row: T) => Promise<boolean>;
  /** 编辑操作 */
  onEdit: (row: T) => void;
  /** 新建操作 */
  onCreate: () => void;
  /** 刷新列表 */
  onRefresh: () => void;
}

/**
 * 通用 CRUD 操作 Composable
 */
export function useCrudActions<T extends BaseRow = BaseRow>(
  options: UseCrudActionsOptions<T>,
): UseCrudActionsReturn<T> {
  const {
    gridApi,
    formDrawerApi,
    formModalApi,
    deleteApi,
    toggleStatusApi,
    i18nPrefix,
    nameField = 'name',
  } = options;

  // 从 i18nPrefix 提取实体名称（用于 message key）
  const name = i18nPrefix.split('.').pop() || 'item';

  // 形式化的弹窗 API
  const popupApi = formDrawerApi || formModalApi;

  /**
   * 刷新列表
   */
  function onRefresh() {
    gridApi.query();
  }

  /**
   * 新建
   */
  function onCreate() {
    popupApi?.setData({ mode: 'add' as FormMode }).open();
  }

  /**
   * 编辑
   */
  function onEdit(row: T) {
    popupApi?.setData({ ...row, mode: 'edit' as FormMode }).open();
  }

  /**
   * 删除
   */
  function onDelete(row: T) {
    if (!deleteApi) {
      console.warn(`[useCrudActions] deleteApi not provided for ${name}`);
      return;
    }

    const displayName = String(row[nameField] || row.id);
    const messageKey = `delete_${name}`;

    Modal.confirm({
      title: $t(`${i18nPrefix}.messages.deleteTitle`),
      content: $t(`${i18nPrefix}.messages.deleteConfirm`, {
        name: displayName,
      }),
      okText: $t('common.delete'),
      okButtonProps: { danger: true },
      type: 'warning',
      onOk: async () => {
        const hideLoading = message.loading({
          content: $t(`${i18nPrefix}.messages.deleting`, { name: displayName }),
          duration: 0,
          key: messageKey,
        });
        try {
          await deleteApi(row.id);
          message.success({
            content: $t(`${i18nPrefix}.messages.deleteSuccess`),
            key: messageKey,
          });
          onRefresh();
        } catch {
          hideLoading();
        }
      },
    });
  }

  /**
   * 切换状态
   */
  async function onToggleStatus(newStatus: boolean, row: T): Promise<boolean> {
    if (!toggleStatusApi) {
      console.warn(`[useCrudActions] toggleStatusApi not provided for ${name}`);
      return false;
    }

    const displayName = String(row[nameField] || row.id);
    const action = newStatus
      ? $t('admin.common.enable')
      : $t('admin.common.disable');

    try {
      await new Promise<void>((resolve, reject) => {
        Modal.confirm({
          title: $t(`${i18nPrefix}.messages.toggleStatusTitle`),
          content: $t(`${i18nPrefix}.messages.toggleStatusConfirm`, {
            action,
            name: displayName,
          }),
          onOk: () => resolve(),
          onCancel: () => reject(new Error('cancelled')),
        });
      });

      await toggleStatusApi(row.id, { is_active: newStatus });
      message.success(`${action}${$t('ui.actionMessage.operationSuccess')}`);
      return true;
    } catch {
      return false;
    }
  }

  return {
    onDelete,
    onToggleStatus,
    onEdit,
    onCreate,
    onRefresh,
  };
}

export default useCrudActions;
