<template>
  <div v-if="isPreviewMode" class="permission-preview-mode">
    <div class="permission-preview-mode__banner">
      <div class="permission-preview-mode__info">
        <i class="permission-preview-mode__icon iconoir-eye"></i>
        <span class="permission-preview-mode__text">
          {{ $t('accessControl.preview.title') }}:
          <strong class="permission-preview-mode__user">
            {{ previewUserName }}
          </strong>
        </span>
      </div>
      <Button
        type="secondary"
        size="small"
        class="permission-preview-mode__exit-btn"
        @click="exitPreview"
      >
        {{ $t('accessControl.preview.exitPreview') }}
      </Button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PermissionPreviewMode',
  props: {
    // 是否处于预览模式
    isPreviewMode: {
      type: Boolean,
      default: false,
    },
    // 预览的用户信息
    previewUser: {
      type: Object,
      default: null,
    },
  },
  computed: {
    // 获取预览用户的显示名称
    previewUserName() {
      if (!this.previewUser) return ''
      return (
        this.previewUser.name ||
        this.previewUser.first_name ||
        this.previewUser.email ||
        `User ${this.previewUser.id}`
      )
    },
  },
  methods: {
    // 退出预览模式
    exitPreview() {
      this.$emit('exit-preview')
    },
  },
}
</script>
