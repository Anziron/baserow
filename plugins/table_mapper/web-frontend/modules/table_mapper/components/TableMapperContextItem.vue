<template>
  <a class="context__menu-item-link" @click="openConfig">
    <i class="context__menu-item-icon iconoir-link"></i>
    {{ $t('tableMapper.configureMapping') }}
    <TableMapperConfigModal
      ref="modal"
      :table="table"
      :database="database"
    />
  </a>
</template>

<script>
import TableMapperConfigModal from '@table_mapper/components/TableMapperConfigModal'

export default {
  name: 'TableMapperContextItem',
  components: {
    TableMapperConfigModal,
  },
  props: {
    workspace: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
  },
  methods: {
    openConfig() {
      this.$refs.modal.show()
    },
  },
}
</script>
