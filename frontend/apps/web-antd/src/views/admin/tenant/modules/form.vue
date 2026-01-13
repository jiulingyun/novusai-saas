<script lang="ts" setup>
/**
 * 租户新建/编辑表单抽屉
 * 遵循 vben-admin 规范
 */
import type { adminApi } from '#/api';

import { computed, nextTick, ref } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';

import { useVbenForm } from '#/adapter/form';
import { adminApi as admin } from '#/api';
import { $t } from '#/locales';

type TenantInfo = adminApi.TenantInfo;

import { useFormSchema } from '../data';

const emits = defineEmits<{
  success: [];
}>();

// 表单数据
const formData = ref<TenantInfo & { isEdit?: boolean }>();
const isEdit = ref(false);
const tenantId = ref<number>();

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
      if (isEdit.value && tenantId.value) {
        // 编辑模式
        await admin.updateTenantApi(tenantId.value, {
          name: values.name,
          contact_name: values.contact_name || null,
          contact_phone: values.contact_phone || null,
          contact_email: values.contact_email || null,
          plan: values.plan,
          expires_at: values.expires_at || null,
          remark: values.remark || null,
        });
      } else {
        // 新建模式
        await admin.createTenantApi({
          code: values.code,
          name: values.name,
          contact_name: values.contact_name || null,
          contact_phone: values.contact_phone || null,
          contact_email: values.contact_email || null,
          plan: values.plan || 'free',
          expires_at: values.expires_at || null,
          remark: values.remark || null,
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
      const data = drawerApi.getData<TenantInfo & { isEdit?: boolean }>();
      formData.value = data;
      isEdit.value = data?.isEdit ?? false;
      tenantId.value = data?.id;

      // 重置表单
      await formApi.resetForm();

      // 更新表单 schema
      formApi.setState({
        schema: useFormSchema(isEdit.value),
      });

      await nextTick();

      // 编辑模式时填充数据
      if (data && isEdit.value) {
        formApi.setValues({
          code: data.code,
          name: data.name,
          contact_name: data.contactName,
          contact_phone: data.contactPhone,
          contact_email: data.contactEmail,
          plan: data.plan,
          expires_at: data.expiresAt,
          remark: data.remark,
        });
      }
    }
  },
});

/**
 * 抽屉标题
 */
const drawerTitle = computed(() => {
  return isEdit.value ? $t('admin.tenant.edit') : $t('admin.tenant.create');
});
</script>

<template>
  <Drawer :title="drawerTitle">
    <Form />
  </Drawer>
</template>
