<script setup>
import { ref, reactive } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const API_URL = 'http://localhost:8000';

// 表单数据
const formData = reactive({
  url: '',
  prompt: '',
  max_length: 500
});

// 输出结果
const outputResult = ref('');
const loading = ref(false);
const copySuccess = ref(false);
const showSettings = ref(false);

// URL验证
const validateUrl = (url) => {
  const pattern = /^https?:\/\/.+/i;
  return pattern.test(url);
};

// 处理表单提交
const handleSubmit = async () => {
  // 验证URL
  if (!validateUrl(formData.url)) {
    ElMessage.error('请输入有效的URL地址（以http://或https://开头）');
    return;
  }
  
  // 验证提示词不为空
  if (!formData.prompt.trim()) {
    ElMessage.error('请输入提示词');
    return;
  }
  
  try {
    loading.value = true;
    
    const response = await axios.post(`${API_URL}/process_content`, {
      url: formData.url,
      prompt: formData.prompt,
      max_length: formData.max_length
    });
    
    outputResult.value = response.data.result;
    ElMessage.success('处理成功');
  } catch (error) {
    let errorMsg = '处理失败';
    if (error.response && error.response.data) {
      errorMsg = error.response.data.detail || errorMsg;
    }
    ElMessage.error(errorMsg);
    console.error('Error:', error);
  } finally {
    loading.value = false;
  }
};

// 复制结果到剪贴板
const copyToClipboard = () => {
  if (!outputResult.value) {
    ElMessage.warning('没有可复制的内容');
    return;
  }
  
  navigator.clipboard.writeText(outputResult.value)
    .then(() => {
      copySuccess.value = true;
      ElMessage.success('已复制到剪贴板');
      
      // 重置复制状态
      setTimeout(() => {
        copySuccess.value = false;
      }, 2000);
    })
    .catch(err => {
      ElMessage.error('复制失败');
      console.error('复制失败:', err);
    });
};

// 清空所有输入和输出
const clearAll = () => {
  formData.url = '';
  formData.prompt = '';
  outputResult.value = '';
  ElMessage.info('已清空所有内容');
};

// 预览原始URL
const openUrlPreview = () => {
  if (!validateUrl(formData.url)) {
    ElMessage.warning('请先输入有效URL');
    return;
  }
  window.open(formData.url, '_blank');
};

// 重置设置
const resetSettings = () => {
  formData.max_length = 500;
  ElMessage.success('已重置设置');
};
</script>

<template>
  <div class="app-container">
    <header class="header">
      <h1>卡片制作小工具</h1>
      <p class="subtitle">快速从网页创建内容卡片</p>
    </header>
    
    <main class="main-content">
      <div class="card-container">
        <!-- 左侧输入区 -->
        <div class="input-section">
          <div class="section-header">
            <h2>输入</h2>
            <el-button 
              type="info" 
              size="small"
              plain
              @click="showSettings = !showSettings"
              class="settings-btn"
            >
              <i class="el-icon-setting"></i>
              {{ showSettings ? '隐藏设置' : '高级设置' }}
            </el-button>
          </div>
          
          <el-form>
            <el-form-item label="网页地址">
              <div class="url-input-group">
                <el-input 
                  v-model="formData.url" 
                  placeholder="请输入http://或https://开头的URL" 
                  :disabled="loading"
                  clearable
                />
                <el-button 
                  type="default" 
                  size="default" 
                  icon="el-icon-view"
                  @click="openUrlPreview"
                  :disabled="!formData.url"
                  title="在新窗口打开URL预览"
                >
                  预览
                </el-button>
              </div>
            </el-form-item>
            
            <el-collapse-transition>
              <div v-show="showSettings">
                <el-form-item label="内容长度限制">
                  <div class="slider-container">
                    <el-slider
                      v-model="formData.max_length"
                      :min="100"
                      :max="5000"
                      :step="100"
                      :format-tooltip="value => `${value}字符`"
                      :disabled="loading"
                    ></el-slider>
                    <span class="slider-value">{{ formData.max_length }}字符</span>
                  </div>
                  <div class="reset-link">
                    <a href="#" @click.prevent="resetSettings">恢复默认值</a>
                  </div>
                </el-form-item>
              </div>
            </el-collapse-transition>
            
            <el-form-item label="提示词">
              <el-input 
                v-model="formData.prompt" 
                type="textarea" 
                :rows="6"
                placeholder="请输入提示词" 
                :disabled="loading"
                resize="none"
              />
            </el-form-item>
            
            <el-form-item>
              <div class="button-group">
                <el-button 
                  type="primary" 
                  @click="handleSubmit" 
                  :loading="loading"
                  class="submit-btn"
                >
                  生成卡片
                </el-button>
                <el-button
                  type="info"
                  plain
                  @click="clearAll"
                  :disabled="loading"
                >
                  清空
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 右侧输出区 -->
        <div class="output-section">
          <h2>输出结果</h2>
          
          <div class="output-container">
            <el-input
              v-model="outputResult"
              type="textarea"
              :rows="14"
              placeholder="生成的卡片内容将显示在这里"
              resize="none"
              class="output-textarea"
            />
            
            <div class="output-stats" v-if="outputResult">
              <span>内容长度: {{ outputResult.length }} 字符</span>
            </div>
            
            <div class="copy-btn-container">
              <el-button 
                @click="copyToClipboard" 
                :disabled="!outputResult"
                :type="copySuccess ? 'success' : 'primary'"
                class="copy-btn"
              >
                {{ copySuccess ? '已复制' : '复制内容' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </main>
    
    <footer class="footer">
      <p>© 2025 卡片制作小工具</p>
    </footer>
  </div>
</template>

<style>
:root {
  --primary-color: #3E63DD;
  --primary-hover: #2D4CB3;
  --secondary-color: #6E56CF;
  --accent-color: #F59E0B;
  --text-color: #1A2027;
  --bg-color: #FCFCFC;
  --card-bg: #FFFFFF;
  --border-color: #E5E7EB;
  --shadow-color: rgba(0, 0, 0, 0.05);
  --success-color: #10B981;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg-color);
  color: var(--text-color);
  line-height: 1.6;
}

.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

h1 {
  font-size: 2.25rem;
  color: var(--primary-color);
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.1rem;
  color: var(--text-color);
  opacity: 0.8;
}

.main-content {
  margin-bottom: 2rem;
}

.card-container {
  display: flex;
  gap: 2rem;
  background-color: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 4px 20px var(--shadow-color);
  padding: 2rem;
}

.input-section, .output-section {
  flex: 1;
  min-width: 0; /* 防止flexbox子元素溢出 */
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

h2 {
  font-size: 1.25rem;
  color: var(--secondary-color);
  margin: 0;
}

.button-group {
  display: flex;
  gap: 1rem;
}

.submit-btn {
  flex: 2;
  transition: transform 0.2s, box-shadow 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(62, 99, 221, 0.2);
}

.output-container {
  position: relative;
}

.output-textarea {
  font-size: 14px;
  line-height: 1.6;
}

.output-stats {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #666;
  text-align: right;
}

.copy-btn-container {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-end;
}

.copy-btn {
  transition: transform 0.2s;
}

.copy-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.url-input-group {
  display: flex;
  gap: 0.5rem;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.slider-value {
  font-size: 0.9rem;
  color: #666;
  min-width: 70px;
}

.reset-link {
  margin-top: 0.5rem;
  text-align: right;
  font-size: 0.85rem;
}

.reset-link a {
  color: var(--primary-color);
  text-decoration: none;
}

.reset-link a:hover {
  text-decoration: underline;
}

.footer {
  text-align: center;
  margin-top: 3rem;
  font-size: 0.9rem;
  color: #666;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-container {
    flex-direction: column;
    gap: 2rem;
  }
  
  .app-container {
    padding: 1rem;
  }
  
  h1 {
    font-size: 1.75rem;
  }
  
  .url-input-group {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .button-group {
    flex-direction: column;
  }
}
</style>
