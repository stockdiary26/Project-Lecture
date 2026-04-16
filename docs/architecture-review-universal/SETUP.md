# Architecture Review — 셋업 가이드

## 📦 설치 명세 (Claude가 읽고 자동 실행)

- **종류**: 슬래시 커맨드 (Slash Command)
- **호출**: `/architecture-review`
- **원본 본문 파일**: `docs/architecture-review-universal/COMMAND.md`
- **설치 위치 (프로젝트 로컬)**: `.claude/commands/architecture-review.md`
- **설치 위치 (글로벌)**: `~/.claude/commands/architecture-review.md`
- **설치 방법**: 원본을 **그대로 복사** (프론트매터 없음, 가공 불필요)
- **보조 참조 파일**: 없음

사용자가 "이 커맨드 설치해줘"라고 요청하면 Claude는 위 정보를 사용해 `cp` 한 번으로 설치한다.

### 단일 명령

```bash
mkdir -p .claude/commands
cp docs/architecture-review-universal/COMMAND.md .claude/commands/architecture-review.md
```

설치 후 Claude Code가 `.claude/commands/*.md`를 자동 인식하여 `/architecture-review`로 호출 가능해진다.

---

## 왜 스킬이 아닌 커맨드인가

architecture-review는 사용자가 명시적으로 "지금 돌린다"고 결정하는 무거운 분석 도구다. 스킬로 두면 description이 세션마다 상시 컨텍스트에 올라와 비용이 나간다. 커맨드는 슬래시 호출 시에만 로드되어 평소 컨텍스트가 가볍다. `intent-review`는 반대로 가볍고 자주 쓰이므로 스킬로 유지.

### 2. intent-review와의 연계 (권장)

`/architecture-review`는 intent-review의 **후속 커맨드**다. intent-review 보고서 말미에 이 커맨드로의 연결을 자동 포함시키면 학습자이 자연스럽게 다음 단계로 이동할 수 있다.

intent-review 스킬의 `SKILL.md` 보고서 템플릿에 다음 조건부 섹션이 이미 포함돼 있다:

```markdown
## 다음 단계 권장
(조건: "분산된 의도" ≥ 3건인 경우만 출력)

분산된 의도가 {N}건 발견되었습니다. 이것은 함수 단위 문제가 아니라 아키텍처 차원의 문제일 가능성이 있습니다.

→ `/architecture-review` 커맨드 실행을 권장합니다.
```

이 연결이 있어야 학습자이 "언제 위 커맨드를 써야 하는지" 스스로 판단하지 않아도 된다.

---

## 플랜 스킬 연계 (중요)

architecture-review는 **진단과 방향 제안까지만** 한다. 실행 가능한 단계별 plan, 커밋 계획, Golden Master 시나리오 구체 목록은 플랜 스킬이 담당한다.

권장 플랜 스킬: **`superpowers:writing-plans`**

### 흐름

```
1. architecture-review 돌려줘
   → docs/reviews/architecture-review-YYYY-MM-DD.md (방향 제안 포함)

2. /superpowers:writing-plans
   → 위 방향 제안 문서를 입력으로 전달
   → 라운드별 독립 plan 파일 생성
   → Golden Master 시나리오 구체화는 여기서

3. 플랜에 따라 단계별 실행
```

**architecture-review는 코드를 수정하지 않는다.** 어떤 경우에도 진단 보고서 이상을 내놓지 않는다. 실행 가능한 task 목록, 커밋 계획, Golden Master 시나리오 명세는 전부 플랜 스킬의 출력이다.

---

## 동작 원칙 (설치 전 확인)

1. **진단까지만.** 이 스킬은 어떤 경우에도 코드를 수정하지 않고, 단계별 plan도 작성하지 않는다. 출력은 진단 보고서 1개.

2. **한 번에 한 패턴.** SSOT + Command + Event Emission을 동시에 제안하지 않는다. 한 라운드에 하나, 나머지는 대기 리스트.

3. **플랜은 별도 스킬.** 방향 제안을 받은 뒤 `superpowers:writing-plans` 같은 플랜 스킬을 호출해 실행 가능한 plan으로 변환한다.

4. **Golden Master는 플랜 스킬의 영역.** 이 스킬은 "Golden Master가 필요하다"까지만 표시한다. 시나리오 목록과 실행 절차는 플랜 스킬이 작성한다.

---

## CLAUDE.md 연동 예시

프로젝트 CLAUDE.md에 다음을 추가하면 Claude가 이 스킬의 존재와 규칙을 인지한 상태로 작업한다:

```markdown
## 아키텍처 원칙 (상세: `.claude/skills/architecture-review/SKILL.md`)

- 상태는 한 곳에만 저장한다 (SSOT)
- 같은 이벤트는 한 곳에서 해석한다 (Command Pattern)
- 자식은 부모 내부를 모른다 (Event Emission)
- 구조 변경은 3단계 커밋으로, Golden Master 확보 후에만
```

---

## intent-review 보다 먼저 쓰지 않기

이 스킬은 **intent-review가 선행된 것을 전제**로 한다. 함수 단위 문제가 섞여 있는 상태에서 아키텍처 재설계를 하면, 결과물은 여전히 이름이 엉망인 함수들로 차 있게 된다.

권장 순서:

1. intent-review 먼저 (함수 이름 정리)
2. 보고서에서 "분산된 의도 ≥ 3건" 확인
3. 그때 architecture-review 실행

이 순서를 지킬 때 두 스킬의 시너지가 나온다.
