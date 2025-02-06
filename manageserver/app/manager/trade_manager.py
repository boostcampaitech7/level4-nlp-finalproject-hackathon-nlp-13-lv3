from app.manager.trade_workflow import create_trade_workflow

class TradeManagementManager:
    def __init__(self):
        self.workflow = create_trade_workflow()

    def execute_trade(self, user_id, position, justification):
        """
        매매 로직 실행
        - 사용자 ID를 포함하여 매매 상태 전달
        """
        initial_state = {
            "user_id": user_id,             # ✅ 사용자 ID 추가
            "position": position,
            "justification": justification
        }
        final_state = self.workflow.invoke(initial_state)
        return final_state
