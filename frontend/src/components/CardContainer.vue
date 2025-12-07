<template>
  <div class="card-container">
    <div class="card-header">
      <div class="card-header-content">
        <img v-if="cardData.icon" :src="cardData.icon" alt="icon" class="policy-icon" />
        <h2 class="card-title">{{ cardData.name }}</h2>
      </div>
      <span :class="['card-status', getStatusClass(cardData.status)]">{{ cardData.status }}</span>
    </div>
    <div class="card-body">
      <ul class="card-details-list">
        <li v-for="col in columns" :key="col.key">
          <strong>{{ col.label }}:</strong> <span>{{ cardData[col.key] }}</span>
        </li>
      </ul>
    </div>
    <div class="card-footer">
      <CustomButton
        v-for="(btn, idx) in buttons"
        :key="btn.name + idx"
        :config="btn"
        @click="$emit('button-click', { card: cardData, button: btn })"
      />
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import CustomButton from './CustomButton.vue';
defineProps({
  cardData: { type: Object, required: true },
  columns: { type: Array, required: true }, // [{ label, key }]
  buttons: { type: Array, default: () => [] }
});
defineEmits(['button-click']);
function getStatusClass(status) {
  if (!status) return '';
  return status.toLowerCase().replace(/\s+/g, '-');
}
</script>

<style scoped>
.card-container {
  background-color: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card-container:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0,0,0,0.1);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--card-header-bg);
  padding: 16px;
  border-bottom: 1px solid var(--card-header-border);
}
.card-header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}
.policy-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #fff;
  box-shadow: 0 0 5px rgba(0,0,0,0.1);
}
.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--card-title-color);
  margin: 0;
}
.card-status {
  font-size: var(--card-status-font);
  font-weight: var(--card-status-font-weight);
  padding: 4px 10px;
  border-radius: var(--card-status-radius);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.card-status.on-rent {
  background-color: var(--status-on-rent-bg);
  color: var(--status-on-rent-text);
}
.card-status.on-sell {
  background-color: var(--status-on-sell-bg);
  color: var(--status-on-sell-text);
}
.card-status.renovation {
  background-color: var(--status-renovation-bg);
  color: var(--status-renovation-text);
}
.card-status.on-construction {
  background-color: var(--status-on-construction-bg);
  color: var(--status-on-construction-text);
}
.card-body {
  padding: 20px;
  flex-grow: 1;
  background-color: var(--card-body-bg);
}
.card-details-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.card-details-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
  color: var(--card-details-value);
  border-bottom: 1px dashed var(--card-details-border);
  padding-bottom: 10px;
}
.card-details-list li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.card-details-list li strong {
  font-weight: 600;
  color: var(--card-details-label);
}
.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--card-footer-border);
  background-color: var(--card-footer-bg);
}
</style> 