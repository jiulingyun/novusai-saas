<script setup lang="ts">
/**
 * 远程下拉组件
 *
 * 基于 useRemoteSelect Hook 封装的可复用远程下拉组件，
 * 兼容 Ant Design Vue Select API
 *
 * @example
 * ```vue
 * <!-- 基本用法 -->
 * <RemoteSelect v-model:value="roleId" url="/admin/roles/select" />
 *
 * <!-- 带搜索 -->
 * <RemoteSelect
 *   v-model:value="userId"
 *   url="/admin/users/select"
 *   searchable
 *   placeholder="搜索用户"
 * />
 *
 * <!-- 自定义字段 -->
 * <RemoteSelect
 *   v-model:value="categoryId"
 *   url="/api/categories"
 *   value-field="id"
 *   label-field="name"
 * />
 * ```
 */
import type { DefaultOptionType, SelectValue } from 'ant-design-vue/es/select';

import type { UseRemoteSelectOptions } from '#/composables';
import type { SelectOption } from '#/types';

import { computed, watch } from 'vue';

import { Select } from 'ant-design-vue';

import { useRemoteSelect } from '#/composables';

// Props 定义
interface Props {
  /** 选中的值（支持 v-model:value） */
  value?: null | number | string;
  /** API URL */
  url: string;
  /** 是否在组件挂载时自动加载 */
  immediate?: boolean;
  /** 是否支持搜索 */
  searchable?: boolean;
  /** 搜索防抖延迟（ms） */
  searchDebounce?: number;
  /** 搜索参数名 */
  searchParamName?: string;
  /** 额外的请求参数 */
  extraParams?: Record<string, unknown>;
  /** 值字段名 */
  valueField?: string;
  /** 标签字段名 */
  labelField?: string;
  /** 数据转换函数 */
  transform?: (data: unknown[]) => SelectOption[];
  /** 占位文本 */
  placeholder?: string;
  /** 是否允许清空 */
  allowClear?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 下拉模式 */
  mode?: 'multiple' | 'tags';
  /** 弹出层样式 */
  dropdownStyle?: Record<string, string>;
  /** 弹出层类名 */
  popupClassName?: string;
}

const props = withDefaults(defineProps<Props>(), {
  value: undefined,
  immediate: true,
  searchable: false,
  searchDebounce: 300,
  searchParamName: 'search',
  extraParams: () => ({}),
  valueField: 'value',
  labelField: 'label',
  transform: undefined,
  placeholder: undefined,
  allowClear: true,
  disabled: false,
  mode: undefined,
  dropdownStyle: undefined,
  popupClassName: undefined,
});

// Emits 定义
const emit = defineEmits<{
  (e: 'update:value', value: null | number | string | undefined): void;
  (
    e: 'change',
    value: null | number | string | undefined,
    option: SelectOption | SelectOption[] | undefined,
  ): void;
  (e: 'search', value: string): void;
}>();

// 使用 useRemoteSelect Hook
const { options, loading, fetchOptions, onSearch, refresh } = useRemoteSelect({
  url: props.url,
  immediate: props.immediate,
  searchable: props.searchable,
  searchDebounce: props.searchDebounce,
  searchParamName: props.searchParamName,
  extraParams: props.extraParams,
  valueField: props.valueField,
  labelField: props.labelField,
  transform: props.transform,
} as UseRemoteSelectOptions);

// 计算选中的值
const selectedValue = computed({
  get: () => props.value,
  set: (val) => emit('update:value', val),
});

// 监听 URL 变化，重新获取数据
watch(
  () => props.url,
  () => {
    if (props.immediate) {
      refresh();
    }
  },
);

/**
 * 处理选择变化
 */
function handleChange(
  value: SelectValue,
  option: DefaultOptionType | DefaultOptionType[],
) {
  const val = value as null | number | string | undefined;
  emit('update:value', val);
  emit('change', val, option as SelectOption | SelectOption[]);
}

/**
 * 处理搜索
 */
function handleSearch(value: string) {
  onSearch(value);
  emit('search', value);
}

// 暴露方法
defineExpose({
  refresh,
  fetchOptions,
});
</script>

<template>
  <Select
    :value="selectedValue as SelectValue"
    :options="options"
    :loading="loading"
    :placeholder="placeholder"
    :allow-clear="allowClear"
    :disabled="disabled"
    :mode="mode"
    :show-search="searchable"
    :filter-option="searchable ? false : undefined"
    :dropdown-style="dropdownStyle"
    :popup-class-name="popupClassName"
    @update:value="
      (v: SelectValue) =>
        (selectedValue = v as null | number | string | undefined)
    "
    @change="handleChange"
    @search="searchable ? handleSearch : undefined"
  />
</template>
