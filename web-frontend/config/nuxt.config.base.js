export default function (
  base = '@',
  premiumBase = '@/../premium/web-frontend',
  enterpriseBase = '@/../enterprise/web-frontend'
) {
  // Support adding in extra modules say from a plugin using the ADDITIONAL_MODULES
  // env variable which is a comma separated list of absolute module paths.
  const additionalModulesCsv = process.env.ADDITIONAL_MODULES
  const additionalModules = additionalModulesCsv
    ? additionalModulesCsv
        .split(',')
        .map((m) => m.trim())
        .filter((m) => m !== '')
    : []

  if (additionalModules.length > 0) {
    console.log(`Loading extra plugin modules: ${additionalModules}`)
  }
  const baseModules = [
    base + '/modules/core/module.js',
    base + '/modules/database/module.js',
    base + '/modules/integrations/module.js',
    base + '/modules/builder/module.js',
    base + '/modules/dashboard/module.js',
    base + '/modules/automation/module.js',
    // AI Assistant 插件
    base + '/../plugins/ai_assistant/web-frontend/modules/ai_assistant/module.js',
    // Excel Importer 插件
    base + '/../plugins/excel_importer/web-frontend/modules/excel_importer/module.js',
    // Row Author Tracker 插件 - 自动填写人追踪
    base + '/../plugins/row_author_tracker/web-frontend/modules/row-author-tracker/module.js',
    // Access Control 插件 - 细粒度访问控制
    base + '/../plugins/access_control/web-frontend/modules/access-control/module.js',
  ]
  if (!process.env.BASEROW_OSS_ONLY) {
    baseModules.push(
      premiumBase + '/modules/baserow_premium/module.js',
      enterpriseBase + '/modules/baserow_enterprise/module.js'
    )
  }
  baseModules.push('@nuxtjs/sentry')

  const modules = baseModules.concat(additionalModules)
  return {
    server: {
      host: '0.0.0.0',
      port: 3128
    },
    modules,
    buildModules: [
      '@nuxtjs/stylelint-module',
      '@nuxtjs/svg',
      '@nuxtjs/composition-api/module',
    ],
    sentry: {
      clientIntegrations: {
        Dedupe: {},
        ExtraErrorData: {},
        RewriteFrames: {},
        ReportingObserver: null,
      },
      clientConfig: {
        attachProps: true,
        logErrors: true,
      },
    },
    build: {
      extend(config, ctx) {
        config.node = { fs: 'empty' }
        config.module.rules.push({
          test: /\.(m|c)js$/,
          include: /node_modules/,
          type: 'javascript/auto',
        })
        const zipPkgDir = require('path').dirname(
          require.resolve('@zip.js/zip.js/package.json')
        )
        const zipUmdPath = require('path').join(zipPkgDir, 'dist/zip.min.js')
        config.resolve.alias = {
          ...(config.resolve.alias || {}),
          '@vue2-flow/core': require.resolve('@vue2-flow/core'),
          // Expose a stable alias pointing to the UMD build path bypassing package exports
          'zipjs-umd': zipUmdPath,
        }
      },
      babel: { compact: true },
      transpile: [
        'axios',
        'tiptap-markdown',
        'markdown-it',
        'vue-chartjs',
        'chart.js',
        '@vue2-flow/core',
      ],
    },
  }
}
