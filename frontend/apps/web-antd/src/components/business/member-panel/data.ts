/**
 * 成员管理 - 表单配置
 * 遵循 vben-admin 规范，独立于具体视图页面
 */
import type { VbenFormSchema } from '#/adapter/form';

import { z } from '#/adapter/form';
import { $t } from '#/locales';

/**
 * 管理员新建/编辑表单 Schema
 * @param isEdit 是否编辑模式
 * @param nodeName 组织节点名称（用于角色显示）
 */
export function useAdminFormSchema(
  isEdit: boolean = false,
  nodeName?: string,
): VbenFormSchema[] {
  return [
    // === 基本信息 ===
    {
      component: 'Divider',
      componentProps: {
        orientation: 'left',
      },
      fieldName: 'divider_basic',
      label: '',
      renderComponentContent: () => ({
        default: () => $t('admin.common.basicInfo'),
      }),
    },
    {
      component: 'Input',
      componentProps: {
        disabled: isEdit,
        placeholder: $t('admin.system.admin.placeholder.inputUsername'),
      },
      fieldName: 'username',
      label: $t('admin.system.admin.username'),
      rules: isEdit ? undefined : 'required',
      help: isEdit
        ? $t('admin.system.admin.help.usernameEdit')
        : $t('admin.system.admin.help.usernameCreate'),
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.system.admin.placeholder.inputNickname'),
      },
      fieldName: 'nickname',
      label: $t('admin.system.admin.nickname'),
    },
    // 密码字段仅在新建模式显示
    ...(isEdit
      ? []
      : [
          {
            component: 'Input',
            componentProps: {
              placeholder: $t('admin.system.admin.placeholder.inputPassword'),
              type: 'password',
            },
            fieldName: 'password',
            label: $t('admin.system.admin.password'),
            rules: 'required',
          },
        ]),
    // === 联系方式 ===
    {
      component: 'Divider',
      componentProps: {
        orientation: 'left',
      },
      fieldName: 'divider_contact',
      label: '',
      renderComponentContent: () => ({
        default: () => $t('admin.common.contactInfo'),
      }),
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.system.admin.placeholder.inputEmail'),
      },
      fieldName: 'email',
      label: $t('admin.system.admin.email'),
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.system.admin.placeholder.inputPhone'),
      },
      fieldName: 'phone',
      label: $t('admin.system.admin.phone'),
    },
    // === 权限设置 ===
    {
      component: 'Divider',
      componentProps: {
        orientation: 'left',
      },
      fieldName: 'divider_permission',
      label: '',
      renderComponentContent: () => ({
        default: () => $t('admin.common.permissionSettings'),
      }),
    },
    // 角色显示（只读）
    ...(nodeName
      ? [
          {
            component: 'Input',
            componentProps: {
              disabled: true,
            },
            fieldName: 'role_display',
            label: $t('admin.system.admin.role'),
            defaultValue: nodeName,
            help: '角色自动绑定当前组织节点',
          },
        ]
      : []),
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        optionType: 'button',
        options: [
          { label: $t('admin.common.enabled'), value: true },
          { label: $t('admin.common.disabled'), value: false },
        ],
      },
      defaultValue: true,
      fieldName: 'is_active',
      label: $t('admin.common.accountStatus'),
    },
  ];
}

/**
 * 管理员表单默认值（新建模式）
 * @param nodeName 组织节点名称
 */
export function getAdminFormDefaults(nodeName?: string): Record<string, any> {
  return {
    is_active: true,
    role_display: nodeName || $t('admin.common.notSelected'),
  };
}

/**
 * 重置密码表单 Schema
 * 密码一致性校验通过 Zod dependencies 实现
 */
export function useResetPasswordSchema(): VbenFormSchema[] {
  return [
    {
      component: 'InputPassword',
      componentProps: {
        placeholder: $t('admin.system.admin.placeholder.inputNewPassword'),
      },
      fieldName: 'new_password',
      label: $t('admin.system.admin.newPassword'),
      rules: z.string().min(6, $t('admin.system.admin.validation.passwordMin')),
    },
    {
      component: 'InputPassword',
      componentProps: {
        placeholder: $t('admin.system.admin.placeholder.confirmPassword'),
      },
      fieldName: 'confirm_password',
      label: $t('admin.system.admin.confirmPassword'),
      dependencies: {
        triggerFields: ['new_password'],
        rules: (values) =>
          z
            .string()
            .min(1, $t('admin.system.admin.validation.confirmRequired'))
            .refine((v) => v === values.new_password, {
              message: $t('admin.system.admin.messages.passwordMismatch'),
            }),
      },
    },
  ];
}
