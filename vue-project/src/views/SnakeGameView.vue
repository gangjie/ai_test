<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// 类型定义
type Direction = 'up' | 'down' | 'left' | 'right'
interface Position {
  x: number
  y: number
}

// 游戏配置
const GRID_SIZE = 20
const CANVAS_SIZE = 400
const TILE_COUNT = CANVAS_SIZE / GRID_SIZE

// 游戏状态
const canvasRef = ref<HTMLCanvasElement | null>(null)
const score = ref(0)
const highScore = ref(0)
const isGameRunning = ref(false)
const startBtnText = ref('开始游戏')
const isAIMode = ref(false)

// 游戏变量
let snake: Position[] = []
let food: Position = { x: 0, y: 0 }
let direction: Direction = 'right'
let nextDirection: Direction = 'right'
let gameLoop: number | null = null
let gameSpeed = 100

// 初始化最高分
onMounted(() => {
  const savedHighScore = localStorage.getItem('snakeHighScore')
  if (savedHighScore) {
    highScore.value = parseInt(savedHighScore)
  }
})

// 组件卸载时清理
onUnmounted(() => {
  if (gameLoop) {
    clearInterval(gameLoop)
  }
})

// 初始化游戏
const initGame = () => {
  snake = [
    { x: 5, y: 10 },
    { x: 4, y: 10 },
    { x: 3, y: 10 }
  ]
  direction = 'right'
  nextDirection = 'right'
  score.value = 0
  gameSpeed = 100
  spawnFood()
  draw()
}

// 生成食物
const spawnFood = () => {
  do {
    food = {
      x: Math.floor(Math.random() * TILE_COUNT),
      y: Math.floor(Math.random() * TILE_COUNT)
    }
  } while (snake.some(segment => segment.x === food.x && segment.y === food.y))
}

// 检查位置是否安全
const isSafe = (pos: Position, snakeBody: Position[]): boolean => {
  return pos.x >= 0 && pos.x < TILE_COUNT &&
         pos.y >= 0 && pos.y < TILE_COUNT &&
         !snakeBody.some(s => s.x === pos.x && s.y === pos.y)
}

// BFS路径搜索
const bfsPath = (start: Position, end: Position, snakeBody: Position[]): Position[] => {
  const queue: Array<{ pos: Position; path: Position[] }> = [{ pos: start, path: [start] }]
  const visited = new Set<string>()
  visited.add(`${start.x},${start.y}`)

  const directions = [
    { dx: 0, dy: -1, dir: 'up' as Direction },
    { dx: 0, dy: 1, dir: 'down' as Direction },
    { dx: -1, dy: 0, dir: 'left' as Direction },
    { dx: 1, dy: 0, dir: 'right' as Direction }
  ]

  while (queue.length > 0) {
    const { pos, path } = queue.shift()!

    if (pos.x === end.x && pos.y === end.y) {
      return path
    }

    for (const d of directions) {
      // 不允许180度掉头
      if (d.dir === 'up' && direction === 'down') continue
      if (d.dir === 'down' && direction === 'up') continue
      if (d.dir === 'left' && direction === 'right') continue
      if (d.dir === 'right' && direction === 'left') continue

      const newX = pos.x + d.dx
      const newY = pos.y + d.dy
      const newPos: Position = { x: newX, y: newY }
      const key = `${newX},${newY}`

      if (isSafe(newPos, snakeBody) && !visited.has(key)) {
        visited.add(key)
        queue.push({
          pos: newPos,
          path: [...path, newPos]
        })
      }
    }
  }

  return []
}

// 绘制游戏
const draw = () => {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 清空画布
  ctx.fillStyle = '#0a0a0a'
  ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)

  // 绘制网格
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)'
  ctx.lineWidth = 1
  for (let i = 0; i <= TILE_COUNT; i++) {
    ctx.beginPath()
    ctx.moveTo(i * GRID_SIZE, 0)
    ctx.lineTo(i * GRID_SIZE, CANVAS_SIZE)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(0, i * GRID_SIZE)
    ctx.lineTo(CANVAS_SIZE, i * GRID_SIZE)
    ctx.stroke()
  }

  // 绘制食物
  ctx.fillStyle = '#ff4444'
  ctx.shadowBlur = 10
  ctx.shadowColor = '#ff4444'
  ctx.beginPath()
  ctx.arc(
    food.x * GRID_SIZE + GRID_SIZE / 2,
    food.y * GRID_SIZE + GRID_SIZE / 2,
    GRID_SIZE / 2 - 2,
    0,
    Math.PI * 2
  )
  ctx.fill()
  ctx.shadowBlur = 0

  // 绘制蛇
  snake.forEach((segment, index) => {
    // 蛇头用不同颜色
    if (index === 0) {
      ctx.fillStyle = '#00ff88'
      ctx.shadowBlur = 10
      ctx.shadowColor = '#00ff88'
    } else {
      // 渐变色身体
      const hue = 120 + (index * 2) % 60
      ctx.fillStyle = `hsl(${hue}, 100%, 50%)`
      ctx.shadowBlur = 5
      ctx.shadowColor = ctx.fillStyle
    }

    ctx.fillRect(
      segment.x * GRID_SIZE + 1,
      segment.y * GRID_SIZE + 1,
      GRID_SIZE - 2,
      GRID_SIZE - 2
    )

    // 绘制蛇眼
    if (index === 0) {
      ctx.fillStyle = '#000'
      ctx.shadowBlur = 0
      const eyeSize = 3
      const eyeOffset = 5

      switch (direction) {
        case 'right':
          ctx.fillRect(segment.x * GRID_SIZE + GRID_SIZE - eyeOffset, segment.y * GRID_SIZE + 5, eyeSize, eyeSize)
          ctx.fillRect(segment.x * GRID_SIZE + GRID_SIZE - eyeOffset, segment.y * GRID_SIZE + GRID_SIZE - 8, eyeSize, eyeSize)
          break
        case 'left':
          ctx.fillRect(segment.x * GRID_SIZE + eyeOffset - 3, segment.y * GRID_SIZE + 5, eyeSize, eyeSize)
          ctx.fillRect(segment.x * GRID_SIZE + eyeOffset - 3, segment.y * GRID_SIZE + GRID_SIZE - 8, eyeSize, eyeSize)
          break
        case 'up':
          ctx.fillRect(segment.x * GRID_SIZE + 5, segment.y * GRID_SIZE + eyeOffset - 3, eyeSize, eyeSize)
          ctx.fillRect(segment.x * GRID_SIZE + GRID_SIZE - 8, segment.y * GRID_SIZE + eyeOffset - 3, eyeSize, eyeSize)
          break
        case 'down':
          ctx.fillRect(segment.x * GRID_SIZE + 5, segment.y * GRID_SIZE + GRID_SIZE - eyeOffset, eyeSize, eyeSize)
          ctx.fillRect(segment.x * GRID_SIZE + GRID_SIZE - 8, segment.y * GRID_SIZE + GRID_SIZE - eyeOffset, eyeSize, eyeSize)
          break
      }
    }
  })
  ctx.shadowBlur = 0
}

// 计算可达空间大小（Flood Fill算法）
const countReachableSpace = (start: Position, snakeBody: Position[]): number => {
  const visited = new Set<string>()
  const queue: Position[] = [start]
  visited.add(`${start.x},${start.y}`)
  let count = 0

  while (queue.length > 0 && count < TILE_COUNT * TILE_COUNT) {
    const current = queue.shift()!
    count++

    const neighbors = [
      { x: current.x, y: current.y - 1 },
      { x: current.x, y: current.y + 1 },
      { x: current.x - 1, y: current.y },
      { x: current.x + 1, y: current.y }
    ]

    for (const neighbor of neighbors) {
      const key = `${neighbor.x},${neighbor.y}`
      if (!visited.has(key) && isSafe(neighbor, snakeBody)) {
        visited.add(key)
        queue.push(neighbor)
      }
    }
  }

  return count
}

// 模拟移动并检查安全性
const simulateMove = (snakeBody: Position[], move: Direction): { newSnake: Position[]; isSafe: boolean } => {
  const head = snakeBody[0]
  if (!head) return { newSnake: snakeBody, isSafe: false }

  const newHead: Position = { ...head }
  switch (move) {
    case 'up':
      newHead.y--
      break
    case 'down':
      newHead.y++
      break
    case 'left':
      newHead.x--
      break
    case 'right':
      newHead.x++
      break
  }

  // 检查新位置是否安全（考虑蛇尾会收缩）
  const tail = snakeBody[snakeBody.length - 1]
  const bodyWithoutTail = snakeBody.slice(0, -1)

  // 新位置不能是蛇身（除了尾巴，因为尾巴会移动）
  const isCollision = bodyWithoutTail.some(s => s.x === newHead.x && s.y === newHead.y) ||
                     (tail && newHead.x === tail.x && newHead.y === tail.y && snakeBody.length > 2)

  // 检查墙壁
  const isWall = newHead.x < 0 || newHead.x >= TILE_COUNT ||
                newHead.y < 0 || newHead.y >= TILE_COUNT

  if (isCollision || isWall) {
    return { newSnake: snakeBody, isSafe: false }
  }

  // 创建新蛇
  const newSnake = [newHead, ...bodyWithoutTail]
  return { newSnake, isSafe: true }
}

// AI决策 - 使用改进的算法
const getAIMove = (): Direction => {
  const head = snake[0]
  if (!head) return direction

  // 获取所有可能的移动方向
  const moves: Direction[] = ['up', 'down', 'left', 'right']
  const validMoves = moves.filter(move => {
    // 不允许180度掉头
    if (move === 'up' && direction === 'down') return false
    if (move === 'down' && direction === 'up') return false
    if (move === 'left' && direction === 'right') return false
    if (move === 'right' && direction === 'left') return false

    return true
  })

  // 评估每个移动
  type MoveEvaluation = {
    move: Direction
    score: number
    spaceSize: number
    newSnake: Position[]
  }

  const evaluations: MoveEvaluation[] = []

  for (const move of validMoves) {
    const { newSnake, isSafe: safe } = simulateMove(snake, move)

    if (!safe) {
      evaluations.push({ move, score: -1000, spaceSize: 0, newSnake: [] })
      continue
    }

    if (newSnake.length === 0) {
      evaluations.push({ move, score: -1000, spaceSize: 0, newSnake: [] })
      continue
    }

    // 计算可达空间大小
    const spaceSize = countReachableSpace(newSnake[0]!, newSnake)

    // 计算到食物的距离
    const newHead = newSnake[0]!
    const distanceToFood = Math.abs(newHead.x - food.x) + Math.abs(newHead.y - food.y)

    // 尝试从新位置到达食物
    const pathToFood = bfsPath(newHead, food, newSnake)
    const canReachFood = pathToFood.length > 0

    // 尝试从新位置到达尾巴
    const tail = newSnake[newSnake.length - 1]
    if (tail) {
      const pathToTail = bfsPath(newHead, tail, newSnake)
      const canReachTail = pathToTail.length > 0

      // 综合评分
      let score = 0

      // 可达空间越大越好
      score += spaceSize * 10

      // 能到达食物得高分
      if (canReachFood) {
        score += 1000
        score -= distanceToFood * 10
      }

      // 能到达尾巴保证安全
      if (canReachTail) {
        score += 500
      }

      // 距离食物近一点好
      score -= distanceToFood

      evaluations.push({ move, score, spaceSize, newSnake })
    } else {
      // 没有尾巴的情况（理论上不应该发生）
      evaluations.push({ move, score: -1000, spaceSize: 0, newSnake })
    }
  }

  // 按评分排序
  evaluations.sort((a, b) => b.score - a.score)

  // 返回最佳移动
  return evaluations[0]?.move ?? direction
}

// 更新游戏状态
const update = () => {
  // AI模式自动决策
  if (isAIMode.value) {
    const aiMove = getAIMove()
    if (aiMove !== direction) {
      nextDirection = aiMove
    }
  }

  direction = nextDirection

  // 计算新的蛇头位置
  const head = snake[0]
  if (!head) return

  const newHead: Position = { ...head }
  switch (direction) {
    case 'up':
      newHead.y--
      break
    case 'down':
      newHead.y++
      break
    case 'left':
      newHead.x--
      break
    case 'right':
      newHead.x++
      break
  }

  // 检查碰撞
  if (newHead.x < 0 || newHead.x >= TILE_COUNT ||
    newHead.y < 0 || newHead.y >= TILE_COUNT ||
    snake.some(segment => segment.x === newHead.x && segment.y === newHead.y)) {
    gameOver()
    return
  }

  snake.unshift(newHead)

  // 检查是否吃到食物
  if (newHead.x === food.x && newHead.y === food.y) {
    score.value += 10
    spawnFood()
    // 稍微加快速度（仅非AI模式）
    if (!isAIMode.value && gameSpeed > 50) {
      gameSpeed -= 2
      if (gameLoop) {
        clearInterval(gameLoop)
        gameLoop = setInterval(gameStep, gameSpeed)
      }
    }
  } else {
    snake.pop()
  }
}

// 游戏步骤
const gameStep = () => {
  update()
  draw()
}

// 游戏结束
const gameOver = () => {
  if (gameLoop) {
    clearInterval(gameLoop)
    gameLoop = null
  }
  isGameRunning.value = false
  isAIMode.value = false
  startBtnText.value = '重新开始'

  // 更新最高分
  if (score.value > highScore.value) {
    highScore.value = score.value
    localStorage.setItem('snakeHighScore', score.value.toString())
  }

  // 显示游戏结束消息
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
  ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)

  ctx.fillStyle = '#fff'
  ctx.font = 'bold 30px Arial'
  ctx.textAlign = 'center'
  ctx.fillText('游戏结束!', CANVAS_SIZE / 2, CANVAS_SIZE / 2 - 20)

  ctx.font = '20px Arial'
  ctx.fillText(`得分: ${score.value}`, CANVAS_SIZE / 2, CANVAS_SIZE / 2 + 20)
}

// 开始游戏
const startGame = () => {
  if (isGameRunning.value && gameLoop) {
    clearInterval(gameLoop)
  }
  initGame()
  isGameRunning.value = true
  isAIMode.value = false
  startBtnText.value = '重新开始'
  gameLoop = setInterval(gameStep, gameSpeed)
}

// AI自动玩
const startAI = () => {
  if (isGameRunning.value && gameLoop) {
    clearInterval(gameLoop)
  }
  initGame()
  isGameRunning.value = true
  isAIMode.value = true
  startBtnText.value = 'AI运行中...'
  gameSpeed = 50 // AI模式速度更快
  gameLoop = setInterval(gameStep, gameSpeed)
}

// 键盘控制
const handleKeyDown = (e: KeyboardEvent) => {
  if (!isGameRunning.value) {
    if (e.code === 'Space' || e.code === 'Enter') {
      startGame()
    }
    return
  }

  switch (e.key) {
    case 'ArrowUp':
    case 'w':
    case 'W':
      if (direction !== 'down') nextDirection = 'up'
      break
    case 'ArrowDown':
    case 's':
    case 'S':
      if (direction !== 'up') nextDirection = 'down'
      break
    case 'ArrowLeft':
    case 'a':
    case 'A':
      if (direction !== 'right') nextDirection = 'left'
      break
    case 'ArrowRight':
    case 'd':
    case 'D':
      if (direction !== 'left') nextDirection = 'right'
      break
  }
}

// 移动端控制
const moveUp = () => {
  if (direction !== 'down') nextDirection = 'up'
}
const moveDown = () => {
  if (direction !== 'up') nextDirection = 'down'
}
const moveLeft = () => {
  if (direction !== 'right') nextDirection = 'left'
}
const moveRight = () => {
  if (direction !== 'left') nextDirection = 'right'
}

// 添加键盘事件监听
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div class="snake-game">
    <div class="game-container">
      <h1>🐍 贪吃蛇</h1>

      <div class="score-board">
        <div class="score-item">
          得分: <span>{{ score }}</span>
        </div>
        <div class="score-item">
          最高分: <span>{{ highScore }}</span>
        </div>
      </div>

      <canvas
        ref="canvasRef"
        :width="CANVAS_SIZE"
        :height="CANVAS_SIZE"
        id="gameCanvas"
      ></canvas>

      <div class="controls">
        <div class="button-group">
          <button class="btn" @click="startGame">{{ startBtnText }}</button>
          <button class="btn ai-btn" @click="startAI">🤖 AI自动玩</button>
        </div>
        <div class="mobile-controls">
          <button class="mobile-btn" @click="moveUp" style="grid-column: 2;">↑</button>
          <button class="mobile-btn" @click="moveLeft" style="grid-column: 1; grid-row: 2;">←</button>
          <button class="mobile-btn" @click="moveDown" style="grid-column: 2; grid-row: 2;">↓</button>
          <button class="mobile-btn" @click="moveRight" style="grid-column: 3; grid-row: 2;">→</button>
        </div>
      </div>

      <div class="instructions">
        使用方向键或 WASD 控制蛇的移动，或点击 AI 自动玩
      </div>
    </div>
  </div>
</template>

<style scoped>
.snake-game {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 0;
}

.game-container {
  text-align: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  background: linear-gradient(45deg, #00ff88, #00ccff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.score-board {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
  font-size: 1.2rem;
}

.score-item {
  padding: 10px 20px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
}

.score-item span {
  color: #00ff88;
  font-weight: bold;
}

#gameCanvas {
  border: 3px solid #00ff88;
  border-radius: 10px;
  background: #0a0a0a;
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
}

.controls {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.button-group {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  justify-content: center;
}

.btn {
  padding: 12px 30px;
  font-size: 1.1rem;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  background: linear-gradient(45deg, #00ff88, #00ccff);
  color: #1a1a2e;
  font-weight: bold;
  transition: all 0.3s ease;
}

.btn:hover {
  transform: scale(1.05);
  box-shadow: 0 5px 20px rgba(0, 255, 136, 0.5);
}

.btn:active {
  transform: scale(0.95);
}

.ai-btn {
  background: linear-gradient(45deg, #ff6b6b, #feca57);
}

.ai-btn:hover {
  box-shadow: 0 5px 20px rgba(255, 107, 107, 0.5);
}

.mobile-controls {
  display: none;
  margin-top: 20px;
  grid-template-columns: repeat(3, 60px);
  gap: 5px;
}

.mobile-btn {
  width: 60px;
  height: 60px;
  font-size: 1.5rem;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mobile-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.mobile-btn:active {
  background: rgba(0, 255, 136, 0.5);
}

.instructions {
  margin-top: 20px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

@media (max-width: 768px) {
  .mobile-controls {
    display: grid;
  }

  #gameCanvas {
    width: 320px;
    height: 320px;
  }

  h1 {
    font-size: 2rem;
  }

  .button-group {
    flex-direction: column;
  }
}
</style>
