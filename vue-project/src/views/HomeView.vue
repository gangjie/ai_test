<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 创建简单的粒子效果
const particlesContainer = ref<HTMLElement | null>(null)

// 定义按钮点击事件
const handleCodeCompare = () => {
  alert('代码比对审查功能')
}

const handleStaticReview = () => {
  alert('静态代码审查功能')
}

const handleManualInput = () => {
  alert('手动输入审查功能')
}

// 创建粒子效果
onMounted(() => {
  const container = particlesContainer.value
  if (!container) return

  // 创建粒子
  interface Particle {
    element: HTMLDivElement
    x: number
    y: number
    speedX: number
    speedY: number
  }

  const particles: Particle[] = []
  const particleCount = 100

  for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div') as HTMLDivElement
    particle.className = 'particle'
    particle.style.left = `${Math.random() * 100}%`
    particle.style.top = `${Math.random() * 100}%`
    particle.style.width = `${Math.random() * 5 + 1}px`
    particle.style.height = particle.style.width
    particle.style.backgroundColor = '#00ff00'
    particle.style.opacity = `${Math.random() * 0.5 + 0.3}`
    container.appendChild(particle)
    particles.push({
      element: particle,
      x: parseFloat(particle.style.left),
      y: parseFloat(particle.style.top),
      speedX: (Math.random() - 0.5) * 0.5,
      speedY: (Math.random() - 0.5) * 0.5
    })
  }

  // 动画循环
  const animate = () => {
    particles.forEach(particle => {
      let x = particle.x + particle.speedX
      let y = particle.y + particle.speedY

      if (x > 100 || x < 0) particle.speedX *= -1
      if (y > 100 || y < 0) particle.speedY *= -1

      particle.x += particle.speedX
      particle.y += particle.speedY

      particle.element.style.left = `${particle.x}%`
      particle.element.style.top = `${particle.y}%`
    })
    requestAnimationFrame(animate)
  }

  animate()
})
</script>

<template>
  <div class="home-container" ref="particlesContainer">
    <!-- 内容区域 -->
    <div class="content">
      <div class="title-section">
        <h1 class="main-title">代码审查助手</h1>
        <p class="subtitle">智能化代码质量检测平台</p>
      </div>
      
      <div class="buttons-section">
        <button class="action-button" @click="handleCodeCompare">
          <span class="button-icon">🔍</span>
          <span class="button-text">代码比对审查</span>
        </button>
        
        <button class="action-button" @click="handleStaticReview">
          <span class="button-icon">📜</span>
          <span class="button-text">静态代码审查</span>
        </button>
        
        <button class="action-button" @click="handleManualInput">
          <span class="button-icon">⌨️</span>
          <span class="button-text">手动输入审查</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: white;
  font-family: 'Arial', sans-serif;
}

.particle {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
  padding: 20px;
}

.title-section {
  margin-bottom: 50px;
}

.main-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 15px;
  text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
  background: linear-gradient(to right, #00ff00, #00cc00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
  from {
    text-shadow: 0 0 5px #fff, 0 0 10px #00ff00, 0 0 15px #00ff00, 0 0 20px #00ff00;
  }
  to {
    text-shadow: 0 0 10px #fff, 0 0 20px #00ff00, 0 0 30px #00ff00, 0 0 40px #00ff00;
  }
}

.subtitle {
  font-size: 1.2rem;
  opacity: 0.8;
  max-width: 600px;
  line-height: 1.6;
}

.buttons-section {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 30px;
  max-width: 800px;
}

.action-button {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 255, 0, 0.3);
  border-radius: 15px;
  padding: 25px 30px;
  width: 220px;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 3;
}

.action-button:hover {
  background: rgba(0, 255, 0, 0.1);
  border-color: rgba(0, 255, 0, 0.6);
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 255, 0, 0.2);
}

.button-icon {
  font-size: 2.5rem;
  margin-bottom: 15px;
}

.button-text {
  font-size: 1.2rem;
  font-weight: 600;
}

@media (max-width: 768px) {
  .main-title {
    font-size: 2.5rem;
  }
  
  .buttons-section {
    flex-direction: column;
    gap: 20px;
  }
  
  .action-button {
    width: 100%;
    max-width: 300px;
  }
}
</style>