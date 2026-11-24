"""Validates one LLM entry. Returns a list of error messages (empty = valid)."""
import json, re, sys
ROLES={"admin","doctor","nurse","patient","pharmacist","laboratorist","accountant","member","system"}
OPS={"view","edit","delete","manage","none"}
OWN={"own","other","none"}
TAMP={"identifier","action","endpoint","session","none"}
REQ=["step","actor","role","operation","resource","ownership","tampered_parameter"]
def validate(raw, statement_step=None, resources=None):
    try: e=json.loads(raw)
    except Exception as x: return [f"not valid JSON: {x}"],None
    if not isinstance(e,dict): return ["output is not a JSON object"],None
    err=[]
    for k in REQ:
        if k not in e: err.append(f"missing field {k}")
    for k in e:
        if k not in REQ: err.append(f"unknown field {k}")
    if err: return err,None
    if not re.match(r"^(BTF|SATF|SAF) ?\d+(\.\d+)?$",e["step"]): err.append("step label has a wrong form")
    if statement_step and e["step"].replace(" ","")!=statement_step.replace(" ",""): err.append(f"step must be {statement_step}")
    if e["role"] not in ROLES: err.append("role not allowed")
    if e["operation"] not in OPS: err.append("operation not allowed")
    if e["ownership"] not in OWN: err.append("ownership not allowed")
    if e["tampered_parameter"] not in TAMP: err.append("tampered_parameter not allowed")
    if resources is not None and e["resource"] not in resources and e["role"]!="system":
        err.append("resource is not a resource type of the context")
    if e["ownership"]=="own" and e["tampered_parameter"]!="none" and e["role"]!="system":
        err.append("an own record cannot be a tampered target")
    return err,(e if not err else None)
if __name__=="__main__":
    print(validate(sys.stdin.read()))
