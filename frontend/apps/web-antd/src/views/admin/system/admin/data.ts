/**
 * 平台管理员管理 - 表格列和表单配置
 * 遵循 vben-admin 规范
 */
import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { adminApi } from '#/api';

import { $t } from '#/locales';

type AdminInfo = adminApi.AdminInfo;

/**
 * 表格列定义
 * @param onActionClick 操作按钮点击回调
 * @param onStatusChange 状态切换回调
 */
export function useColumns<T = AdminInfo>(
  onActionClick: OnActionClickFn<T>,
  onStatusChange?: (
    newStatus: boolean,
    row: T,
  ) => PromiseLike<boolean | undefined>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'userInfo',
      title: $t('admin.system.admin.username'),
      minWidth: 240,
      slots: { default: 'user_info' },
    },
    {
      field: 'phone',
      title: $t('admin.system.admin.phone'),
      width: 140,
      slots: { default: 'phone_cell' },
    },
    {
      field: 'roleName',
      title: $t('admin.system.admin.role'),
      width: 130,
      slots: { default: 'role_cell' },
    },
    {
      cellRender: {
        attrs: {
          beforeChange: onStatusChange,
          checkedValue: true,
          unCheckedValue: false,
        },
        name: onStatusChange ? 'CellSwitch' : 'CellTag',
        options: [
          { color: 'success', label: $t('admin.common.enabled'), value: true },
          { color: 'error', label: $t('admin.common.disabled'), value: false },
        ],
      },
      field: 'isActive',
      title: $t('admin.system.admin.status'),
      width: 100,
      align: 'center',
    },
    {
      field: 'isSuper',
      title: $t('admin.system.admin.type'),
      width: 120,
      align: 'center',
      slots: { default: 'type_cell' },
    },
    {
      field: 'createdAt',
      title: $t('admin.system.admin.createdAt'),
      width: 180,
      slots: { default: 'time_cell' },
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          resource: 'admin_user',  // 自动检查 admin_user:update, admin_user:delete
          nameField: 'username',
          nameTitle: $t('admin.system.admin.username'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          'edit',  // 自动鉴权: admin_user:update
          {
            code: 'resetPassword',
            text: $t('admin.system.admin.resetPassword'),
            icon: 'lucide:key-round',
            accessCodes: ['admin_user:reset_password'],  // 自定义权限
          },
          'delete',  // 自动鉴权: admin_user:delete
        ],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('admin.common.operation'),
      width: 120,
    },
  ];
}

/**
 * 搜索表单 Schema
 * 字段名直接使用 JSON:API 格式
 */
export function useGridFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
        placeholder: $t('admin.system.admin.placeholder.searchUsername'),
      },
      fieldName: 'filter[username][ilike]',
      label: $t('admin.system.admin.username'),
    },
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
        placeholder: $t('admin.system.admin.placeholder.searchEmail'),
      },
      fieldName: 'filter[email][ilike]',
      label: $t('admin.system.admin.email'),
    },
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
        placeholder: $t('admin.system.admin.placeholder.searchPhone'),
      },
      fieldName: 'filter[phone][ilike]',
      label: $t('admin.system.admin.phone'),
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: $t('admin.common.enabled'), value: true },
          { label: $t('admin.common.disabled'), value: false },
        ],
        placeholder: $t('admin.system.admin.placeholder.allStatus'),
      },
      fieldName: 'filter[is_active]',
      label: $t('admin.system.admin.status'),
    },
  ];
}

/**
 * 新建/编辑表单 Schema
 * @param isEdit 是否编辑模式
 */
export function useFormSchema(isEdit: boolean = false): VbenFormSchema[] {
  return [
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
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        fieldNames: { label: 'name', value: 'id' },
        placeholder: $t('admin.system.admin.placeholder.selectRole'),
      },
      fieldName: 'role_id',
      label: $t('admin.system.admin.role'),
      help: $t('admin.system.admin.help.roleHelp'),
    },
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
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        optionType: 'button',
        options: [
          { label: $t('admin.system.admin.normalAdmin'), value: false },
          { label: $t('admin.system.admin.superAdmin'), value: true },
        ],
      },
      defaultValue: false,
      fieldName: 'is_super',
      label: $t('admin.system.admin.type'),
      help: $t('admin.system.admin.help.superAdminHelp'),
    },
  ];
}

/**
 * 重置密码表单 Schema
 */
export function useResetPasswordSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.system.admin.placeholder.inputNewPassword'),
        type: 'password',
      },
      fieldName: 'new_password',
      label: $t('admin.system.admin.newPassword'),
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.system.admin.placeholder.confirmPassword'),
        type: 'password',
      },
      fieldName: 'confirm_password',
      label: $t('admin.system.admin.confirmPassword'),
      rules: 'required',
    },
  ];
}
