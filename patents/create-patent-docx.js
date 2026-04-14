const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat,
} = require('docx');
const fs = require('fs');

const A4_W = 11906, A4_H = 16838, MARGIN = 1440, CW = A4_W - MARGIN * 2;
const BM = { top: 80, bottom: 80, left: 120, right: 120 };
const BD = { style: BorderStyle.SINGLE, size: 1, color: "999999" };
const BDR = { top: BD, bottom: BD, left: BD, right: BD };

// helpers
const T = (text, opts = {}) => new TextRun({ text, font: 'Arial', size: 24, ...opts });
const P = (children, opts = {}) => new Paragraph({ children: Array.isArray(children) ? children : [children], spacing: { before: 60, after: 60 }, ...opts });
const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: 'Arial', bold: true, size: 30, color: '1A3A5A' })], spacing: { before: 360, after: 180 } });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: 'Arial', bold: true, size: 26, color: '2C5282' })], spacing: { before: 240, after: 120 } });
const H3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text, font: 'Arial', bold: true, size: 24, color: '2D3748' })], spacing: { before: 160, after: 80 } });
const BLANK = () => new Paragraph({ children: [T('')], spacing: { before: 60, after: 60 } });
const PB = () => new Paragraph({ children: [new PageBreak()] });

const WARN = (text) => new Paragraph({
  children: [new TextRun({ text, italics: true, size: 20, color: 'CC0000', font: 'Arial' })],
  spacing: { before: 120, after: 120 }, shading: { fill: 'FFF0F0', type: ShadingType.CLEAR }
});

const CELL = (content, opts = {}) => new TableCell({
  borders: BDR, margins: BM, verticalAlign: VerticalAlign.TOP,
  ...opts,
  children: Array.isArray(content) ? content : [new Paragraph({ children: [T(content)] })]
});

// ─── rows ────────────────────────────────────────────────
const hdrRow = (cols) => new TableRow({
  children: cols.map(([text, w]) => CELL(
    [new Paragraph({ children: [new TextRun({ text, bold: true, font: 'Arial', size: 22 })] })],
    { width: { size: w, type: WidthType.DXA }, shading: { fill: '1A3A5A', type: ShadingType.CLEAR } }
  ))
});

const dataRow = (cols, altColor) => new TableRow({
  children: cols.map(([text, w]) => CELL(
    [new Paragraph({ children: [T(text, { size: 22 })] })],
    { width: { size: w, type: WidthType.DXA }, shading: { fill: altColor ? 'F0F7FF' : 'FFFFFF', type: ShadingType.CLEAR } }
  ))
});

// ─── main content ─────────────────────────────────────────
const content = [

  // Title
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 480, after: 240 },
    children: [new TextRun({ text: '专利申请书', bold: true, font: 'Arial', size: 52 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 480 },
    children: [new TextRun({ text: '（初稿 — 供专利律师参考使用，不具备法律效力）', italics: true, font: 'Arial', size: 22, color: '666666' })] }),

  WARN('本文件为初稿，仅供专利律师参考使用。撰写人：大闸蟹（AI助理）| 日期：2026-03-28'),
  BLANK(),

  // 一、发明名称
  H1('一、发明名称'),
  P([T('一种基于三层文件记忆架构的企业级AI智能体协作系统及方法', { bold: true, size: 26 })]),

  // 二、技术领域
  H1('二、技术领域'),
  P([T('本发明属于人工智能技术领域，具体涉及一种通过文件系统实现多个AI智能体（Agent）长期协作的企业级方法架构。')]),

  // 三、背景技术
  H1('三、背景技术'),
  H2('3.1 现有技术的不足'),

  H3('（1）会话记忆无法跨周期积累'),
  P([T('现有AI Agent基于单次会话运行，对话结束后所有上下文丢失。每次启动均为从零开始，无法形成持续增长的能力积累。')]),

  H3('（2）多Agent协作依赖外部系统'),
  P([T('现有多Agent方案通常依赖消息队列、API调用或数据库作为协调层，系统复杂度高，部署成本大，且存在单点故障风险。')]),

  H3('（3）企业场景的上下文断裂'),
  P([T('企业运营涉及多角色（销售/运营/客服/管理层），各角色AI之间的信息不互通，无法形成统一的组织记忆，导致AI输出与企业实际需求脱节。')]),

  H3('（4）缺乏可持续演化的架构'),
  P([T('现有方案将AI能力固化在模型本身，而非固化在积累的上下文文件中。一旦更换模型，所有经验归零。')]),

  H2('3.2 现有技术的典型方案'),
  new Table({
    width: { size: CW, type: WidthType.DXA },
    columnWidths: [2200, 6818],
    rows: [
      hdrRow([['技术方案', 2200], ['主要缺陷', 6818]]),
      dataRow([['OpenAI/Claude Assistant API', 2200]], false),
      new TableRow({ children: [
        CELL('Assistant API', { width: { size: 2200, type: WidthType.DXA } }),
        CELL('基于向量数据库存储记忆，需要额外工程开发', { width: { size: 6818, type: WidthType.DXA } }),
      ]}),
      new TableRow({ children: [
        CELL('CrewAI等框架', { width: { size: 2200, type: WidthType.DXA } }),
        CELL('基于代码层协调，依赖API调用', { width: { size: 6818, type: WidthType.DXA } }),
      ]}),
      new TableRow({ children: [
        CELL('传统企业AI系统', { width: { size: 2200, type: WidthType.DXA } }),
        CELL('基于数据库+规则引擎，缺乏自适应演化能力', { width: { size: 6818, type: WidthType.DXA } }),
      ]}),
    ]
  }),

  BLANK(),

  // 四、发明内容
  H1('四、发明内容'),
  H2('4.1 核心创新点'),
  P([T('本发明提出一种'), T('三层文件记忆架构', { bold: true }), T('，通过文件系统作为集成层，实现AI智能体的长期协作与组织记忆积累，无需数据库、消息队列或复杂中间件。')]),

  H2('4.2 系统架构'),
  P([T('系统由以下三层构成：')]),

  // 架构总表
  new Table({
    width: { size: CW, type: WidthType.DXA },
    columnWidths: [1800, 7218],
    rows: [
      hdrRow([['层次', 1800], ['内容说明', 7218]]),
      new TableRow({ children: [
        CELL([new Paragraph({ children: [new TextRun({ text: '第一层 身份层', bold: true, color: '1A3A5A', font: 'Arial', size: 22 })] })],
          { width: { size: 1800, type: WidthType.DXA }, shading: { fill: 'EAF3FF', type: ShadingType.CLEAR } }),
        CELL([
          P([T('SOUL.md', { bold: true, size: 22 }), T(' — 智能体角色定位与行为性格定义', { size: 22 })]),
          P([T('IDENTITY.md', { bold: true, size: 22 }), T(' — 快速参考名片（名字/角色/风格）', { size: 22 })]),
          P([T('USER.md', { bold: true, size: 22 }), T(' — 服务对象画像与偏好', { size: 22 })]),
        ], { width: { size: 7218, type: WidthType.DXA } }),
      ]}),
      new TableRow({ children: [
        CELL([new Paragraph({ children: [new TextRun({ text: '第二层 操作层', bold: true, color: '1A3A5A', font: 'Arial', size: 22 })] })],
          { width: { size: 1800, type: WidthType.DXA }, shading: { fill: 'EAF3FF', type: ShadingType.CLEAR } }),
        CELL([
          P([T('AGENTS.md', { bold: true, size: 22 }), T(' — 启动流程与行为规则', { size: 22 })]),
          P([T('HEARTBEAT.md', { bold: true, size: 22 }), T(' — 自检监控与健康检查', { size: 22 })]),
          P([T('专业规则文件', { bold: true, size: 22 }), T(' — 角色专属操作指南', { size: 22 })]),
        ], { width: { size: 7218, type: WidthType.DXA } }),
      ]}),
      new TableRow({ children: [
        CELL([new Paragraph({ children: [new TextRun({ text: '第三层 知识层', bold: true, color: '1A3A5A', font: 'Arial', size: 22 })] })],
          { width: { size: 1800, type: WidthType.DXA }, shading: { fill: 'EAF3FF', type: ShadingType.CLEAR } }),
        CELL([
          P([T('MEMORY.md', { bold: true, size: 22 }), T(' — 长期记忆（精炼版）', { size: 22 })]),
          P([T('memory/YYYY-MM-DD.md', { bold: true, size: 22 }), T(' — 每日操作日志', { size: 22 })]),
          P([T('shared-context/THESIS.md', { bold: true, size: 22 }), T(' — 组织当前战略世界观', { size: 22 })]),
          P([T('shared-context/FEEDBACK-LOG.md', { bold: true, size: 22 }), T(' — 跨角色纠错记录', { size: 22 })]),
          P([T('shared-context/SIGNALS.md', { bold: true, size: 22 }), T(' — 外部信号与趋势追踪', { size: 22 })]),
        ], { width: { size: 7218, type: WidthType.DXA } }),
      ]}),
    ]
  }),

  BLANK(),

  H2('4.3 核心方法步骤'),
  P([T('步骤一：', { bold: true }), T('初始化组织级身份层 — 为每个智能体配置SOUL.md定义其角色定位与行为原则，配置USER.md定义其服务对象的背景与偏好。')]),
  P([T('步骤二：', { bold: true }), T('建立共享上下文中枢 — 创建shared-context/目录，其中THESIS.md记录组织的战略方向，FEEDBACK-LOG.md记录跨智能体纠错，SIGNALS.md追踪外部环境变化。')]),
  P([T('步骤三：', { bold: true }), T('构建前后端双层协作结构 — 后端智能体（策略中枢）负责制定战略、更新共享上下文；前端智能体（执行终端）读共享上下文，按指令执行任务。两者通过单写者规则避免写入冲突。')]),
  P([T('步骤四：', { bold: true }), T('建立时间积累机制 — 每日操作日志定期提炼至MEMORY.md，实现经验的跨周期传递。')]),
  P([T('步骤五：', { bold: true }), T('心跳自检与系统自演化 — 通过HEARTBEAT.md定期检查各智能体的运行状态，捕获静默失败，自动触发修复。')]),
  H2('4.4 技术效果对比'),
  new Table({
    width: { size: CW, type: WidthType.DXA },
    columnWidths: [2600, 3209, 3209],
    rows: [
      hdrRow([['指标', 2600], ['现有技术', 3209], ['本发明', 3209]]),
      ...([
        ['多Agent协作依赖', '消息队列/API', '文件系统（零依赖）'],
        ['经验复用', '每次从零开始', '提炼入MEMORY.md'],
        ['跨角色纠错', '需要重复告知', 'FEEDBACK-LOG一次记录'],
        ['新Agent启动', '需完整重新配置', '读共享上下文即对齐'],
        ['护城河积累', '依附于模型', '依附于文件，可跨模型迁移'],
      ].map(([idx, old, neu], i) => new TableRow({
        children: [
          CELL([new Paragraph({ children: [T(idx, { size: 22 })] })], { width: { size: 2600, type: WidthType.DXA } }),
          CELL([new Paragraph({ children: [T(old, { size: 22 })] })], { width: { size: 3209, type: WidthType.DXA } }),
        ]
      })))
    ]
  }),

  PB(),

  // 五、具体实施方式
  H1('五、具体实施方式'),

  H2('5.1 实施例一：企业营销团队场景'),
  P([T('某招商加盟企业部署本系统，包含：管理层智能体（大龙虾·后端）、获客智能体（小龙虾A）、客服智能体（小龙虾B）、内容智能体（小龙虾C）。')]),
  P([T('管理层智能体扫描市场数据，更新shared-context/SIGNALS.md；分析后更新shared-context/THESIS.md；获客/客服/内容三条小龙虾分别读共享上下文，自动生成对应输出。所有纠正在FEEDBACK-LOG.md记录一次，三条小龙虾均读取并修正。')]),

  H2('5.2 实施例二：个人知识管理者场景'),
  P([T('研究智能体扫描行业信息写入intel/DAILY-INTEL.md；写作智能体读该文件生成文章草稿；主智能体审核后给出纠正，写入FEEDBACK-LOG.md；写作智能体下次启动时自动加载纠错，无需重复告知。')]),

  // 六、权利要求书
  H1('六、权利要求书'),

  new Paragraph({ spacing: { before: 120, after: 80 },
    children: [new TextRun({ text: '独立权利要求', bold: true, underline: {}, font: 'Arial', size: 24 })] }),

  P([T('1. ', { bold: true }), T('一种基于文件系统实现的多智能体协作方法，其特征在于：为每个智能体配置身份定义文件，建立角色定位；构建共享上下文中枢，包含战略世界观文件、跨智能体纠错日志文件和环境信号追踪文件；共享上下文中枢被所有智能体在每次启动时读取；多个智能体之间通过文件读写进行任务交接，以单写者规则避免写入冲突。')]),

  P([T('2. ', { bold: true }), T('一种企业级AI智能体协作系统，其特征在于：第一层身份定义模块，用于配置各智能体的角色定位、服务对象画像和行为规则；第二层操作控制模块，用于定义各智能体的工作流程和启动检查规则；第三层知识积累模块，包括长期记忆文件、每日操作日志和共享上下文中枢；共享上下文中枢包含战略世界观文件、跨智能体纠错日志文件和环境信号追踪文件；各智能体通过读取共享上下文中枢实现跨周期经验积累。')]),

  new Paragraph({ spacing: { before: 240, after: 80 },
    children: [new TextRun({ text: '从属权利要求', bold: true, underline: {}, font: 'Arial', size: 24 })] }),

  P([T('3. 根据权利要求1所述的方法，其特征在于：所述长期记忆文件在每次会话启动时自动加载，内容包括经提炼的重要决策、业务教训和持续优化的行为规则。')], { indent: { left: 360 } }),
  P([T('4. 根据权利要求1所述的方法，其特征在于：所述每日操作日志以日期命名，定期由人工或智能体将高频纠错和重要经验提炼至所述长期记忆文件。')], { indent: { left: 360 } }),
  P([T('5. 根据权利要求1所述的方法，其特征在于：还包括心跳自检模块，用于定时检查各智能体的任务执行状态，在检测到静默失败时自动触发修复流程。')], { indent: { left: 360 } }),
  P([T('6. 根据权利要求2所述的系统，其特征在于：所述系统部署于企业运营场景，包括后端策略智能体和至少一个前端执行智能体，所述后端智能体负责更新所述战略世界观文件，所述前端执行智能体依据所述战略世界观文件执行具体任务。')], { indent: { left: 360 } }),
  P([T('7. 根据权利要求6所述的系统，其特征在于：所述后端策略智能体与所述前端执行智能体之间不存在直接的API调用或消息队列通信，仅通过文件系统中的共享文件进行任务交接。')], { indent: { left: 360 } }),

  PB(),

  // 七、摘要
  H1('七、摘要'),
  P([T('本发明公开了一种基于三层文件记忆架构的企业级AI智能体协作系统及方法。系统由身份层（定义智能体角色）、操作层（定义工作流程）和知识层（积累组织记忆）三层构成，通过文件系统作为集成层实现多智能体的跨周期协作与经验积累。共享上下文中枢作为单一真相来源，包含战略世界观、跨智能体纠错日志和环境信号追踪文件，确保所有智能体对齐同一组织目标。本发明无需数据库、消息队列等复杂中间件，仅通过文件读写实现零依赖协作，使组织记忆随时间持续积累，形成难以复制的AI能力护城河。')]),

  BLANK(),
  new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { before: 480 },
    children: [T('附：待专利律师补充附图（系统架构图、文件目录结构图、工作流程时序图）', { italics: true, size: 20, color: '888888' })] }),
];

// ─── build doc ───────────────────────────────────────────
const doc = new Document({
  numbering: { config: [] },
  styles: {
    default: { document: { run: { font: 'Arial', size: 24 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 30, bold: true, font: 'Arial', color: '1A3A5A' },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: 'Arial', color: '2C5282' },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, font: 'Arial', color: '2D3748' },
        paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: { page: { size: { width: A4_W, height: A4_H }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    headers: { default: new Header({ children: [new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '1A3A5A', space: 4 } },
      children: [new TextRun({ text: '专利申请书 — 初稿（供律师参考，不具备法律效力）', italics: true, size: 18, color: '888888', font: 'Arial' })]
    })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      border: { top: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC', space: 4 } },
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({ text: '第 ', size: 18, color: '888888', font: 'Arial' }),
        new TextRun({ children: [PageNumber.CURRENT], size: 18, color: '888888', font: 'Arial' }),
        new TextRun({ text: ' 页', size: 18, color: '888888', font: 'Arial' }),
      ]
    })] }) },
    children: content,
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/Users/mac/.openclaw/workspace/patents/专利申请书-三层文件记忆架构-初稿.docx', buf);
  console.log('Document generated successfully.');
});
