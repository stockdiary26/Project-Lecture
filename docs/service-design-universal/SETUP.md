# Service Design — 셋업 가이드

이 문서는 `service-design` 스킬의 설치와 다른 스킬과의 연계를 안내한다. 스킬 자체는 설정 없이도 동작하지만, 3층 구조(service-design → architecture-review → intent-review)로 연계하면 시너지가 크다.

## 모드 안내 — 학습자에게 배포할 때

이 스킬은 두 모드가 있다:

- **guided** (기본) — AI가 코드 읽고 선택지 제시, 사용자는 선택만. 비개발자 학습자도 사용 가능.
- **full** — 자유 기술 인터뷰. 개발자/기획자용.

학습자 대상이라면 **guided 모드가 기본**이 되도록 CLAUDE.md에 명시해두는 것을 권한다:

```markdown
## 스킬 기본 설정

service-design 호출 시 별도 지정이 없으면 `guided` 모드로 진행한다.
```

그리고 학습자에게는 guided 모드 한 가지만 안내하고, full 모드는 언급하지 말 것. 필요한 사람만 자연스럽게 full로 올라오게.

### 언제 학습자에게 소개할지

**처음부터 이 커맨드를 설치시키지 말 것을 권한다.** 학습자은 먼저 intent-review(스킬)와 `/architecture-review`(커맨드)로 감을 잡아야 이 커맨드의 가치를 이해한다. 도입 시점:

- `/architecture-review`를 3회 이상 돌린 뒤
- 또는 `/architecture-review` 보고서에서 "service-design 고려" 권고가 떴을 때
- 또는 학습자이 "이 원칙을 다음 번에도 기억해야 하는데..."라고 고민할 때

그 시점에 `install-guide.md`의 설치 명령을 추가로 실행하여 이 커맨드 하나만 추가 설치하게 한다.

---

## 📦 설치 명세 (Claude가 읽고 자동 실행)

- **종류**: 슬래시 커맨드 (Slash Command)
- **호출**: `/service-design`
- **원본 본문 파일**: `docs/service-design-universal/COMMAND.md`
- **설치 위치 (프로젝트 로컬)**: `.claude/commands/service-design.md`
- **설치 위치 (글로벌)**: `~/.claude/commands/service-design.md`
- **설치 방법**: 원본을 **그대로 복사** (프론트매터 없음, 가공 불필요)
- **보조 참조 파일**:
  - 원본: `docs/service-design-universal/KNOWLEDGE-GAPS.md`
  - 설치 위치: `.claude/refs/service-design-knowledge-gaps.md`
  - 설치 방법: `cp`로 복사. 커맨드 본문이 런타임에 이 경로를 `Read` 도구로 참조한다.
- **출력 폴더**: `docs/design/` (없으면 `mkdir -p docs/design`로 생성)

사용자가 "이 커맨드 설치해줘"라고 요청하면 Claude는 위 정보를 사용해 아래 명령으로 설치한다.

### 설치 명령

```bash
mkdir -p .claude/commands .claude/refs docs/design
cp docs/service-design-universal/COMMAND.md .claude/commands/service-design.md
cp docs/service-design-universal/KNOWLEDGE-GAPS.md .claude/refs/service-design-knowledge-gaps.md
```

보조 참조 파일을 `.claude/refs/` 아래 복사하면 커맨드가 자립한다. 학습자이 나중에 `docs/*-universal/` 폴더를 정리해도 커맨드는 계속 작동한다.

---

## 왜 스킬이 아닌 커맨드인가

이 도구는 프로젝트당 1-2회만 사용되는 무거운 인터뷰형 작업이다. 스킬로 두면 긴 description이 세션마다 상시 컨텍스트를 차지하므로, 명시 호출 시에만 로드되는 커맨드가 더 효율적이다.

---

## 모드 선택

사용자가 커맨드를 호출할 때 모드를 명시할 수 있다:

```
/service-design                  (기본: guided 모드)
/service-design full 모드로 돌려줘  (개발자용 자유 기술)
```

명시하지 않으면 guided 모드로 진행한다.

### 학습자용 기본값 권장

바이브코딩 학습자에게 전달할 때는 CLAUDE.md에 기본값을 명시해두는 것을 권한다:

```markdown
## 스킬 기본 설정

service-design 호출 시 별도 지정이 없으면 `beginner` 모드로 진행한다.
결정 개수를 3개 이하로 제한하고, 로드맵은 "다음에 추가할 기능 1개"만 받는다.
```

---

## 다른 스킬과의 연계

### 권장 호출 순서

```
1. service-design  → docs/design/service-principles.md 생성
2. architecture-review  → principles.md를 참조해 현재 코드 진단
3. intent-review  → 리팩토링 후 새 함수들 이름 검증
```

### architecture-review 쪽 연결

`architecture-review`의 SKILL.md에 다음 우선순위 로직을 포함시킨다 (또는 포함시켜야 한다):

```markdown
## 시작 전 확인

- `docs/design/service-principles.md` 존재 여부 확인
  - 있으면: 그 문서를 기준으로 현재 코드의 이탈 지점을 찾는다
  - 없으면: 사용자에게 "설계 원칙 문서가 없습니다. service-design을 먼저 실행하는 것을 권장합니다" 안내
    - 사용자가 계속 진행을 원하면: 일반 원칙 기반으로 진단 (이전 방식)
    - 사용자가 service-design으로 전환을 원하면: 해당 스킬로 넘긴다
```

### intent-review 쪽 연결

`intent-review`는 service-principles.md가 있을 때 **도메인 언어 검증**을 강화한다:

- 함수명/변수명이 `service-principles.md`의 엔티티명과 일치하는가?
- 관계가 없는 도메인 용어가 섞여 들어가지 않았는가?

이 연결은 선택이지만, 있으면 "같은 개념에 여러 이름이 쓰이는 문제"를 조기 탐지한다.

---

## 반복 주기

설계 원칙 문서는 **살아 있는 문서**다. 다음 시점에 재생성하거나 갱신한다:

- **새 주요 기능 추가 직전** — 로드맵 업데이트
- **3~6개월마다 정기 점검** — 확장 축이 바뀌지 않았는지
- **대규모 리팩토링 직전** — architecture-review가 원칙 문서 부재를 보고했을 때
- **팀/제약 변화 시** — 스택 변경, 팀 규모 변화 등

재생성은 이전 문서를 **덮어쓰지 않는다**. `service-principles-YYYY-MM-DD.md` 형태로 버전 저장하고, 최신 버전을 `service-principles.md` 심볼릭 링크(또는 복사본)로 유지한다.

---

## 🔴 경고를 만났을 때의 운영 규칙

인터뷰 중 🔴 경고가 뜨면 사용자는 다음 중 하나를 선택해야 한다:

1. **개념 학습 후 재개** — 인터뷰 일시 중단, `KNOWLEDGE-GAPS.md` 해당 항목 읽고 돌아옴
2. **임시 결정으로 진행** — 기본값 적용, 설계 원칙 문서에 ⚠️ 태그 자동 부착

### 학습자에게 전할 때

학습자은 대부분 2번을 고를 것이다. 괜찮다. 다만:

- 임시 결정은 **후속 검토 항목 목록**으로 반드시 명시된다
- 다음 라운드에서 같은 항목이 다시 뜨면 AI가 "지난 번 임시 결정이 아직 확정되지 않았습니다. 지금 학습하시겠습니까?" 하고 되묻는다
- 6개월 이상 임시 결정 상태로 남으면 AI가 경고 레벨을 올린다

이 장치가 있어야 "임시 결정"이 영구 결정으로 굳어지는 것을 막는다.

---

## Hook 연계 (선택)

`docs/design/service-principles.md` 파일이 수정될 때 architecture-review를 자동 트리거할 수 있다.

`.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "f=$(jq -r '.tool_input.file_path // empty'); case \"$f\" in */docs/design/service-principles.md) echo '[service-design] 설계 원칙 문서가 갱신되었습니다. architecture-review로 현재 코드 적합성 점검을 권장합니다.';; esac"
          }
        ]
      }
    ]
  }
}
```

이 hook은 파일 갱신 시 콘솔에 안내만 출력하고, 실행을 강제하지 않는다.

---

## 문제 해결

**Q. 인터뷰가 너무 길어서 학습자이 지친다.**
A. beginner 모드를 명시하고, Phase 4(로드맵)를 "추가 기능 1개"로 제한한다. CLAUDE.md에 기본값 설정 참고.

**Q. 🔴 경고가 너무 자주 뜬다.**
A. 확장 축에 "실시간성"이나 "동시 협업"이 들어간 경우다. 이 두 축은 근본적으로 개발 지식을 요구한다. 학습자에게는 이 축을 선택하지 말 것을 권하거나, 임시 결정으로 가고 후속 학습을 추천한다.

**Q. 기존 프로젝트에 이 스킬을 도입할 때 기능 인벤토리를 AI가 알아서 뽑을 수 있나?**
A. 코드 구조만 보고 일부는 추출 가능하지만, "의도"까지는 파악 못한다. AI가 초안을 만들고 사용자가 검수하는 방식을 권장한다.

**Q. 설계 원칙 문서가 너무 길어진다.**
A. full 모드의 문서는 본래 길다. beginner 모드로 다시 돌리거나, 문서의 Section 7(결정 목록)만 유지하고 나머지를 별도 파일로 분리한다.

---

## 요약

- 3개 문서(`SKILL.md`, `KNOWLEDGE-GAPS.md`, `SETUP.md`)를 `.claude/skills/service-design/`에 둔다
- 학습자에게는 beginner 모드를 기본으로
- 설계 원칙 문서는 `docs/design/service-principles.md`
- architecture-review와 intent-review가 이 문서를 자동 참조하도록 연결 (설정 필요)
- 🔴 경고는 무시하지 말되, 학습하거나 임시 결정으로 처리 — "임시 결정"은 반드시 목록화
