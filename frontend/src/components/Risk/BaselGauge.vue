<template>
  <div class="basel-gauge" :style="containerStyle">
    <svg :viewBox="`0 0 ${width} ${height}`" class="basel-gauge-svg">
      <!-- Background arc -->
      <path :d="bgArcPath" :stroke="bgColor" :stroke-width="stroke" fill="none" stroke-linecap="round"/>
      <!-- Filled arc with optional gradient per chart -->
      <defs>
        <linearGradient :id="gradientId" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" :stop-color="colorStart" />
          <stop offset="100%" :stop-color="colorEnd" />
        </linearGradient>
      </defs>
      <path :d="valueArcPath" :stroke="useGradient ? `url(#${gradientId})` : color" :stroke-width="stroke" fill="none" stroke-linecap="round"/>

      <!-- Center value -->
      <text :x="centerX" :y="centerY - 5" text-anchor="middle" class="basel-gauge-value-text">{{ centerText }}</text>
      <text :x="centerX" :y="centerY + 14" text-anchor="middle" class="basel-gauge-subtitle">{{ subtitle }}</text>

      <!-- Ticks baseline -->
      <line :x1="leftX" :y1="baselineY" :x2="rightX" :y2="baselineY" :stroke="tickColor" stroke-width="1"/>
      <!-- 0 / 50 / 100 labels -->
      <text :x="leftX" :y="baselineY + 16" class="basel-gauge-tick" text-anchor="middle">0</text>
      <text :x="centerX" :y="baselineY + 16" class="basel-gauge-tick" text-anchor="middle">50</text>
      <text :x="rightX" :y="baselineY + 16" class="basel-gauge-tick" text-anchor="middle">100</text>
    </svg>
  </div>
  
</template>

<script>
export default {
  name: 'BaselGauge',
  props: {
    value: { type: Number, required: true },
    max: { type: Number, default: 100 },
    color: { type: String, default: '#2ecc71' },
    colorStart: { type: String, default: '#2ecc71' },
    colorEnd: { type: String, default: '#27ae60' },
    bgColor: { type: String, default: '#e6ebf1' },
    tickColor: { type: String, default: '#cfd7df' },
    displayText: { type: String, default: '' },
    subtitle: { type: String, default: '' },
    width: { type: Number, default: 160 },
    height: { type: Number, default: 100 },
    stroke: { type: Number, default: 10 },
    useGradient: { type: Boolean, default: true },
    // Shift the starting position clockwise from 9 o'clock (in degrees)
    startOffsetDeg: { type: Number, default: 90 }
  },
  computed: {
    centerX() { return this.width / 2; },
    centerY() { return this.height * 0.75; },
    radius() { return Math.min(this.width, this.height) * 0.55; },
    leftX() { return this.centerX - this.radius + this.stroke * 0.2; },
    rightX() { return this.centerX + this.radius - this.stroke * 0.2; },
    baselineY() { return this.centerY + this.stroke * 0.2; },
    normalizedPercent() {
      if (!this.max || this.max <= 0) return 0;
      return Math.max(0, Math.min(100, (this.value / this.max) * 100));
    },
    bgArcPath() {
      return this.buildArcPath(0, 100);
    },
    valueArcPath() {
      return this.buildArcPath(0, this.normalizedPercent);
    },
    centerText() {
      return this.displayText || `${Math.round(this.normalizedPercent)}%`;
    },
    containerStyle() {
      return { width: '100%', display: 'flex', justifyContent: 'center' };
    },
    gradientId() {
      return `basel-gauge-grad-${this._uid}`;
    }
  },
  methods: {
    polarToCartesian(cx, cy, r, deg) {
      const rad = (deg - 90) * Math.PI / 180;
      return {
        x: cx + r * Math.cos(rad),
        y: cy + r * Math.sin(rad)
      };
    },
    buildArcPath(startPercent, endPercent) {
      // Draw along the TOP semicircle only, starting at 9 o'clock (180°)
      // and moving clockwise towards 3 o'clock (360°/0°)
      const clamped = Math.max(0, Math.min(100, endPercent));
      // Apply a small clockwise offset so the arc start is slightly to the right
      const startAngle = 180 + this.startOffsetDeg;
      const endAngle = startAngle + clamped * 1.8;
      const start = this.polarToCartesian(this.centerX, this.centerY, this.radius, startAngle);
      const end = this.polarToCartesian(this.centerX, this.centerY, this.radius, endAngle);
      const largeArc = endAngle - startAngle >= 180 ? 1 : 0;
      const sweep = 1; // clockwise
      return `M ${start.x} ${start.y} A ${this.radius} ${this.radius} 0 ${largeArc} ${sweep} ${end.x} ${end.y}`;
    }
  }
}
</script>

<style scoped>
.basel-gauge {
  display: inline-flex;
}
.basel-gauge-svg {
  width: 160px;
  height: 100px;
  overflow: visible;
}
.basel-gauge-value-text {
  font-size: 18px;
  font-weight: 700;
  fill: #2c3e50;
}
.basel-gauge-subtitle {
  font-size: 11px;
  fill: #7f8c8d;
}
.basel-gauge-tick {
  font-size: 9px;
  fill: #95a5a6;
}
</style>


