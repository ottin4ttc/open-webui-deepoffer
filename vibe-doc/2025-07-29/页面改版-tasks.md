# DeepOffer 页面改版 - 代码实施细节计划

## 第一阶段：功能限制实施（2天）

### Day 1: 权限配置与后端限制

#### Task 1.1: 修改默认权限配置
**文件**: `src/lib/stores/index.ts`
- [ ] 找到权限相关的store定义
- [ ] 修改默认权限对象，禁用以下功能：
  - workspace.models = false
  - workspace.knowledge = false
  - workspace.prompts = false
  - workspace.tools = false
  - chat.controls = false
  - chat.file_upload = false
  - chat.share = false
  - chat.stt = false
  - chat.tts = false
  - chat.call = false
  - chat.multiple_models = false
  - features.direct_tool_servers = false
  - features.web_search = false
  - features.image_generation = false
  - features.notes = false

#### Task 1.2: 后端权限验证
**文件**: `backend/open_webui/routers/` 相关路由文件
- [ ] 检查并加强权限验证逻辑
- [ ] 确保前端权限限制与后端同步

### Day 2: 前端功能屏蔽

#### Task 2.1: 简化侧边栏
**文件**: `src/lib/components/layout/Sidebar.svelte`
- [ ] 使用条件渲染隐藏以下菜单项：
  ```svelte
  {#if false}
    <!-- 工作区入口 -->
    <!-- 笔记功能 -->
    <!-- 游乐场功能 -->
  {/if}
  ```
- [ ] 保留：聊天历史、设置

#### Task 2.2: 精简聊天界面
**文件**: `src/lib/components/chat/MessageInput.svelte`
- [ ] 隐藏语音输入按钮（第1191-1237行）
  ```svelte
  {#if $_user?.permissions?.chat?.stt && false}
    <!-- 语音输入按钮代码 -->
  {/if}
  ```
- [ ] 隐藏电话/通话按钮（第1264-1325行）
  ```svelte
  {#if $_user?.permissions?.chat?.call && false}
    <!-- 通话按钮代码 -->
  {/if}
  ```

**文件**: `src/lib/components/chat/MessageInput/InputMenu.svelte`
- [ ] 隐藏文件上传相关菜单项
- [ ] 使用权限控制：`$_user?.permissions?.chat?.file_upload`

**文件**: `src/lib/components/chat/Messages/ResponseMessage.svelte`
- [ ] 隐藏消息朗读按钮（第1019-1030行）
  ```svelte
  {#if $_user?.permissions?.chat?.tts && false}
    <!-- 朗读按钮代码 -->
  {/if}
  ```

**文件**: `src/lib/components/chat/Navbar.svelte`
- [ ] 隐藏三点菜单按钮（第89-121行）
- [ ] 隐藏Controls按钮（第124-136行）
  ```svelte
  {#if $_user?.permissions?.chat?.controls && false}
    <!-- Controls按钮代码 -->
  {/if}
  ```

## 第二阶段：界面简化实施（2天）

### Day 3: 设置页面精简

#### Task 3.1: 修改设置模态框
**文件**: `src/lib/components/chat/SettingsModal.svelte`
- [ ] 修改tabs数组定义（第32-260行），只保留：
  ```javascript
  const allowedTabs = ['general', 'account'];
  const tabs = originalTabs.filter(tab => 
    $user?.role === 'admin' || allowedTabs.includes(tab.id)
  );
  ```
- [ ] 隐藏搜索框（第410-420行）：
  ```svelte
  {#if false}
    <div class="hidden md:flex w-full rounded-xl -mb-1 px-0.5 gap-2" id="settings-search">
      <!-- 搜索框内容 -->
    </div>
  {/if}
  ```

#### Task 3.2: 简化通用设置
**文件**: `src/lib/components/chat/Settings/General.svelte`
- [ ] 保留主题选择（第241-258行）
- [ ] 保留语言选择（第260-288行）
- [ ] 移除通知设置（第290-308行）
- [ ] 移除系统提示词设置
- [ ] 移除高级参数设置

### Day 4: 路由和权限控制

#### Task 4.1: 限制页面访问
**文件**: `src/routes/(app)/workspace/+page.svelte`
- [ ] 添加权限检查，非管理员重定向到首页：
  ```javascript
  import { goto } from '$app/navigation';
  
  onMount(() => {
    if (!$user?.role === 'admin') {
      goto('/');
    }
  });
  ```

**文件**: `src/routes/(app)/playground/+page.svelte`
- [ ] 同上处理

**文件**: `src/routes/(app)/notes/+page.svelte`
- [ ] 同上处理

#### Task 4.2: 全局导航守卫
**文件**: `src/routes/(app)/+layout.svelte`
- [ ] 添加全局权限检查逻辑
- [ ] 限制普通用户访问高级功能页面

## 第三阶段：品牌定制实施（1天）

### Day 5: Logo和品牌元素替换

#### Task 5.1: 替换应用图标
- [ ] 处理 `vibe-doc/2025-07-29/asserts/deepoffer.png`，生成不同尺寸, 适配深色模式
  - favicon.png (标准图标)
  - favicon-96x96.png (96x96像素)
  - apple-touch-icon.png (180x180像素)
  - splash.png (启动画面，建议512x512像素)
  - splash-dark.png (深色模式启动画面，可基于splash.png调整)
- [ ] 替换 `/static/favicon.png`
- [ ] 替换 `/static/splash.png` （启动画面 - 正常模式）
- [ ] 替换 `/static/splash-dark.png` （启动画面 - 深色模式）
- [ ] 替换 `/static/favicon-96x96.png`
- [ ] 替换 `/static/apple-touch-icon.png`

#### Task 5.2: 修改页面内Logo
**文件**: `src/lib/components/layout/Sidebar.svelte`
- [ ] 替换侧边栏Logo引用（使用 `/static/splash.png`）

**文件**: `src/routes/auth/+page.svelte`
- [ ] 替换登录页面Logo（使用 `/static/splash.png`）

**文件**: `src/lib/components/chat/Messages/Placeholder.svelte`
- [ ] 替换聊天占位符中的头像

**注意**: 启动画面会在以下位置自动使用替换后的图片：
- `src/app.html` 中的启动画面（包含自动深色模式切换逻辑）
- `src/lib/components/app/AppSidebar.svelte` 侧边栏Logo
- 登录页面Logo

#### Task 5.3: 文案修改
**文件**: `src/lib/stores/index.ts`
- [ ] 修改应用名称：
  ```javascript
  export const WEBUI_NAME = writable('DeepOffer');
  ```

**文件**: `src/app.html`
- [ ] 修改默认页面标题为 "DeepOffer"

**文件**: `src/lib/i18n/locales/zh-CN/translation.json`
- [ ] 修改中文翻译文件中的相关文案
- [ ] 更新欢迎语、提示语等

#### Task 5.4: 主题配色
**文件**: `src/app.css`
- [ ] 添加DeepOffer主题变量：
  ```css
  :root {
    --deepoffer-primary: #1E88E5;
    --deepoffer-secondary: #42A5F5;
    --deepoffer-accent: #64B5F6;
    --deepoffer-dark: #0D47A1;
    --deepoffer-light: #E3F2FD;
  }
  ```
- [ ] 更新相关组件的配色引用

## 第四阶段：测试优化（1天）

### Day 6: 测试与优化

#### Task 6.1: 功能测试清单
- [ ] 测试普通用户权限限制
  - [ ] 无法访问工作区
  - [ ] 无法访问笔记
  - [ ] 无法访问游乐场
  - [ ] 无法使用语音功能
  - [ ] 无法上传文件
  - [ ] 无法使用多模型
- [ ] 测试管理员权限
  - [ ] 确保管理员保留所有功能
- [ ] 测试聊天基础功能
  - [ ] 发送消息
  - [ ] 接收回复
  - [ ] 查看历史
  - [ ] 导出对话

#### Task 6.2: UI/UX检查
- [ ] 检查所有隐藏功能是否完全不可见
- [ ] 验证品牌元素是否正确显示
- [ ] 确认配色方案一致性
- [ ] 测试响应式布局

#### Task 6.3: 性能优化
- [ ] 移除未使用的组件导入
- [ ] 检查控制台是否有错误
- [ ] 优化加载性能

## 代码实施注意事项

### 1. Git分支管理
```bash
# 创建功能分支
git checkout -b feat/deepoffer-customization

# 每完成一个阶段后提交
git add .
git commit -m "feat: 完成第X阶段 - [阶段描述]"
```

### 2. 配置文件备份
- 备份原始配置文件
- 创建 `.env.deepoffer` 配置文件模板

### 3. 测试环境准备
```bash
# 本地测试
npm run dev

# 构建测试
npm run build
npm run preview
```

### 4. 文档记录
- 记录所有修改的文件清单
- 保存修改前后的对比截图
- 编写部署说明文档

## 风险控制

1. **升级兼容性**
   - 使用条件渲染而非删除代码
   - 保留原始功能，仅通过配置控制显示
   - 维护修改记录文档

2. **权限安全**
   - 前后端双重验证
   - 定期审查权限配置
   - 防止客户端绕过

3. **回滚方案**
   - 保留原始代码分支
   - 可通过环境变量切换模式
   - 准备快速回滚脚本

## 进度跟踪模板

```markdown
## 实施进度
- 第一阶段：功能限制 ⏳ [0/10]
- 第二阶段：界面简化 ⏳ [0/8]
- 第三阶段：品牌定制 ⏳ [0/13]
- 第四阶段：测试优化 ⏳ [0/10]

总进度: [0/41] 0%
```

## 后续维护计划

1. **定期同步上游**
   ```bash
   # 添加上游仓库
   git remote add upstream https://github.com/open-webui/open-webui.git
   
   # 同步更新
   git fetch upstream
   git merge upstream/main
   ```

2. **功能开关设计**
   - 实现基于配置的功能开关
   - 支持动态启用/禁用功能
   - 便于后续功能调整

3. **监控与日志**
   - 添加用户行为监控
   - 记录功能使用情况
   - 收集性能指标
