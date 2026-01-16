/**
 * CRUD 表单通用 Composable
 *
 * 配合 useCrudPage 使用，自动处理：
 * - create/update 请求
 * - 表单重置
 * - Schema 切换
 * - 编辑模式数据填充
 *
 * @example
 * ```ts
 * const [Drawer, drawerApi, crudForm] = useCrudDrawer<AdminInfo>({
 *   formApi,
 *   schema: useFormSchema,
 *   transform: (values, isEdit) => ({ ... }),
 *   toFormValues: (data) => ({ ... }),  // 编辑模式：后端数据 -> 表单值
 *   onSuccess: () => emits('success'),
 * });
 * ```
 */
import type { FormMode } from '#/adapter/vxe-table';

import { computed, nextTick, ref } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';

import { $t } from '#/locales';
import { requestClient } from '#/utils/request';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export interface UseCrudFormOptions<_T = any> {
  /** Drawer/Modal API */
  drawerApi: {
    getData: <D = any>() => D | undefined;
    lock: () => void;
    unlock: () => void;
    close: () => void;
  } | any;

  /** Form API */
  formApi: {
    validate: () => Promise<{ valid: boolean }>;
    getValues: () => Promise<Record<string, any>>;
    resetForm: () => Promise<void>;
    setValues: (values: Record<string, any>) => void;
  } | any;

  /**
   * 数据转换函数（表单值 -> API 请求体）
   * @param values 表单原始值
   * @param isEdit 是否编辑模式
   */
  transform: (values: Record<string, any>, isEdit: boolean) => Record<string, any>;

  /** 成功回调 */
  onSuccess?: () => void;
}

/**
 * useCrudDrawer 配置选项
 */
export interface UseCrudDrawerOptions<T = any> {
  /** Form API */
  formApi: any;

  /**
   * Schema 工厂函数
   * @param isEdit 是否编辑模式
   */
  schema: (isEdit: boolean) => any[];

  /**
   * 数据转换函数（表单值 -> API 请求体）
   */
  transform: (values: Record<string, any>, isEdit: boolean) => Record<string, any>;

  /**
   * 后端数据 -> 表单值（编辑模式填充）
   * @param data 后端返回的数据
   */
  toFormValues?: (data: T) => Record<string, any>;

  /** 成功回调 */
  onSuccess?: () => void;

  /** 打开时额外操作（如加载远程数据） */
  onOpen?: () => Promise<void> | void;

  /** 打开后额外操作（如更新下拉选项） */
  afterOpen?: (formApi: any, isEdit: boolean) => Promise<void> | void;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export interface UseCrudFormReturn<_T = any> {
  /** 提交表单 */
  submit: () => Promise<void>;
  /** 是否编辑模式 */
  isEdit: ReturnType<typeof computed<boolean>>;
  /** 当前模式 */
  mode: ReturnType<typeof ref<FormMode>>;
  /** 记录 ID（编辑模式） */
  recordId: ReturnType<typeof ref<number | string | undefined>>;
  /** 资源路径 */
  resource: ReturnType<typeof ref<string>>;
}

export function useCrudForm<T = any>(
  options: UseCrudFormOptions<T>,
): UseCrudFormReturn<T> {
  const { drawerApi, formApi, transform, onSuccess } = options;

  const mode = ref<FormMode>('add');
  const recordId = ref<number | string>();
  const resource = ref<string>('');

  const isEdit = computed(() => mode.value === 'edit');

  /**
   * 初始化表单数据（在 onOpenChange 中调用）
   */
  function initFromDrawerData() {
    const data = drawerApi.getData() as (T & { mode?: FormMode; _resource?: string; id?: number | string }) | undefined;
    mode.value = data?.mode ?? 'add';
    recordId.value = data?.id;
    resource.value = data?._resource ?? '';
    return data;
  }

  /**
   * 提交表单
   */
  async function submit() {
    const { valid } = await formApi.validate();
    if (!valid) return;

    const values = await formApi.getValues();
    const requestData = transform(values, isEdit.value);

    drawerApi.lock();

    try {
      if (isEdit.value && recordId.value) {
        // 编辑模式：PUT {resource}/{id}
        await requestClient.put(`${resource.value}/${recordId.value}`, requestData, {
          showSuccessMessage: true,
          successMessage: $t('ui.actionMessage.updateSuccess'),
        });
      } else {
        // 新建模式：POST {resource}
        await requestClient.post(resource.value, requestData, {
          showSuccessMessage: true,
          successMessage: $t('ui.actionMessage.createSuccess'),
        });
      }
      onSuccess?.();
      drawerApi.close();
    } catch {
      drawerApi.unlock();
    }
  }

  return {
    submit,
    isEdit,
    mode,
    recordId,
    resource,
    /** 内部方法，供 onOpenChange 使用 */
    _initFromDrawerData: initFromDrawerData,
  } as UseCrudFormReturn<T> & { _initFromDrawerData: typeof initFromDrawerData };
}

/**
 * 一体化 CRUD 抽屉
 * 整合 useVbenDrawer + useCrudForm，进一步简化表单组件
 */
export function useCrudDrawer<T = any>(options: UseCrudDrawerOptions<T>) {
  const { formApi, schema, transform, toFormValues, onSuccess, onOpen, afterOpen } = options;

  const mode = ref<FormMode>('add');
  const recordId = ref<number | string>();
  const resource = ref<string>('');
  const rowData = ref<T>();

  const isEdit = computed(() => mode.value === 'edit');

  // 防抖状态
  const isSubmitting = ref(false);

  const [Drawer, drawerApi] = useVbenDrawer({
    async onConfirm() {
      // 防抖：如果正在提交中，直接返回
      if (isSubmitting.value) return;

      const { valid } = await formApi.validate();
      if (!valid) return;

      const values = await formApi.getValues();
      const requestData = transform(values, isEdit.value);

      isSubmitting.value = true;
      drawerApi.lock();

      try {
        if (isEdit.value && recordId.value) {
          await requestClient.put(`${resource.value}/${recordId.value}`, requestData, {
            showSuccessMessage: true,
            successMessage: $t('ui.actionMessage.updateSuccess'),
          });
        } else {
          await requestClient.post(resource.value, requestData, {
            showSuccessMessage: true,
            successMessage: $t('ui.actionMessage.createSuccess'),
          });
        }
        onSuccess?.();
        drawerApi.close();
      } catch {
        drawerApi.unlock();
      } finally {
        isSubmitting.value = false;
      }
    },

    async onOpenChange(isOpen) {
      if (!isOpen) return;

      // 从 drawerApi 获取数据
      const data = drawerApi.getData() as (T & { mode?: FormMode; _resource?: string; id?: number | string }) | undefined;
      mode.value = data?.mode ?? 'add';
      recordId.value = data?.id;
      resource.value = data?._resource ?? '';
      rowData.value = data as T;

      // 重置表单
      await formApi.resetForm();

      // 执行 onOpen（如加载远程数据）
      await onOpen?.();

      // 更新 schema
      formApi.setState({ schema: schema(isEdit.value) });
      await nextTick();

      // 执行 afterOpen（如更新下拉选项）
      await afterOpen?.(formApi, isEdit.value);

      // 编辑模式填充数据
      if (data && isEdit.value && toFormValues) {
        formApi.setValues(toFormValues(data as T));
      }
    },
  });

  return {
    Drawer,
    drawerApi,
    isEdit,
    mode,
    recordId,
    resource,
    rowData,
  };
}
