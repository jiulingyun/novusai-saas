<script lang="ts" setup>
/**
 * 平台管理员新建/编辑表单抽屉
 */
import type { adminApi } from '#/api';

import { computed } from 'vue';

import { useVbenForm } from '#/adapter/form';
import { useCrudDrawer, useRemoteSelect } from '#/composables';
import { $t } from '#/locales';

import { useFormSchema } from '../data';

type AdminInfo = adminApi.AdminInfo;

const emits = defineEmits<{ success: [] }>();

// 角色选项
const { options: roleOptions, refresh: refreshRoles } = useRemoteSelect({
  url: '/admin/roles/select',
  immediate: false,
});

// 表单
const [Form, formApi] = useVbenForm({
  schema: useFormSchema(false),
  showDefaultActions: false,
});

// CRUD 抽屉（一体化）
const { Drawer, isEdit } = useCrudDrawer<AdminInfo>({
  formApi,
  schema: useFormSchema,
  transform: (values, isEdit) => ({
    ...(isEdit ? {} : { username: values.username, password: values.password }),
    email: values.email,
    phone: values.phone || null,
    nickname: values.nickname || null,
    is_active: values.is_active ?? true,
    is_super: values.is_super ?? false,
    role_id: values.role_id || null,
  }),
  toFormValues: (data) => ({
    username: data.username,
    email: data.email,
    phone: data.phone,
    nickname: data.nickname,
    is_active: data.isActive,
    is_super: data.isSuper,
    role_id: data.roleId,
  }),
  onOpen: refreshRoles,
  afterOpen: (api) => api.updateSchema([{
    componentProps: { options: roleOptions.value },
    fieldName: 'role_id',
  }]),
  onSuccess: () => emits('success'),
});

const title = computed(() =>
  isEdit.value ? $t('admin.system.admin.edit') : $t('admin.system.admin.create')
);
</script>

<template>
  <Drawer :title="title">
    <Form />
  </Drawer>
</template>
