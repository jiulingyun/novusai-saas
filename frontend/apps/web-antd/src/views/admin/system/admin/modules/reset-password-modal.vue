<script lang="ts" setup>
/**
 * 重置密码弹窗
 */
import type { adminApi } from '#/api';

import { ref } from 'vue';

import { useVbenModal } from '@vben/common-ui';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { adminApi as admin } from '#/api';
import { $t } from '#/locales';

import { useResetPasswordSchema } from '../data';

type AdminInfo = adminApi.AdminInfo;

const emits = defineEmits<{
  success: [];
}>();

const adminData = ref<AdminInfo>();

// 表单
const [Form, formApi] = useVbenForm({
  schema: useResetPasswordSchema(),
  showDefaultActions: false,
});

// 弹窗
const [Modal, modalApi] = useVbenModal({
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (!valid) return;

    const values = await formApi.getValues();

    // 验证两次密码一致
    if (values.new_password !== values.confirm_password) {
      message.error($t('admin.system.admin.messages.passwordMismatch'));
      return;
    }

    if (!adminData.value?.id) return;

    modalApi.lock();
    try {
      await admin.resetAdminPasswordApi(adminData.value.id, {
        new_password: values.new_password,
      });
      message.success($t('admin.system.admin.messages.resetPasswordSuccess'));
      emits('success');
      modalApi.close();
    } catch {
      modalApi.unlock();
    }
  },

  async onOpenChange(isOpen) {
    if (isOpen) {
      const data = modalApi.getData<AdminInfo>();
      adminData.value = data;
      await formApi.resetForm();
    }
  },

  title: $t('admin.system.admin.resetPassword'),
});
</script>

<template>
  <Modal>
    <div v-if="adminData" class="mb-4 text-gray-500">
      {{
        $t('admin.system.admin.messages.resetPasswordFor', {
          name: adminData.username,
        })
      }}
    </div>
    <Form />
  </Modal>
</template>
