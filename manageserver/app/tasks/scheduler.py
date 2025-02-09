import schedule
import time
from app.services.kakao_notification import KakaoNotification


class Scheduler:
    """ 스케줄링 기능 """

    def __init__(self):
        self.kakao_notifier = KakaoNotification()

    def send_scheduled_notifications(self):
        """ 스케줄링된 주식 정보를 카카오톡으로 전송 """
        # DB에서 관심 주식 목록 조회
        interests = self.kakao_notifier.db.get_interested_stocks()
        if not interests:
            print("📌 [INFO] 관심 주식이 없습니다.")
            return

        for user_id, stock_code in interests:
            self.kakao_notifier.send_trade_request(stock_code)
            print(f"📢 [SCHEDULE] {user_id}님에게 {stock_code}의 정보를 전송했습니다.")

    def schedule_notifications(self):
        """ 매일 12시, 6시, 9시에 알림 전송 """
        schedule.every().day.at("12:00").do(self.send_scheduled_notifications)
        schedule.every().day.at("18:00").do(self.send_scheduled_notifications)
        schedule.every().day.at("21:00").do(self.send_scheduled_notifications)

        print("📌 [INFO] 스케줄링 시작...")
        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    Scheduler().schedule_notifications()
