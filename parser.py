from typing import TypedDict

class AgentOutput(TypedDict):
    match_score: int
    strong_matches: list[str]
    missing_skills: list[str]
    suggested_edits: list[str]
    ai_insights: str

def parseAgentOutput(result) -> AgentOutput:
    result = result.strip()

    key_score = "**Match Score:"
    key_matches = "**Strong Matches:"
    key_skills = "**Missing Skills:"
    key_edits = "**Suggested Edits:"
    key_insights = "**AI Insights:"

    index_key_score = result.find(key_score)
    index_key_matches = result.find(key_matches)
    index_key_skills = result.find(key_skills)
    index_key_edits = result.find(key_edits)
    index_key_insights = result.find(key_insights)

    if(index_key_score == -1 or index_key_matches == -1 or index_key_skills == -1 or index_key_edits == -1 or index_key_insights == -1):
        return None

    value_score = None
    value_matches = ""
    value_skills = ""
    value_edits = ""
    value_insights = ""

    # score
    int_accumulator = ""
    i = index_key_score + len(key_score)
    while(i < index_key_matches):
        c = result[i]
        if(c in "0123456789"):
            int_accumulator += c
        i += 1
    if(len(int_accumulator) > 0):
        value_score = int(int_accumulator)

    # matches
    i = index_key_matches + len(key_matches)
    while(i < index_key_skills):
        value_matches += result[i]
        i += 1

    # skills
    i = index_key_skills + len(key_skills)
    while(i < index_key_edits):
        value_skills += result[i]
        i += 1

    # edits
    i = index_key_edits + len(key_edits)
    while(i < index_key_insights):
        value_edits += result[i]
        i += 1

    # insights
    i = index_key_insights + len(key_insights)
    while(i < len(result)):
        value_insights += result[i]
        i += 1

    def cleanup(s: str):
        spl = s.split("\n")
        splnew = []
        if(len(spl) == 0): return ""
        if(spl[0].replace("*", "").strip() == ""):
            del spl[0]
        for i in range(len(spl)):
            ln = spl[i].strip()
            if(ln.find("-") == 0):
                ln = ln[1:]
            ln = ln.strip()
            if(ln == ""): continue
            splnew.append(ln)
        return "\n".join(splnew)

    value_matches = cleanup(value_matches)
    value_skills = cleanup(value_skills)
    value_edits = cleanup(value_edits)
    value_insights = cleanup(value_insights)

    return {
        "match_score": value_score,
        "strong_matches": value_matches.split("\n"),
        "missing_skills": value_skills.split("\n"),
        "suggested_edits": value_edits.split("\n"),
        "ai_insights": value_insights
    }
