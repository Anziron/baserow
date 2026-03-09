<template>
  <li>
    <a @click="openConfig">
      <i class="iconoir-link"></i>
      {{ $t('tableMapper.configureMapping') }}
    </a>
    <TableMapperConfigModal
      v-if="modalOpen"
      :table="table"
      :database="database"
      @hidden="modalOpen = false"
    />
  </li>
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
      required: false,
      default: null,
    },
  },
  data() {
    return {
      modalOpen: false,
    }
  },
  methods: {
    openConfig() {
      this.modalOpen = true
    },
  },
}
</script>
