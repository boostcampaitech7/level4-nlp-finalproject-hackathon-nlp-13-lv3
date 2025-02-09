# fin_report_scorer_agent.py

import os
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from LangGraph_base import Node, GraphState

def safe_softmax(logits: torch.Tensor, dim: int = 0) -> torch.Tensor:
    if torch.all(torch.isinf(logits)):
        return torch.ones_like(logits) / logits.numel()
    max_val, _ = torch.max(logits, dim=dim, keepdim=True)
    if max_val.item() == -float("inf"):
        return torch.ones_like(logits) / logits.numel()
    exps = torch.exp(logits - max_val)
    sum_exps = exps.sum(dim=dim, keepdim=True)
    if sum_exps.item() == 0:
        return torch.ones_like(logits) / logits.numel()
    return exps / sum_exps

class ReportScorerAgent(Node):
    def __init__(self, name: str, eval_model: str) -> None:
        super().__init__(name)
        self.model_name = eval_model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
        self.model.to(self.device)
        self.model.eval()
        self._prepare_valid_tokens()

    def _prepare_valid_tokens(self):
        self.valid_tokens = {}
        for num in range(0, 10):
            token_str = str(num)
            token_ids = self.tokenizer.encode(token_str, add_special_tokens=False)
            if len(token_ids) != 1:
                raise ValueError(
                    f"토큰 '{token_str}'가 여러 토큰({token_ids})으로 인코딩됩니다. 모델을 재검토하세요."
                )
            self.valid_tokens[token_str] = token_ids[0]
        self.valid_token_list = [str(num) for num in range(0, 10)]
        self.numeric_values = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                                             dtype=torch.float32,
                                             device=self.device)

    @torch.no_grad()
    def process(self, state: GraphState) -> GraphState:
        """
        state["integrated_report"]에 저장된 보고서 텍스트를 평가하여,
        1~10 사이의 점수를 가중평균 방식으로 산출하고, 이를 state["report_score"]에 저장합니다.
        """
        report = state.get("integrated_report", "")
        if not report:
            state["report_score"] = 0.0
            return state

        prompt = f"""
        다음 주식 리포트가 잘 작성되어 있는지 꼼꼼하게 확인하고, 리포트의 품질을 0에서 9점 사이의 점수로 평가해주세요.\n {report}\n
        평가 점수: """  # 평가 대상 텍스트로 사용
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        outputs = self.model(**inputs)
        logits = outputs.logits[0, -1, :]  # 마지막 토큰의 logits

        token_logits = []
        for token in self.valid_token_list:
            token_id = self.valid_tokens[token]
            token_logits.append(logits[token_id])
        token_logits = torch.stack(token_logits)
        # 온도 스케일링 (여기서는 temperature=1.0)
        token_logits = token_logits / 1.0
        probs = safe_softmax(token_logits, dim=0)
        t = torch.tensor([1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                         dtype=torch.float32,
                         device=self.device)
        final_score = (probs * t).sum().item()
        state["report_score"] = final_score
        print(f"[{self.name}] 보고서 평가 점수: {final_score:.2f} / 10")
        time.sleep(0.5)
        return state

if __name__ == "__main__":
    scorer = ReportScorerAgent("ReportScorerAgent", eval_model="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
    test_report = (
        "최종 통합 보고서 예시: LG화학의 종합 평가 리포트 내용..."
    )
    state = {
        "integrated_report": test_report,
        "company_name": "LG화학" 
    }
    state = scorer.process(state)
    print("최종 평가 점수:", state.get("report_score"))
