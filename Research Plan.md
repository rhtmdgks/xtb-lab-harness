You are an expert AI research-system architect and coding agent. Your task is to understand, design, and implement an R&E prototype titled **“LLM MAS-based xTB Tool Scientific Agent System”**.

This project is not a generic experiment-recommendation chatbot. It is a **tool-augmented scientific multi-agent system** that uses **only one external computation tool: xTB Tool**. The LLM-based multi-agent system must analyze an experiment objective, evaluate candidate materials using xTB calculation results, and generate a structured experiment design report.

The system scope is strictly defined as follows:

- Use **LLM MAS + xTB Tool only**.
- Do **not** use RDKit, Open Babel, Avogadro, PySCF, Psi4, ORCA, Gaussian, OpenMM, GROMACS, LAMMPS, or any additional simulation/chemistry tool.
- Do **not** add extra calculators or custom physics engines unless explicitly instructed later.
- Candidate materials are assumed to be provided as pre-prepared `.xyz` molecular structure files.
- xTB Tool is responsible for computational chemistry calculations only.
- LLM agents are responsible for interpretation, validation, ranking, and report generation.

The xTB Tool must support the following core operations:

1. Run geometry optimization on a given `.xyz` file.
2. Extract total energy from xTB output.
3. Extract charge distribution or charge summary from xTB output.
4. Extract dipole moment if available from xTB output.
5. Return all parsed values in structured JSON.
6. Preserve raw output references or logs for evidence tracking.

## 0. 최종 결론

**툴 구성은 `LLM MAS + xTB Tool` 단일 구조로 확정한다.**

즉, RDKit, Open Babel, Avogadro, PySCF, Psi4, ORCA, 별도 Custom Calculator는 MVP 범위에서 제외한다.

최종 포지션은 다음이다.

> **LLM 기반 멀티에이전트 시스템이 실험 목적을 분석하고, xTB Tool만을 호출하여 후보 물질의 구조 안정성, 에너지, 전하 분포, 쌍극자 모멘트 등 계산화학적 지표를 산출한 뒤, 전문 에이전트들이 이를 검토하여 실험 후보 물질과 실험 설계 보고서를 생성하는 시스템**

핵심은 “여러 툴을 연결한 복잡한 자동화”가 아니다.  
**xTB 하나를 깊게 래핑하고, MAS가 계산 결과를 해석·검증·보고서화하는 구조**다.

---

# 1. 최종 연구 주제

## 추천 제목

> **xTB Tool 기반 계산화학 결과와 멀티에이전트 검증을 활용한 실험 후보 물질 추천 시스템 개발**

조금 더 고급스럽게 쓰면:

> **LLM MAS-based xTB Tool을 활용한 후보 물질 선별 및 실험 설계 자동화 연구**

UNIST R&E용으로는 첫 번째가 더 안전하다.

> **xTB Tool 기반 계산화학 결과와 멀티에이전트 검증을 활용한 실험 후보 물질 추천 시스템 개발**

이 제목은 과장 없이 기술 구조가 명확하다.

---

# 2. 최종 시스템명

## 추천 이름

> **xTB Lab Harness**

또는

> **xTB-MAS Lab**

내 추천은 **xTB Lab Harness**다.

이름의 의미는 명확하다.

- **xTB**: 계산화학 엔진
    
- **Lab**: 실험 설계 영역
    
- **Harness**: 통제·검증·보고서화 시스템
    

---

# 3. 핵심 문제 정의

## Problem

- 실험 후보 물질을 선정할 때 연구자는 선행연구, 물성, 안전성, 실험 가능성, 변인통제 가능성을 동시에 고려해야 한다.
    
- 그러나 실제 R&E나 탐구 실험에서는 후보 물질 선정이 직관, 단순 검색, 기존 사례 모방에 의존하는 경우가 많다.
    
- 일반 LLM은 후보 물질을 추천할 수 있지만, 실제 분자의 구조 안정성, 전하 분포, 쌍극자 모멘트, 에너지 차이 등 계산화학적 근거 없이 그럴듯한 설명을 생성할 위험이 있다.
    
- 특히 실험 효과가 잘 나타날 가능성이 높은 물질을 고르려면, 물질의 작용 가능성을 정량적 계산 결과와 연결해야 한다.
    
- 따라서 단일 LLM 답변이 아니라, **xTB 계산 결과를 기반으로 멀티에이전트가 후보 물질을 검증하는 구조**가 필요하다.
    

---

# 4. 최종 Solution

## Solution

- 사용자가 실험 목적을 입력하면 LLM Orchestrator가 실험 목적을 분석한다.
    
- Candidate Material Agent가 후보 물질군을 제안한다.
    
- xTB Tool은 각 후보 물질에 대해 구조 최적화, 에너지, 전하 분포, 쌍극자 모멘트 등 계산화학적 지표를 산출한다.
    
- 전문 에이전트들은 xTB 계산 결과를 각자의 기준으로 검토한다.
    
- Orchestrator는 에이전트별 평가를 종합하여 최종 후보 물질 랭킹과 실험 설계 보고서를 생성한다.
    

핵심 구조는 다음이다.

```text
LLM MAS
+ xTB Tool
+ Agent Validation
+ Report Generation
```

---

# 5. 왜 xTB Tool 하나로 가는가

## xTB 단일 Tool 확정 사유

|기준|판단|
|---|---|
|무료 사용 가능성|적합|
|계산화학 R&E 적합성|높음|
|후보 물질 다수 비교|적합|
|MCP/Tool 래핑 난이도|낮음|
|CLI 기반 자동화|적합|
|UNIST용 기술성|충분|
|시스템 복잡도|통제 가능|
|실패 리스크|낮아짐|
|보고서 설득력|높음|

여러 계산 도구를 붙이면 시스템은 화려해지지만, R&E에서는 구현 리스크가 커진다.  
반대로 xTB Tool 하나로 제한하면 연구 질문이 선명해진다.

> **“xTB 계산 결과를 LLM MAS가 얼마나 잘 해석하고 후보 물질 추천에 활용할 수 있는가?”**

이게 핵심 연구 질문이 된다.

---

# 6. 최종 아키텍처

```text
[사용자 실험 목적 입력]
        ↓
[Orchestrator Agent]
        ↓
[Hypothesis Agent]
        ↓
[Candidate Material Agent]
        ↓
[xTB Tool]
        ├─ 구조 최적화
        ├─ 총 에너지 계산
        ├─ 전하 분포 계산
        ├─ 쌍극자 모멘트 계산
        └─ 계산 결과 파싱
        ↓
[전문 검증 Agent]
        ├─ Electrostatic Interaction Agent
        ├─ van der Waals / Dispersion Interpretation Agent
        ├─ Structural Stability Agent
        ├─ Safety Reasoning Agent
        ├─ Variable Control Agent
        └─ Critic Agent
        ↓
[Harness Debate / Validation]
        ↓
[최종 후보 물질 랭킹]
        ↓
[실험 설계 보고서 자동 생성]
```

---

# 7. 도구 구성 최종 확정

## 사용 도구

|도구|역할|채택 여부|
|---|---|--:|
|**xTB Tool**|계산화학 결과 산출|**채택**|
|LLM MAS|해석, 검증, 보고서 생성|**채택**|
|RDKit|구조 생성, descriptor 계산|제외|
|Open Babel|파일 변환|제외|
|Avogadro|시각화|제외|
|PySCF|정밀 양자화학 계산|제외|
|Psi4|정밀 계산 검증|제외|
|ORCA|고급 계산|제외|
|Custom Physics Calculator|원심분리·물리 계산|제외|

## 중요한 제한

xTB는 기본적으로 계산 엔진이지, 후보 물질의 모든 전처리를 자동으로 해결하는 도구가 아니다.  
따라서 MVP에서는 후보 물질의 입력 구조를 다음 중 하나로 제한해야 한다.

- 사전 준비된 `.xyz` 구조 파일
    
- 사용자가 입력한 xTB 계산 가능 구조 파일
    
- 연구자가 미리 구축한 후보 물질 구조 데이터셋
    

즉, MVP에서는 **SMILES → 3D 구조 자동 변환**까지 욕심내지 않는다.  
이 범위를 자르는 것이 맞다.

---

# 8. xTB Tool 기능 확정

## xTB Tool 이름

> **xtb_lab_tool**

## xTB Tool 기능 목록

```text
optimize_geometry_with_xtb(input_xyz)
calculate_total_energy(input_xyz)
calculate_partial_charges(input_xyz)
calculate_dipole_moment(input_xyz)
extract_xtb_summary(output_files)
compare_xtb_results(candidate_results)
generate_xtb_evidence_table(candidate_results)
```

## Tool 작동 구조

```text
Agent Request
  ↓
xtb_lab_tool
  ↓
xTB CLI 실행
  ↓
결과 파일 생성
  ↓
Parser가 계산값 추출
  ↓
JSON 반환
  ↓
전문 Agent 해석
```

---

# 9. xTB Tool 출력 JSON 예시

```json
{
  "candidate": "candidate_A",
  "calculation_status": "success",
  "geometry_optimized": true,
  "total_energy": -28.4132,
  "dipole_moment": 3.42,
  "charge_summary": {
    "max_positive_charge": 0.38,
    "max_negative_charge": -0.47,
    "charge_distribution_note": "polarized structure"
  },
  "stability_note": "optimized without convergence failure",
  "raw_evidence": {
    "xtb_energy_file": "candidate_A_energy.out",
    "xtb_optimization_file": "candidate_A_opt.out"
  }
}
```

이 JSON을 각 에이전트가 받아서 자기 관점으로 해석한다.

---

# 10. 멀티에이전트 역할 확정

## 1) Orchestrator Agent

역할:

- 전체 작업 분해
    
- 후보 물질 평가 순서 결정
    
- xTB Tool 호출
    
- 에이전트별 평가 결과 수집
    
- 최종 점수 산출
    
- 보고서 생성
    

---

## 2) Hypothesis Agent

역할:

- 사용자의 실험 목적을 검증 가능한 가설로 변환
    

예시:

> “후보 물질의 전하 분포와 쌍극자 모멘트 차이는 특정 실험 조건에서 관찰 가능한 상호작용 차이를 만들 것이다.”

---

## 3) Candidate Material Agent

역할:

- 실험 목적에 맞는 후보 물질군 제안
    
- 후보 물질 선정 이유 작성
    
- xTB 계산 가능한 구조 파일이 있는 후보를 우선 선정
    
- 위험하거나 실험 부적합한 후보를 1차 제외
    

단, 이 Agent는 계산을 직접 하지 않는다.  
계산은 반드시 xTB Tool이 수행한다.

---

## 4) Electrostatic Interaction Agent

역할:

- xTB 결과 중 전하 분포와 쌍극자 모멘트 해석
    
- 정전기적 상호작용 가능성 평가
    
- 극성/비극성 차이에 따른 실험 효과 가능성 판단
    

평가 근거:

- 쌍극자 모멘트
    
- 부분 전하 분포
    
- 전하 편중 정도
    
- 분자 내 극성 영역 존재 여부
    

---

## 5) van der Waals / Dispersion Interpretation Agent

역할:

- xTB 계산 결과를 바탕으로 비공유 상호작용 가능성을 해석
    
- 분자 크기, 구조 안정성, 극성, 에너지 경향을 종합하여 분산력/vdW 가능성 평가
    

주의할 점:

- xTB Tool 하나만 쓰는 MVP에서는 분산력과 반데르발스 힘을 고정밀 분해 계산하지 않는다.
    
- 대신 계산화학적 지표를 바탕으로 **상호작용 가능성의 경향성**을 평가한다.
    

즉, 표현은 이렇게 해야 한다.

> “분산력과 반데르발스 상호작용을 정밀 분해 계산하였다.”

가 아니라,

> “xTB 계산 결과를 바탕으로 비공유 상호작용 가능성을 해석하였다.”

이게 정확하다.

---

## 6) Structural Stability Agent

역할:

- 구조 최적화 성공 여부 검토
    
- 계산 수렴 여부 확인
    
- 총 에너지 비교
    
- 구조적으로 불안정하거나 계산 실패한 후보 제외
    

평가 근거:

- 최적화 성공 여부
    
- 계산 수렴 여부
    
- 상대 에너지
    
- 구조 왜곡 여부
    
- 계산 실패 로그
    

---

## 7) Safety Reasoning Agent

역할:

- 후보 물질의 일반적 위험성 검토
    
- 실험실 취급 가능성 판단
    
- 위험 물질은 최종 추천에서 감점 또는 제외
    

단, 이 시스템은 SDS 전문 DB Tool을 쓰지 않는다.  
따라서 Safety Agent는 LLM의 일반 지식과 사용자가 제공한 정보에 기반해 1차 판단만 수행한다.

보고서에는 반드시 다음 한계를 명시해야 한다.

> “본 시스템의 안전성 검토는 1차 필터링이며, 실제 실험 전에는 공식 SDS/MSDS 확인이 필요하다.”

---

## 8) Variable Control Agent

역할:

- 독립변인, 종속변인, 통제변인 분류
    
- 대조군 설정
    
- 반복 횟수 제안
    
- 농도, 온도, pH, 시간, 용매 등 통제 조건 제안
    

이 에이전트는 R&E 보고서 완성도를 크게 높인다.

---

## 9) Critic Agent

역할:

- 과장된 결론 제거
    
- 계산값과 해석의 일치성 검토
    
- xTB Tool 결과 없는 주장을 차단
    
- 실험 불가능한 설계 제거
    
- 한계와 후속 연구 정리
    

Critic Agent는 반드시 다음 기준으로 검토한다.

```text
계산 결과가 있는가?
계산 결과와 해석이 연결되는가?
실험 설계가 가능한가?
변인통제가 충분한가?
안전성 한계가 명시되었는가?
결론이 과장되지 않았는가?
```

---

# 11. 최종 연구 설계

## 연구 목적

> 본 연구는 실험 후보 물질 선정 과정에서 발생하는 주관적 판단과 변인통제 누락 문제를 해결하기 위해, xTB Tool 기반 계산화학 결과와 LLM 멀티에이전트 검증 구조를 결합한 실험 후보 물질 추천 시스템을 개발하는 것을 목적으로 한다.

---

## 연구 가설

> xTB Tool을 통해 산출된 계산화학 결과를 멀티에이전트가 역할별로 검증하는 구조는 단일 LLM 기반 추천보다 후보 물질 선정의 근거성, 변인통제 완성도, 실험 설계 보고서 품질을 향상시킬 것이다.

---

## 독립변인

|구분|내용|
|---|---|
|시스템 구조|단일 LLM / MAS only / xTB Tool + MAS|
|계산 도구 사용 여부|xTB Tool 미사용 / xTB Tool 사용|
|검증 방식|단일 응답 / 에이전트별 검증 / Critic 검토|

---

## 종속변인

|평가 항목|측정 방식|
|---|---|
|후보 물질 추천 근거성|xTB 계산값 포함 여부, 근거 명확성|
|변인통제 완성도|누락된 통제변인 개수|
|보고서 품질|평가 루브릭 점수|
|추천 일관성|동일 조건 반복 시 결과 변동|
|계산 근거 반영률|최종 추천 사유 중 xTB 결과 기반 문장 비율|
|실험 가능성|비용, 장비, 시간, 난이도 평가|

---

## 통제변인

- 동일한 실험 주제
    
- 동일한 후보 물질군
    
- 동일한 xTB 입력 구조
    
- 동일한 LLM 모델
    
- 동일한 프롬프트 입력
    
- 동일한 평가 루브릭
    
- 동일한 보고서 양식
    
- 동일한 계산 조건
    

---

# 12. 비교 실험 구조

## 비교군

|그룹|설명|
|---|---|
|Baseline 1|일반 LLM 단독 추천|
|Baseline 2|MAS 기반 추천, xTB Tool 미사용|
|Experiment|**xTB Tool + LLM MAS 기반 추천**|

## 핵심 비교

> xTB Tool + LLM MAS 구조가 일반 LLM 단독 추천보다 더 근거 있는 후보 물질 추천과 더 완성도 높은 실험 설계 보고서를 생성하는지 비교한다.

---

# 13. 후보 물질 평가 점수식 예시

```text
Final Score =
0.25 × Electrostatic Score
+ 0.20 × Structural Stability Score
+ 0.20 × Experimental Feasibility Score
+ 0.15 × Safety Score
+ 0.10 × Variable Control Score
+ 0.10 × Critic Reliability Score
```

## 평가 항목

|항목|근거|
|---|---|
|Electrostatic Score|xTB 전하 분포, 쌍극자 모멘트|
|Structural Stability Score|xTB 구조 최적화 성공 여부, 에너지 안정성|
|Experimental Feasibility Score|관찰 가능성, 실험 장비, 시간, 비용|
|Safety Score|1차 안전성 검토|
|Variable Control Score|변인통제 용이성|
|Critic Reliability Score|과장 여부, 계산 근거 일치성|

---

# 14. 최종 보고서 출력 양식

```text
1. 실험 목적
2. 연구 가설
3. 후보 물질 목록
4. xTB Tool 계산 조건
5. 후보 물질별 xTB 계산 결과
   5-1. 구조 최적화 결과
   5-2. 총 에너지
   5-3. 전하 분포
   5-4. 쌍극자 모멘트
   5-5. 계산 성공/실패 여부
6. 전문 에이전트별 검토 결과
   6-1. Electrostatic Interaction Agent
   6-2. vdW/Dispersion Interpretation Agent
   6-3. Structural Stability Agent
   6-4. Safety Reasoning Agent
   6-5. Variable Control Agent
   6-6. Critic Agent
7. 최종 후보 물질 랭킹
8. 추천 물질 선정 근거
9. 제외 물질 사유
10. 실험 설계안
11. 대조군 및 반복 실험 설계
12. 예상 실패 요인
13. 연구의 한계
14. 후속 연구
```

---

# 15. 최종 MVP 범위

## 1단계 MVP

> **xTB Tool 계산 결과를 활용한 후보 물질 랭킹 및 실험 설계 보고서 생성**

포함 기능:

- 후보 물질 5~10개 입력
    
- 후보 물질별 `.xyz` 구조 파일 준비
    
- xTB Tool로 구조 최적화 수행
    
- xTB Tool로 에너지, 전하 분포, 쌍극자 모멘트 추출
    
- MAS 기반 후보 물질 평가
    
- 최종 랭킹 생성
    
- 실험 설계 보고서 생성
    

---

## 2단계 고도화

> **에이전트 검증 구조 강화**

추가 기능:

- Critic Agent 고도화
    
- xTB 결과 기반 근거 문장 자동 생성
    
- 계산 결과와 보고서 문장 간 일치성 검사
    
- 후보 물질 제외 사유 자동 생성
    
- 동일 조건 반복 실행 후 추천 일관성 비교
    

---

## 3단계 확장

> **실제 실험 검증**

추가 기능:

- xTB-MAS 추천 후보와 일반 LLM 추천 후보 비교
    
- 실제 실험 수행
    
- 예측 후보와 실험 결과 비교
    
- 추천 정확도 평가
    
- 후속 모델 개선
    
