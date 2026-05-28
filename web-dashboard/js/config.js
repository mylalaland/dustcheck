// ============================================================
// DustCheck Firebase 설정 파일
// ============================================================
// ★ 아래 값을 본인의 Firebase 프로젝트 값으로 교체하세요!
//   (FIREBASE_GUIDE.md의 '4. 웹 앱 등록' 참고)
// ============================================================

const FIREBASE_CONFIG = {
    apiKey: "AIzaSyDHow15zcgOpN6HYwD9jWljAaDQ_i9yySc",
    authDomain: "dustcheck-da9e1.firebaseapp.com",
    databaseURL: "https://dustcheck-da9e1-default-rtdb.firebaseio.com",
    projectId: "dustcheck-da9e1",
    storageBucket: "dustcheck-da9e1.firebasestorage.app",
    messagingSenderId: "622287577036",
    appId: "1:622287577036:web:2d51fec1e576a9b3270769",
    measurementId: "G-EZZ1K8Q9WM"
};

// 공기질 등급 기준 (μg/m³)
const AIR_QUALITY = {
    pm1: [
        { label: "좋음", labelEn: "Good", max: 10, emoji: "😊", color: "#00d4aa", bg: "rgba(0,212,170,0.15)" },
        { label: "보통", labelEn: "Normal", max: 25, emoji: "🙂", color: "#ffc107", bg: "rgba(255,193,7,0.15)" },
        { label: "나쁨", labelEn: "Bad", max: 50, emoji: "😷", color: "#ff6b35", bg: "rgba(255,107,53,0.15)" },
        { label: "매우나쁨", labelEn: "Very Bad", max: 9999, emoji: "🚨", color: "#ff2d55", bg: "rgba(255,45,85,0.15)" },
    ],
    pm25: [
        { label: "좋음", labelEn: "Good", max: 15, emoji: "😊", color: "#00d4aa", bg: "rgba(0,212,170,0.15)" },
        { label: "보통", labelEn: "Normal", max: 35, emoji: "🙂", color: "#ffc107", bg: "rgba(255,193,7,0.15)" },
        { label: "나쁨", labelEn: "Bad", max: 75, emoji: "😷", color: "#ff6b35", bg: "rgba(255,107,53,0.15)" },
        { label: "매우나쁨", labelEn: "Very Bad", max: 9999, emoji: "🚨", color: "#ff2d55", bg: "rgba(255,45,85,0.15)" },
    ],
    pm4: [
        { label: "좋음", labelEn: "Good", max: 20, emoji: "😊", color: "#00d4aa", bg: "rgba(0,212,170,0.15)" },
        { label: "보통", labelEn: "Normal", max: 50, emoji: "🙂", color: "#ffc107", bg: "rgba(255,193,7,0.15)" },
        { label: "나쁨", labelEn: "Bad", max: 100, emoji: "😷", color: "#ff6b35", bg: "rgba(255,107,53,0.15)" },
        { label: "매우나쁨", labelEn: "Very Bad", max: 9999, emoji: "🚨", color: "#ff2d55", bg: "rgba(255,45,85,0.15)" },
    ],
    pm10: [
        { label: "좋음", labelEn: "Good", max: 30, emoji: "😊", color: "#00d4aa", bg: "rgba(0,212,170,0.15)" },
        { label: "보통", labelEn: "Normal", max: 80, emoji: "🙂", color: "#ffc107", bg: "rgba(255,193,7,0.15)" },
        { label: "나쁨", labelEn: "Bad", max: 150, emoji: "😷", color: "#ff6b35", bg: "rgba(255,107,53,0.15)" },
        { label: "매우나쁨", labelEn: "Very Bad", max: 9999, emoji: "🚨", color: "#ff2d55", bg: "rgba(255,45,85,0.15)" },
    ],
};

// 각 PM 타입별 차트 색상
const PM_CHART_COLORS = {
    pm1:  { border: '#f472b6', bg: 'rgba(244,114,182,0.08)' },  // 핑크
    pm25: { border: '#22c55e', bg: 'rgba(34,197,94,0.08)' },    // 초록
    pm4:  { border: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },   // 주황
    pm10: { border: '#6366f1', bg: 'rgba(99,102,241,0.08)' },   // 인디고
};

// PM 타입 메타 정보
const PM_TYPES = [
    { key: 'pm1',  label: 'PM1.0',  unit: 'μg/m³' },
    { key: 'pm25', label: 'PM2.5',  unit: 'μg/m³' },
    { key: 'pm4',  label: 'PM4.0',  unit: 'μg/m³' },
    { key: 'pm10', label: 'PM10',   unit: 'μg/m³' },
];

function getAirQuality(type, value) {
    const levels = AIR_QUALITY[type] || AIR_QUALITY.pm25;
    for (const level of levels) {
        if (value <= level.max) return level;
    }
    return levels[levels.length - 1];
}

// ─── Memo Config ───
const MEMO_PIN = '1231';
const MEMO_COLOR = '#8b5cf6'; // violet
