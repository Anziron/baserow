<template>
  <div class="member-permission-field">
    <a
      class="member-permission-field__link"
      :title="$t('accessControl.workspace.managePermissions')"
      @click.prevent="openPermissionModal"
    >
      <i class="member-permission-field__icon iconoir-settings"></i>
      <span class="member-permission-field__text">
        {{ $t('accessControl.workspace.permissions') }}
      </span>
    </a>
  </div>
</template>

<script>
export default {
  name: 'MemberPermissionField',
  props: {
    row: {
      required: true,
      type: Object,
    },
  },
  methods: {
    openPermissionModal() {
      this.$bus.$emit('access-control-open-permission-modal', this.row)
    },
  },
}
</script>
