# Mercur (MedusaJS) 多商户商城 — 后端架构研究报告

> 研究对象：https://github.com/mercurjs/mercur  
> 研究日期：2026-03-27  
> 适用场景：OPC-Mall 多商户商城后端选型

---

## 一、核心架构分析

### 1.1 技术栈

| 层次 | 技术选型 |
|------|---------|
| 运行时 | Node.js 20+ |
| 语言 | TypeScript（全链路） |
| 核心框架 | **MedusaJS v2**（非 v1） |
| 数据库 | PostgreSQL |
| ORM | **MikroORM**（Medusa v2 内置，**非 Prisma**） |
| 前端面板 | React 18 + Vite + React Router |
| 数据获取 | TanStack React Query |
| UI 组件 | Medusa UI + Radix UI |
| 表单/校验 | React Hook Form + Zod |
| 构建工具 | Turborepo（monorepo）+ Bun（包管理器）+ tsup |
| 国际化 | i18next |
| 支付 | Stripe Connect（内置） |
| 通知 | Resend（内置） |

> ⚠️ **关键区分**：Mercur 基于 **MedusaJS v2**（2024 年重构），而非 v1。**ORM 是 MikroORM，不是 Prisma**。v2 与 v1 在插件模型、模块架构上有根本性差异。

### 1.2 目录结构（Monorepo）

```
mercur/
├── packages/
│   ├── core-plugin/      # 🏠 核心插件（所有商城逻辑所在）
│   │   └── src/
│   │       ├── modules/        # Seller、Commission、Payout、CustomFields
│   │       ├── links/         # 17 个跨模块关联定义
│   │       ├── workflows/     # 完整订单分单/佣金/支付工作流
│   │       ├── api/            # HTTP 路由（admin/vendor/store 三套）
│   │       ├── subscribers/    # 事件订阅器
│   │       ├── providers/     # 第三方集成（Stripe Connect 等）
│   │       └── jobs/           # 定时任务
│   ├── cli/               # @mercurjs/cli 脚手架工具
│   ├── client/            # @mercurjs/client 类型安全 API 客户端
│   ├── admin/             # Admin Panel（React）
│   ├── vendor/            # Vendor Portal（React）
│   ├── dashboard-sdk/     # Vite 插件（路由生成 + HMR）
│   └── dashboard-shared/ # Admin/Vendor 共享 UI 组件
└── apps/docs/            # Mintlify 文档站
```

### 1.3 分层架构

```
┌─────────────────────────────────────────┐
│  Frontend: Admin / Vendor / Store (React)│
├─────────────────────────────────────────┤
│  API Layer: /admin/* | /vendor/* | /store/*│
├─────────────────────────────────────────┤
│  Marketplace Layer (Mercur)              │
│   Modules: Seller | Commission | Payout  │
│   Workflows: 订单分单·佣金计算·支付切分    │
│   Links: 17 个跨模块关联                  │
├─────────────────────────────────────────┤
│  Commerce Layer (Medusa v2)              │
│   Products · Carts · Orders · Payments  │
│   Fulfillment · Promotions · Inventory   │
├─────────────────────────────────────────┤
│  PostgreSQL + Redis                       │
└─────────────────────────────────────────┘
```

---

## 二、会员/等级体系支持程度

### 2.1 现状评估

| 需求 | Mercur 原生支持 | 说明 |
|------|----------------|------|
| 基础会员 | ✅ 可扩展 | Custom Fields 可给 Customer 加 `tier` 字段 |
| 会员等级 | ⚠️ 需二次开发 | 自定义枚举字段可记录 bronze/silver/gold，需业务逻辑 |
| 会员价格等级 | ❌ 不存在 | Price List 支持按 Customer Group 定价，不按会员等级 |
| 积分系统 | ❌ 不存在 | 需要全新模块 |
| 钱包余额 | ❌ 不存在 | 需要全新模块 |
| 分销/推荐体系 | ❌ 不存在 | 需要全新模块 |

### 2.2 Custom Fields 模块（已有）

Mercur 提供 Custom Fields 模块，可通过配置扩展 Medusa Customer 实体：

```ts
// medusa-config.ts
{
  resolve: "@mercurjs/core-plugin/modules/custom-fields",
  options: {
    customFields: {
      Customer: {
        tier: { type: "enum", enum: ["bronze","silver","gold"], defaultValue: "bronze" },
        referral_code: { type: "string" },
        referrer_id: { type: "string" },
        points_balance: { type: "integer", defaultValue: 0 },
      }
    }
  }
}
```

这说明扩展会员字段无需修改核心代码，但**积分计算、等级变动逻辑需要自建**。

### 2.3 Price List（价格等级基础）

Medusa v2 原生支持 `PriceList`，可以：
- 按 Customer Group 设定不同价格
- 按 Region 设定不同价格
- 用 `min_quantity` 设定阶梯价

可与 Custom Fields 配合，实现「会员等级 → Customer Group → Price List」的联动。

---

## 三、插件扩展机制 & 分销模块叠加方案

### 3.1 Block-Based 架构（Mercur 特色）

Mercur 采用类 shadcn/ui 的 **Block 分发模式**：

```
代码直接复制到项目 → 完全代码所有权 → 无黑盒依赖
```

CLI 命令：`mercurjs add <block-name>` → 从 Registry 拉取源码写入本地。

核心 Block 类型：
- **Modules** — 数据模型 + 服务（可装入新的自定义模块）
- **Links** — 实体间关联
- **Workflows** — 多步骤业务流程
- **API Routes** — HTTP 端点
- **Admin/Vendor Extensions** — 管理面板 UI 扩展

### 3.2 自定义分销模块叠加方案

分销模块（Referral/Distribution）是**必须自建**的核心模块，推荐以下叠加路径：

```
Step 1: Custom Fields 建立 Referrer 关系
  Customer.referrer_id + referral_code

Step 2: 新建 Referral Module（Block 方式）
  modules/referral/
  ├── models/              # ReferralLink, ReferralReward
  ├── services/            # ReferralService
  ├── workflows/           # rewardOnOrderWorkflow
  └── api/                 # /store/referrals/*, /admin/referrals/*

Step 3: Subscriber 监听 order.placed 事件
  → 检测订单 Customer.referrer_id
  → 计算佣金/积分奖励
  → 写入钱包或积分表

Step 4: Links 关联 ReferralLink → Order/Customer
```

**分销佣金计算方式**有两种主流：
- **首单奖励**：Customer 首次下单时触发
- **多级分销**：A 推荐 B，B 推荐 C，按层级支付（需要 OrderGroup 追溯）

### 3.3 Workflow Hook 扩展点

Mercur 的 `completeCartWithSplitOrdersWorkflow` 暴露了以下钩子：

| 钩子 | 时机 | 用途 |
|------|------|------|
| `validate` | 订单完成前校验 | 分销资格校验 |
| `beforePaymentAuthorization` | 支付前 | 积分抵扣/钱包扣款 |
| `orderGroupCreated` | 订单组创建后 | 计算分销奖励 |

---

## 四、数据库 ORM & 积分/钱包系统实现

### 4.1 ORM 选择

**Medusa v2 使用 MikroORM**，不是 Prisma。

```
Medusa v1  → TypeORM
Medusa v2  → MikroORM（性能更好，TypeScript-first）
Mercur     → MikroORM（继承自 Medusa v2）
```

Mercur 的 Model 定义示例（参考 core-plugin/modules）：

```ts
// MikroORM entity
@Model()
export class Seller {
  @Id() id: string;
  @NameColumn() name: string;
  @EnumColumn({ enum: SellerStatus }) status: SellerStatus;
  @ManyToMany(() => Customer) customers = new Collection<Customer>(this);
}
```

> ⚠️ 如果团队熟悉 Prisma，迁移到 MikroORM 需要学习曲线。MikroORM 的 QueryBuilder 风格与 Prisma 差异较大。

### 4.2 积分/钱包系统实现建议

**原生不支持，需要全新模块**，推荐实现方案：

```ts
// modules/loyalty/models/Wallet.ts（ MikroORM）
@Entity()
export class Wallet {
  @PrimaryKey() id: string;
  @Property() customer_id: string;
  @Property() balance: number = 0;           // 可正可负
  @Property() points_balance: number = 0;    // 积分（独立）
  @EnumColumn({ enum: CurrencyCode }) currency: CurrencyCode;
}

// models/WalletTransaction.ts
@Entity()
export class WalletTransaction {
  @Id() id: string;
  @Property() wallet_id: string;
  @EnumColumn({ enum: TransactionType }) type: 'earn'|'redeem'|'refund'|'distribution';
  @Property() amount: number;
  @Property() order_id?: string;
  @Property() description: string;
  @DateColumn() created_at: Date;
}

// 推荐积分计算规则（非负整数）
// 1 元 = 1 积分（可配置）
// 积分抵现：100 积分 = 1 元（可配置）
```

**Workflow 设计**：
```
order.placed 事件触发
  → checkReferral(customer_id)
  → calculateReward(referral_tier, order_total)
  → walletService.credit(referrer_wallet_id, amount)
  → walletTransactionService.create({ type: 'distribution', ... })
```

**存储选型**：
- 钱包余额表：需要事务保护（防止并发扣款）
- 积分表：需要 BigNumber 精度
- 流水表：只增不减，支持对账

---

## 五、REST API 结构 & 微信小程序对接

### 5.1 API 分层

| API | 路径前缀 | 消费者 | 说明 |
|-----|---------|--------|------|
| Admin | `/admin/*` | 平台运营方 | 商户审核、佣金配置、订单监控 |
| Vendor | `/vendor/*` | 入驻商家 | 商品管理、订单履约、货款查看 |
| Store | `/store/*` | 消费者 | 商品浏览、加购、下单 |

### 5.2 Store API 核心端点

```
POST   /store/carts                        # 创建购物车
POST   /store/carts/:id/line-items         # 添加商品（多商户商品）
POST   /store/carts/:id/complete           # 触发分单工作流（核心）
GET    /store/orders/:id                   # 查询订单（含分单信息）
POST   /store/customers                    # 注册会员
GET    /store/customers/me                # 当前会员信息
POST   /store/auth/emailpass               # 邮箱密码登录
POST   /store/payment-collections/:id/maybeTransact  # 支付
```

**关键**：订单分单逻辑在后端 `completeCartWithSplitOrdersWorkflow` 自动完成，前端/小程序只需调用 `/store/carts/:id/complete`。

### 5.3 微信小程序对接方案

微信小程序**无法直接调用微信支付 v2/v3**，需通过商户后端中转：

```
┌────────────┐     ┌─────────────────┐     ┌──────────────┐
│  小程序前端  │────▶│  Mercur 后端    │────▶│  微信支付    │
│  (HTTPS)   │     │  (Admin/Store)  │     │  API         │
└────────────┘     └─────────────────┘     └──────────────┘
```

**对接步骤**：

1. **静默登录**：小程序 `wx.login()` → 后端兑换 `code` → 建立 Session/JWT
2. **创建会员**：`POST /store/customers`（Mercur 原生支持）
3. **获取商品**：`GET /store/products`（原生支持）
4. **创建购物车**：`POST /store/carts`（原生支持）
5. **订单分单**：`POST /store/carts/:id/complete`（原生支持，**多商户自动分单**）
6. **发起支付**：
   - Mercur 后端需新增 `POST /store/payments/wechat` 端点
   - 调用微信支付 `v3/transactions/jsapi` 预下单
   - 返回 `paymentConfig` 给小程序
   - 小程序调 `wx.requestPayment()`
7. **支付回调**：微信支付后回调 → 更新订单状态

**关键挑战**：
- 微信登录需要自定义实现（Mercur 原生是 Email/Password 或 OAuth Google）
- 微信支付需要商户号（需企业资质）
- 分销模块需新建 API（`GET /store/referrals/stats`）
- JWT Token 需要支持微信 OpenID 作为标识

---

## 六、适合本项目的理由

### ✅ 强烈推荐（适合）的理由

1. **多商户分单逻辑开箱即用**：`completeCartWithSplitOrdersWorkflow` 自动处理「一单多商户 → 拆分为多个 Seller Order → 分别履约」的完整链路，这是最难开发的部分，Mercur 已实现。
2. **佣金体系完善**：Rule-Based Commission，支持按商品类目/商户/配送方式配置佣金规则，优先级匹配，CommissionLine 审计追踪。
3. **Stripe Connect 集成**：Mercur 已实现与 Stripe Connect 对接，Payout 模块已内置；对于国内场景可参考该模式对接微信支付分账。
4. **Block 架构**：代码复制到项目，本地完全可控；分销模块可作为新 Block 开发，不污染核心。
5. **活跃社区**：Discord + GitHub，v2 正在积极迭代。

### ⚠️ 需要注意的风险

1. **积分/钱包/分销**：三者均需**从零开发**，Mercur 只提供扩展骨架
2. **微信小程序对接**：需要额外处理微信登录和微信支付，接入工作量不小
3. **团队 MikroORM 经验**：如果团队熟悉 Prisma，MikroORM 有学习成本
4. **成熟度**：Mercur 1.0 于 2024 年底发布，属于较新项目，企业级稳定性待验证
5. **国内生态**：Stripe Connect 替代品（如微信分账、连连支付）需要自建对接

---

## 七、需要二次开发的核心模块清单

| # | 模块名称 | 优先级 | 工作量估计 | 说明 |
|---|---------|--------|----------|------|
| 1 | **会员体系模块** | P0 | 中 | Custom Fields 扩展 + 等级业务逻辑 |
| 2 | **积分系统模块** | P0 | 中 | 积分获取/兑换/过期规则、Wallet/Transaction 表 |
| 3 | **钱包系统模块** | P0 | 中 | 余额充值/扣款/提现、事务保护 |
| 4 | **分销/推荐模块** | P1 | 中高 | ReferralLink、奖励计算、多级分销 |
| 5 | **微信登录对接** | P1 | 中 | 小程序 code 登录、OpenID → Customer 映射 |
| 6 | **微信支付对接** | P1 | 中高 | JSAPI 预下单 + 支付回调 + 分账（微信支付 V3） |
| 7 | **会员价格等级** | P2 | 中 | PriceList + Customer Group 联动 |
| 8 | **CRM 导出/数据看板** | P2 | 低 | Admin API 扩展 + 报表 |
| 9 | **物流轨迹对接** | P2 | 中 | 订阅微信/顺丰/中通事件推送 |
| 10 | **短信/推送通知** | P2 | 低 | 国内短信通道（阿里云/腾讯云）替换 Resend |

---

## 八、MedusaJS 版本建议：v2（必须）

| | Medusa v1 | Medusa v2（Mercur） |
|--|----------|-------------------|
| 架构 | 单体插件 | 模块化（Modules/Workflows/Links） |
| ORM | TypeORM | MikroORM |
| API | REST（混在一起） | REST + Admin API + Store API 分离 |
| 扩展方式 | 补丁/覆盖 | Links + Workflows Hooks（原生扩展） |
| 插件生态 | 较丰富 | v2 生态建设中（但更先进） |
| 活跃度 | 维护中（不演进） | 活跃开发 |

> **结论**：Mercur 仅支持 v2。v2 的模块化架构对分销/积分二次开发更友好（Links 关联无需 Fork 核心代码）。不要选择 v1。

---

## 九、总结建议

```
🦀 推荐程度：⭐⭐⭐⭐（4/5）
最适合：已有 TypeScript/Node.js 团队，想快速搭建多商户 + 多商户分单 + 佣金体系的商城
最大优势：订单分单 + 佣金计算开箱即用，Block 架构保证代码所有权
最大风险：积分/钱包/分销需要从零开发，微信小程序对接需额外工作量
```

**第一步建议**：用 Mercur CLI 快速搭出本地 Demo（30 分钟），跑通多商户下单分单流程，再评估二次开发工作量。
