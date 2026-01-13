/**
 * 平台角色管理 - 表格列和表单配置
 * 遵循 vben-admin 规范
 */
import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { adminApi } from '#/api';

import { dragColumn } from '#/adapter/vxe-table';
import { $t } from '#/locales';
import { ADMIN_PERMISSIONS } from '#/utils/access';

type RoleInfo = adminApi.RoleInfo;

/**
 * 表格列定义
 * @param onActionClick 操作按钮点击回调
 */
export function useColumns<T = RoleInfo>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    dragColumn,
    {
      field: 'roleInfo',
      title: $t('admin.system.role.name'),
      minWidth: 180,
      slots: { default: 'role_info' },
    },
    {
      field: 'description',
      title: $t('admin.system.role.description'),
      minWidth: 160,
      showOverflow: 'tooltip',
      slots: { default: 'desc_cell' },
    },
    {
      field: 'permissions',
      title: $t('admin.system.role.permissions'),
      minWidth: 140,
      slots: { default: 'permissions_cell' },
    },
    {
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('admin.common.enabled'), value: true },
          { color: 'error', label: $t('admin.common.disabled'), value: false },
        ],
      },
      field: 'isActive',
      title: $t('admin.system.role.status'),
      width: 100,
      align: 'center',
    },
    {
      field: 'sortOrder',
      title: $t('admin.system.role.sortOrder'),
      width: 80,
      align: 'center',
      slots: { default: 'sort_cell' },
    },
    {
      field: 'createdAt',
      title: $t('admin.system.role.createdAt'),
      width: 160,
      slots: { default: 'time_cell' },
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'name',
          nameTitle: $t('admin.system.role.name'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'edit',
            text: $t('common.edit'),
            icon: 'lucide:pencil',
            accessCodes: [ADMIN_PERMISSIONS.ROLE_UPDATE],
          },
          {
            code: 'delete',
            text: $t('common.delete'),
            icon: 'lucide:trash-2',
            accessCodes: [ADMIN_PERMISSIONS.ROLE_DELETE],
          },
        ],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('admin.common.operation'),
      width: 80,
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
      component: 'Input',
      componentProps: {
        disabled: isEdit,
        placeholder: $t('admin.system.role.placeholder.inputCode'),
      },
      fieldName: 'code',
      label: $t('admin.system.role.code'),
      rules: isEdit ? undefined : 'required',
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.system.role.placeholder.inputName'),
      },
      fieldName: 'name',
      label: $t('admin.system.role.name'),
      rules: 'required',
    },
    {
      component: 'Textarea',
      componentProps: {
        placeholder: $t('admin.system.role.placeholder.inputDescription'),
        rows: 3,
      },
      fieldName: 'description',
      label: $t('admin.system.role.description'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('admin.common.enabled'), value: true },
          { label: $t('admin.common.disabled'), value: false },
        ],
        optionType: 'button',
      },
      defaultValue: true,
      fieldName: 'is_active',
      label: $t('admin.system.role.status'),
    },
    {
      component: 'InputNumber',
      componentProps: {
        min: 0,
        placeholder: $t('admin.system.role.placeholder.inputSortOrder'),
      },
      defaultValue: 0,
      fieldName: 'sort_order',
      label: $t('admin.system.role.sortOrder'),
    },
    {
      // 权限树使用插槽渲染
      component: 'Input',
      fieldName: 'permission_ids',
      formItemClass: 'items-start',
      label: $t('admin.system.role.permissions'),
    },
  ];
}
