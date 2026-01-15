/**
 * 声明式 CRUD 列表页 Composable
 *
 * 将表格、表单弹窗、CRUD 操作、分页、排序等统一封装，
 * 用户只需关心：列定义、API、表单组件。
 *
 * @example
 * ```ts
 * const { Grid, FormDrawer, onCreate, onRefresh } = useCrudPage<AdminInfo>({
 *   api: {
 *     list: admin.getAdminListApi,
 *     delete: admin.deleteAdminApi,
 *     toggleStatus: admin.toggleAdminStatusApi,
 *   },
 *   columns: useColumns,
 *   searchSchema: useGridFormSchema(),
 *   formComponent: Form,
 *   i18nPrefix: 'admin.system.admin',
 *   nameField: 'username',
 * });
 * ```
 */

import type { BaseRow, FormMode, OnActionClickParams, UseCrudPageOptions } from './types';

import { useVbenDrawer, useVbenModal } from '@vben/common-ui';

import { message, Modal } from 'ant-design-vue';

import { $t } from '#/locales';

import { useGridSearchFormOptions, useVbenVxeGrid } from './use-vxe-grid';

/**
 * 声明式 CRUD 列表页 Composable
 */
export function useCrudPage<T extends BaseRow = BaseRow>(
  options: UseCrudPageOptions<T>,
) {
  const {
    api,
    columns,
    searchSchema,
    formComponent,
    formType = 'drawer',
    i18nPrefix,
    nameField = 'name' as keyof T & string,
    defaultSort = '-created_at',
    rowHeight = 64,
    pager = true,
    toolbar = { custom: true, export: true, refresh: true, search: true, zoom: true },
    customActions = {},
  } = options;

  // 从 i18nPrefix 提取实体名称（用于 message key）
  const entityName = i18nPrefix.split('.').pop() || 'item';

  // ==================== 表单弹窗 ====================
  let FormPopup: ReturnType<typeof useVbenDrawer>[0] | null = null;
  let formPopupApi: ReturnType<typeof useVbenDrawer>[1] | ReturnType<typeof useVbenModal>[1] | null = null;

  if (formComponent) {
    if (formType === 'modal') {
      const [ModalComp, modalApi] = useVbenModal({
        connectedComponent: formComponent,
        destroyOnClose: true,
      });
      FormPopup = ModalComp as any;
      formPopupApi = modalApi as any;
    } else {
      const [Drawer, drawerApi] = useVbenDrawer({
        connectedComponent: formComponent,
        destroyOnClose: true,
      });
      FormPopup = Drawer;
      formPopupApi = drawerApi;
    }
  }

  // ==================== CRUD 操作 ====================

  // 前置声明 gridApi（用于闭包引用）
  let gridApi: ReturnType<typeof useVbenVxeGrid>[1];

  /** 刷新列表 */
  function onRefresh() {
    gridApi?.query();
  }

  /** 重载列表（回到第一页） */
  function onReload() {
    gridApi?.reload();
  }

  /** 新建 */
  function onCreate() {
    formPopupApi?.setData({ mode: 'add' as FormMode }).open();
  }

  /** 编辑 */
  function onEdit(row: T) {
    formPopupApi?.setData({ ...row, mode: 'edit' as FormMode }).open();
  }

  /** 删除 */
  function onDelete(row: T) {
    if (!api.delete) {
      console.warn(`[useCrudPage] api.delete not provided for ${entityName}`);
      return;
    }

    const displayName = String(row[nameField] || row.id);
    const messageKey = `delete_${entityName}`;

    Modal.confirm({
      title: $t(`${i18nPrefix}.messages.deleteTitle`),
      content: $t(`${i18nPrefix}.messages.deleteConfirm`, { name: displayName }),
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
          await api.delete!(row.id);
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

  /** 切换状态 */
  async function onToggleStatus(newStatus: boolean, row: T): Promise<boolean> {
    if (!api.toggleStatus) {
      console.warn(`[useCrudPage] api.toggleStatus not provided for ${entityName}`);
      return false;
    }

    const displayName = String(row[nameField] || row.id);
    const action = newStatus ? $t('admin.common.enable') : $t('admin.common.disable');

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

      await api.toggleStatus(row.id, { is_active: newStatus });
      message.success(`${action}${$t('ui.actionMessage.operationSuccess')}`);
      return true;
    } catch {
      return false;
    }
  }

  // ==================== 操作处理器 ====================

  /** 操作按钮点击处理 */
  function handleActionClick(e: OnActionClickParams<T>) {
    switch (e.code) {
      case 'delete': {
        onDelete(e.row);
        break;
      }
      case 'edit': {
        onEdit(e.row);
        break;
      }
      default: {
        // 自定义操作
        const action = customActions[e.code];
        if (action) {
          action(e.row);
        }
        break;
      }
    }
  }

  /** 状态切换处理（供列定义使用） */
  function handleToggleStatus(newStatus: boolean, row: T) {
    return onToggleStatus(newStatus, row);
  }

  // ==================== 表格配置 ====================

  const gridOptions = {
    columns: columns(handleActionClick, handleToggleStatus),
    keepSource: true,
    pagerConfig: { enabled: pager },
    proxyConfig: {
      ajax: {
        query: async ({ page }: any, formValues: any) => {
          return await api.list({
            ...formValues,
            'page[number]': page.currentPage,
            'page[size]': page.pageSize,
            sort: defaultSort,
          });
        },
      },
    },
    cellConfig: { height: rowHeight },
    rowConfig: { keyField: 'id' },
    toolbarConfig: toolbar,
  };

  // 创建表格
  const [Grid, _gridApi] = useVbenVxeGrid({
    formOptions: searchSchema ? useGridSearchFormOptions(searchSchema) : undefined,
    gridOptions,
  });

  // 赋值给闭包引用
  gridApi = _gridApi;

  return {
    // 组件
    Grid,
    gridApi,
    FormDrawer: FormPopup,
    formApi: formPopupApi,

    // CRUD 操作
    onCreate,
    onEdit,
    onDelete,
    onToggleStatus,
    onRefresh,
    onReload,

    // 处理器
    handleActionClick,
    handleToggleStatus,
  };
}
