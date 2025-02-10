import os
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from LangGraph_base import Node, GraphState

def safe_softmax(logits: torch.Tensor, dim: int = 0) -> torch.Tensor:
    """
    안전한 softmax 연산을 수행합니다.
    
    일반적인 softmax의 숫자 불안정성 문제를 처리하여,
    inf나 -inf 값이 있는 경우에도 안전하게 확률을 계산합니다.

    Args:
        logits (torch.Tensor): 입력 로짓 텐서
        dim (int, optional): softmax를 적용할 차원. 기본값은 0

    Returns:
        torch.Tensor: 계산된 확률 분포

    Note:
        - 모든 값이 inf인 경우 균일 분포를 반환
        - 최대값이 -inf인 경우 균일 분포를 반환
        - 지수 합이 0인 경우 균일 분포를 반환
    """
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
    """
    주식 리포트의 품질을 평가하는 에이전트입니다.
    
    LLM을 사용하여 통합 리포트의 품질을 0-10점 사이의 점수로 평가합니다.
    지정된 임계값(기본값: 5점)을 넘지 못하면 품질 개선 프로세스가 시작됩니다.

    Attributes:
        name (str): 에이전트의 이름
        model_name (str): 사용할 LLM 모델의 이름
        device (str): 연산에 사용할 디바이스 ('cuda' 또는 'cpu')
        tokenizer: 텍스트 토크나이저
        model: 로드된 LLM 모델
        valid_tokens (dict): 유효한 숫자 토큰들의 매핑
    """
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
        """
        숫자 평가를 위한 토큰을 준비합니다.
        
        0-9까지의 숫자에 대한 토큰 ID를 미리 계산하고 저장하며,
        각 숫자에 대한 텐서를 준비합니다.
        
        Raises:
            ValueError: 단일 숫자가 여러 개의 토큰으로 인코딩될 경우 발생
        """
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
        통합 리포트의 품질을 평가하고 점수를 부여합니다.

        통합 리포트 텍스트를 입력받아 LLM을 통해 품질을 평가하고,
        0-10점 사이의 점수를 계산하여 state에 저장합니다.

        Args:
            state (GraphState): 현재 그래프의 상태
                필수 키:
                - integrated_report: 평가할 통합 리포트 텍스트

        Returns:
            GraphState: 업데이트된 상태
                추가되는 키:
                - report_score: 산출된 리포트 품질 점수 (float)

        Note:
            리포트가 없을 경우 0점을 부여합니다.
            점수 계산은 토큰 확률의 가중 평균을 사용합니다.
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
