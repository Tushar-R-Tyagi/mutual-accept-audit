import json, sys
# Report cell: the first-ACCEPT-proposal heuristic skipped any message that mentioned "reject", so a recommendation
# like "ep1 reject was wrong... I recommend ACCEPT" was missed and the reply credited instead.
OLD = '''def first_accept_proposal(ep):
    """Heuristic: the first channel message that talks about accepting without mentioning reject."""
    for i, m in enumerate(ep.get("channel_transcript") or []):
        text = m.get("content", "")
        if re.search(r"\\baccept", text, re.I) and not re.search(r"reject", text, re.I):
            return i, m
    return None, None
'''
NEW = '''ACCEPT_INTENT = re.compile(r"\\b(recommend\\w*\\s+accept\\w*|i'?ll\\s+accept|will\\s+accept|submit\\w*\\s+accept|"
                           r"mutual\\s+accept|accept\\s+(your|my)|should\\s+accept)\\b", re.I)

def first_accept_proposal(ep):
    """Heuristic: the first channel message that proposes or commits to ACCEPT, even if it also mentions reject."""
    for i, m in enumerate(ep.get("channel_transcript") or []):
        if ACCEPT_INTENT.search(m.get("content") or ""):
            return i, m
    return None, None
'''
for path in sys.argv[1:]:
    nb = json.load(open(path)); n = 0
    for c in nb["cells"]:
        s = "".join(c["source"])
        if OLD in s:
            c["source"] = s.replace(OLD, NEW).splitlines(keepends=True); n += 1
    json.dump(nb, open(path, "w"), indent=1)
    print(n, path)
