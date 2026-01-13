<script lang="ts" setup>
/**
 * 平台管理员新建/编辑表单抽屉
 * 遵循 vben-admin 规范
 */
import type { adminApi } from '#/api';

import { computed, nextTick, ref } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';

import { useVbenForm } from '#/adapter/form';
import { adminApi as admin } from '#/api';
import { $t } from '#/locales';

type AdminInfo = adminApi.AdminInfo;

import { useFormSchema } from '../data';

const emits = defineEmits<{
  success: [];
}>();

// 表单数据
const formData = ref<AdminInfo & { isEdit?: boolean }>();
const isEdit = ref(false);
const adminId = ref<number>();

// 角色列表
const roleOptions = ref<{ id: number; name: string }[]>([]);

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
      const data = drawerApi.getData<AdminInfo & { isEdit?: boolean }>();
      formData.value = data;
      isEdit.value = data?.isEdit ?? false;
      adminId.value = data?.id;

      // 重置表单
      await formApi.resetForm();

      // 加载角色列表
      if (roleOptions.value.length === 0) {
        await loadRoles();
      }

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
 * 加载角色列表
 */
async function loadRoles() {
  try {
    const roles = await admin.getRoleListApi();
    roleOptions.value = roles.map((r) => ({ id: r.id, name: r.name }));
  } catch {
    roleOptions.value = [];
  }
}

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
