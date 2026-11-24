"""Stage 2, program part: completes each validated LLM entry.
Sets request template, policy reference, expected decision, rule pair, required evidence,
and builds the graph from Decision Group and Flow Target. Logs every difference."""
import csv, json, re
RULE={"BTF":("OWN_RESOURCE","OWN_RESOURCE_TAMPERED"),
      "SATF1":("SAME_ACTION","SAME_ACTION_TAMPERED"),
      "SATF2":("AUTHORIZED_ROLE","AUTHORIZED_ROLE_TAMPERED"),
      "SATF3":("VALID_SESSION","NO_SESSION")}
READ={"view"}; WRITE={"edit","delete","manage"}
def load_matrix(path="permission_matrix_hms_DRAFT.csv"):
    return list(csv.DictReader(open(path)))
def load_instances(path="instances.json"):
    return {i["resource"]:i for i in json.load(open(path))}
def step_group(step):
    m=re.match(r"(BTF|SATF|SAF) ?(\d+)?",step)
    if m.group(1)=="SATF": return "SATF"+m.group(2)
    return m.group(1)
def lookup(matrix,role,op,res,own):
    for r in matrix:
        if r["role"]==role and r["resource"]==res and r["ownership"]==own and r["operation"].split()[0]==op:
            return r
    return None
def complete(entry,matrix,instances,log):
    e=dict(entry); g=step_group(e["step"])
    inst=instances.get(e["resource"])
    if g=="SAF" or e["role"]=="system":
        e.update(policy_ref=None,expected_decision="deny",request_template=None,baseline_rule=None,
                 attack_rule=None,required_evidence=[]); return e
    if inst is None: log.append((e["step"],"resource has no instance")); inst={"endpoint":None}
    row=lookup(matrix,e["role"],e["operation"],e["resource"],e["ownership"])
    if row is None:
        log.append((e["step"],f"no matrix row for {e['role']},{e['operation']},{e['resource']},{e['ownership']}"))
        e["policy_ref"]=None; e["expected_decision"]=None
    else:
        e["policy_ref"]=row["policy_ref"]; e["expected_decision"]=row["decision"]
    e["request_template"]=inst["endpoint"]
    base,att=RULE.get(g,(None,None)); e["baseline_rule"]=base; e["attack_rule"]=att
    ev=["transport","differential"]
    if e["operation"] in READ: ev.append("content")
    if e["operation"] in WRITE: ev.append("state")
    e["required_evidence"]=ev
    return e
def build_graph(entries):
    """Edges: step order inside a flow; SATF starts at BTF 5 (RFS) and resumes at BTF 8."""
    edges=[]; steps=[x["step"].replace(" ","") for x in entries]
    for a,b in zip(steps,steps[1:]):
        if a[:3]==b[:3] and not a.startswith("SATF") or (a.startswith("SATF") and b.startswith("SATF") and a.split(".")[0]==b.split(".")[0]):
            edges.append((a,b))
    for s in steps:
        if s.startswith("SATF") and s.endswith(".1"): edges.append(("BTF5",s))
    last={}
    for s in steps:
        if s.startswith("SATF"): last[s.split(".")[0]]=s
    for k,v in last.items(): edges.append((v,"BTF8"))
    return edges
