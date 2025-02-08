import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from captum.attr import IntegratedGradients

def safe_softmax(logits: torch.Tensor, dim: int = 0) -> torch.Tensor:
    if torch.all(torch.isinf(logits)) or (torch.max(logits).item() == -float("inf")):
        return torch.ones_like(logits) / logits.numel()
    max_val, _ = torch.max(logits, dim=dim, keepdim=True)
    exps = torch.exp(logits - max_val)
    sum_exps = exps.sum(dim=dim, keepdim=True)
    if sum_exps.item() == 0:
        return torch.ones_like(logits) / logits.numel()
    return exps / sum_exps

class StockReportScorer:
    def __init__(self,
                 model_name: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
                 device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name,
            torch_dtype=torch.float16,
            trust_remote_code=True,
            )
        self.model = AutoModelForCausalLM.from_pretrained(model_name,
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
                raise ValueError(f"토큰 '{token_str}'가 여러 토큰({token_ids})으로 인코딩됩니다.")
            self.valid_tokens[token_str] = token_ids[0]
        self.valid_token_list = [str(num) for num in range(0, 10)]
        self.digit_values = torch.arange(0, 10, dtype=torch.float32, device=self.device)

    @torch.no_grad()
    def score_report(self, prompt: str, temperature: float = 1.0) -> float:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        outputs = self.model(**inputs)
        logits = outputs.logits[0, -1, :]
        token_logits = torch.stack([logits[self.valid_tokens[token]] for token in self.valid_token_list])
        token_logits = token_logits / temperature
        probs = safe_softmax(logits=token_logits, dim=0)
        final_score = (probs * self.digit_values).sum().item() + 1
        return final_score


def forward_from_embeds(embedded_inputs):
    # 자동 혼합 정밀도 사용 (권장 device_type 인수 사용)
    with torch.amp.autocast(device_type="cuda"):
        outputs = scorer.model(inputs_embeds=embedded_inputs)
    # 마지막 토큰의 logits 추출
    logits = outputs.logits[0, -1, :]  
    token_logits = torch.stack([logits[scorer.valid_tokens[token]] for token in scorer.valid_token_list])
    probs = safe_softmax(logits=token_logits, dim=0)
    final_score = (probs * scorer.digit_values).sum()
    # 최종 스칼라 값을 (1, 1) 텐서로 반환 (이렇게 하면 target column 선택이 가능해집니다)
    return final_score.unsqueeze(0).unsqueeze(0)

def group_attributions_by_paragraph(tokens, attributions_sum, tokenizer):
    """
    tokens: tokenizer.convert_ids_to_tokens()로 얻은 토큰 리스트
    attributions_sum: 각 토큰에 대한 attribution (이미 임베딩 차원 합산된 값)
    tokenizer: 해당 모델의 토크나이저 (문자열 디코딩을 위해 사용)
    """
    paragraphs = []
    para_attr = []
    current_tokens = []
    current_sum = 0.0

    # 토큰 리스트를 순회하면서, 토큰에 "\n" 문자가 포함되면 문단 구분으로 간주
    for token, attr in zip(tokens, attributions_sum):
        current_tokens.append(token)
        current_sum += attr.item()
        # 토큰에 줄바꿈 문자가 포함된 경우 문단 경계를 감지
        if "####" in token:
            paragraph = tokenizer.convert_tokens_to_string(current_tokens)
            if paragraph.strip():
                paragraphs.append(paragraph)
                para_attr.append(current_sum)
            current_tokens = []
            current_sum = 0.0

    # 마지막에 남은 토큰 처리
    if current_tokens:
        paragraph = tokenizer.convert_tokens_to_string(current_tokens)
        if paragraph.strip():
            paragraphs.append(paragraph)
            para_attr.append(current_sum)
    
    if len(paragraphs) > 2:
        return paragraphs[1:-1], para_attr[1:-1]
    else:
        return paragraphs, para_attr

"""
사용가능한 모델 리스트
1.deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
2.LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct
3.deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
"""
scorer = StockReportScorer(
    model_name="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    device="cuda"
)

prompt = (
     "다음 주식 리포트가 잘 작성되어 있는지 꼼꼼하게 확인하고, 리포트의 품질을 0에서 9점 사이의 점수로 평가해주세요.\n\n"
        #f"{report.content}\n\n"
        """
        ### LG화학 종합 평가 리포트

---

#### 1. 핵심 사업 및 경쟁력

LG화학은 전통적인 화학 사업을 기반으로 다양한 사업 영역을 확장해 왔으나, 최근 에스테틱 사업부의 매각 추진과 생명과학 분야 강화 전략을 통해 포트폴리오를 재편하고 있습니다. 에스테틱 사업부 매각은 기업의 핵심 역량을 재집중시키는 움직임으로 해석될 수 있으나, 단기적으로는 사업 재편 과정에서의 불확실성과 비용이 발생할 수 있습니다. 네이트 뉴스, 블로터, 이데일리 등 여러 뉴스 매체에서 보도된 바와 같이 에스테틱 사업부 매각과 관련된 실적 악화 및 성과급 축소 소식은 기업 내부의 구조 조정이 진행 중임을 시사하며, 이는 단기적인 투자자 신뢰도에 부정적인 영향을 미칠 수 있습니다.

그럼에도 불구하고, 생명과학 분야로의 집중은 미래 성장 가능성을 높이는 긍정적인 전략으로 평가됩니다. 특히, HSBC증권의 주관사 선정과 함께 전문성을 강화하는 움직임은 장기적인 시장 경쟁력 확보에 기여할 것으로 기대됩니다. 그러나 현재의 실적 악화와 같은 구조적 문제는 이러한 전략의 성공적인 실행을 위해 해결되어야 할 중요한 과제로 남아 있습니다.

#### 2. 거시경제적 환경과 시장 전망

현재 한국 경제는 원화 약세와 금리 상승이라는 두 축의 거시경제적 압력을 받고 있습니다. USD/KRW 환율이 1,456.30으로 소폭 상승하면서 원화 약세가 지속되고 있는 가운데, 이는 수입 원자재 비용 상승으로 이어져 LG화학의 원가 부담을 증가시키고 있습니다. 원자재 가격의 안정세에도 불구하고, 원화 약세와 금리 인상은 기업의 차입 비용을 증가시키며, 이는 전반적인 재무 건전성에 부정적인 영향을 미칠 수 있습니다.

특히, 미국과 한국의 국채 금리가 상승하고 있는 상황에서 금리 인상은 주식 시장의 매력도를 낮추고 투자 자금을 채권 시장으로 유입시키는 경향이 있습니다. 금리 상승은 LG화학과 같은 고부채 기업의 자금 조달 비용을 증가시켜 재무 부담을 가중시킬 수 있으며, 이는 주가에 추가적인 하방 압력을 제공할 가능성이 있습니다.

또한, 글로벌 경제 불확실성과 경기 사이클의 변화는 LG화학의 수출 주도형 사업 모델에 영향을 미칠 수 있습니다. 원화 약세는 수출 기업에 긍정적인 영향을 미치지만, 글로벌 경기 둔화는 수요 감소로 이어질 가능성이 있어 주의가 필요합니다.

#### 3. 최근 뉴스나 이슈가 가져올 파급효과

최근 보도된 LG화학의 실적 악화와 에스테틱 사업부 매각 추진은 기업 실적과 이미지에 중대한 영향을 미칠 수 있습니다.

1. **실적 악화 및 순손실 발표**: 4분기 영업손실 2,272억 원과 순손실 소식은 투자자들에게 부정적인 신호로 작용하며, 주가 하락의 주요 원인으로 작용할 수 있습니다. 이러한 실적 악화는 기업의 운영 효율성 저하와 매출 감소를 반영하며, 단기적인 투자 심리를 위축시킬 수 있습니다.

2. **성과급 축소**: 성과급 축소는 직원들의 사기 저하와 생산성 저하로 이어질 우려가 있습니다. 이는 장기적으로 기업의 혁신 역량과 경쟁력에 부정적인 영향을 미칠 수 있습니다.

3. **사업 매각 추진**: 에스테틱 사업부 매각은 기업의 핵심 사업 재편의 일환으로 긍정적인 신호로 보이지만, 매각 과정의 불확실성과 성공적인 매각 완료까지의 시간적인 여유가 필요합니다. 또한, 매각 후 생명과학 분야로의 집중이 얼마나 효과적으로 이루어질지가 향후 성장에 중요한 변수로 작용할 것입니다.

4. **트럼프 리스크**: 글로벌 정치 리스크, 특히 트럼프와 같은 외부 요인으로 인한 손실 가능성은 기업의 재무 안정성에 추가적인 불확실성을 제공합니다. 이는 투자자들에게 추가적인 리스크 요인으로 작용하여 주가에 부정적인 영향을 미칠 수 있습니다.

이러한 이슈들은 단기적으로 LG화학의 주가에 부정적인 영향을 미칠 가능성이 크며, 시장 심리에 큰 영향을 미치는 요소로 작용하고 있습니다.

#### 4. 재무 상태

LG화학의 최근 재무제표 분석 결과, 기업은 심각한 재무적 어려움을 겪고 있습니다.

- **부채비율**: 2023년 부채비율이 40.15%로 감소했으나, 이는 2022년의 44.86%에 비해 개선된 수치이나 여전히 낮은 수준을 유지하고 있습니다. 이는 장기적인 재무 건전성에는 긍정적이나, 단기적인 유동성 확보에는 어려움이 존재합니다.
  
- **이자보상배율**: -0.8%로, 이자비용을 감당할 수 없는 상황입니다. 이는 영업이익의 적자 전환으로 인해 이자 지급 능력이 현저히 부족함을 나타내며, 신용 등급 하락 및 추가적인 자금 조달의 어려움을 초래할 수 있습니다.

- **수익성 지표**:
  - **ROE**: 1.12%로 크게 하락하여 주주에게 돌아가는 수익이 현저히 감소했습니다.
  - **ROA**: 0.67%로 자산을 활용한 수익 창출 능력이 저하되었습니다.
  - **영업이익**: 2023년 영업이익이 -1,091억 원으로 적자 전환, 운영 효율성 저하를 반영합니다.
  - **매출**: 2023년 매출액이 2022년 대비 절반으로 급감, 성장성 큰 저하.

- **유동성 지표**:
  - **유동비율**: 131.02%로 여전히 단기 채무를 감당 가능하지만, 2022년에 비해 크게 감소하여 유동성 악화를 시사합니다.
  - **매출채권회전율**: 안정적인 수준을 유지하고 있으나, 이는 매출 감소와 맞물려 전반적인 활동성 저하를 보완하지는 못합니다.

종합적으로, LG화학은 지속적인 영업적자와 매출 감소, 이자 지급 능력 부족 등의 문제로 심각한 재무적 위험에 직면해 있습니다. 이러한 상황에서는 단기적인 투자보다 장기적인 회복 가능성을 신중히 고려할 필요가 있습니다.

#### 5. 기술적 분석 요약

LG화학의 최근 주가 흐름과 기술적 지표를 종합적으로 분석한 결과, 다음과 같은 시사점을 도출할 수 있습니다.

- **주요 지지선과 저항선**:
  - **일봉**: 지지선 217,000원, 저항선 222,000원. 현재가가 지지선 근처에 위치하여 매수 타이밍으로 활용 가능.
  - **월봉**: 지지선 250,000원, 저항선 287,500원. 장기적으로는 월봉 저항선 돌파 시 추가 상승 가능성.

- **거래량**: 최근 거래량 증가(322,872주 vs. 224,642주)는 매수세 강화 신호로 해석됩니다.

- **기술적 지표**:
  - **이동평균선**: 20일 이동평균선 상승세, 단기 상승 추세 유지.
  - **RSI**: 55로 과매도 구간에 진입하지 않아 추가 상승 여력 존재.
  - **MACD**: 신호선 상향 돌파, 상승 신호.
  - **다우 이론 및 엘리어트 이론**: 상승 추세 확인 및 5파 상승 마지막 단계 진입, 추가 상승 예상.

- **투자 타이밍**:
  - **추천 구매 가격**: 215,000원 (지지선 아래 설정)
  - **추천 익절 가격**: 225,000원 (저항선 근처)
  - **추천 손절 가격**: 210,000원 (지지선 아래)

- **전망**:
  - **단기**: 1-2주 내 220,000원까지 상승 가능성 높음.
  - **중기**: 2-3개월 내 250,000원까지 상승 예상.
  - **장기**: 6개월 이상 300,000원 도달 가능성 있음.

기술적 분석에서는 주가 상승 신호가 다수 포착되었으나, 재무적 리스크와 시장 심리의 변동 가능성을 감안할 때 신중한 접근이 요구됩니다.

#### 결론 및 투자 추천

LG화학은 현재 심각한 재무적 어려움과 실적 악화를 겪고 있으며, 외부 리스크 요인 또한 다수 존재합니다. 그러나 기술적 분석에서는 단기적인 상승 가능성이 확인되고 있어, 일부 투자자들에게는 매수 기회로 해석될 수 있습니다. 

**종합 투자 의견**: **신중한 매수**가 필요합니다. 재무적 리스크와 단기적인 실적 악화를 고려할 때, 단기적인 기술적 상승 신호를 활용한 매수 전략은 가능하지만, 장기적인 재무 구조 개선과 실적 회복이 이루어지지 않는 한 높은 투자 위험을 수반합니다. 따라서 리스크 관리와 함께 포트폴리오 다각화를 통해 투자하는 것이 바람직합니다.

---

**주의사항**: 본 리포트는 제공된 자료를 기반으로 작성되었으며, 실제 투자 결정 시 추가적인 정보와 전문가의 조언을 참고하시기 바랍니다.
===== 최종 보고서 =====
최종 매매의견: 매수, 자산 배분 제안: 사용 가능한 자본의 10% 매수
        """
        "평가 점수:"
)

prompt2=("""
        ### LG화학 종합 평가 리포트

---

#### 1. 핵심 사업 및 경쟁력

LG화학은 전통적인 화학 사업을 기반으로 다양한 사업 영역을 확장해 왔으나, 최근 에스테틱 사업부의 매각 추진과 생명과학 분야 강화 전략을 통해 포트폴리오를 재편하고 있습니다. 에스테틱 사업부 매각은 기업의 핵심 역량을 재집중시키는 움직임으로 해석될 수 있으나, 단기적으로는 사업 재편 과정에서의 불확실성과 비용이 발생할 수 있습니다. 네이트 뉴스, 블로터, 이데일리 등 여러 뉴스 매체에서 보도된 바와 같이 에스테틱 사업부 매각과 관련된 실적 악화 및 성과급 축소 소식은 기업 내부의 구조 조정이 진행 중임을 시사하며, 이는 단기적인 투자자 신뢰도에 부정적인 영향을 미칠 수 있습니다.

그럼에도 불구하고, 생명과학 분야로의 집중은 미래 성장 가능성을 높이는 긍정적인 전략으로 평가됩니다. 특히, HSBC증권의 주관사 선정과 함께 전문성을 강화하는 움직임은 장기적인 시장 경쟁력 확보에 기여할 것으로 기대됩니다. 그러나 현재의 실적 악화와 같은 구조적 문제는 이러한 전략의 성공적인 실행을 위해 해결되어야 할 중요한 과제로 남아 있습니다.

#### 2. 거시경제적 환경과 시장 전망

현재 한국 경제는 원화 약세와 금리 상승이라는 두 축의 거시경제적 압력을 받고 있습니다. USD/KRW 환율이 1,456.30으로 소폭 상승하면서 원화 약세가 지속되고 있는 가운데, 이는 수입 원자재 비용 상승으로 이어져 LG화학의 원가 부담을 증가시키고 있습니다. 원자재 가격의 안정세에도 불구하고, 원화 약세와 금리 인상은 기업의 차입 비용을 증가시키며, 이는 전반적인 재무 건전성에 부정적인 영향을 미칠 수 있습니다.

특히, 미국과 한국의 국채 금리가 상승하고 있는 상황에서 금리 인상은 주식 시장의 매력도를 낮추고 투자 자금을 채권 시장으로 유입시키는 경향이 있습니다. 금리 상승은 LG화학과 같은 고부채 기업의 자금 조달 비용을 증가시켜 재무 부담을 가중시킬 수 있으며, 이는 주가에 추가적인 하방 압력을 제공할 가능성이 있습니다.

또한, 글로벌 경제 불확실성과 경기 사이클의 변화는 LG화학의 수출 주도형 사업 모델에 영향을 미칠 수 있습니다. 원화 약세는 수출 기업에 긍정적인 영향을 미치지만, 글로벌 경기 둔화는 수요 감소로 이어질 가능성이 있어 주의가 필요합니다.

#### 3. 최근 뉴스나 이슈가 가져올 파급효과

최근 보도된 LG화학의 실적 악화와 에스테틱 사업부 매각 추진은 기업 실적과 이미지에 중대한 영향을 미칠 수 있습니다.

1. **실적 악화 및 순손실 발표**: 4분기 영업손실 2,272억 원과 순손실 소식은 투자자들에게 부정적인 신호로 작용하며, 주가 하락의 주요 원인으로 작용할 수 있습니다. 이러한 실적 악화는 기업의 운영 효율성 저하와 매출 감소를 반영하며, 단기적인 투자 심리를 위축시킬 수 있습니다.

2. **성과급 축소**: 성과급 축소는 직원들의 사기 저하와 생산성 저하로 이어질 우려가 있습니다. 이는 장기적으로 기업의 혁신 역량과 경쟁력에 부정적인 영향을 미칠 수 있습니다.

3. **사업 매각 추진**: 에스테틱 사업부 매각은 기업의 핵심 사업 재편의 일환으로 긍정적인 신호로 보이지만, 매각 과정의 불확실성과 성공적인 매각 완료까지의 시간적인 여유가 필요합니다. 또한, 매각 후 생명과학 분야로의 집중이 얼마나 효과적으로 이루어질지가 향후 성장에 중요한 변수로 작용할 것입니다.

4. **트럼프 리스크**: 글로벌 정치 리스크, 특히 트럼프와 같은 외부 요인으로 인한 손실 가능성은 기업의 재무 안정성에 추가적인 불확실성을 제공합니다. 이는 투자자들에게 추가적인 리스크 요인으로 작용하여 주가에 부정적인 영향을 미칠 수 있습니다.

이러한 이슈들은 단기적으로 LG화학의 주가에 부정적인 영향을 미칠 가능성이 크며, 시장 심리에 큰 영향을 미치는 요소로 작용하고 있습니다.

#### 4. 재무 상태

LG화학의 최근 재무제표 분석 결과, 기업은 심각한 재무적 어려움을 겪고 있습니다.

- **부채비율**: 2023년 부채비율이 40.15%로 감소했으나, 이는 2022년의 44.86%에 비해 개선된 수치이나 여전히 낮은 수준을 유지하고 있습니다. 이는 장기적인 재무 건전성에는 긍정적이나, 단기적인 유동성 확보에는 어려움이 존재합니다.
  
- **이자보상배율**: -0.8%로, 이자비용을 감당할 수 없는 상황입니다. 이는 영업이익의 적자 전환으로 인해 이자 지급 능력이 현저히 부족함을 나타내며, 신용 등급 하락 및 추가적인 자금 조달의 어려움을 초래할 수 있습니다.

- **수익성 지표**:
  - **ROE**: 1.12%로 크게 하락하여 주주에게 돌아가는 수익이 현저히 감소했습니다.
  - **ROA**: 0.67%로 자산을 활용한 수익 창출 능력이 저하되었습니다.
  - **영업이익**: 2023년 영업이익이 -1,091억 원으로 적자 전환, 운영 효율성 저하를 반영합니다.
  - **매출**: 2023년 매출액이 2022년 대비 절반으로 급감, 성장성 큰 저하.

- **유동성 지표**:
  - **유동비율**: 131.02%로 여전히 단기 채무를 감당 가능하지만, 2022년에 비해 크게 감소하여 유동성 악화를 시사합니다.
  - **매출채권회전율**: 안정적인 수준을 유지하고 있으나, 이는 매출 감소와 맞물려 전반적인 활동성 저하를 보완하지는 못합니다.

종합적으로, LG화학은 지속적인 영업적자와 매출 감소, 이자 지급 능력 부족 등의 문제로 심각한 재무적 위험에 직면해 있습니다. 이러한 상황에서는 단기적인 투자보다 장기적인 회복 가능성을 신중히 고려할 필요가 있습니다.

#### 5. 기술적 분석 요약

LG화학의 최근 주가 흐름과 기술적 지표를 종합적으로 분석한 결과, 다음과 같은 시사점을 도출할 수 있습니다.

- **주요 지지선과 저항선**:
  - **일봉**: 지지선 217,000원, 저항선 222,000원. 현재가가 지지선 근처에 위치하여 매수 타이밍으로 활용 가능.
  - **월봉**: 지지선 250,000원, 저항선 287,500원. 장기적으로는 월봉 저항선 돌파 시 추가 상승 가능성.

- **거래량**: 최근 거래량 증가(322,872주 vs. 224,642주)는 매수세 강화 신호로 해석됩니다.

- **기술적 지표**:
  - **이동평균선**: 20일 이동평균선 상승세, 단기 상승 추세 유지.
  - **RSI**: 55로 과매도 구간에 진입하지 않아 추가 상승 여력 존재.
  - **MACD**: 신호선 상향 돌파, 상승 신호.
  - **다우 이론 및 엘리어트 이론**: 상승 추세 확인 및 5파 상승 마지막 단계 진입, 추가 상승 예상.

- **투자 타이밍**:
  - **추천 구매 가격**: 215,000원 (지지선 아래 설정)
  - **추천 익절 가격**: 225,000원 (저항선 근처)
  - **추천 손절 가격**: 210,000원 (지지선 아래)

- **전망**:
  - **단기**: 1-2주 내 220,000원까지 상승 가능성 높음.
  - **중기**: 2-3개월 내 250,000원까지 상승 예상.
  - **장기**: 6개월 이상 300,000원 도달 가능성 있음.

기술적 분석에서는 주가 상승 신호가 다수 포착되었으나, 재무적 리스크와 시장 심리의 변동 가능성을 감안할 때 신중한 접근이 요구됩니다.

#### 결론 및 투자 추천

LG화학은 현재 심각한 재무적 어려움과 실적 악화를 겪고 있으며, 외부 리스크 요인 또한 다수 존재합니다. 그러나 기술적 분석에서는 단기적인 상승 가능성이 확인되고 있어, 일부 투자자들에게는 매수 기회로 해석될 수 있습니다. 

**종합 투자 의견**: **신중한 매수**가 필요합니다. 재무적 리스크와 단기적인 실적 악화를 고려할 때, 단기적인 기술적 상승 신호를 활용한 매수 전략은 가능하지만, 장기적인 재무 구조 개선과 실적 회복이 이루어지지 않는 한 높은 투자 위험을 수반합니다. 따라서 리스크 관리와 함께 포트폴리오 다각화를 통해 투자하는 것이 바람직합니다.

---""")

inputs = scorer.tokenizer(prompt2, return_tensors="pt")
input_ids = inputs["input_ids"].to(scorer.device)
embedded_inputs = scorer.model.get_input_embeddings()(input_ids)

ig = IntegratedGradients(forward_from_embeds)
baseline = torch.zeros_like(embedded_inputs)

# n_steps와 internal_batch_size를 줄여서 메모리 사용 최적화
attributions, delta = ig.attribute(
    embedded_inputs,
    baseline,
    target=0,
    n_steps=10,
    internal_batch_size=1,
    return_convergence_delta=True
)

torch.cuda.empty_cache()

attributions_sum = attributions.sum(dim=-1).squeeze(0)
tokens = scorer.tokenizer.convert_ids_to_tokens(input_ids.squeeze(0))

# 예시: Integrated Gradients 계산 후 문단 단위로 그룹화하기
sentences, sentence_attr = group_attributions_by_paragraph(tokens, attributions_sum, scorer.tokenizer)
print("\n문단별 Attribution 합계:")
for p, a in zip(sentences, sentence_attr):
    print(f"Paragraph: {p}\nAttribution Sum: {a:.4f}\n")

# 가장 부정적인 기여를 보인 문단 출력
min_index = sentence_attr.index(min(sentence_attr))
print("=== 최종 평가 점수가 낮은 원인을 추정한 결과 (문단 단위) ===")
print(f"가장 부정적인 기여를 보인 문단: {sentences[min_index]}")
print(f"해당 문단의 Attribution 합계: {sentence_attr[min_index]:.4f}")

final_score = scorer.score_report(prompt, temperature=1.0)
print(f"\n최종 평가 점수: {final_score:.2f} / 10")
