# OPC Mall 微信小程序架构设计

> 版本：v1.0 | 日期：2026-03-27 | 角色：产品架构师

---

## 一、项目概述

OPC Mall 是一款基于微信小程序的社交电商系统，核心场景是积分商城 + 分销裂变，配套会员体系与智能体商城。业务核心逻辑是**扫码即绑定上下级关系**，驱动用户自发裂变。

**后端技术栈**：MedusaJS（Headless eCommerce）
**目标用户**：OPC 生态内的消费者与分销商
**核心业务指标**：注册转化率、下线绑定率、订单完成率、佣金提现率

---

## 二、技术选型对比

| 维度 | 原生小程序 | Taro | uni-app | kbone |
|------|-----------|------|---------|-------|
| 语言 | TypeScript/JS | React/Vue | Vue/Native | Web→微信适配层 |
| 生态 | 微信独有 | 多端统一 | 多端统一 | 微信独有 |
| 包体积 | ⭐⭐⭐⭐⭐ 最优 | ⭐⭐⭐ 中等 | ⭐⭐⭐ 中等 | ⭐⭐ 较大 |
| 学习曲线 | 陡（自研组件） | 陡（需熟悉框架） | 平缓（Vue开发者友好） | 中等 |
| 状态管理 | 原生setData | Redux/Zustand | Pinia/Vuex | Web生态 |
| UI组件 | 需自建 | Taro UI / NutUI | uni-ui 丰富 | Web组件 |
| Web兼容 | 无 | 需适配层 | 需适配层 | ✅ 最优 |
| 调试体验 | ⭐⭐⭐⭐ 官方工具好 | ⭐⭐⭐ 编译后略慢 | ⭐⭐⭐ 略慢 | ⭐⭐ 复杂 |
| 长期维护 | 微信强依赖 | 社区活跃 | DCloud背书 | 微信内部项目 |

### 结论：**推荐 Taro + Vue 3 + TypeScript**

**理由**：
1. **Vue 3 上手快**：团队如果是Vue技术栈，开发效率最高
2. **多端预留**：未来可平滑扩展到 H5、App、抖音小程序
3. **类型安全**：TypeScript 保证复杂业务（分销关系、佣金计算）不出错
4. **生态成熟**：Taro 3.x+ 已稳定，社区文档丰富
5. **包体积可控**：通过 Tree-shaking + 分包加载，可控制在 2MB 以内

> ⚠️ 如果团队已有 React 技术栈，直接用 Taro + React，结论不变。

---

## 三、核心页面清单

### TabBar 页面（底部导航，4个）

#### 1. 首页（/pages/index/index）
```
核心功能：
- Banner 轮播（活动入口）
- 快捷入口：积分商城 / 智能体商城 / 会员中心 / 分销中心
- 热门商品列表（积分商品 + 智能体商品）
- 弹窗：新人引导 / 活动通知
- 底部：升级进度条（距下一等级还差X积分）
```

#### 2. 积分商城（/pages/mall/mall）
```
核心功能：
- 分类 Tab：全部 / 实物商品 / 虚拟商品 / Token包
- 商品列表（瀑布流 or 列表）
- 搜索框（商品名称 / SKU）
- 筛选：价格区间、销量排序
- 点击商品→商品详情
```

#### 3. 我的下线/社交（/pages/network/network）
```
核心功能：
- 头像墙：展示直接下线（头像+昵称+等级）
- 业绩概览卡片：本月新增下线数 / 本月佣金 / 下线总数
- 分销海报生成（点击生成专属邀请海报）
- 二维码展示（供他人扫码绑定）
- 佣金明细（本月 / 上月 / 累计）
```

#### 4. 个人中心（/pages/user/user）
```
核心功能：
- 会员信息卡片：头像 / 昵称 / 会员等级 / 积分余额
- 积分充值入口（跳转微信支付）
- 我的订单（全部/待支付/待发货/已完成/已退款）
- 我的佣金（可提现余额 / 佣金明细）
- 升级进度（当前等级 → 下一等级，进度条+所需积分）
- 收货地址管理
- 客服中心
- 设置（清除缓存 / 退出登录）
```

### 非TabBar 页面（功能页面）

#### 5. 商品详情（/pages/goods/detail）
```
核心功能：
- 商品轮播图（支持分享海报）
- 商品名称、价格、库存
- 规格选择（弹层）
- 积分+现金混合支付说明
- 商品详情图文
- 购买按钮：立即购买 / 加入购物车
- 底部：客服 / 收藏 / 分享（生成带参数的分享卡片）
```

#### 6. 会员注册（/pages/auth/register）
```
核心功能：
- 微信一键授权登录（获取手机号/昵称/头像）
- 补充信息表单：姓名、推荐人（扫码自动填入）
- 会员等级选择（OPC/工会/社区/城市）
- 隐私协议勾选
- 提交后跳转首页
```

#### 7. 扫码入口页（/pages/auth/scan-landing）
```
核心功能：
- 检测 URL 参数中的推荐人 code
- 写入本地 Storage（推荐人ID + 扫码时间戳）
- 跳转注册页或直接绑定（已注册用户）
- 有效期校验（建议72小时）
```

#### 8. 智能体商城（/pages/agent/agent-mall）
```
核心功能：
- 智能体分类：写作助手 / 图像生成 / 代码助手 / 定制智能体
- 智能体卡片展示：图标 / 名称 / 功能简介 / 价格
- 详情页：功能演示 / 使用说明 / 价格套餐
- Token 包购买（固定面额：100/500/1000/5000 Tokens）
- 立即购买→微信支付
```

#### 9. 邀请海报生成（/pages/invite/poster）
```
核心功能：
- 选择模板（多个风格）
- 预览海报（含用户头像+昵称+二维码）
- 保存到相册 / 分享给朋友
- 二维码内含参数：推荐人ID + 时间戳 + 场景值
```

#### 10. 订单确认（/pages/order/confirm）
```
核心功能：
- 收货地址选择/新建
- 商品信息确认
- 积分抵扣说明
- 支付方式：积分全额 / 积分+微信支付
- 订单备注
- 提交订单→微信支付
```

#### 11. 佣金明细（/pages/commission/detail）
```
核心功能：
- 时间筛选：近7天 / 近30天 / 自定义
- 佣金流水列表：来源下线+订单+金额+时间
- 佣金统计：已结算 / 待结算 / 已提现
- 提现申请按钮
```

#### 12. 积分充值（/pages/points/recharge）
```
核心功能：
- 充值档位选择：100/500/1000/5000/自定义
- 微信支付调用
- 充值到账通知
- 充值记录查询
```

---

## 四、与 MedusaJS 后端对接 API 清单

### 认证模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/wx/miniapp` | 微信小程序登录，获取 JWT token |
| POST | `/auth/wx/phone` | 微信手机号解密，获取用户手机 |
| GET | `/auth/profile` | 获取当前用户资料 |
| PUT | `/auth/profile` | 更新用户资料（昵称、头像） |

### 会员体系

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/members/register` | 注册新会员（含推荐人ID） |
| GET | `/members/me` | 获取我的会员信息（含等级/积分） |
| GET | `/members/levels` | 获取会员等级配置 |
| PUT | `/members/level-up` | 申请等级升级 |
| GET | `/members/upgrade-progress` | 升级进度查询 |

### 分销网络

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/distribution/tree` | 获取我的下线树（4级） |
| GET | `/distribution/directs` | 获取直接下线列表（分页） |
| GET | `/distribution/invite-code` | 获取我的邀请码 |
| POST | `/distribution/bind` | 手动绑定推荐关系（扫码场景用） |
| GET | `/distribution/qr-config` | 获取二维码生成配置（带参数URL） |

### 商品模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/products` | 商品列表（支持分类/搜索/分页） |
| GET | `/products/:id` | 商品详情 |
| GET | `/products/:id/stock` | 实时库存查询 |
| GET | `/categories` | 商品分类列表 |
| GET | `/agents` | 智能体商品列表 |
| GET | `/agents/:id` | 智能体详情 |

### 订单模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/orders` | 创建订单 |
| GET | `/orders` | 我的订单列表（状态筛选） |
| GET | `/orders/:id` | 订单详情 |
| PUT | `/orders/:id/cancel` | 取消订单 |
| POST | `/orders/:id/confirm-receive` | 确认收货 |
| GET | `/orders/:id/tracking` | 物流跟踪（实物商品） |

### 积分模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/points/balance` | 查询积分余额 |
| GET | `/points/history` | 积分变动明细 |
| POST | `/points/recharge` | 创建积分充值订单（微信支付） |
| POST | `/points/recharge/callback` | 微信支付回调（通知地址） |

### 佣金模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/commissions/balance` | 可提现佣金余额 |
| GET | `/commissions/history` | 佣金流水明细 |
| POST | `/commissions/withdraw` | 申请佣金提现 |
| GET | `/commissions/withdraw/records` | 提现记录 |
| GET | `/commissions/settlements` | 结算记录 |

### 微信支付（微信开放能力）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/payments/precreate` | 预创建支付（积分充值/商品购买） |
| POST | `/payments/notify` | 微信支付回调通知 |
| GET | `/payments/status/:orderId` | 支付状态查询 |

---

## 五、微信开放能力清单

### 1. 微信支付（积分充值）
```
能力：wx.requestPayment
场景：
  - 积分充值（Points Recharge）
  - 商品订单支付（混合支付：积分+微信支付）
  - 佣金提现（用户发起，企业付款到零钱）
配置：
  - 申请微信支付商户号（Native / JSAPI）
  - 小程序需开通 "支付" 能力，并关联商户号
  - 后端调用统一下单 API，签名返回在小程序调起支付
```

### 2. 微信用户授权登录
```
能力：wx.login + wx.getUserProfile
场景：
  - 首次访问自动静默登录，获取 code
  - 注册时解密昵称头像，或使用 button open-type="getPhoneNumber"
  - 静默登录后换取 openid + session_key，绑定本地会员账号
注意：
  - 2023年5月起，昵称头像需要用户主动点击按钮授权
  - 手机号强烈建议获取（会员核心数据）
```

### 3. 二维码生成（邀请海报）
```
能力：wx.scanCode + 后端 QRCode API
方案：
  - 后端生成含参二维码（场景值=推荐人ID，时间戳，scene）
  - 微信后台配置：小程序页面路径 + query 参数
  - 用户扫码 → 微信打开小程序 → onLoad(options) 读取参数
  - 参数写入本地缓存（推荐人ID，扫码时间）
  - 注册时从缓存读取并自动填入推荐人字段
```

### 其他必要能力

| 能力 | API | 用途 |
|------|-----|------|
| 分享 | Page.onShareAppMessage | 分享商品/海报给好友 |
| 地理位置 | wx.getLocation | 城市会员定位（可选） |
| 收藏 | wx.openCustomerServiceChat | 客服 |
| 订阅消息 | wx.requestSubscribeMessage | 订单状态/佣金到账通知 |
| 保存相册 | wx.saveImageToPhotosAlbum | 海报保存 |
| 剪切板 | wx.setClipboardData | 复制邀请链接 |

---

## 六、核心业务逻辑：扫码即绑定上下级关系

这是整个业务模型的地基，必须做到万无一失。

### 整体流程图

```
[A用户：推荐人]
       │
       │ 生成带参二维码
       │ 包含：inviterId + timestamp + source
       ▼
[微信后台] → 生成小程序码（scene=inviterId）
       │
       │ 用户B扫码
       ▼
[微信] → 打开小程序（指定页面 + query参数）
       │
       │ onLoad(options) → { inviterId: 'xxx', ts: 'xxx' }
       ▼
[小程序本地] → 写入 Storage：{ inviterId, scanTime, bound: false }
       │
       ├─ 如果用户已登录 → 直接调用 /distribution/bind 绑定
       │
       └─ 如果用户未登录 → 跳转注册页，自动带入推荐人ID
              │
              │ 注册成功后
              ▼
       [后端] → 查询 inviterId 是否有效
              │
              ├─ 有效 → 创建 member 并建立 parent_id 关系
              │        触发：成长值+给推荐人、佣金初始化
              │
              └─ 无效/已过期 → 提示"邀请码已失效"，不建立关系
```

### 技术实现细节

#### Step 1：后端生成带参小程序码

```javascript
// MedusaJS 后端（Node.js）
const wxMiniapp = require('wx-miniapp-sdk'); // 或使用 weixin-api

async function generateInviteQRCode(inviterId) {
  const scene = Buffer.from(JSON.stringify({
    i: inviterId,    // inviterId（推荐人ID）
    t: Date.now(),   // timestamp（时间戳，用于判断是否过期）
    s: 'poster'      // source（来源：海报/分享/扫码）
  })).toString('base64');

  const result = await wxMiniapp.createQRCode({
    scene,           // 最大32个可见字符
    page: 'pages/auth/scan-landing/index',  // 扫码落页
    width: 430,
    expire_hours: 72 // 二维码有效期
  });

  return result.image_url; // 返回二维码图片URL
}
```

#### Step 2：扫码落地页处理逻辑

```javascript
// 小程序：pages/auth/scan-landing/index.js
Page({
  data: { inviterId: '', expired: false },

  onLoad(query) {
    // 微信打开时自动带上参数
    const { i, t, s } = query;

    // 校验时间戳（72小时过期）
    const SCAN_EXPIRE_MS = 72 * 60 * 60 * 1000;
    const isExpired = Date.now() - Number(t) > SCAN_EXPIRE_MS;

    if (isExpired) {
      this.setData({ expired: true });
      return;
    }

    // 存储推荐人关系（持久化）
    wx.setStorageSync('pending_inviter', {
      inviterId: i,
      source: s,
      scanTime: Number(t)
    });

    // 判断用户登录状态
    const token = wx.getStorageSync('token');
    if (token) {
      // 已登录 → 直接绑定
      this.bindInviter(i);
    } else {
      // 未登录 → 跳转注册页
      wx.redirectTo({ url: `/pages/auth/register?inviterId=${i}` });
    }
  },

  async bindInviter(inviterId) {
    try {
      const res = await Taro.request({
        url: `${API_BASE}/distribution/bind`,
        method: 'POST',
        data: { inviterId }
      });
      if (res.code === 0) {
        wx.setStorageSync('pending_inviter', null); // 清除待绑定状态
        Taro.showToast({ title: '绑定成功' });
      }
    } catch (e) {
      console.error('绑定失败', e);
    }
  }
});
```

#### Step 3：注册时关联推荐人

```javascript
// 注册页：pages/auth/register/index.js
Page({
  data: { inviterId: '' },

  onLoad(query) {
    // 从URL参数获取（扫码跳转过来）
    if (query.inviterId) {
      this.setData({ inviterId: query.inviterId });
    } else {
      // 或从本地缓存读取（从落地页已存）
      const pending = wx.getStorageSync('pending_inviter');
      if (pending && !pending.expired) {
        this.setData({ inviterId: pending.inviterId });
      }
    }
  },

  async onRegister(formData) {
    // 表单数据 + inviterId 一起提交
    await Taro.request({
      url: `${API_BASE}/members/register`,
      method: 'POST',
      data: {
        ...formData,
        inviterId: this.data.inviterId || null, // 关键：可为空，但不能漏
        registerSource: 'miniapp'
      }
    });

    // 注册成功 → 触发绑定逻辑（同 Step 2）
    // → 清除 pending_inviter
  }
});
```

#### Step 4：后端绑定逻辑（MedusaJS）

```javascript
// MedusaJS: src/api/routes/distribution/bind.ts
registerationWorkflow.register({
  do: async ({ context, services }) => {
    const { inviterId, memberId } = context;

    // 查询推荐人是否存在
    const inviter = await services.memberService.retrieve(inviterId);
    if (!inviter) throw new Error('邀请人不存在');

    // 绑定上下级关系
    await services.memberService.update(memberId, {
      parent_id: inviterId,
      invited_at: new Date()
    });

    // 给推荐人加积分（邀请奖励）
    await services.pointsService.add(inviterId, {
      amount: INVITE_REWARD_POINTS,
      reason: `邀请新会员 ${memberId}`,
      type: 'invite_reward'
    });

    // 初始化佣金账户
    await services.commissionService.initAccount(memberId);
  }
});
```

#### Step 5：4级下线关系查询

```javascript
// 查询我所有4级下线
async function getMyDownlineTree(memberId) {
  const tree = await services.distributionService.getDownlineTree(memberId, {
    depth: 4, // OPC需求：4级分销
    includeStats: true  // 包含订单数/佣金/下线数
  });
  return tree;
}

// 返回结构示例
{
  memberId: 'A',
  level: 1,       // 直接下线
  children: [
    {
      memberId: 'B',
      level: 2,
      children: [
        { memberId: 'C', level: 3, children: [...] },
        { memberId: 'D', level: 3, children: [...] }
      ]
    }
  ]
}
```

### 绑定关系防刷机制

```
1. 时效限制：二维码72小时内有效，超时提示"邀请码已过期"
2. 单向绑定：绑定后不可变更（防止套佣）
3. 等级保护：城市等级才能发展下线（低等级会员扫码不绑定）
4. 自绑禁止：自己扫自己的码不绑定
5. 频率限制：同一推荐人每天最多绑定100个新下线（防刷）
6. IP/设备频控：同一IP/设备24小时内注册超过5个，触发风控
```

---

## 七、分包加载策略（包体积优化）

小程序主包限制 2MB，推荐采用**主包+业务分包**结构：

```
主包（~1.2MB）：
  - pages/index/index       首页
  - pages/auth/*            认证相关（登录/注册/扫码落地）
  - pages/user/user         个人中心
  - components/*            公共组件
  - utils/*                 工具函数
  - assets/*                全局资源

业务分包A：积分商城（~600KB）
  - pages/mall/mall
  - pages/goods/detail
  - pages/order/confirm
  - pages/points/recharge

业务分包B：分销裂变（~500KB）
  - pages/network/network
  - pages/invite/poster
  - pages/commission/detail

业务分包C：智能体商城（~500KB）
  - pages/agent/agent-mall
  - pages/agent/agent-detail
```

---

## 八、会员4级体系与分销佣金设计

### 会员等级

| 等级 | 名称 | 注册门槛 | 晋升条件 | 分销权限 |
|------|------|---------|---------|---------|
| L1 | OPC | 扫码注册 | 默认 | 无分销权（仅自购） |
| L2 | 工会 | 自购满500积分 | 团队满10人 | 1级下线佣金 |
| L3 | 社区 | 自购满2000+团队50人 | 累计佣金达1000 | 3级下线佣金 |
| L4 | 城市 | 社区满1年+团队500人 | 累计佣金达20000 | 4级下线佣金 |

### 佣金比例（示例）

| 下线等级 | L2→L3晋升中 | L4（城市）佣金比例 |
|---------|-----------|-----------------|
| 直接下线（L1） | 5% | 10% |
| 二级下线 | - | 5% |
| 三级下线 | - | 3% |
| 四级下线 | - | 1% |

> 具体比例由运营后台配置，API 可动态获取

---

## 九、项目目录结构（推荐）

```
opc-mall/
├── src/
│   ├── app.vue
│   ├── main.ts
│   ├── app.config.ts          # 全局配置（tabBar/页面路径/窗口）
│   │
│   ├── pages/                 # 页面
│   │   ├── index/             # 首页
│   │   ├── mall/              # 积分商城
│   │   ├── network/           # 我的下线
│   │   ├── user/              # 个人中心
│   │   ├── goods/             # 商品
│   │   ├── auth/              # 认证（登录/注册/扫码落地）
│   │   ├── order/             # 订单
│   │   ├── points/            # 积分
│   │   ├── commission/        # 佣金
│   │   ├── invite/            # 邀请海报
│   │   └── agent/             # 智能体商城
│   │
│   ├── components/            # 公共组件
│   │   ├── goods-card/
│   │   ├── commission-card/
│   │   ├── member-level/
│   │   └── poster-canvas/    # 海报canvas组件
│   │
│   ├── services/              # API 服务层
│   │   ├── auth.ts
│   │   ├── member.ts
│   │   ├── product.ts
│   │   ├── order.ts
│   │   ├── points.ts
│   │   ├── commission.ts
│   │   └── distribution.ts
│   │
│   ├── stores/                # 状态管理（Pinia）
│   │   ├── user.ts
│   │   ├── cart.ts
│   │   └── points.ts
│   │
│   ├── utils/                 # 工具函数
│   │   ├── request.ts         # axios / Taro.request 封装
│   │   ├── storage.ts
│   │   ├── wx-api.ts           # 微信 API 封装
│   │   └── commission.ts       # 佣金计算公式
│   │
│   └── config/
│       └── env.ts              # 环境变量（API_BASE等）
│
├── config/
│   └── index.html             # Web端入口（兼容用）
│
├── package.json
├── taro.config.ts
└── medusa/                    # 后端（MedusaJS）扩展
    └── src/
        ├── services/
        │   ├── member.ts      # 会员服务
        │   ├── distribution.ts # 分销服务
        │   ├── commission.ts  # 佣金服务
        │   └── points.ts      # 积分服务
        └── api/routes/         # 自定义API路由
```

---

## 十、开发里程碑建议

```
Phase 1（MVP，4-6周）：
  - 微信登录 + 会员注册（含扫码绑定）
  - 积分商城（商品展示 + 购买）
  - 个人中心（积分余额 + 基本信息）
  - 微信支付集成（积分充值）

Phase 2（增长，2-3周）：
  - 分销网络（下线列表 + 佣金查看）
  - 邀请海报生成
  - 4级佣金体系

Phase 3（完善，2-3周）：
  - 智能体商城
  - 会员升级体系
  - 订单管理全流程
  - 订阅消息通知

Phase 4（运营支撑，长期）：
  - 运营后台完善
  - 数据看板
  - 风控系统
```

---

> **🦀 核心结论**：技术选型 Taro+Vue3+TypeScript；业务核心是**扫码绑定上下级关系**，通过带参小程序码+本地Storage+注册时关联实现，全流程闭环在3步内完成，用户无感知。
