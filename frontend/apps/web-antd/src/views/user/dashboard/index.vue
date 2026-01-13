<script setup lang="ts">
/**
 * 用户端首页
 */
import { $t } from '#/locales';
</script>

<template>
  <div class="user-dashboard p-4">
    <h1 class="text-2xl font-bold mb-4">
      {{ $t('dashboard.title') }}
    </h1>
    <p class="text-gray-600">
      {{ $t('dashboard.welcome') }}
    </p>
  </div>
</template>
