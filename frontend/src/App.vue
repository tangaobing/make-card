<script setup>
import { ref, reactive, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage, ElDialog } from 'element-plus';
import { 
  Link, 
  View, 
  Upload, 
  MagicStick, 
  Delete, 
  Check, 
  DocumentCopy,
  Edit,
  List
} from '@element-plus/icons-vue';

const API_URL = 'http://localhost:8000';

// 表单数据
const formData = reactive({
  url: '',
  prompt: '',
  // 去除最大字符限制
});

// 文件上传相关
const htmlFile = ref(null);
const fileUploadRef = ref(null);
const isFileMode = ref(false);

// 输出结果
const outputResult = ref('');
const loading = ref(false);
const copySuccess = ref(false);

// 提示词相关
const dialogVisible = ref(false);
const tempPrompt = ref('');
const presetPrompts = ref([]);
const loadingPrompts = ref(false);

// URL验证
const validateUrl = (url) => {
  const pattern = /^https?:\/\/.+/i;
  return pattern.test(url);
};

// 页面加载时获取预设提示词
onMounted(async () => {
  await fetchPresetPrompts();
});

// 获取预设提示词列表
const fetchPresetPrompts = async () => {
  try {
    loadingPrompts.value = true;
    const response = await axios.get(`${API_URL}/preset_prompts`);
    presetPrompts.value = response.data.prompts || [];
  } catch (error) {
    console.error('获取预设提示词失败:', error);
    ElMessage.error('获取预设提示词失败');
  } finally {
    loadingPrompts.value = false;
  }
};

// 设置输入模式
const setInputMode = (fileMode) => {
  if (loading.value) return;
  isFileMode.value = fileMode;
  
  // 清空相关输入
  if (fileMode) {
    formData.url = '';
  } else {
    htmlFile.value = null;
    if (fileUploadRef.value) {
      fileUploadRef.value.clearFiles();
    }
  }
};

// 打开提示词弹窗
const openPromptDialog = () => {
  tempPrompt.value = formData.prompt;
  dialogVisible.value = true;
};

// 保存提示词
const savePrompt = () => {
  formData.prompt = tempPrompt.value;
  dialogVisible.value = false;
};

// 使用预设提示词
const usePresetPrompt = (prompt) => {
  formData.prompt = prompt;
  dialogVisible.value = false;
  ElMessage.success('已应用预设提示词');
};

// 处理文件变更
const handleFileChange = (file) => {
  const isHTML = file.raw.type === 'text/html' || file.name.endsWith('.html') || file.name.endsWith('.htm');
  if (!isHTML) {
    ElMessage.error('只能上传HTML文件!');
    fileUploadRef.value.clearFiles();
    return false;
  }
  
  htmlFile.value = file.raw;
  return false;
};

// 处理表单提交
const handleSubmit = async () => {
  // 检查提示词
  if (!formData.prompt.trim()) {
    ElMessage.error('请输入提示词');
    openPromptDialog();
    return;
  }
  
  try {
    loading.value = true;
    
    let response;
    
    if (isFileMode.value) {
      // 文件模式处理
      if (!htmlFile.value) {
        ElMessage.error('请选择HTML文件');
        loading.value = false;
        return;
      }
      
      const formData2 = new FormData();
      formData2.append('file', htmlFile.value);
      formData2.append('prompt', formData.prompt);
      // 不再传递max_length参数
      
      response = await axios.post(`${API_URL}/process_html_file`, formData2, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
    } else {
      // URL模式处理
      if (!validateUrl(formData.url)) {
        ElMessage.error('请输入有效的URL地址（以http://或https://开头）');
        loading.value = false;
        return;
      }
      
      response = await axios.post(`${API_URL}/process_content`, {
        url: formData.url,
        prompt: formData.prompt
        // 不再传递max_length参数
      });
    }
    
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
  htmlFile.value = null;
  if (fileUploadRef.value) {
    fileUploadRef.value.clearFiles();
  }
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
</script>

<template>
  <div class="app-container">
    <header class="header">
      <h1>卡片制作小工具</h1>
      <p class="subtitle">快速从网页或HTML文件创建内容卡片</p>
    </header>
    
    <main class="main-content">
      <div class="card-container">
        <!-- 左侧输入区 -->
        <div class="input-section">
          <div class="section-header">
            <div class="title-row">
              <h2>输入</h2>
              <div class="input-mode-tabs">
                <div 
                  class="tab-item" 
                  :class="{active: !isFileMode}" 
                  @click="setInputMode(false)"
                  :disabled="loading"
                >
                  <el-icon><Link /></el-icon> 网址
                </div>
                <div 
                  class="tab-item" 
                  :class="{active: isFileMode}"
                  @click="setInputMode(true)"
                  :disabled="loading"
                >
                  <el-icon><Upload /></el-icon> HTML
                </div>
              </div>
            </div>
          </div>
          
          <div class="compact-form">
            <!-- URL输入区域 -->
            <div v-if="!isFileMode" class="url-area">
              <div class="url-input-group">
                <el-input 
                  v-model="formData.url" 
                  placeholder="请输入http://或https://开头的URL" 
                  :disabled="loading"
                  clearable
                  size="default"
                >
                  <template #prefix>
                    <el-icon><Link /></el-icon>
                  </template>
                </el-input>
                <el-button 
                  type="default" 
                  @click="openUrlPreview"
                  :disabled="!formData.url"
                  title="预览"
                  class="preview-btn"
                  size="default"
                >
                  <el-icon><View /></el-icon>
                </el-button>
              </div>
            </div>
            
            <!-- HTML文件上传区域 -->
            <div v-else class="file-area">
              <el-upload
                ref="fileUploadRef"
                action="#"
                :auto-upload="false"
                :limit="1"
                :on-change="handleFileChange"
                :multiple="false"
                class="html-uploader"
              >
                <el-button type="primary" size="default">
                  <el-icon><Upload /></el-icon> 选择HTML文件
                </el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    仅支持HTML格式文件
                  </div>
                </template>
              </el-upload>
            </div>
            
            <!-- 提示词按钮 -->
            <div class="prompt-button-area">
              <el-button 
                @click="openPromptDialog" 
                type="primary" 
                plain
                size="default"
                class="prompt-btn"
              >
                <el-icon><Edit /></el-icon>
                {{ formData.prompt ? '编辑提示词' : '添加提示词' }}
              </el-button>
              <div class="prompt-preview" v-if="formData.prompt">
                {{ formData.prompt.length > 20 ? formData.prompt.substring(0, 20) + '...' : formData.prompt }}
              </div>
            </div>
            
            <!-- 操作按钮区域 -->
            <div class="action-area">
              <div class="button-group">
                <el-button 
                  type="primary" 
                  @click="handleSubmit" 
                  :loading="loading"
                  class="submit-btn"
                  size="default"
                >
                  <el-icon><MagicStick /></el-icon> 生成卡片
                </el-button>
                <el-button
                  type="info"
                  plain
                  @click="clearAll"
                  :disabled="loading"
                  class="clear-btn"
                  size="default"
                >
                  <el-icon><Delete /></el-icon> 清空
                </el-button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 右侧输出区 -->
        <div class="output-section">
          <div class="section-header">
            <h2>输出结果</h2>
            <div class="output-stats" v-if="outputResult">
              <span>{{ outputResult.length }} 字符</span>
            </div>
          </div>
          
          <div class="output-container">
            <el-input
              v-model="outputResult"
              type="textarea"
              :rows="10"
              placeholder="生成的卡片内容将显示在这里"
              resize="none"
              class="output-textarea"
            />
            
            <div class="copy-btn-container">
              <el-button 
                @click="copyToClipboard" 
                :disabled="!outputResult"
                :type="copySuccess ? 'success' : 'primary'"
                class="copy-btn"
                size="default"
              >
                <el-icon v-if="copySuccess"><Check /></el-icon>
                <el-icon v-else><DocumentCopy /></el-icon>
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
    
    <!-- 提示词弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="编辑提示词"
      width="50%"
      :before-close="() => dialogVisible = false"
    >
      <!-- 自定义提示词输入 -->
      <div class="custom-prompt-section">
        <el-input
          v-model="tempPrompt"
          type="textarea"
          :rows="4"
          placeholder="请输入提示词"
        />
      </div>
      
      <!-- 预设提示词列表 -->
      <div class="preset-prompts-section" v-if="presetPrompts.length > 0">
        <h3>预设提示词</h3>
        <p class="prompt-tip">点击下方提示词可直接使用</p>
        <el-skeleton v-if="loadingPrompts" :rows="3" animated />
        <div v-else class="preset-prompt-list">
          <div 
            v-for="(prompt, index) in presetPrompts" 
            :key="index"
            class="preset-prompt-item"
            @click="usePresetPrompt(prompt)"
          >
            <el-icon><List /></el-icon>
            <span>{{ prompt.length > 50 ? prompt.substring(0, 50) + '...' : prompt }}</span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePrompt">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style>
:root {
  /* 柔和的配色方案 */
  --primary-color: #6e7de0;  /* 柔和的蓝紫色 */
  --primary-hover: #5a69c2;
  --secondary-color: #a593e0; /* 柔和的紫色 */
  --accent-color: #e6c19a;    /* 柔和的杏色 */
  --text-color: #384259;      /* 深蓝灰色 */
  --bg-color: #f5f7fa;        /* 极浅的蓝灰色 */
  --card-bg: #ffffff;
  --border-color: #e9edf5;
  --shadow-color: rgba(151, 165, 205, 0.1);
  --success-color: #7ac9a1;   /* 柔和的绿色 */
  --section-bg: #f8faff;      /* 浅蓝背景色 */
  --input-bg: #fff;           /* 输入区背景 */
  --highlight-color: #f0f4ff; /* 高亮背景色 */
  --tab-active-bg: #dee6ff;   /* 选项卡活动背景 */
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Roboto', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  background-color: var(--bg-color);
  color: var(--text-color);
  line-height: 1.6;
  background-image: linear-gradient(120deg, #f5f7fa 0%, #f0f4ff 100%);
  min-height: 100vh;
}

.app-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 1rem 0.8rem;
  position: relative;
}

.header {
  text-align: center;
  margin-bottom: 1rem;
  position: relative;
}

h1 {
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(120deg, var(--primary-color), var(--secondary-color));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.2rem;
}

.subtitle {
  font-size: 0.9rem;
  color: var(--text-color);
  opacity: 0.8;
  font-weight: 300;
}

.main-content {
  margin-bottom: 1rem;
  position: relative;
}

.card-container {
  display: flex;
  gap: 1rem;
  background-color: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 4px 12px var(--shadow-color);
  padding: 1rem;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.card-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
  z-index: 0;
}

.input-section, .output-section {
  flex: 1;
  min-width: 0; /* 防止flexbox子元素溢出 */
  position: relative;
  border-radius: 10px;
  padding: 10px;
  background-color: var(--section-bg);
  box-shadow: 0 2px 6px var(--shadow-color);
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.4rem;
}

.title-row {
  display: flex;
  align-items: center;
  width: 100%;
}

h2 {
  font-size: 1.1rem;
  color: var(--primary-color);
  margin: 0;
  margin-right: 8px;
  font-weight: 600;
}

h3 {
  font-size: 1rem;
  color: var(--text-color);
  margin-bottom: 8px;
  font-weight: 500;
}

.input-mode-tabs {
  display: flex;
  background-color: var(--highlight-color);
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  margin-left: auto;
}

.tab-item {
  padding: 5px 10px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.tab-item:not(:last-child) {
  border-right: 1px solid var(--border-color);
}

.tab-item.active {
  background-color: var(--tab-active-bg);
  color: var(--primary-color);
  font-weight: 500;
}

.tab-item:hover:not(.active) {
  background-color: rgba(222, 230, 255, 0.5);
}

.compact-form {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  flex-grow: 1;
}

.url-area, .file-area, .prompt-button-area {
  width: 100%;
}

.url-input-group {
  display: flex;
  gap: 0.4rem;
  align-items: center;
}

.url-input-group .el-input {
  flex: 1;
}

.action-area {
  margin-top: auto;
}

.button-group {
  display: flex;
  gap: 0.4rem;
}

.submit-btn {
  flex: 2;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  background: linear-gradient(120deg, var(--primary-color), var(--primary-hover));
  border: none;
  font-weight: 500;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(110, 125, 224, 0.25);
}

.clear-btn:hover:not(:disabled) {
  opacity: 0.85;
}

.output-container {
  position: relative;
  padding: 8px;
  background: var(--input-bg);
  border-radius: 6px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.output-textarea {
  flex-grow: 1;
  font-size: 14px;
  line-height: 1.6;
  background-color: transparent;
  border: 1px solid var(--border-color);
  transition: border 0.3s;
}

.output-textarea:focus {
  border-color: var(--primary-color);
}

.output-stats {
  font-size: 0.8rem;
  color: var(--text-color);
  opacity: 0.7;
}

.copy-btn-container {
  margin-top: 0.6rem;
  display: flex;
  justify-content: flex-end;
}

.copy-btn {
  transition: all 0.25s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.copy-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
}

.preview-btn {
  transition: all 0.25s ease;
  min-width: unset;
  padding: 8px;
}

.preview-btn:hover:not(:disabled) {
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.html-uploader {
  width: 100%;
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  padding: 8px;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.html-uploader:hover {
  border-color: var(--primary-color);
  background-color: var(--highlight-color);
}

.el-upload__tip {
  margin-top: 5px;
  color: var(--text-color);
  font-size: 0.8rem;
  opacity: 0.7;
}

.prompt-button-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prompt-btn {
  white-space: nowrap;
}

.prompt-preview {
  font-size: 0.85rem;
  color: var(--text-color);
  background-color: var(--highlight-color);
  padding: 6px 10px;
  border-radius: 4px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.footer {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-color);
  opacity: 0.7;
  padding: 5px;
}

/* 提示词弹窗样式 */
.custom-prompt-section {
  margin-bottom: 20px;
}

.preset-prompts-section {
  margin-top: 20px;
  border-top: 1px solid var(--border-color);
  padding-top: 15px;
}

.prompt-tip {
  font-size: 0.8rem;
  color: var(--text-color);
  opacity: 0.7;
  margin-bottom: 10px;
}

.preset-prompt-list {
  max-height: 200px;
  overflow-y: auto;
  background-color: var(--section-bg);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.preset-prompt-item {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
  font-size: 0.9rem;
}

.preset-prompt-item:last-child {
  border-bottom: none;
}

.preset-prompt-item:hover {
  background-color: var(--highlight-color);
}

.preset-prompt-item .el-icon {
  color: var(--primary-color);
  font-size: 1rem;
}

@media (max-width: 768px) {
  .card-container {
    flex-direction: column;
    gap: 1rem;
    padding: 0.8rem;
  }
  
  .app-container {
    padding: 0.5rem;
  }
  
  h1 {
    font-size: 1.5rem;
  }
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.submit-btn:active {
  animation: pulse 0.3s ease;
}
</style>
