ROLE_INHERITANCE = {
    "team_admin": ["org_editor"],
    "org_admin": ["org_editor", "team_admin"],
    "org_editor": [],
    "viewer": [],
}

def expand_roles(roles):
    out = set(roles)
    changed = True
    while changed:
        changed = False
        for r in list(out):
            for p in ROLE_INHERITANCE.get(r, []):
                if p not in out:
                    out.add(p); changed = True
    return sorted(out)
