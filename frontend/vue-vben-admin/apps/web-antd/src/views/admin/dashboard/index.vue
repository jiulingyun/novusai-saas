<script lang="ts" setup>
import { Card } from 'ant-design-vue';

import { useUserStore } from '@vben/stores';

const userStore = useUserStore();
</script>

<template>
  <div class="p-5">
    <Card title="平台管理控制台" class="mb-4">
      <template #extra>
        <span class="text-gray-500">欢迎回来</span>
      </template>
      <div class="text-lg">
        您好，{{ userStore.userInfo?.realName || '管理员' }}！
      </div>
      <p class="mt-2 text-gray-500">
        这是平台管理端控制台，您可以在这里管理平台的各项配置。
      </p>
    </Card>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <template #title>
          <span class="text-blue-500">租户总数</span>
        </template>
        <div class="text-3xl font-bold">--</div>
      </Card>
      <Card>
        <template #title>
          <span class="text-green-500">活跃租户</span>
        </template>
        <div class="text-3xl font-bold">--</div>
      </Card>
      <Card>
        <template #title>
          <span class="text-orange-500">用户总数</span>
        </template>
        <div class="text-3xl font-bold">--</div>
      </Card>
      <Card>
        <template #title>
          <span class="text-purple-500">今日登录</span>
        </template>
        <div class="text-3xl font-bold">--</div>
      </Card>
    </div>
  </div>
</template>
