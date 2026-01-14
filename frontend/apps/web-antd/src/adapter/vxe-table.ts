import type { VxeTableGridOptions } from '@vben/plugins/vxe-table';
import type { Recordable } from '@vben/types';

import { h } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { $te } from '@vben/locales';
import {
  setupVbenVxeTable,
  useVbenVxeGrid as useGrid,
} from '@vben/plugins/vxe-table';
import { useAccessStore } from '@vben/stores';
import { get, isFunction, isString } from '@vben/utils';

import { objectOmit } from '@vueuse/core';
import {
  Button,
  Image,
  Popconfirm,
  Switch,
  Tag,
  Tooltip,
} from 'ant-design-vue';

import { $t } from '#/locales';
import { checkPermission } from '#/utils/access';

import { useVbenForm } from './form';
import { exportToExcel } from './vxe-table-extensions';

setupVbenVxeTable({
  configVxeTable: (vxeUI) => {
    vxeUI.setConfig({
      grid: {
        align: 'center',
        border: false,
        columnConfig: {
          resizable: true,
        },
        minHeight: 180,
        formConfig: {
          // 全局禁用vxe-table的表单配置，使用formOptions
          enabled: false,
        },
        pagerConfig: {
          pageSize: 10,
          pageSizes: [10, 20, 50, 100],
        },
        proxyConfig: {
          autoLoad: true,
          response: {
            result: 'items',
            total: 'total',
            list: 'items',
          },
          showActiveMsg: true,
          showResponseMsg: false,
        },
        // 导出配置（仅支持 csv）
        exportConfig: {
          type: 'csv',
        },
        round: true,
        showOverflow: true,
        size: 'small',
      } as VxeTableGridOptions,
    });

    /**
     * 解决vxeTable在热更新时可能会出错的问题
     */
    vxeUI.renderer.forEach((_item, key) => {
      if (key.startsWith('Cell') || key === 'DragHandle') {
        vxeUI.renderer.delete(key);
      }
    });

    // 拖拽手柄渲染器
    vxeUI.renderer.add('DragHandle', {
      renderTableDefault() {
        return h(IconifyIcon, {
          icon: 'lucide:grip-vertical',
          class: 'drag-handle cursor-move text-gray-400 hover:text-gray-600',
        });
      },
    });

    // 表格配置项可以用 cellRender: { name: 'CellImage' },
    vxeUI.renderer.add('CellImage', {
      renderTableDefault(renderOpts, params) {
        const { props } = renderOpts;
        const { column, row } = params;
        return h(Image, { src: row[column.field], ...props });
      },
    });

    // 表格配置项可以用 cellRender: { name: 'CellLink' },
    vxeUI.renderer.add('CellLink', {
      renderTableDefault(renderOpts) {
        const { props } = renderOpts;
        return h(
          Button,
          { size: 'small', type: 'link' },
          { default: () => props?.text },
        );
      },
    });

    // 单元格渲染： Tag
    vxeUI.renderer.add('CellTag', {
      renderTableDefault({ options, props }, { column, row }) {
        const value = get(row, column.field);
        const tagOptions = options ?? [
          { color: 'success', label: $t('common.enabled'), value: 1 },
          { color: 'error', label: $t('common.disabled'), value: 0 },
        ];
        const tagItem = tagOptions.find((item) => item.value === value);
        return h(
          Tag,
          {
            ...props,
            ...objectOmit(tagItem ?? {}, ['label']),
          },
          { default: () => tagItem?.label ?? value },
        );
      },
    });

    // 单元格渲染： Switch
    vxeUI.renderer.add('CellSwitch', {
      renderTableDefault({ attrs, props }, { column, row }) {
        const loadingKey = `__loading_${column.field}`;
        const finallyProps = {
          checkedChildren: $t('common.enabled'),
          checkedValue: true,
          unCheckedChildren: $t('common.disabled'),
          unCheckedValue: false,
          ...props,
          ...attrs,
          checked: row[column.field],
          loading: row[loadingKey] ?? false,
          'onUpdate:checked': onChange,
        };
        async function onChange(newVal: any) {
          row[loadingKey] = true;
          try {
            const result = await attrs?.beforeChange?.(newVal, row);
            if (result !== false) {
              row[column.field] = newVal;
            }
          } finally {
            row[loadingKey] = false;
          }
        }
        return h(Switch, finallyProps);
      },
    });

    /**
     * 注册表格的操作按钮渲染器
     * 现代化样式：纯图标按钮 + Tooltip 提示
     *
     * 权限控制：
     * - 设置 attrs.resource 后，CRUD 按钮自动根据 {resource}:{action} 格式检查权限
     * - 自动映射：edit -> {resource}:update, delete -> {resource}:delete
     * - 自定义按钮可通过 accessCodes 手动指定权限码
     * - 超级管理员（拥有 '*' 权限）自动拥有所有权限
     *
     * @example
     * ```ts
     * cellRender: {
     *   name: 'CellOperation',
     *   attrs: {
     *     resource: 'admin_user',  // 自动检查 admin_user:update, admin_user:delete
     *     onClick: onActionClick,
     *   },
     *   options: ['edit', 'delete'],  // 标准 CRUD 按钮，自动鉴权
     * }
     * ```
     */
    vxeUI.renderer.add('CellOperation', {
      renderTableDefault({ attrs, options }, { column, row }) {
        let align = 'end';
        switch (column.align) {
          case 'center': {
            align = 'center';
            break;
          }
          case 'left': {
            align = 'start';
            break;
          }
          default: {
            align = 'end';
            break;
          }
        }

        // 标准 CRUD 操作与权限动作的映射
        const crudActionMap: Record<string, string> = {
          edit: 'update',
          delete: 'delete',
          create: 'create',
          view: 'read',
          detail: 'read',
        };

        // 预设操作配置
        const presets: Recordable<Recordable<any>> = {
          delete: {
            danger: true,
            text: $t('common.delete'),
            icon: 'lucide:trash-2',
          },
          edit: {
            text: $t('common.edit'),
            icon: 'lucide:pencil',
          },
          resetPassword: {
            text: $t('common.resetPassword'),
            icon: 'lucide:key-round',
          },
        };

        // 获取当前用户的权限码
        const accessStore = useAccessStore();
        const userCodes = accessStore.accessCodes;
        const resource = attrs?.resource as string | undefined;

        /**
         * 计算操作按钮的实际权限码
         * 优先使用手动指定的 accessCodes，否则根据 resource 自动计算
         */
        function getAccessCodes(
          opt: Recordable<any>,
        ): string[] | undefined {
          // 1. 如果手动指定了 accessCodes，直接使用
          if (opt.accessCodes) {
            return opt.accessCodes;
          }
          // 2. 如果设置了 resource 且是标准 CRUD 操作，自动计算权限码
          if (resource && crudActionMap[opt.code]) {
            return [`${resource}:${crudActionMap[opt.code]}`];
          }
          // 3. 其他情况不限制权限（返回 undefined 表示不检查）
          return undefined;
        }

        const operations: Array<Recordable<any>> = (
          options || ['edit', 'delete']
        )
          .map((opt) => {
            if (isString(opt)) {
              return presets[opt]
                ? { code: opt, ...presets[opt] }
                : {
                    code: opt,
                    text: $te(`common.${opt}`) ? $t(`common.${opt}`) : opt,
                  };
            } else {
              return { ...presets[opt.code], ...opt };
            }
          })
          .map((opt) => {
            const optBtn: Recordable<any> = {};
            Object.keys(opt).forEach((key) => {
              optBtn[key] = isFunction(opt[key]) ? opt[key](row) : opt[key];
            });
            return optBtn;
          })
          .filter((opt) => opt.show !== false)
          // 按权限码过滤操作按钮（使用自动计算的权限码）
          .filter((opt) => checkPermission(getAccessCodes(opt), userCodes));

        // 渲染图标按钮（带 Tooltip）
        function renderIconBtn(opt: Recordable<any>, listen = true) {
          const iconBtn = h(
            Button,
            {
              type: 'text',
              size: 'small',
              danger: opt.danger,
              class: 'action-icon-btn',
              onClick: listen
                ? () =>
                    attrs?.onClick?.({
                      code: opt.code,
                      row,
                    })
                : undefined,
            },
            {
              default: () =>
                h(IconifyIcon, {
                  icon: opt.icon || 'lucide:circle',
                  class: 'text-base',
                }),
            },
          );

          // 用 Tooltip 包裹
          return h(
            Tooltip,
            {
              title: opt.text,
              placement: 'top',
            },
            { default: () => iconBtn },
          );
        }

        function renderConfirm(opt: Recordable<any>) {
          let viewportWrapper: HTMLElement | null = null;
          const iconBtn = h(
            Button,
            {
              type: 'text',
              size: 'small',
              danger: true,
              class: 'action-icon-btn',
            },
            {
              default: () =>
                h(IconifyIcon, {
                  icon: opt.icon || 'lucide:trash-2',
                  class: 'text-base',
                }),
            },
          );

          return h(
            Popconfirm,
            {
              getPopupContainer(el) {
                viewportWrapper = el.closest('.vxe-table--viewport-wrapper');
                return document.body;
              },
              placement: 'topLeft',
              title: $t('ui.actionTitle.delete', [attrs?.nameTitle || '']),
              onOpenChange: (open: boolean) => {
                if (open) {
                  viewportWrapper?.style.setProperty('pointer-events', 'none');
                } else {
                  viewportWrapper?.style.removeProperty('pointer-events');
                }
              },
              onConfirm: () => {
                attrs?.onClick?.({
                  code: opt.code,
                  row,
                });
              },
            },
            {
              default: () =>
                h(
                  Tooltip,
                  { title: opt.text, placement: 'top' },
                  { default: () => iconBtn },
                ),
              description: () =>
                h(
                  'div',
                  { class: 'truncate' },
                  $t('ui.actionMessage.deleteConfirm', [
                    row[attrs?.nameField || 'name'],
                  ]),
                ),
            },
          );
        }

        const btns = operations.map((opt) =>
          opt.code === 'delete' ? renderConfirm(opt) : renderIconBtn(opt),
        );

        return h(
          'div',
          {
            class: 'flex items-center gap-1 table-operations',
            style: { justifyContent: align },
          },
          btns,
        );
      },
    });

    // 这里可以自行扩展 vxe-table 的全局配置，比如自定义格式化
    // vxeUI.formats.add
  },
  useVbenForm,
});

export type OnActionClickParams<T = Recordable<any>> = {
  code: string;
  row: T;
};
export type OnActionClickFn<T = Recordable<any>> = (
  params: OnActionClickParams<T>,
) => void;

/**
 * 标准列表搜索表单配置
 *
 * 用于列表页面的搜索表单，提供统一的配置：
 * - 启用输入即搜索 (submitOnChange)
 * - 隐藏搜索按钮（因为已启用输入即搜索）
 * - 重置按钮使用文字样式，与收起按钮一致
 *
 * @param schema 表单 schema
 * @returns formOptions 配置对象
 *
 * @example
 * ```ts
 * const [Grid, gridApi] = useVbenVxeGrid({
 *   formOptions: useGridSearchFormOptions(useGridFormSchema()),
 *   gridOptions: { ... },
 * });
 * ```
 */
export function useGridSearchFormOptions(schema: any[]) {
  return {
    schema,
    submitOnChange: true,
    // 隐藏搜索按钮（因为已启用 submitOnChange）
    submitButtonOptions: {
      show: false,
    },
    // 重置按钮使用文字样式，与收起按钮一致
    resetButtonOptions: {
      variant: 'ghost' as const,
      size: 'sm' as const,
    },
  };
}
// 拖拽排序
export {
  dragColumn,
  type DragSortConfig,
  useTableDragSort,
} from './vxe-table-drag-sort';

/**
 * 增强版 useVbenVxeGrid
 * - 添加 exportExcel 方法
 *
 * @example
 * ```ts
 * const [Grid, gridApi] = useVbenVxeGrid({ gridOptions });
 *
 * // 导出 Excel
 * gridApi.exportExcel({ filename: '用户列表' });
 * ```
 */
export function useVbenVxeGrid(
  options: Parameters<typeof useGrid>[0],
) {
  // 调用原始的 useGrid
  const result = useGrid(options);

  // 扩展 gridApi，添加导出方法
  const [Grid, originalGridApi] = result;

  // 添加导出方法到原始 API
  (originalGridApi as any).exportExcel = (
    exportOptions?: Parameters<typeof exportToExcel>[1],
  ) => {
    return exportToExcel(originalGridApi.grid, exportOptions);
  };

  return [Grid, originalGridApi] as const;
}

/**
 * 表格配置工厂函数 - 极简化表格配置
 *
 * 提供合理的默认值，用户只需传入必要配置
 *
 * @example
 * ```ts
 * const [Grid, gridApi] = useVbenVxeGrid({
 *   formOptions: useGridSearchFormOptions(useGridFormSchema()),
 *   gridOptions: useGridOptions({
 *     columns: useColumns(onActionClick, onToggleStatus),
 *     queryApi: (params) => api.getListApi(params),
 *   }),
 * });
 * ```
 */
export interface GridOptionsConfig<T = any> {
  /** 列配置（必填） */
  columns: VxeTableGridOptions<T>['columns'];
  /** 查询 API 函数（必填） */
  queryApi: (params: Record<string, any>) => Promise<any>;
  /** 默认排序字段，默认 '-created_at' */
  defaultSort?: string;
  /** 行高，默认 64 */
  rowHeight?: number;
  /** 是否启用分页，默认 true */
  pager?: boolean;
  /** 工具栏配置，默认显示全部 */
  toolbar?: {
    custom?: boolean;
    export?: boolean;
    refresh?: boolean;
    search?: boolean;
    zoom?: boolean;
  };
  /** 其他自定义配置 */
  [key: string]: any;
}

export function useGridOptions<T = any>(
  config: GridOptionsConfig<T>,
): VxeTableGridOptions<T> {
  const {
    columns,
    queryApi,
    defaultSort = '-created_at',
    rowHeight = 64,
    pager = true,
    toolbar = { custom: true, export: true, refresh: true, search: true, zoom: true },
    ...rest
  } = config;

  return {
    columns,
    keepSource: true,
    pagerConfig: { enabled: pager },
    proxyConfig: {
      ajax: {
        query: async ({ page }, formValues) => {
          return await queryApi({
            ...formValues,
            'page[number]': page.currentPage,
            'page[size]': page.pageSize,
            'sort': defaultSort,
          });
        },
      },
    },
    cellConfig: { height: rowHeight },
    rowConfig: { keyField: 'id' },
    toolbarConfig: toolbar,
    ...rest,
  } as VxeTableGridOptions<T>;
}

// 表格扩展功能
export {
  // 批量选择
  checkboxColumn,
  clearSelection,
  createExpandConfig,
  // 展开行
  expandColumn,
  type ExpandConfig,
  type ExportColumn,
  type ExportOptions,
  // Excel 导出
  exportToExcel,
  getSelectedIds,
  getSelectedRows,
  seqColumn,
} from './vxe-table-extensions';

export type * from '@vben/plugins/vxe-table';
