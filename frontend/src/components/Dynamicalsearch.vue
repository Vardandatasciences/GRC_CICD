<template>
    <div class="dynamic-search-bar">
      <i class="fas fa-search search-icon"></i>
      <input
        v-model="inputValue"
        :placeholder="placeholder"
        class="dynamic-search-input"
        @input="onInput"
        @keyup.enter="onEnter"
      />
      <button v-if="inputValue" class="clear-btn" @click="clearInput">✕</button>
    </div>
  </template>
  
  <script>
  export default {
    name: 'DynamicSearchBar',
    props: {
      modelValue: {
        type: String,
        default: ''
      },
      placeholder: {
        type: String,
        default: 'Search...'
      }
    },
    data() {
      return {
        inputValue: this.modelValue
      }
    },
    watch: {
      modelValue(val) {
        this.inputValue = val;
      }
    },
    methods: {
      onInput() {
        this.$emit('update:modelValue', this.inputValue);
        this.$emit('input', this.inputValue);
      },
      onEnter() {
        this.$emit('search', this.inputValue);
      },
      clearInput() {
        this.inputValue = '';
        this.onInput();
      }
    }
  }
  </script>
  
  <style scoped>
  .dynamic-search-bar {
    position: relative;
    width: 100%;
    max-width: 500px;
    border-radius: 50px;
    margin: 0;
    display: flex;
    align-items: center;
    border: none;
    box-shadow: none;
    transition: all 0.3s;
  }
  

  .search-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: #888;
    font-size: 16px;
    z-index: 10;
  }

  .dynamic-search-input {
    width: 100%;
    height: 38px;
    padding: 8px 16px 8px 60px !important;
    border: 2px solid #e0e0e0 !important;
    border-radius: 20px !important;
    font-size: 16px !important;
    color: #333 !important;
    outline: none !important;
    background: white !important;
    transition: border-color 0.3s !important;
  }

  .dynamic-search-input:focus {
    border-color: #7B6FDD;
    box-shadow: 0 0 0 3px rgba(123, 111, 221, 0.1);
  }
  
  .dynamic-search-input::placeholder {
    font-size: 16px;
  }
  
  .clear-btn {
    position: absolute;
    right: 12px;
    background: none;
    border: none;
    color: #888;
    font-size: 16px;
    cursor: pointer;
    padding: 0 5px;
    border-radius: 50%;
    transition: background 0.2s;
  }
  
  .clear-btn:hover {
    background: #eee;
    color: #d32f2f;
  }
  </style>