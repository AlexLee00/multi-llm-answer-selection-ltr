def rule_select(candidates):
    """
    Rule-based selector.
    - 빈 answer_summary 후보는 최하위로 밀어낸다.
    - 모든 후보가 비어 있으면 첫 번째 후보를 반환한다 (방어 처리).
    """

    def score(c):
        ans = c.get("answer_summary") or ""
        # 빈 답변은 -999점으로 사실상 제외
        if not ans.strip():
            return -999
        s = 0
        if len(ans) > 50:
            s += 1
        if c.get("has_code"):
            s += 2
        if "Step" in ans or "단계" in ans:
            s += 1
        return s

    scored = [(c, score(c)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]
