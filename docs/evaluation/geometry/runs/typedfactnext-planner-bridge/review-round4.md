# Independent review — round 4 (confirmation)

Reviewer: the same read-only agent, on the round-3 fix. Verdict: **no BLOCKER, no IMPORTANT remains.**

- The round-3 repros (a negation governing a list, "… hay không?", "thay vì", "mà không dựng") are all refused.
- Legitimate ratio wordings still serve with the oracle value 1/8: "Tỉ số thể tích của hai khối chóp S.MNP và S.ABC bằng
  bao nhiêu?", "Tính tỉ số thể tích giữa / của khối chóp S.MNP và / so với khối chóp S.ABC.", "Tìm tỉ số thể tích hai
  khối chóp S.MNP và S.ABC."
- The optional "tỉ số thể tích …" opener does not admit a non-request clause: "Cho biết: / Ta có: / Nhận xét: tỉ số thể
  tích … bằng 1/2 (1/8)." are refused (`QUESTION_CONTEXT_UNSUPPORTED`, `NOT_ASKED_IN_SOURCE`); "Giả sử …" and "Chứng
  minh …" are refused by the clause-role check (`UNSUPPORTED_CAPABILITY`). The reviewer notes these clauses pass the
  lead-in allow-list after the ":" split and are stopped by those existing checks — the allow-list is one layer, not the
  only one.
- MINOR (fail-closed, already recorded in `SOURCE_GATE_INTEGRATION_REPORT.md` §4): the sentence-wide negation scan
  refuses a request whose sentence negates anything else, e.g. "(không cần rút gọn)".

No code change after this round. Review closed for Session 1.
