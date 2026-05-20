import type { CompanionContent, PhaseContentMap } from './types'

const planningContent: CompanionContent = {
  expression: 'Loading',
  phrases: [
    '正在分析你的需求...',
    '交通方案规划中...',
    '正在为你挑选最佳住宿...',
    '美食推荐进行中...',
    '马上就好，稍等哦~',
    '点击我查看规划进度！',
  ],
  clickTips: [
    '点击我查看详细规划进度，还可以和我聊天~',
  ],
}

const noPlanContent: CompanionContent = {
  expression: 'Idle',
  phrases: [
    '有什么可以帮你的吗？',
    '点击查看今日行程~',
    '需要导航吗？',
    '今天天气不错！☀️',
    '分享链接给我，我可以学习哦~',
    '我已学会X条新知识！',
    '嘿！想去哪里玩呢？点击我帮你规划~',
    '世界那么大，一起去看看！',
  ],
  clickTips: [
    '点击我开始对话，告诉我你想去哪里、玩几天、预算多少，我来帮你规划！',
    '也可以直接在首页填写出行条件，一键生成方案哦~',
  ],
}

const planGeneratedContent: CompanionContent = {
  expression: 'StarEye',
  phrases: [
    '有什么可以帮你的吗？',
    '点击查看今日行程~',
    '需要导航吗？',
    '方案已就绪！点击我查看详细行程~',
    '看看我为你准备的专属计划吧！',
    '分享链接给我，我可以学习哦~',
    '我已学会X条新知识！',
  ],
  clickTips: [
    '点击查看详细行程、每日安排和预算明细。确认无误后点击"开始这趟旅行"即可开启旅途~',
  ],
}

const tripActiveContent: CompanionContent = {
  expression: 'Amaze',
  phrases: [
    '有什么可以帮你的吗？',
    '点击查看今日行程~',
    '需要导航吗？',
    '今天天气不错！☀️',
    '分享链接给我，我可以学习哦~',
    '旅途愉快！需要什么帮助随时点我~',
    '别忘了拍照记录美好瞬间！',
    '玩得开心最重要！',
  ],
  clickTips: [
    '点击我查看实时贴士：天气预报、景点拥挤提醒、交通提示、当地便民信息~',
  ],
}

export const phaseContent: PhaseContentMap = {
  no_plan: noPlanContent,
  planning: planningContent,
  plan_generated: planGeneratedContent,
  trip_active: tripActiveContent,
}

export function getCompanionContent(phase: keyof PhaseContentMap): CompanionContent {
  return phaseContent[phase] || noPlanContent
}
