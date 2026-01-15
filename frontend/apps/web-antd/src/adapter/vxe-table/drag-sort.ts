/**
 * 表格拖拽排序功能
 * 基于 sortablejs 实现，与 vxe-table 配合使用
 */
import type { VxeGridInstance } from 'vxe-table';

import { h, nextTick, onUnmounted } from 'vue';

import { IconifyIcon } from '@vben/icons';

import { message } from 'ant-design-vue';
import Sortable from 'sortablejs';

import { $t } from '#/locales';

/**
 * 拖拽排序配置
 */
export interface DragSortConfig {
  /**
   * 更新排序的 API 函数
   * @param id 记录 ID
   * @param sortOrder 新的排序值
   */
  onUpdate: (id: number | string, sortOrder: number) => Promise<any>;

  /**
   * 排序字段名（用于获取和更新排序值）
   * @default 'sortOrder'
   */
  sortField?: string;

  /**
   * 主键字段名
   * @default 'id'
   */
  keyField?: string;

  /**
   * 成功提示文本
   */
  successMessage?: string;

  /**
   * 失败提示文本
   */
  errorMessage?: string;
}

let sortableInstance: null | Sortable = null;
let currentConfig: DragSortConfig | null = null;
let currentGridRef: null | { value: undefined | VxeGridInstance } = null;

/**
 * 初始化 Sortable 拖拽
 */
function initSortable() {
  destroySortable();

  const gridEl = document.querySelector('.vxe-table--body tbody');
  if (!gridEl) return;

  sortableInstance = Sortable.create(gridEl as HTMLElement, {
    animation: 150,
    handle: '.drag-handle',
    ghostClass: 'sortable-ghost',
    onEnd: handleDragEnd,
  });
}

/**
 * 销毁 Sortable 实例
 */
function destroySortable() {
  if (sortableInstance) {
    sortableInstance.destroy();
    sortableInstance = null;
  }
}

/**
 * 刷新表格
 */
async function refreshDragTable() {
  destroySortable();
  const grid = currentGridRef?.value;
  if (grid) {
    grid.loadData([]);
    await nextTick();
    grid.commitProxy('query');
  }
}

/**
 * 处理拖拽结束事件
 */
async function handleDragEnd(evt: Sortable.SortableEvent) {
  if (!currentConfig || !currentGridRef) return;

  const { oldIndex, newIndex } = evt;
  if (oldIndex === undefined || newIndex === undefined) return;
  if (oldIndex === newIndex) return;

  const grid = currentGridRef.value;
  if (!grid) return;

  const {
    sortField = 'sortOrder',
    keyField = 'id',
    onUpdate,
    successMessage,
    errorMessage,
  } = currentConfig;

  // vxe-grid 使用 getTableData().fullData 获取全量数据
  const { fullData } = grid.getTableData();
  const tableData = [...(fullData || [])];
  if (tableData.length === 0) return;

  const movedItem = tableData.splice(oldIndex, 1)[0];
  if (!movedItem) return;
  tableData.splice(newIndex, 0, movedItem);

  const updates: Array<{ id: number | string; sortOrder: number }> = [];
  tableData.forEach((item: any, index) => {
    if (item[sortField] !== index) {
      updates.push({ id: item[keyField], sortOrder: index });
    }
  });

  if (updates.length === 0) return;

  try {
    await Promise.all(updates.map((u) => onUpdate(u.id, u.sortOrder)));
    message.success(successMessage || $t('shared/common.sortSuccess'));
  } catch {
    message.error(errorMessage || $t('shared/common.sortFailed'));
  } finally {
    await refreshDragTable();
  }
}

/**
 * 拖拽排序 Composable
 * 简化版：自动处理初始化和销毁
 */
export function useTableDragSort(
  gridRef: { value: undefined | VxeGridInstance },
  config: DragSortConfig,
) {
  currentConfig = config;
  currentGridRef = gridRef;

  onUnmounted(() => {
    destroySortable();
    currentConfig = null;
    currentGridRef = null;
  });

  return {
    /** 初始化拖拽（在 query 完成后调用） */
    initDragSort: initSortable,
    /** 刷新表格 */
    refreshTable: refreshDragTable,
  };
}

/**
 * 拖拽列定义（带渲染器）
 * 直接使用，无需写模板插槽
 */
export const dragColumn = {
  field: '_drag',
  title: '',
  width: 40,
  align: 'center' as const,
  cellRender: {
    name: 'DragHandle',
  },
};

/**
 * 注册拖拽手柄渲染器
 * 在 vxe-table 初始化时调用
 */
export function registerDragHandleRenderer(vxeUI: any) {
  vxeUI.renderer.add('DragHandle', {
    renderTableDefault() {
      return h(IconifyIcon, {
        icon: 'lucide:grip-vertical',
        class: 'drag-handle cursor-move text-gray-400 hover:text-gray-600',
      });
    },
  });
}
