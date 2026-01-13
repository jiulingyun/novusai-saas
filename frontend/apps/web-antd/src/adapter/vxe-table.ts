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
import { Button, Image, Popconfirm, Switch, Tag, Tooltip } from 'ant-design-vue';

import { $t } from '#/locales';

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
        const isSuperAdmin = userCodes.includes('*');

        /**
         * 检查操作按钮的权限
         */
        function hasAccess(accessCodes?: string | string[]): boolean {
          if (!accessCodes || accessCodes.length === 0) return true;
          if (isSuperAdmin) return true;
          const codes = Array.isArray(accessCodes)
            ? accessCodes
            : [accessCodes];
          return codes.some((code) => userCodes.includes(code));
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
          // 按权限码过滤操作按钮
          .filter((opt) => hasAccess(opt.accessCodes));

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
export type * from '@vben/plugins/vxe-table';

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
export function useVbenVxeGrid<T = any>(
  options: Parameters<typeof useGrid>[0],
) {
  // 调用原始的 useGrid
  const result = useGrid(options);

  // 扩展 gridApi，添加导出方法
  const [Grid, originalGridApi] = result;
  
  // 添加导出方法到原始 API
  (originalGridApi as any).exportExcel = (exportOptions?: Parameters<typeof exportToExcel>[1]) => {
    return exportToExcel(originalGridApi.grid, exportOptions);
  };

  return [Grid, originalGridApi] as const;
}

// 拖拽排序
export {
  dragColumn,
  useTableDragSort,
  type DragSortConfig,
} from './vxe-table-drag-sort';

// 表格扩展功能
export {
  // 批量选择
  checkboxColumn,
  seqColumn,
  getSelectedRows,
  getSelectedIds,
  clearSelection,
  // Excel 导出
  exportToExcel,
  type ExportColumn,
  type ExportOptions,
  // 展开行
  expandColumn,
  createExpandConfig,
  type ExpandConfig,
} from './vxe-table-extensions';
