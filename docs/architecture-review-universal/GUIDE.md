# Architecture Review — 왜 필요한가

## intent-review로 해결되지 않는 지점

intent-review는 **함수 단위** 문제를 해결한다. 의도를 명명 함수로 추출하면 한 함수의 가독성과 안정성이 올라간다.

하지만 다음 증상은 이름 짓기로 해결되지 않는다:

- **상태가 중복 저장된다** — 같은 값이 여러 컴포넌트에 각자 저장돼 있어 동기화 버그가 반복된다
- **명령 디스패치가 분산돼 있다** — 같은 단축키/이벤트가 페이지마다 다르게 처리된다
- **컴포넌트 의존이 그물망이다** — A가 B의 내부를 알고, B는 C의 내부를 알고, 순환 의존까지 생긴다

이런 증상은 **함수 이름의 문제가 아니라 경로의 문제**다. 경로를 이름 붙은 구조로 재편해야 한다.

## 세 가지 핵심 패턴

이 스킬이 제안할 수 있는 패턴은 **의도적으로 세 가지로 제한**된다. 선택지가 많으면 판단이 흐려지고 오적용이 늘어난다.

### 1. Single Source of Truth (단일 수원지)

**증상**: 같은 값이 여러 곳에 저장되고, 동기화 버그가 반복된다.

Before:
```
// 헤더 컴포넌트
<span>{this.userName}</span>          // 자체 복사본

// 설정 페이지
<input value={settings.name} />       // 또 다른 복사본

// 댓글 영역
<div>{comment.authorName}</div>       // 또 다른 복사본
```

이름을 바꾸면 세 곳을 각각 업데이트해야 한다. 한 곳을 놓치면 불일치.

After:
```
// 한 곳에만 저장
const userStore = { name: 'Alice', ... }

// 모든 컴포넌트는 store에서 읽는다
header.subscribe(userStore)
settings.subscribe(userStore)
comments.subscribe(userStore)

// 쓰기도 store를 통해서만
userStore.set({ name: 'Bob' })   // 세 컴포넌트 자동 갱신
```

**이동 원칙**: 모든 읽기는 store에서. 모든 쓰기도 store를 통해서. 컴포넌트는 자기 복사본을 갖지 않는다.

### 2. Command Pattern (커맨드 중앙화)

**증상**: 같은 입력 이벤트(키보드/버튼/메뉴)가 여러 곳에서 제각각 처리된다.

Before:
```
// editor.js
onKeyDown(e) { if (e.metaKey && e.key === 's') saveDoc() }

// listView.js
onKeyDown(e) { if (e.metaKey && e.key === 's') saveList() }  // 다른 save

// home.js
// Cmd+S 아예 안 잡음 — 사용자는 왜 안 되는지 모름
```

After:
```
// commands.js — 중앙 등록표
registerCommand('save', {
  shortcut: 'Cmd+S',
  run: () => activeView().save()
})
registerCommand('close', {
  shortcut: 'Esc',
  run: () => activeView().close()
})

// 어느 페이지에서든 같은 단축키가 일관된 의미로 동작
```

**이점**: 새 단축키 추가는 한 줄. 단축키 충돌은 등록 시점에 즉시 탐지. 단축키 도움말 페이지를 자동 생성할 수 있다. 메뉴/버튼/단축키가 모두 같은 command를 가리키므로 UI 정합성도 확보된다.

### 3. Event Emission (의존 역전)

**증상**: 자식이 부모의 내부 구조를 직접 호출한다. 부모를 바꾸면 자식이 전부 깨진다.

Before:
```
// Child 내부에서
this.parent.cart.items.push(item)
this.parent.total = recompute(this.parent.cart)
this.parent.sidebar.refresh()
```

자식이 부모의 필드명/메서드명을 알고 있다. 부모 리팩토링 시 자식도 연쇄 수정.

After:
```
// Child는 "일어났다"만 알린다
this.emit('itemAdded', { item })

// Parent가 듣고 자기 사정대로 반응
child.on('itemAdded', ({ item }) => {
  this.cart.add(item)
  this.updateTotal()
  this.sidebar.refresh()
})
```

자식은 부모가 어떻게 생겼는지 모른다. 부모를 완전히 교체해도 자식은 변함이 없다.

## 왜 딱 세 가지인가

더 많은 패턴이 존재한다 — Observer, Mediator, CQRS, Hexagonal, Actor, Finite State Machine… 하지만 소규모 프로젝트와 바이브코딩 범위에서는 이 세 가지가 **증상의 80%를 커버**하고, 나머지는 과대설계가 되기 쉽다.

스킬은 의도적으로 **세 패턴 중 하나만 추천**한다. 여러 개를 동시에 적용하지 않는다. 한 라운드에 하나씩, 안정화된 후 다음 라운드.

## 안전 원칙

### Golden Master 우선

패턴을 적용하기 전에 현재 앱의 동작 스냅샷을 뜬다 — 주요 화면의 스크린샷, 콘솔 출력 로그, 핵심 상태 값. 리팩토링 후 이 스냅샷과 대조해서 동작이 보존됐는지 확인한다.

테스트가 없는 앱일수록 Golden Master가 **유일한 안전망**이다.

### 3단계 커밋

모든 패턴 전환은 정확히 3단계로 쪼갠다:

1. **새 구조의 뼈대 도입** — 기존 코드와 병행 존재
2. **호출 지점 이전** — 한 번에 1-3곳씩, 각 이전마다 Golden Master 재확인
3. **기존 구조 제거** — 참조 없는 레거시 삭제

각 단계는 독립 커밋이어야 한다. 문제가 생기면 마지막 커밋으로 롤백하면 즉시 복구.

### 매개변수 3개 룰

새 구조의 함수나 이벤트 페이로드가 4개 이상 매개변수를 요구한다면 설계가 잘못됐다. 객체로 묶거나 관심사를 쪼갠다.

### 동시 적용 금지

SSOT + Command + Emission을 한 번에 다 하지 않는다. 복합 변경은 롤백 단위를 잃는다. 한 라운드에 하나의 패턴만.

## 언제 쓰고 언제 쓰지 말지

**쓸 때**

- intent-review 보고서에 "분산된 의도" ≥ 3건
- 같은 종류 버그가 다른 모듈에서 3회 이상 재발
- 새 기능 추가가 예상보다 훨씬 많은 파일 수정을 요구
- "이 값은 어디서 관리되지?"라는 질문에 답할 수 없음

**쓰지 말 때 (과대설계 방지)**

- 앱이 한 파일/한 화면 규모 — intent-review로 충분
- 중복 상태가 ≤ 2곳이고 동기화 버그 이력이 없음 — YAGNI
- 커맨드가 ≤ 3개 — 분산이 아니라 단순함
- 현재 구조로도 기능 추가가 매끄럽다 — 구조가 이미 성숙한 것

## 시작 방법

Claude Code에서:

```
architecture-review 돌려줘
```

스킬은 다음 순서로 움직인다. **사용자 승인 전에는 코드를 바꾸지 않는다** — 이건 강제 원칙이다.

1. 상태 흐름 맵 작성 (읽기/쓰기 지점 목록화)
2. 이벤트 경로 맵 작성
3. 증상 매칭 → 한 개의 패턴 선택
4. 단계별 이주 계획 작성
5. Golden Master 시나리오 목록을 사용자와 함께 확정
6. 사용자 승인 → 단계 1부터 진행

## 관련 문서

- `SKILL.md` — AI 실행 기준, 증상/패턴 매핑, 보고서 템플릿
- `SETUP.md` — 설치, intent-review 연계, Golden Master 스크립트
