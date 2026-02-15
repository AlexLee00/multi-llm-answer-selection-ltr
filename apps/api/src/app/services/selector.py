def rule_select(candidates):
    def score(c):
        s = 0
        if len(c["answer_summary"]) > 50:
            s += 1
        if c.get("has_code"):
            s += 2
        if "Step" in c["answer_summary"]:
            s += 1
        return s

    scored = [(c, score(c)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]
