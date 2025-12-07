const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  
  // Public path for production builds
  publicPath: process.env.NODE_ENV === 'production' ? '/' : '/',
  
  // Output directory
  outputDir: 'dist',
  
  // Disable source maps in production for smaller bundle size
  productionSourceMap: false,
  
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    },
    historyApiFallback: true
  },
  
  // Configure webpack
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all'
      }
    }
  }
})
