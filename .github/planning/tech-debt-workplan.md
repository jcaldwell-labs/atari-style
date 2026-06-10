# Tech Debt Workplan

Prioritized plan for resolving open tech debt issues, sequenced by dependency and impact.
Created 2026-03-17 from analysis of issues #149-#155.
Updated 2026-06-10: reconciled with actual state — the 2026-03-19 sprint closed most of this.

## Status Key
- [ ] Not started
- [x] Complete
- [~] In progress

## Tier 1 — Independent, high value (no architecture decision needed)

- [x] **#149** — Replace bare except clauses with specific exception types (closed 2026-03-19, PR #158)
- [x] **#151** — Create shared font loading utility (closed 2026-03-19, PR #160)

## Tier 2 — Strategic decision (unblocks Tier 3)

- [x] **#155** — Architecture guide: resolved 2026-06-10, see /ARCHITECTURE.md
  - Decided: `atari_style/` is canonical; `terminal_arcade/` deprecated, games kept as read-only content
  - Decided: GL pipeline and terminal renderer are permanent peers (video output vs interactive)
  - Decided: plugin system kept dormant, not required for new features

## Tier 3 — Was blocked by #155

- [x] **#150** — Duplicate InputHandler (closed 2026-03-19; resolved by deprecating
      terminal_arcade rather than extracting a shared module — atari_style copy is canonical)
- [x] **#152** — Duplicate buffer handling (closed 2026-03-19 as architectural:
      terminal and GL renderers have distinct buffer concerns, no shared base class needed)

## Tier 4 — Lower priority

- [x] **#153** — Add validation to Config dataclass (closed 2026-03-19, PR #157)
- [x] **#154** — Optimize inefficient loop patterns (closed 2026-03-19, PR #159)
- [x] **#144** — Enhance project visibility and discoverability (closed 2026-03-20)

## Remaining open work

- [ ] **#161** — Revisit zone mode for shader embedding (decision needed: is there a
      downstream consumer, e.g. my-grid? If yes, fresh PR on ContentRegistry with
      safer IPC than TCP setattr — see issue for blockers found in PR #143 review)
- [ ] terminal_arcade migration end-state: port games out opportunistically (see ARCHITECTURE.md §1)

## Content pipeline notes (June 2026)

Channel analytics review (25 videos, ~1.3k views) established the publishing profile:
bright/saturated > dark/sparse; recognizable subjects; <60s; no shell chrome in frame;
end on the strongest frame. Codified in ARCHITECTURE.md §6.
