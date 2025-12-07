@echo off

REM Clean and rebuild Vue.js project
echo 🧹 Cleaning project...

REM Remove node_modules cache
if exist "node_modules\.cache" rmdir /s /q "node_modules\.cache"

REM Remove dist folder
if exist "dist" rmdir /s /q "dist"

REM Remove ESLint cache
if exist ".eslintcache" del /q ".eslintcache"

echo 📦 Reinstalling dependencies...
npm install

echo 🔍 Running linter with fix...
npm run lint:fix

echo 🚀 Starting development server...
npm run serve

pause 