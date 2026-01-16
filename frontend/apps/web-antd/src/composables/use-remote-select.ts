/**
 * 远程下拉数据获取 Hook
 *
 * 封装远程下拉组件的数据获取逻辑，支持：
 * - 传入 URL 自动获取选项
 * - 支持 search 参数搜索（防抖）
 * - 返回 options/loading/fetchOptions
 *
 * @module composables/use-remote-select
 *
 * @example
 * ```ts
 * // 基本用法
 * const { options, loading, fetchOptions } = useRemoteSelect({
 *   url: '/admin/roles/select',
 * });
 *
 * // 带搜索
 * const { options, loading, onSearch } = useRemoteSelect({
 *   url: '/admin/users/select',
 *   searchable: true,
 *   searchDebounce: 300,
 * });
 *
 * // 在 Select 组件中使用
 * <Select
 *   v-model="roleId"
 *   :options="options"
 *   :loading="loading"
 *   show-search
 *   :filter-option="false"
 *   @search="onSearch"
 * />
 * ```
 */

import type { Ref } from 'vue';

import type { SelectOption } from '#/types';

import { onMounted, ref, watch } from 'vue';

import { requestClient } from '#/utils/request';

/**
 * useRemoteSelect 配置选项
 */
export interface UseRemoteSelectOptions {
  /** API URL（返回 SelectResponse 格式） */
  url: string;
  /** 是否在组件挂载时自动加载 */
  immediate?: boolean;
  /** 是否支持搜索 */
  searchable?: boolean;
  /** 搜索防抖延迟（ms） */
  searchDebounce?: number;
  /** 搜索参数名，默认 'search' */
  searchParamName?: string;
  /** 额外的请求参数 */
  extraParams?: Record<string, unknown>;
  /** 值字段名，默认 'value' */
  valueField?: string;
  /** 标签字段名，默认 'label' */
  labelField?: string;
  /** 数据转换函数 */
  transform?: (data: unknown[]) => SelectOption[];
}

/**
 * useRemoteSelect 返回值
 */
export interface UseRemoteSelectReturn {
  /** 选项列表 */
  options: Ref<SelectOption[]>;
  /** 加载状态 */
  loading: Ref<boolean>;
  /** 手动获取选项 */
  fetchOptions: (search?: string) => Promise<void>;
  /** 搜索回调（用于 Select 组件的 onSearch） */
  onSearch: (value: string) => void;
  /** 刷新选项（重新获取） */
  refresh: () => Promise<void>;
  /** 清空选项 */
  clear: () => void;
}

/**
 * 远程下拉数据获取 Hook
 *
 * @param options - 配置选项
 * @returns 选项数据和操作方法
 */
export function useRemoteSelect(
  options: UseRemoteSelectOptions,
): UseRemoteSelectReturn {
  const {
    url,
    immediate = true,
    searchable = false,
    searchDebounce = 300,
    searchParamName = 'search',
    extraParams = {},
    valueField = 'value',
    labelField = 'label',
    transform,
  } = options;

  // 状态
  const selectOptions = ref<SelectOption[]>([]);
  const loading = ref(false);

  // 防抖定时器
  let debounceTimer: null | ReturnType<typeof setTimeout> = null;

  /**
   * 获取选项数据
   */
  async function fetchOptions(search?: string): Promise<void> {
    loading.value = true;

    try {
      const params: Record<string, unknown> = { ...extraParams };

      if (search && searchable) {
        params[searchParamName] = search;
      }

      const response = await requestClient.get<{
        items: Array<Record<string, unknown>>;
      }>(url, { params });

      // 转换数据
      selectOptions.value = transform
        ? transform(response.items)
        : response.items.map((item) => ({
            label: String(item[labelField] ?? ''),
            value: item[valueField] as number | string,
            extra: item,
            disabled: item.disabled as boolean | undefined,
          }));
    } catch (error) {
      console.error('Failed to fetch remote select options:', error);
      selectOptions.value = [];
    } finally {
      loading.value = false;
    }
  }

  /**
   * 搜索回调（带防抖）
   */
  function onSearch(value: string): void {
    if (!searchable) return;

    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    debounceTimer = setTimeout(() => {
      fetchOptions(value);
    }, searchDebounce);
  }

  /**
   * 刷新选项
   */
  async function refresh(): Promise<void> {
    await fetchOptions();
  }

  /**
   * 清空选项
   */
  function clear(): void {
    selectOptions.value = [];
  }

  // 监听 URL 变化，重新获取
  watch(
    () => url,
    () => {
      if (immediate) {
        fetchOptions();
      }
    },
  );

  // 组件挂载时自动加载
  onMounted(() => {
    if (immediate) {
      fetchOptions();
    }
  });

  return {
    options: selectOptions,
    loading,
    fetchOptions,
    onSearch,
    refresh,
    clear,
  };
}

export default useRemoteSelect;
