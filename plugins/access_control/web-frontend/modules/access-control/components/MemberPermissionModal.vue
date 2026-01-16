<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('accessControl.workspace.memberPermissions') }}
    </h2>
    <div v-if="member" class="member-permission-modal__member-info">
      <Avatar
        :initials="member.name | nameAbbreviation"
        size="medium"
        rounded
      />
      <div class="member-permission-modal__member-details">
        <span class="member-permission-modal__member-name">{{ member.name }}</span>
        <span class="member-permission-modal__member-email">{{ member.email }}</span>
      </div>
    </div>

    <div class="member-permission-modal__sections">
      <PluginPermissionManager
        v-if="member && workspace"
        :workspace="workspace"
        :member="member"
        @permission-updated="onPermissionUpdated"
      />
    </div>

    <div class="actions">
      <Button type="secondary" size="large" @click="hide()">
        {{ $t('action.close') }}
      </Button>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import PluginPermissionManager from '@access-control/components/PluginPermissionManager'
import StructurePermissionManager from '@access-control/components/StructurePermissionManager'

export default {
  name: 'MemberPermissionModal',
  components: {
    PluginPermissionManager,
    StructurePermissionManager,
  },
  mixins: [modal],
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      member: null,
    }
  },
  methods: {
    show(member, ...args) {
      this.member = member
      return modal.methods.show.call(this, ...args)
    },
    onPermissionUpdated(event) {
      this.$emit('permission-updated', {
        ...event,
        member: this.member,
      })
    },
  },
}
</script>
