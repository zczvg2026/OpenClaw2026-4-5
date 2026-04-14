# OPC Mall 数据库 Schema 设计

> 版本：v1.0  
> 日期：2026-03-27  
> 技术栈：MedusaJS (PostgreSQL) + Prisma

---

## 一、ER 图（文字版）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MedusaJS 核心表（复用）                          │
│                                                                         │
│  ┌──────────┐    1:N    ┌──────────┐    N:1    ┌──────────────┐          │
│  │  Store   │──────────│  Product │──────────│ ProductType  │          │
│  └──────────┘          └──────────┘           └──────────────┘          │
│                              │ N:1                                   │
│                              │ has_many variants                     │
│                         ┌────┴──────────┐                           │
│                         │ ProductVariant│                           │
│                         └───────────────┘                           │
│                                                                         │
│  ┌──────────┐    1:N    ┌──────────┐    N:1    ┌──────────┐           │
│  │  Order   │──────────│LineItem  │──────────│  Product │           │
│  └──────────┘          └──────────┘           └──────────┘           │
│       │                                                     │
│       │ 1:1 (扩展)                                          │
│       ▼                                                     │
│  ┌──────────┐                                               │
│  │OrderPoint │◄── 积分消费订单                               │
│  └──────────┘                                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         OPC 扩展业务表                                   │
│                                                                         │
│  ┌──────────────────┐                                                  │
│  │  MemberLevel      │  会员等级配置表（等级名称/积分价格倍率）            │
│  └────────┬─────────┘                                                  │
│           │ 1:N                                                       │
│           ▼                                                           │
│  ┌──────────────────┐        ┌──────────────────┐                     │
│  │   Member          │◄──N:1──│  DistributionNode│  分销关系表          │
│  │  (扩展MedusaJS    │        │  (扫描绑定,终身)  │                     │
│  │   Customer)       │        └────────┬─────────┘                     │
│  └────────┬─────────┘                 │ N:1 (parent)                   │
│           │                           │ recursive 3层（中国合规）         │
│           │ 1:1                       │                                │
│           ▼                           ▼                                │
│  ┌──────────────────┐        ┌──────────────────┐                     │
│  │  PointAccount     │        │ DistributionPath │  分销链路快照表        │
│  │  积分账户表        │        │  (预计算+索引优化) │                     │
│  └────────┬─────────┘        └──────────────────┘                     │
│           │                                                           │
│           │ 1:N                                                       │
│           ▼                                                           │
│  ┌──────────────────┐                                                  │
│  │  PointLedger     │  积分流水表（充值/消费/退款/奖励）                  │
│  └──────────────────┘                                                  │
│                                                                         │
│  ┌──────────────────┐        ┌──────────────────┐                     │
│  │ ProductLevelPrice│◄──N:1──│   ProductVariant │  商品等级价格表        │
│  │  (等级定价)       │        └──────────────────┘                     │
│  └──────────────────┘                                                  │
│                                                                         │
│  ┌──────────────────┐        ┌──────────────────┐                     │
│  │  LevelAdvancement│◄──N:1──│     Member       │  等级晋升记录表        │
│  └──────────────────┘        └──────────────────┘                     │
│                                                                         │
│  ┌──────────────────┐                                                  │
│  │  InviteCode      │  邀请码表（扫码绑定关系）                          │
│  └──────────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 二、合规设计说明（中国多级分销限制）

### 法律依据
- 《禁止传销条例》（国务院令第444号）：传销分为拉人头、交入门费、多层次计酬三种
- **关键合规点**：实际结算层级不超过 3 层（Level 1/2/3），第 4 层（城市）仅作为身份标识，不参与分润结算

### 实现策略
```
身份层级（4级）：OPC → OPC工会 → OPC社区 → OPC城市   ← 会员身份标签，无分润
      │
      ▼
分润层级（3层）：推荐人(Referrer) → 上级(Level1) → 上上级(Level2)  ← 实际佣金结算
```

- `DistributionNode.parent_id` 最多追溯 3 代（`depth ≤ 3`）
- `DistributionPath` 预计算表控制在 3 层以内
- Level 4（城市）享受团队业绩奖励，但奖励从 Level 3 联盟池统一分配

---

## 三、核心扩展表设计

### 3.1 MemberLevel（会员等级配置表）

> 存储4个等级的名称、积分价格倍率、晋升条件

```prisma
model MemberLevel {
  id            String    @id @default(uuid())
  code          String    @unique  // opc | opc_union | opc_community | opc_city
  name          String                  // OPC | OPC工会 | OPC社区 | OPC城市
  nameEn        String?                 // English name
  icon          String?                  // 等级图标 URL
  pointRate     Decimal  @db.Decimal(5,4) // 积分价格倍率（相对于原价，如 0.80 = 8折）
  // OPC = 1.00, OPC工会 = 0.90, OPC社区 = 0.85, OPC城市 = 0.80
  minPurchaseAmt Decimal @default(0)    // 升级所需最低采购金额累计（元）
  minReferrals   Int      @default(0)    // 升级所需推荐人数（如 OPC→工会：需推荐5个OPC）
  requireUnion   Int      @default(0)    // 升级所需下级工会数（如 工会→社区：需2个工会）
  requireCommunity Int    @default(0)    // 升级所需下级社区数（如 社区→城市：需X个社区）
  performanceTarget Decimal @default(0) // 晋升所需业绩目标（元），如城市：300万
  performancePeriodDays Int @default(0) // 业绩周期天数，如城市：365天
  sortOrder     Int      @default(0)    // 排序
  isActive      Boolean  @default(true)

  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  members       Member[]

  @@index([code])
  @@index([sortOrder])
}

-- PostgreSQL DDL
CREATE TABLE member_levels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(100) NOT NULL,
  name_en VARCHAR(100),
  icon VARCHAR(500),
  point_rate DECIMAL(5,4) NOT NULL DEFAULT 1.0000,
  min_purchase_amt DECIMAL(18,2) NOT NULL DEFAULT 0,
  min_referrals INT NOT NULL DEFAULT 0,
  require_union INT NOT NULL DEFAULT 0,
  require_community INT NOT NULL DEFAULT 0,
  performance_target DECIMAL(18,2) NOT NULL DEFAULT 0,
  performance_period_days INT NOT NULL DEFAULT 0,
  sort_order INT NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

### 3.2 Member（会员表 - 扩展 MedusaJS Customer）

> 复用 `public.customer` 表，通过 `member_id` 与本表关联（1:1）

```prisma
model Member {
  id                    String    @id @default(uuid())
  customerId            String    @unique  // FK → public.customers.id (MedusaJS)
  levelCode             String    @default("opc")
  levelId               String?   // FK → member_levels.id
  levelId_at            DateTime? // 获得当前等级时间

  // 积分账户（一对一）
  pointAccount          PointAccount?

  // 上下级关系
  distributionNode      DistributionNode?

  // 推广信息
  inviteCode            String    @unique  // 6位唯一邀请码（用户扫码绑定）
  inviteQrCode          String?            // 推广二维码URL
  bindTime              DateTime?          // 被绑定时间（扫码时间）

  // 业绩统计（每日定时刷新或实时更新）
  totalPurchaseAmt      Decimal   @db.Decimal(18,2) @default(0) // 历史采购总额（元）
  teamPurchaseAmt       Decimal   @db.Decimal(18,2) @default(0) // 团队采购总额（元）
  directReferrals       Int       @default(0)                   // 直接推荐人数
  indirectReferrals     Int       @default(0)                   // 间接推荐人数（含下属）

  // 晋升状态
  promotionStatus       PromotionStatus @default(PENDING)
  promotionAppliedAt    DateTime?
  promotionReviewedAt    DateTime?
  promotionNote         String?

  // 会员状态
  isActive              Boolean   @default(true)
  freezeReason          String?

  createdAt             DateTime  @default(now())
  updatedAt             DateTime  @updatedAt

  // Relations
  level                  MemberLevel?  @relation(fields: [levelId], references: [id])
  advancements           LevelAdvancement[]
  orders                 OrderPoint[]

  @@index([customerId])
  @@index([levelCode])
  @@index([inviteCode])
  @@index([promotionStatus])
  @@index([createdAt])
  @@index([totalPurchaseAmt])
}

enum PromotionStatus {
  PENDING    // 待审核
  APPROVED   // 已晋升
  REJECTED   // 已拒绝
}
```

---

### 3.3 DistributionNode（分销关系表）

> **核心表**，存储用户上下级关系，扫码绑定，终身有效

```prisma
model DistributionNode {
  id              String    @id @default(uuid())
  memberId        String    @unique  // FK → members.id

  // 上级引用（合规：depth ≤ 3 时才有 parent_id）
  parentId        String?   // FK → distribution_nodes.id（直接推荐人）
  grandparentId   String?   // FK → distribution_nodes.id（两级上代）
  greatGrandparentId String? // FK → distribution_nodes.id（三级上代，禁止再往上）

  // 链路深度（0=根节点无上级, 1=一级, 2=二级, 3=三级）
  depth           Int       @default(0)

  // 完整链路（预计算字符串，如 "/uuid1/uuid2/uuid3"，便于快速查询子树）
  ancestorPath    String?   // e.g. "/root-uuid/level1-uuid/level2-uuid"
  descendantPath  String?   // e.g. "/node-uuid/child-uuid/grandchild-uuid"

  // 推广方式
  bindSource      BindSource @default(QRCODE)  // 扫码/链接/手动
  bindScene       String?                  // 扫码场景值（微信）

  // 失效标记（可选：管理员可禁用违规关系）
  isActive        Boolean  @default(true)
  deactivatedAt   DateTime?
  deactivateReason String?

  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  // Relations
  member              Member           @relation(fields: [memberId], references: [id])
  parent              DistributionNode? @relation("NodeHierarchy", fields: [parentId], references: [id])
  children            DistributionNode[] @relation("NodeHierarchy")
  distributionPaths   DistributionPath[] // 该节点作为起点的所有下级链路

  @@index([memberId])
  @@index([parentId])
  @@index([depth])
  @@index([ancestorPath])        -- 前缀查询：WHERE ancestor_path LIKE '/root-uuid/%'
  @@index([descendantPath])      -- 前缀查询：子树查询
  @@index([createdAt])
  @@index([isActive, depth])     -- 组合索引
}

enum BindSource {
  QRCODE    // 扫码绑定
  LINK      // 分享链接
  MANUAL    // 后台手动绑定
}

-- PostgreSQL: 递归CTE查询示例（获取某人所有下级）
-- WITH RECURSIVE downline AS (
--   SELECT id, member_id, depth FROM distribution_nodes WHERE id = :root_id
--   UNION ALL
--   SELECT d.id, d.member_id, d.depth FROM distribution_nodes d
--   INNER JOIN downline p ON d.parent_id = p.id AND d.depth <= 3
-- ) SELECT * FROM downline;
```

---

### 3.4 DistributionPath（分销链路快照表）

> **性能优化表**：为每个用户预计算并存储其所有上级链路（最多3层）
> 用途：快速查询"我的推荐人"、佣金计算、团队业绩统计

```prisma
model DistributionPath {
  id              String    @id @default(uuid())

  // 这条链路的所有者（即"我"）
  ownerId         String    // FK → distribution_nodes.id

  // 链路层级
  level           Int       // 1=直接推荐人, 2=二级, 3=三级

  // 链路上该级节点
  nodeId          String    // FK → distribution_nodes.id
  memberId        String    // FK → members.id（链路上该人的member_id）
  memberLevelCode String?   // 该人当前等级（反查加速）

  // 用于快速佣金计算
  commissionRate  Decimal   @db.Decimal(5,4) @default(0.0000)  // 该层级的佣金比例

  createdAt       DateTime  @default(now())

  // Relations
  owner           DistributionNode @relation(fields: [ownerId], references: [id])

  @@unique([ownerId, level])  -- 每个owner最多3条记录（level 1/2/3）
  @@index([ownerId])
  @@index([memberId])
  @@index([level])
  @@index([memberLevelCode])
}
```

**链路预计算规则**（新增下级时触发）：

```
当新用户 X 被绑定到上级 A：
1. 创建 X 的 DistributionPath：
   - level=1 → nodeId=A
   - level=2 → nodeId=A.parent (若存在)
   - level=3 → nodeId=A.grandparent (若存在)
2. 更新 A 的 directReferrals + 1
3. 递归向上更新 indirectReferrals（A的各级上级 +1）
4. 触发业绩统计更新
```

---

### 3.5 PointAccount（积分账户表）

> 每个会员有且仅有一个积分账户

```prisma
model PointAccount {
  id              String    @id @default(uuid())
  memberId        String    @unique  // FK → members.id

  balance         BigInt    @default(0)  // 积分余额（整数，1积分=1单位）
  frozenBalance   BigInt    @default(0) // 冻结积分（提现审核中等）

  // 累计统计
  totalRecharged  BigInt    @default(0) // 历史充值积分总量
  totalConsumed   BigInt    @default(0) // 历史消费积分总量
  totalWithdrawn  BigInt    @default(0) // 已提现积分总量

  // 安全
  password        String?   // 积分支付密码（bcrypt加密）
  passwordSalt    String?

  // 限额
  dailyRechargeLimit  BigInt @default(0)  // 每日充值上限（0=无限制）
  monthlyRechargeLimit BigInt @default(0) // 每月充值上限

  version         Int       @default(1)  // 乐观锁版本号

  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt

  // Relations
  member          Member         @relation(fields: [memberId], references: [id])
  transactions    PointLedger[]

  @@index([memberId])
  @@index([balance])
}

-- PostgreSQL DDL（使用 BIGINT 避免小数精度问题）
CREATE TABLE point_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id UUID UNIQUE NOT NULL REFERENCES members(id),
  balance BIGINT NOT NULL DEFAULT 0,
  frozen_balance BIGINT NOT NULL DEFAULT 0,
  total_recharged BIGINT NOT NULL DEFAULT 0,
  total_consumed BIGINT NOT NULL DEFAULT 0,
  total_withdrawn BIGINT NOT NULL DEFAULT 0,
  password_hash VARCHAR(255),
  daily_recharge_limit BIGINT NOT NULL DEFAULT 0,
  monthly_recharge_limit BIGINT NOT NULL DEFAULT 0,
  version INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

### 3.6 PointLedger（积分流水表）

> 所有积分变动必须通过本表记录（不可篡改，日志化设计）

```prisma
model PointLedger {
  id              String    @id @default(uuid())

  accountId       String    // FK → point_accounts.id
  memberId        String    // FK → members.id（冗余，加速查询）

  // 变动金额（正=增加，负=减少）
  amount          BigInt    // NOT NULL，符号区分增减

  // 变动前/后余额（审计用）
  balanceBefore   BigInt    @default(0)
  balanceAfter    BigInt    @default(0)

  // 业务类型
  bizType         PointBizType

  // 关联业务ID
  bizId           String?   // 订单ID / 充值ID / 提现ID / 奖励ID
  bizNo           String?   // 业务单号（幂等键）

  // 描述
  description     String?

  // 外部流水号（微信/支付宝）
  externalNo      String?

  // 冻结解冻专用
  frozenAmount    BigInt?   // 冻结流水时为负数，解冻时为正数

  // 过期相关
  expiredAt       DateTime? // 积分过期时间（若有时效积分）

  // 状态
  status          PointLedgerStatus @default(CONFIRMED)

  createdAt       DateTime  @default(now())
  confirmedAt     DateTime?

  // Relations
  account         PointAccount @relation(fields: [accountId], references: [id])

  @@unique([bizNo])  -- 幂等键，防止重复扣款
  @@index([accountId])
  @@index([memberId])
  @@index([bizType])
  @@index([createdAt])
  @@index([bizId])
  @@index([externalNo])
  @@index([status])
  @@index([accountId, createdAt]) -- 账户流水查询
  @@index([accountId, bizType])
}

enum PointBizType {
  // 充值类
  RECHARGE              // 用户充值
  ADMIN_GRANT           // 管理员赠送
  PROMO_GRANT           // 活动奖励

  // 消费类
  ORDER_CONSUME         // 订单消费（购买商品）
  REDEEM                // 积分兑换礼品
  SERVICE_FEE           // 服务费扣减

  // 退款/回滚
  ORDER_REFUND          // 订单退款返还

  // 冻结/解冻
  FREEZE                // 冻结（如提现审核）
  UNFREEZE              // 解冻（如审核拒绝）

  // 提现
  WITHDRAW_REQUEST      // 提现申请冻结
  WITHDRAW_COMPLETE     // 提现完成
  WITHDRAW_REJECT       // 提现拒绝，资金返还

  // 分润/佣金
  COMMISSION_INCOME     // 佣金到账
  COMMISSION_PAYOUT     // 佣金提现

  // 其他
  ADJUST                // 调账（人工）
  EXPIRE                // 积分过期
  TRANSFER_IN           // 转账收入
  TRANSFER_OUT          // 转账支出
}

enum PointLedgerStatus {
  PENDING    // 处理中（如充值待确认）
  CONFIRMED  // 已确认
  CANCELLED  // 已取消
  FAILED     // 失败
}
```

---

### 3.7 ProductLevelPrice（商品等级价格表）

> 不同会员等级购买同一商品，享受不同积分价格

```prisma
model ProductLevelPrice {
  id              String    @id @default(uuid())

  // 商品维度（复用 MedusaJS）
  variantId       String    // FK → product_variants.id

  // 等级维度
  levelCode       String    // FK → member_levels.code

  // 价格配置
  pointPrice      BigInt    // 该等级的积分售价（整数）
  cashPrice       Decimal?  @db.Decimal(18,2) // 现金价（可选，若支持混合支付）
  discountRate    Decimal?  @db.Decimal(5,4) // 折扣率（覆盖默认倍率）

  // 限购
  maxPerOrder     Int?      // 每人每单限购数量
  monthlyLimit    Int?      // 每月限购数量

  isActive        Boolean   @default(true)
  effectiveFrom   DateTime?
  effectiveTo     DateTime?

  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt

  @@unique([variantId, levelCode])
  @@index([variantId])
  @@index([levelCode])
  @@index([isActive])
}
```

**价格计算逻辑**：
```javascript
// 获取某用户购买某商品的价格
function getPrice(memberId, variantId) {
  const member = await getMember(memberId)
  const levelCode = member.levelCode

  // 优先查等级专属价格
  const levelPrice = await db.productLevelPrice.findUnique({
    where: { variantId_levelCode: { variantId, levelCode } }
  })

  if (levelPrice) return { type: 'points', amount: levelPrice.pointPrice }

  // 回退到等级默认倍率
  const level = await db.memberLevel.findUnique({ where: { code: levelCode } })
  const variant = await db.productVariant.findUnique({ where: { id: variantId } })
  const price = Math.round(variant.price * level.pointRate)

  return { type: 'points', amount: price }
}
```

---

### 3.8 LevelAdvancement（等级晋升记录表）

> 记录每次晋升申请和审核历史

```prisma
model LevelAdvancement {
  id              String    @id @default(uuid())

  memberId        String    // FK → members.id

  fromLevelCode   String   // 原等级
  toLevelCode     String   // 申请晋升目标等级

  // 晋升条件达成情况
  conditionReached Json?   // 存储各条件实际值，如：
                           // { referrals: 5, purchaseAmt: 50000, teamAmt: 300000 }

  // 申请/审核状态
  status          AdvancementStatus @default(PENDING)

  // 审核
  reviewerId      String?
  reviewedAt      DateTime?
  reviewNote      String?

  // 生效时间
  effectiveAt     DateTime? // 审核通过后生效时间

  createdAt       DateTime  @default(now())

  // Relations
  member          Member @relation(fields: [memberId], references: [id])

  @@index([memberId])
  @@index([status])
  @@index([createdAt])
  @@index([toLevelCode])
}

enum AdvancementStatus {
  PENDING    // 待审核
  APPROVED   // 已批准
  REJECTED   // 已拒绝
  CANCELLED  // 主动取消
}
```

---

### 3.9 InviteCode（邀请码表）

> 扫码绑定核心入口，每个用户有唯一邀请码

```prisma
model InviteCode {
  id              String    @id @default(uuid())

  code            String    @unique  // 6位数字字母混合（如 "A3K9X2"）
  memberId        String    // FK → members.id（邀请码所有者）

  // 码类型
  codeType        InviteCodeType @default(PERSONAL)  // 每人专属码 / 公共推广码

  // 使用统计
  useCount        Int       @default(0)   // 已被使用次数
  maxUses         Int?      // null=无限，1=单次（如礼品码）

  // 有效期
  effectiveFrom   DateTime? @default(now())
  effectiveTo     DateTime?

  // 关联推广活动
  campaignId      String?

  isActive        Boolean   @default(true)

  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt

  @@index([code])
  @@index([memberId])
  @@index([isActive, effectiveTo])
}

enum InviteCodeType {
  PERSONAL   // 个人推广码（绑定上下级关系）
  CAMPAIGN   // 活动推广码（仅计业绩，不绑定上下级）
  GIFT       // 礼品码（一次性）
}
```

---

## 四、MedusaJS 扩展表（OrderPoint）

### OrderPoint（积分订单扩展表）

```prisma
model OrderPoint {
  id                  String    @id @default(uuid())
  orderId             String    @unique  // FK → orders.id

  // 积分支付详情
  pointsSpent         BigInt    @default(0)   // 消耗积分
  pointsDiscountAmt   Decimal   @db.Decimal(18,2) @default(0) // 积分抵扣金额（元）
  cashSpent           Decimal   @db.Decimal(18,2) @default(0) // 现金支付

  // 订单原价 vs 实付
  originalTotal        Decimal  @db.Decimal(18,2) // 原价总价
  finalTotal           Decimal  @db.Decimal(18,2) // 最终实付

  // 佣金归属（预计算，避免后续递归）
  commissionReceiverId String?   // 佣金归属会员ID
  commissionLevel      Int?      // 佣金归属层级（1/2/3）

  // 积分返还（购物返积分）
  pointsRewarded       BigInt    @default(0)

  createdAt           DateTime  @default(now())

  @@index([orderId])
  @@index([commissionReceiverId])
}
```

---

## 五、完整 Prisma Schema

```prisma
// This is your Prisma schema file,
// OPC Mall Extension for MedusaJS
// ================================

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// ============================================================
// 会员等级配置
// ============================================================

model MemberLevel {
  id                     String    @id @default(uuid())
  code                   String    @unique
  name                   String
  nameEn                 String?
  icon                   String?
  pointRate              Decimal   @db.Decimal(5, 4)
  minPurchaseAmt         Decimal   @db.Decimal(18, 2) @default(0)
  minReferrals           Int       @default(0)
  requireUnion           Int       @default(0)
  requireCommunity       Int       @default(0)
  performanceTarget       Decimal   @db.Decimal(18, 2) @default(0)
  performancePeriodDays  Int       @default(0)
  sortOrder              Int       @default(0)
  isActive               Boolean   @default(true)
  createdAt              DateTime  @default(now())
  updatedAt              DateTime  @updatedAt

  members     Member[]
  advancements LevelAdvancement[]

  @@index([code])
  @@index([sortOrder])
}

// ============================================================
// 会员主表（扩展 MedusaJS Customer，1:1）
// ============================================================

model Member {
  id            String    @id @default(uuid())
  customerId    String    @unique
  levelCode     String   @default("opc")
  levelId       String?
  levelIdAt     DateTime?

  // 推广信息
  inviteCode            String    @unique
  inviteQrCode          String?
  bindTime              DateTime?

  // 业绩统计
  totalPurchaseAmt      Decimal   @db.Decimal(18, 2) @default(0)
  teamPurchaseAmt       Decimal   @db.Decimal(18, 2) @default(0)
  directReferrals       Int       @default(0)
  indirectReferrals     Int       @default(0)

  // 晋升
  promotionStatus       PromotionStatus @default(PENDING)
  promotionAppliedAt    DateTime?
  promotionReviewedAt    DateTime?
  promotionNote          String?

  // 状态
  isActive              Boolean   @default(true)
  freezeReason          String?

  createdAt             DateTime  @default(now())
  updatedAt             DateTime  @updatedAt

  // Relations
  level        MemberLevel?          @relation(fields: [levelId], references: [id])
  pointAccount PointAccount?
  distributionNode DistributionNode?
  advancements  LevelAdvancement[]
  orders        OrderPoint[]

  @@index([customerId])
  @@index([levelCode])
  @@index([inviteCode])
  @@index([promotionStatus])
  @@index([createdAt])
  @@index([totalPurchaseAmt])
}

enum PromotionStatus {
  PENDING
  APPROVED
  REJECTED
}

// ============================================================
// 分销关系（扫描绑定，终身有效）
// ============================================================

model DistributionNode {
  id               String     @id @default(uuid())
  memberId         String     @unique

  // 合规：最多追踪3层
  parentId           String?
  grandparentId      String?
  greatGrandparentId String?

  depth             Int       @default(0)

  // 预计算路径（支持前缀查询）
  ancestorPath   String?
  descendantPath String?

  bindSource       BindSource @default(QRCODE)
  bindScene       String?

  isActive         Boolean    @default(true)
  deactivatedAt    DateTime?
  deactivateReason String?

  createdAt        DateTime   @default(now())
  updatedAt        DateTime   @updatedAt

  // Relations
  member             Member             @relation(fields: [memberId], references: [id])
  parent             DistributionNode?   @relation("NodeHierarchy", fields: [parentId], references: [id])
  children           DistributionNode[]  @relation("NodeHierarchy")
  distributionPaths  DistributionPath[]

  @@index([memberId])
  @@index([parentId])
  @@index([depth])
  @@index([ancestorPath])
  @@index([descendantPath])
  @@index([createdAt])
  @@index([isActive, depth])
}

enum BindSource {
  QRCODE
  LINK
  MANUAL
}

// ============================================================
// 分销链路快照（预计算3层，查询性能优化）
// ============================================================

model DistributionPath {
  id               String           @id @default(uuid())
  ownerId          String
  level            Int
  nodeId           String
  memberId         String
  memberLevelCode String?
  commissionRate   Decimal @db.Decimal(5, 4) @default(0)

  createdAt        DateTime @default(now())

  owner    DistributionNode @relation(fields: [ownerId], references: [id])

  @@unique([ownerId, level])
  @@index([ownerId])
  @@index([memberId])
  @@index([level])
  @@index([memberLevelCode])
}

// ============================================================
// 积分账户
// ============================================================

model PointAccount {
  id                    String   @id @default(uuid())
  memberId              String   @unique

  balance               BigInt   @default(0)
  frozenBalance         BigInt   @default(0)
  totalRecharged        BigInt   @default(0)
  totalConsumed         BigInt   @default(0)
  totalWithdrawn        BigInt   @default(0)

  passwordHash          String?
  dailyRechargeLimit    BigInt   @default(0)
  monthlyRechargeLimit  BigInt   @default(0)

  version               Int      @default(1)

  createdAt             DateTime @default(now())
  updatedAt             DateTime @updatedAt

  member         Member         @relation(fields: [memberId], references: [id])
  transactions   PointLedger[]

  @@index([memberId])
  @@index([balance])
}

// ============================================================
// 积分流水（不可篡改日志）
// ============================================================

model PointLedger {
  id            String    @id @default(uuid())
  accountId     String
  memberId      String

  amount        BigInt
  balanceBefore BigInt    @default(0)
  balanceAfter  BigInt    @default(0)

  bizType       PointBizType
  bizId         String?
  bizNo         String?
  description   String?
  externalNo    String?
  frozenAmount  BigInt?
  expiredAt     DateTime?
  status        PointLedgerStatus @default(CONFIRMED)

  createdAt     DateTime  @default(now())
  confirmedAt   DateTime?

  account       PointAccount @relation(fields: [accountId], references: [id])

  @@unique([bizNo])
  @@index([accountId])
  @@index([memberId])
  @@index([bizType])
  @@index([createdAt])
  @@index([bizId])
  @@index([externalNo])
  @@index([status])
  @@index([accountId, createdAt])
  @@index([accountId, bizType])
}

enum PointBizType {
  RECHARGE
  ADMIN_GRANT
  PROMO_GRANT
  ORDER_CONSUME
  REDEEM
  SERVICE_FEE
  ORDER_REFUND
  FREEZE
  UNFREEZE
  WITHDRAW_REQUEST
  WITHDRAW_COMPLETE
  WITHDRAW_REJECT
  COMMISSION_INCOME
  COMMISSION_PAYOUT
  ADJUST
  EXPIRE
  TRANSFER_IN
  TRANSFER_OUT
}

enum PointLedgerStatus {
  PENDING
  CONFIRMED
  CANCELLED
  FAILED
}

// ============================================================
// 商品等级价格
// ============================================================

model ProductLevelPrice {
  id            String    @id @default(uuid())
  variantId     String
  levelCode     String

  pointPrice    BigInt
  cashPrice     Decimal?  @db.Decimal(18, 2)
  discountRate  Decimal?  @db.Decimal(5, 4)

  maxPerOrder   Int?
  monthlyLimit  Int?

  isActive      Boolean   @default(true)
  effectiveFrom DateTime?
  effectiveTo   DateTime?

  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  @@unique([variantId, levelCode])
  @@index([variantId])
  @@index([levelCode])
  @@index([isActive])
}

// ============================================================
// 等级晋升记录
// ============================================================

model LevelAdvancement {
  id            String    @id @default(uuid())
  memberId      String

  fromLevelCode String
  toLevelCode   String
  conditionReached Json?

  status        AdvancementStatus @default(PENDING)
  reviewerId    String?
  reviewedAt    DateTime?
  reviewNote    String?
  effectiveAt   DateTime?

  createdAt     DateTime  @default(now())

  member        MemberLevel @relation(fields: [toLevelCode], references: [code])

  @@index([memberId])
  @@index([status])
  @@index([createdAt])
  @@index([toLevelCode])
}

enum AdvancementStatus {
  PENDING
  APPROVED
  REJECTED
  CANCELLED
}

// ============================================================
// 邀请码
// ============================================================

model InviteCode {
  id            String       @id @default(uuid())
  code          String       @unique
  memberId      String
  codeType      InviteCodeType @default(PERSONAL)
  useCount      Int          @default(0)
  maxUses       Int?
  effectiveFrom DateTime?    @default(now())
  effectiveTo   DateTime?
  campaignId    String?
  isActive      Boolean      @default(true)
  createdAt     DateTime     @default(now())
  updatedAt     DateTime     @updatedAt

  @@index([code])
  @@index([memberId])
  @@index([isActive, effectiveTo])
}

enum InviteCodeType {
  PERSONAL
  CAMPAIGN
  GIFT
}

// ============================================================
// 积分订单（扩展 MedusaJS Order）
// ============================================================

model OrderPoint {
  id               String   @id @default(uuid())
  orderId          String   @unique

  pointsSpent      BigInt   @default(0)
  pointsDiscountAmt Decimal @db.Decimal(18, 2) @default(0)
  cashSpent        Decimal  @db.Decimal(18, 2) @default(0)
  originalTotal    Decimal  @db.Decimal(18, 2)
  finalTotal       Decimal  @db.Decimal(18, 2)

  commissionReceiverId String?
  commissionLevel      Int?
  pointsRewarded       BigInt  @default(0)

  createdAt        DateTime @default(now())

  @@index([orderId])
  @@index([commissionReceiverId])
}
```

---

## 六、索引策略（高频查询优化）

### 分销链路查询（最高频）

| 查询场景 | SQL 优化方式 |
|---------|------------|
| 查询某人的所有下级 | `ancestor_path LIKE '/owner-id/%'`（前缀索引） |
| 查询某人的所有上级 | 查 `DistributionPath`（已预计算） |
| 查询某团队业绩TOP N | `team_purchase_amt DESC` 索引 + ORDER BY |
| 递归子树查询 | `descendant_path LIKE '/node-id/%'` |
| 检查是否在3层内 | `depth ≤ 3` 组合索引 |

### 积分流水查询

| 查询场景 | 索引 |
|---------|-----|
| 账户余额流水 | `(account_id, created_at)` |
| 按业务类型筛选 | `(account_id, biz_type)` |
| 对账查询 | `(biz_no)` UNIQUE |
| 外部流水号对账 | `(external_no)` |
| 用户交易历史 | `(member_id, created_at)` |

### 晋升查询

```sql
-- 性能关键：晋升条件判断（触发器/定时任务执行）
CREATE INDEX idx_member_promotion_conditions
ON members(level_code, total_purchase_amt, direct_referrals)
WHERE promotion_status = 'PENDING';
```

---

## 七、晋升规则实现

```typescript
// 晋升条件计算（伪代码）
async function checkPromotion(memberId: string): Promise<PromotionResult | null> {
  const member = await db.member.findUnique({
    where: { id: memberId },
    include: {
      level: true,
      distributionNode: {
        include: {
          children: { include: { member: true } } // 下级节点
        }
      }
    }
  })

  const nextLevel = await getNextLevel(member.levelCode)
  if (!nextLevel) return null // 已是最高等级

  const now = new Date()
  const periodStart = subDays(now, nextLevel.performancePeriodDays || 0)

  // 条件1：推荐人数（OPC→工会：5个OPC）
  if (member.directReferrals < nextLevel.minReferrals) {
    return { eligible: false, reason: `还需 ${nextLevel.minReferrals - member.directReferrals} 个直接推荐` }
  }

  // 条件2：采购金额
  if (member.totalPurchaseAmt < nextLevel.minPurchaseAmt) {
    return { eligible: false, reason: `还需消费 ¥${nextLevel.minPurchaseAmt - member.totalPurchaseAmt}` }
  }

  // 条件3：下级工会数（工会→社区：2个工会）
  if (nextLevel.requireUnion > 0) {
    const childUnions = member.distributionNode.children
      .filter(c => c.member.levelCode === 'opc_union')
    if (childUnions.length < nextLevel.requireUnion) {
      return { eligible: false, reason: `还需发展 ${nextLevel.requireUnion - childUnions.length} 个下级工会` }
    }
  }

  // 条件4：社区→城市（1年内300万业绩）
  if (nextLevel.performanceTarget > 0) {
    const teamPerformance = await getTeamPerformance(memberId, periodStart, now)
    if (teamPerformance < nextLevel.performanceTarget) {
      return { eligible: false, reason: `还需 ¥${nextLevel.performanceTarget - teamPerformance} 团队业绩` }
    }
  }

  return { eligible: true, nextLevel }
}
```

---

## 八、数据初始化（Seed）

```sql
-- 会员等级初始数据
INSERT INTO member_levels (code, name, point_rate, min_referrals, require_union, performance_target, performance_period_days, sort_order) VALUES
('opc',          'OPC',          1.0000, 0,   0,           0,      0,     1),
('opc_union',    'OPC工会',       0.9000, 5,   0,           0,      0,     2),  -- 5个OPC升工会
('opc_community','OPC社区',       0.8500, 0,   2,           0,      0,     3),  -- 2个工会升社区
('opc_city',     'OPC城市',       0.8000, 0,   0, 3000000.00, 365,   4);    -- 1年内300万升城市
```

---

## 九、关键设计决策

| 决策项 | 选择 | 理由 |
|-------|-----|------|
| 分润层级 | 3层（实际结算） | 中国《禁止传销条例》合规 |
| 会员等级 | 4层（身份标识） | 区分采购折扣，灵活运营 |
| 积分存储 | BIGINT整数 | 避免浮点精度问题，1积分=1单位 |
| 链路查询 | 预计算+路径索引 | 避免递归CTE，O(1)查询 |
| 佣金表 | DistributionPath | 每笔订单直接查，不用递归 |
| 积分流水 | 不可变日志 | 支持对账、防篡改 |
| 晋升触发 | 定时任务+事件驱动 | 避免频繁计算，批量处理 |
