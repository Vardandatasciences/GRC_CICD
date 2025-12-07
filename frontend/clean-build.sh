#!/bin/bash

# Clean and rebuild Vue.js project
echo "🧹 Cleaning project..."

# Remove node_modules cache
rm -rf node_modules/.cache

# Remove dist folder
rm -rf dist

# Remove ESLint cache
rm -rf .eslintcache

# Clear npm cache
npm cache clean --force

echo "📦 Reinstalling dependencies..."
npm install

echo "🔍 Running linter with fix..."
npm run lint:fix

echo "🚀 Starting development server..."
npm run serve 