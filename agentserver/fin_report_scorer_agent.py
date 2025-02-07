from transformers import AutoTokenizer, AutoModelForCausalLM
from LangGraph_base import Node, GraphState 

import torch
import time

def safe_softmax(logits: torch.Tensor, dim: int = 0) -> torch.Tensor:
    """
    logits에 대해 안정적인 softmax를 계산합니다.
    만약 logits가 모두 -inf이거나, 지수값의 합이 0인 경우 균등분포를 반환합니다.
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
    def __init__(self, name: str,  eval_model: str) -> None:
        super().__init__(name)
        """
        주식 리포트를 평가할 모델과 토크나이저를 초기화합니다.
        
        "1" ~ "10"으로 제시할시 "10"이 단일 토큰으로 인식되지 않습니다.
        그러므로 숫자 "0" ~ "9"가 단일 토큰으로 인코딩되는지를 확인합니다.
        """
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
        숫자 "0"부터 "9"까지에 해당하는 토큰 ID를 미리 구합니다.
        모델마다 다르게 인코딩될 수 있으므로 단일 토큰임을 확인합니다.
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
        # 평가 순서를 위한 리스트와 실제 숫자 값 (GPU(device)에 맞게 생성)
        self.valid_token_list = [str(num) for num in range(0, 10)]
        self.numeric_values = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=torch.float32, device=self.device)

    @torch.no_grad()
    def process(self, state: GraphState) -> GraphState: 
        # prompt: str, temperature: float = 1.0) -> float:
        """
        주어진 주식 리포트(prompt)를 평가하여 0~9 사이의 점수를 가중평균 방식으로 계산합니다.
        모델의 forward pass를 통해 다음 토큰의 logits를 직접 얻어 사용합니다.
        """
        report = state.get("final_report")
        prompt = state.get("eval_prompt")
        temperature = state.get("temperature")

        # 프롬프트를 토큰화한 후, device에 맞게 변환
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 모델의 forward pass를 이용해 전체 시퀀스의 logits를 계산합니다.
        outputs = self.model(**inputs)

        # 마지막 토큰의 logits (배치 내 첫 예시)
        logits = outputs.logits[0, -1, :]  # shape: (vocab_size,)

        # "1"부터 "5"까지에 해당하는 토큰의 logits를 추출합니다.
        token_logits = []
        for token in self.valid_token_list:
            token_id = self.valid_tokens[token]
            token_logits.append(logits[token_id])
        token_logits = torch.stack(token_logits)  # shape: (10,)

        # 온도 스케일링 (필요시)
        token_logits = token_logits / temperature

        # 안전한 softmax 적용: 만약 모든 값이 -inf라면 균등분포를 반환함
        probs = safe_softmax(logits=token_logits, dim=0)

        #1~10으로 점수 스케일링
        t=torch.tensor([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=torch.float32, device=self.device)

        # 가중평균 계산: 각 숫자(1~10)와 해당 확률의 곱의 합산
        final_score = (probs * t).sum().item()

        state["report_score"] = final_score
        
        time.sleep(0.5)
        return state

# 사용 예시 --------------------------------------------------------------
if __name__ == "__main__":
    """
    사용가능한 모델 리스트
    1.deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
    2.LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct
    3.deepseek-ai/DeepSeek-R1-Distill-Qwen-7B

    model_name에 작성하시면 모델 변경 가능합니다.
    """

