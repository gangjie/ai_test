<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// 创建 Monaco Editor 容器引用
const editorContainer = ref<HTMLElement | null>(null)
let editor: any = null

// 示例 Java 代码
const javaCode = ref(`public class CodeReviewExample {
    public static void main(String[] args) {
        System.out.println("欢迎使用代码审查助手！");
        
        // 示例代码审查功能
        int x = 10;
        int y = 20;
        int sum = addNumbers(x, y);
        System.out.println("两数之和: " + sum);
        
        // 潜在问题代码示例
        String str = null;
        System.out.println(str.length()); // 空指针异常风险
    }
    
    /**
     * 计算两个整数的和
     * @param a 第一个整数
     * @param b 第二个整数
     * @return 两数之和
     */
    public static int addNumbers(int a, int b) {
        // 可能的整数溢出问题
        return a + b;
    }
    
    /**
     * 检查字符串是否为空
     * @param str 待检查的字符串
     * @return 如果字符串为空则返回true，否则返回false
     */
    public static boolean isEmpty(String str) {
        // 更好的实现应该是 str == null || str.length() == 0
        return str.length() == 0;
    }
}`)

// 初始化 Monaco Editor
onMounted(async () => {
  if (editorContainer.value) {
    try {
      // 动态导入 Monaco Editor
      const monaco = await import('monaco-editor')
      
      // 创建编辑器实例
      editor = monaco.editor.create(editorContainer.value, {
        value: javaCode.value,
        language: 'java',
        theme: 'vs-dark',
        automaticLayout: true,
        minimap: {
          enabled: true
        },
        fontSize: 14,
        scrollBeyondLastLine: false,
        readOnly: false,
        lineNumbers: 'on',
        roundedSelection: true,
        scrollBeyondLastColumn: 5,
        smoothScrolling: true,
      })
    } catch (error) {
      console.error('Monaco Editor 初始化失败:', error)
    }
  }
})

// 清理编辑器实例
onUnmounted(() => {
  if (editor) {
    editor.dispose()
  }
})
</script>

<template>
  <div class="java-code-view">
    <div class="header">
      <h1>Java 代码展示与审查</h1>
      <p>使用 Monaco Editor 展示和编辑 Java 代码，支持代码高亮和语法检查</p>
    </div>
    
    <div class="editor-container" ref="editorContainer"></div>
    
    <div class="footer">
      <p>代码审查助手 - 智能化代码质量检测平台</p>
    </div>
  </div>
</template>

<style scoped>
.java-code-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  background-color: #1e1e1e;
  color: #ffffff;
}

.header {
  margin-bottom: 20px;
  text-align: center;
}

.header h1 {
  font-size: 2rem;
  margin-bottom: 10px;
  color: #4ec9b0;
}

.header p {
  font-size: 1.1rem;
  opacity: 0.8;
}

.editor-container {
  flex: 1;
  border: 1px solid #3c3c3c;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 20px;
}

.footer {
  text-align: center;
  padding: 10px;
  border-top: 1px solid #3c3c3c;
  font-size: 0.9rem;
  opacity: 0.7;
}
</style>