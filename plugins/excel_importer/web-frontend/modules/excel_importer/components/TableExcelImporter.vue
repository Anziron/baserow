<template>
  <div>
    <div class="control margin-bottom-3">
      <template v-if="values.filename === ''">
        <label class="control__label control__label--small">
          {{ $t('excelImporter.chooseFileLabel') }}
        </label>
        <div class="control__description">
          {{ $t('excelImporter.chooseFileDescription') }}
        </div>
      </template>
      <div class="control__elements">
        <div class="file-upload">
          <input
            v-show="false"
            ref="file"
            type="file"
            accept=".xlsx,.xls"
            @change="select($event)"
          />
          <Button
            type="upload"
            size="large"
            :loading="state !== null"
            :disabled="disabled"
            icon="iconoir-cloud-upload"
            class="file-upload__button"
            @click.prevent="!disabled && $refs.file.click($event)"
          >
            {{ $t('excelImporter.chooseFile') }}
          </Button>
          <div v-if="state === null" class="file-upload__file">
            {{ values.filename }}
          </div>
          <template v-else>
            <ProgressBar
              :value="fileLoadingProgress"
              :show-value="state === 'loading'"
              :status="state === 'loading' ? $t('importer.loading') : stateTitle"
            />
          </template>
        </div>
        <div v-if="v$.values.filename.$error" class="error">
          {{ v$.values.filename.$errors[0]?.$message }}
        </div>
      </div>
    </div>

    <div v-if="values.filename !== ''" class="row">
      <div class="col col-6">
        <div class="control">
          <label class="control__label control__label--small">
            {{ $t('excelImporter.sheetSelection') }}
          </label>
          <div class="control__elements">
            <Dropdown
              v-model="selectedSheet"
              :disabled="isDisabled"
              @input="reloadSheet()"
            >
              <DropdownItem
                v-for="(sheet, index) in sheetNames"
                :key="index"
                :name="sheet"
                :value="index"
              />
            </Dropdown>
          </div>
        </div>
      </div>
      <div class="col col-6">
        <div class="control">
          <label class="control__label control__label--small">
            {{ $t('excelImporter.firstRowHeader') }}
          </label>
          <div class="control__elements">
            <Checkbox
              v-model="firstRowHeader"
              :disabled="isDisabled"
              @input="reloadPreview()"
            >
              {{ $t('common.yes') }}
            </Checkbox>
          </div>
        </div>
      </div>
    </div>

    <div v-if="values.filename !== ''" class="row">
      <div class="col col-8 margin-top-1"><slot name="upsertMapping" /></div>
    </div>

    <Alert v-if="error !== ''" type="error">
      <template #title>{{ $t('common.wrong') }}</template>
      {{ error }}
    </Alert>
  </div>
</template>

<script>
import { required, helpers } from '@vuelidate/validators'
import { useVuelidate } from '@vuelidate/core'
import * as XLSX from 'xlsx'

import form from '@baserow/modules/core/mixins/form'
import importer from '@baserow/modules/database/mixins/importer'

export default {
  name: 'TableExcelImporter',
  mixins: [form, importer],

  setup() {
    return { v$: useVuelidate({ $lazy: true }) }
  },

  data() {
    return {
      firstRowHeader: true,
      selectedSheet: 0,
      sheetNames: [],
      workbook: null,
      parsedData: null,
      values: {
        filename: '',
      },
    }
  },

  validations() {
    return {
      values: {
        filename: {
          required: helpers.withMessage(
            this.$t('error.requiredField'),
            required
          ),
        },
      },
    }
  },

  computed: {
    isDisabled() {
      return this.disabled || this.state !== null
    },
  },

  methods: {
    select(event) {
      if (event.target.files.length === 0) {
        return
      }

      const file = event.target.files[0]
      const maxSize =
        parseInt(this.$config.BASEROW_MAX_IMPORT_FILE_SIZE_MB, 10) * 1024 * 1024

      if (file.size > maxSize) {
        this.values.filename = ''
        this.handleImporterError(
          this.$t('excelImporter.limitFileSize', {
            limit: this.$config.BASEROW_MAX_IMPORT_FILE_SIZE_MB,
          })
        )
        return
      }

      this.resetImporterState()
      this.fileLoadingProgress = 0
      this.parsedData = null
      this.workbook = null
      this.sheetNames = []

      this.$emit('changed')
      this.values.filename = file.name
      this.state = 'loading'

      const reader = new FileReader()
      reader.addEventListener('progress', (event) => {
        this.fileLoadingProgress = (event.loaded / event.total) * 100
      })
      reader.addEventListener('load', (event) => {
        this.fileLoadingProgress = 100
        this.parseExcel(event.target.result)
      })
      reader.readAsArrayBuffer(file)
    },

    async parseExcel(arrayBuffer) {
      const fileName = this.values.filename
      this.resetImporterState()
      this.values.filename = fileName

      this.state = 'parsing'
      await this.$ensureRender()

      try {
        this.workbook = XLSX.read(arrayBuffer, { type: 'array' })
        this.sheetNames = this.workbook.SheetNames

        if (this.sheetNames.length === 0) {
          this.handleImporterError(this.$t('excelImporter.emptyFile'))
          return
        }

        this.selectedSheet = 0
        this.reloadSheet()
      } catch (error) {
        this.handleImporterError(this.$t('excelImporter.parseError'))
      }
    },

    async reloadSheet() {
      if (!this.workbook) return

      this.state = 'parsing'
      await this.$ensureRender()

      try {
        const sheetName = this.sheetNames[this.selectedSheet]
        const worksheet = this.workbook.Sheets[sheetName]

        const jsonData = XLSX.utils.sheet_to_json(worksheet, {
          header: 1,
          defval: '',
          raw: false,
        })

        const limit = this.$config.INITIAL_TABLE_DATA_LIMIT
        if (limit !== null && jsonData.length > limit) {
          this.handleImporterError(
            this.$t('excelImporter.limitError', { limit })
          )
          return
        }

        if (jsonData.length === 0) {
          this.handleImporterError(this.$t('excelImporter.emptySheet'))
          return
        }

        this.parsedData = jsonData.map((row) =>
          row.map((cell) =>
            cell === null || cell === undefined ? '' : String(cell)
          )
        )

        this.reloadPreview()
        this.state = null

        const getData = () => {
          return new Promise((resolve) => {
            if (this.firstRowHeader) {
              const [, ...data] = this.parsedData
              resolve(data)
            } else {
              resolve(this.parsedData)
            }
          })
        }
        this.$emit('getData', getData)
      } catch (error) {
        this.handleImporterError(this.$t('excelImporter.parseError'))
      }
    },

    reloadPreview() {
      if (!this.parsedData || this.parsedData.length === 0) return

      const [rawHeader, ...rawData] = this.firstRowHeader
        ? this.parsedData
        : [[], ...this.parsedData]

      const header = this.prepareHeader(rawHeader, rawData)
      const previewData = this.getPreview(header, rawData)
      this.$emit('data', { header, previewData })
    },
  },
}
</script>
