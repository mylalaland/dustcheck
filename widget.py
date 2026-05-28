import tkinter as tk
import requests
import threading
import time
import urllib3

# Disable SSL warnings for self-signed certificates in corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Firebase URL (웹 대시보드와 동일한 실시간 데이터 노드)
FIREBASE_URL = "https://dustcheck-da9e1-default-rtdb.firebaseio.com/latest.json"
UPDATE_INTERVAL = 10  # 10초마다 업데이트

class DustWidget(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("DustCheck Widget")
        
        # 창 설정: 항상 위, 타이틀바 숨김, 투명도
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.attributes("-alpha", 0.9)
        self.configure(bg="#1a1d2e")

        # 초기 위치 및 크기
        self.geometry("200x140+100+100")

        # 마우스 드래그 이동을 위한 변수
        self._offsetx = 0
        self._offsety = 0
        self.bind("<Button-1>", self.clickwin)
        self.bind("<B1-Motion>", self.dragwin)
        
        # 우클릭 시 종료 메뉴
        self.bind("<Button-3>", self.show_menu)
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="닫기 (Exit)", command=self.destroy)

        # UI 요소 생성
        self.create_widgets()

        # 백그라운드 업데이트 쓰레드 시작
        self.running = True
        self.update_thread = threading.Thread(target=self.fetch_data_loop, daemon=True)
        self.update_thread.start()

    def clickwin(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def dragwin(self, event):
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        self.geometry(f"+{x}+{y}")

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def create_widgets(self):
        # 닫기 버튼 (우상단)
        close_btn = tk.Label(self, text="×", fg="#9ca0b4", bg="#1a1d2e", font=("Helvetica", 14, "bold"), cursor="hand2")
        close_btn.place(x=175, y=5)
        close_btn.bind("<Button-1>", lambda e: self.destroy())

        # 타이틀
        tk.Label(self, text="실내 공기질", fg="#9ca0b4", bg="#1a1d2e", font=("Malgun Gothic", 9, "bold")).place(x=15, y=10)

        # PM2.5
        self.lbl_pm25 = tk.Label(self, text="PM2.5: -- μg/m³", fg="#f0f0f5", bg="#1a1d2e", font=("Helvetica", 16, "bold"))
        self.lbl_pm25.place(x=15, y=35)
        
        # PM1.0
        self.lbl_pm1 = tk.Label(self, text="PM1.0: -- μg/m³", fg="#9ca0b4", bg="#1a1d2e", font=("Helvetica", 11))
        self.lbl_pm1.place(x=15, y=65)

        # 등급 배지
        self.lbl_grade = tk.Label(self, text="대기중", fg="#ffffff", bg="#8b5cf6", font=("Malgun Gothic", 9, "bold"), padx=6, pady=2)
        self.lbl_grade.place(x=15, y=105)

        # 업데이트 시간
        self.lbl_time = tk.Label(self, text="최근: --:--", fg="#64687d", bg="#1a1d2e", font=("Malgun Gothic", 8))
        self.lbl_time.place(x=120, y=110)

    def get_grade_info(self, pm25):
        if pm25 <= 15:
            return "좋음", "#3b82f6"     # Blue
        elif pm25 <= 35:
            return "보통", "#10b981"     # Green
        elif pm25 <= 75:
            return "나쁨", "#f59e0b"     # Orange
        else:
            return "매우나쁨", "#ef4444" # Red

    def update_ui(self, data):
        if not data:
            return
            
        pm25 = data.get('pm25', 0)
        pm1 = data.get('pm1', 0)
        time_str = data.get('time', '').split(' ')[-1][:5] if data.get('time') else "--:--"

        grade_text, grade_color = self.get_grade_info(pm25)

        # Update texts
        self.lbl_pm25.config(text=f"PM2.5: {pm25:.1f} μg/m³")
        self.lbl_pm1.config(text=f"PM1.0: {pm1:.1f} μg/m³")
        
        self.lbl_grade.config(text=grade_text, bg=grade_color)
        self.lbl_time.config(text=f"최근: {time_str}")

    def fetch_data_loop(self):
        while self.running:
            try:
                # 파이와 윈도우가 같은 망에 있든 없든, Firebase를 통하면 가장 안정적으로 최신값 확인 가능
                response = requests.get(FIREBASE_URL, timeout=5, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    # UI 업데이트는 메인 쓰레드에서 실행
                    self.after(0, self.update_ui, data)
            except Exception as e:
                print("Error fetching data:", e)
            
            time.sleep(UPDATE_INTERVAL)

    def destroy(self):
        self.running = False
        super().destroy()

if __name__ == "__main__":
    app = DustWidget()
    app.mainloop()
