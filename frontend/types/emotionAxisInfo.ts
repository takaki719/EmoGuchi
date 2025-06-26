export interface EmotionAxisInfo {
  id: string;
  nameJa: string;
  nameEn: string;
  description: string;
  keywords: string[];
}

export const EMOTION_AXIS_INFO: Record<string, EmotionAxisInfo> = {
  joy: {
    id: 'joy',
    nameJa: '喜び軸',
    nameEn: 'Joy Axis',
    description: '幸福感・満足・楽観を表す感情群',
    keywords: ['幸せ', '満足', '楽観', '陽気', '充実感']
  },
  trust: {
    id: 'trust',
    nameJa: '信頼軸',
    nameEn: 'Trust Axis',
    description: '受容・信頼・安心を表す感情群',
    keywords: ['信頼', '受容', '安心', '親しみ', '協調']
  },
  fear: {
    id: 'fear',
    nameJa: '恐怖軸',
    nameEn: 'Fear Axis',
    description: '不安・恐れ・警戒を表す感情群',
    keywords: ['不安', '恐れ', '警戒', '心配', '緊張']
  },
  surprise: {
    id: 'surprise',
    nameJa: '驚き軸',
    nameEn: 'Surprise Axis',
    description: '驚愕・困惑・注意を表す感情群',
    keywords: ['驚き', '困惑', '注意', '関心', '気づき']
  },
  sadness: {
    id: 'sadness',
    nameJa: '悲しみ軸',
    nameEn: 'Sadness Axis',
    description: '悲しみ・失望・憂鬱を表す感情群',
    keywords: ['悲しみ', '失望', '憂鬱', '寂しさ', '落胆']
  },
  disgust: {
    id: 'disgust',
    nameJa: '嫌悪軸',
    nameEn: 'Disgust Axis',
    description: '嫌悪・拒絶・軽蔑を表す感情群',
    keywords: ['嫌悪', '拒絶', '軽蔑', 'うんざり', '不快']
  },
  anger: {
    id: 'anger',
    nameJa: '怒り軸',
    nameEn: 'Anger Axis',
    description: 'フラストレーション・対立・自己防衛の感情群',
    keywords: ['怒り', 'イライラ', '対立', '不満', '抗議']
  },
  anticipation: {
    id: 'anticipation',
    nameJa: '期待軸',
    nameEn: 'Anticipation Axis',
    description: '期待・興味・準備を表す感情群',
    keywords: ['期待', '興味', '準備', '集中', '意欲']
  }
};