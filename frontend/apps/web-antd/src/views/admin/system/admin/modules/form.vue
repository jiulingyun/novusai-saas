<script lang="ts" setup>
/**
 * 平台管理员新建/编辑表单抽屉
 * 遵循 vben-admin 规范
 */
import type { adminApi } from '#/api';
import type { FormMode } from '#/composables';

import { computed, nextTick, ref } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';

import { useVbenForm } from '#/adapter/form';
import { adminApi as admin } from '#/api';
import { useRemoteSelect } from '#/composables';
import { $t } from '#/locales';

import { useFormSchema } from '../data';

type AdminInfo = adminApi.AdminInfo;

const emits = defineEmits<{
  success: [];
}>();

// 表单数据
const formData = ref<AdminInfo & { mode?: FormMode }>();
const mode = ref<FormMode>('add');
const adminId = ref<number>();
const isEdit = computed(() => mode.value === 'edit');

// 使用 useRemoteSelect 获取角色选项
const {
  options: roleOptions,
  refresh: refreshRoles,
} = useRemoteSelect({
  url: '/admin/roles/select',
  immediate: false,  // 打开抽屉时手动加载
  valueField: 'value',
  labelField: 'label',
});

// 表单
const [Form, formApi] = useVbenForm({
  schema: useFormSchema(false),
  showDefaultActions: false,
});

// 抽屉
const [Drawer, drawerApi] = useVbenDrawer({
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (!valid) return;

    const values = await formApi.getValues();
    drawerApi.lock();

    try {
      if (isEdit.value && adminId.value) {
        // 编辑模式
        await admin.updateAdminApi(adminId.value, {
          email: values.email,
          phone: values.phone || null,
          nickname: values.nickname || null,
          is_active: values.is_active,
          is_super: values.is_super,
          role_id: values.role_id || null,
        });
      } else {
        // 新建模式
        await admin.createAdminApi({
          username: values.username,
          email: values.email,
          password: values.password,
          phone: values.phone || null,
          nickname: values.nickname || null,
          is_active: values.is_active ?? true,
          is_super: values.is_super ?? false,
          role_id: values.role_id || null,
        });
      }
      emits('success');
      drawerApi.close();
    } catch {
      drawerApi.unlock();
    }
  },

  async onOpenChange(isOpen) {
    if (isOpen) {
      const data = drawerApi.getData<AdminInfo & { mode?: FormMode }>();
      formData.value = data;
      mode.value = data?.mode ?? 'add';
      adminId.value = data?.id;

      // 重置表单
      await formApi.resetForm();

      // 加载角色选项（使用 /select 端点）
      await refreshRoles();

      // 更新表单 schema（根据编辑/新建模式）
      formApi.setState({
        schema: useFormSchema(isEdit.value),
      });

      // 等待 DOM 更新
      await nextTick();

      // 更新角色下拉选项
      formApi.updateSchema([
        {
          componentProps: {
            fieldNames: { label: 'label', value: 'value' },
            options: roleOptions.value,
          },
          fieldName: 'role_id',
        },
      ]);

      // 编辑模式时填充数据
      if (data && isEdit.value) {
        formApi.setValues({
          username: data.username,
          email: data.email,
          phone: data.phone,
          nickname: data.nickname,
          is_active: data.isActive,
          is_super: data.isSuper,
          role_id: data.roleId,
        });
      }
    }
  },
});

/**
 * 抽屉标题
 */
const drawerTitle = computed(() => {
  return isEdit.value
    ? $t('admin.system.admin.edit')
    : $t('admin.system.admin.create');
});
</script>

<template>
  <Drawer :title="drawerTitle">
    <Form />
  </Drawer>
</template>
