"""Builds V0, V1 and the 12 mutants of the HMS as small folders that contain only the changed controllers.
Usage: python build_variants.py <path to hms folder, the one that has application/> <output folder>
Nothing in the original folder is changed."""
import os, re, shutil, sys
SRC, OUT = sys.argv[1], sys.argv[2]
CT = os.path.join("application", "controllers")
FILES = ["doctor.php", "patient.php", "admin.php", "login.php", "nurse.php", "pharmacist.php", "accountant.php"]
def read(p): return re.sub(r"\r*\n", "\n", open(p, encoding="utf-8", errors="surrogateescape", newline="").read())
def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8", errors="surrogateescape", newline="").write(s.replace("\n", "\r\n"))
def func_span(s, name):
    m = re.search(r"\n\s*function " + name + r"\(", s)
    assert m, "function not found: " + name
    n = re.search(r"\n(?:\t|    )(?=function |/\*\*\*)", s[m.end():])
    return m.start(), m.end() + (n.start() if n else len(s) - m.end())
def flex(text):
    toks = text.split()
    return r"\s*".join(re.escape(t) for t in toks)
def sub_in_func(s, name, old, new, count=1):
    a, b = func_span(s, name); blk = s[a:b]
    pat = re.compile(flex(old))
    found = len(pat.findall(blk))
    assert found == count, f"{name}: expected {count} of {old!r}, found {found}"
    blk = pat.sub(lambda m: new.lstrip(" \t"), blk)
    return s[:a] + blk + s[b:]
NL = "\n"
def L(*lines): return NL.join(lines) + NL

GUARD_DOC = "\t\tif ($this->session->userdata('doctor_login') != 1)" + NL + "\t\t\tredirect(base_url() . 'index.php?login', 'refresh');"
OWN_UPD = "\t\tif ($param1 == 'edit' && $param2 == 'do_update') { $this->_own_appointment($param3); } //V1-OWN-UPDATE"
OWN_EDT = "\t\tif ($param1 == 'edit' && $param2 != 'do_update') { $this->_own_appointment($param2); } //V1-OWN-EDIT"
OWN_DEL = "\t\tif ($param1 == 'delete') { $this->_own_appointment($param2); } //V1-OWN-DELETE"
HELPER = L("\t/***V1 PATCH: ownership check for appointments (not routable, starts with underscore)***/",
 "\tfunction _own_appointment($appointment_id = '')",
 "\t{",
 "\t\t$row = $this->db->get_where('appointment', array('appointment_id' => $appointment_id))->row();",
 "\t\tif ($row && $row->doctor_id != $this->session->userdata('doctor_id'))",
 "\t\t\tredirect(base_url() . 'index.php?doctor/manage_appointment', 'refresh');",
 "\t}", "\t")

def make_v1(files):
    d = files["doctor.php"]
    d = sub_in_func(d, "manage_appointment", GUARD_DOC, GUARD_DOC + NL + OWN_UPD + NL + OWN_EDT + NL + OWN_DEL)
    marker = "/***MANAGE PRESCRIPTIONS******/"
    assert d.count(marker) == 1
    d = d.replace(marker, HELPER + marker)
    files["doctor.php"] = d
    p = files["patient.php"]
    old = "'prescription_id' => $param2" + NL + "\t\t\t))->result_array();"
    new = "'prescription_id' => $param2," + NL + "\t\t\t\t'patient_id' => $this->session->userdata('patient_id') //V1-OWN-RX" + NL + "\t\t\t))->result_array();"
    p = sub_in_func(p, "view_prescription", old, new)
    old_g = "\t\t//if($this->session->userdata('patient_login')!=1)redirect(base_url().'index.php?login' , 'refresh');"
    new_g = "\t\tif($this->session->userdata('patient_login')!=1)redirect(base_url().'index.php?login' , 'refresh'); //V1-GUARD-INVOICE"
    p = sub_in_func(p, "view_invoice", old_g, new_g)
    files["patient.php"] = p
    l = files["login.php"]
    old = "\t{" + NL + "\t\t$this->session->set_userdata('login_type', $user_type);"
    new = "\t{" + NL + "\t\tif ($this->session->userdata('admin_login') != 1) redirect(base_url() . 'index.php?login', 'refresh'); //V1-GUARD-LOGINAS" + NL + "\t\t$this->session->set_userdata('login_type', $user_type);"
    files["login.php"] = sub_in_func(l, "login_as", old, new)
    return files

def rm_line(s, tag):
    lines = s.split(NL); keep = [x for x in lines if tag not in x]
    assert len(keep) == len(lines) - 1, tag
    return NL.join(keep)
def guard_del(s, fn, role):
    old = f"\t\tif ($this->session->userdata('{role}_login') != 1)" + NL + "\t\t\tredirect(base_url() . 'index.php?login', 'refresh');"
    return sub_in_func(s, fn, old, "\t\t//MUTANT: guard deleted")

M = []  # (id, operator, description, file, function)
def mut(mid, op, desc, fn):
    M.append((mid, op, desc, fn))
def m01(f): f["doctor.php"] = guard_del(f["doctor.php"], "manage_appointment", "doctor"); return f
def m02(f): f["patient.php"] = guard_del(f["patient.php"], "view_prescription", "patient"); return f
def m03(f): f["admin.php"] = guard_del(f["admin.php"], "manage_doctor", "admin"); return f
def m04(f):
    f["patient.php"] = sub_in_func(f["patient.php"], "view_invoice", "if($this->session->userdata('patient_login')!=1)redirect(base_url().'index.php?login' , 'refresh'); //V1-GUARD-INVOICE", "//MUTANT: guard deleted"); return f
def m05(f): f["doctor.php"] = rm_line(f["doctor.php"], "V1-OWN-EDIT"); return f
def m06(f): f["doctor.php"] = rm_line(f["doctor.php"], "V1-OWN-UPDATE"); return f
def m07(f): f["doctor.php"] = rm_line(f["doctor.php"], "V1-OWN-DELETE"); return f
def m08(f):
    f["patient.php"] = sub_in_func(f["patient.php"], "view_prescription", "'prescription_id' => $param2," + NL + "\t\t\t\t'patient_id' => $this->session->userdata('patient_id') //V1-OWN-RX", "'prescription_id' => $param2"); return f
def m09(f): f["admin.php"] = sub_in_func(f["admin.php"], "manage_doctor", "userdata('admin_login') != 1", "userdata('doctor_login') != 1"); return f
def m10(f): f["patient.php"] = sub_in_func(f["patient.php"], "view_prescription", "userdata('patient_login') != 1", "userdata('doctor_login') != 1"); return f
def m11(f): f["doctor.php"] = f["doctor.php"].replace("$this->_own_appointment($param3); } //V1-OWN-UPDATE", "$this->_own_appointment($param2); } //V1-OWN-UPDATE"); return f
def m12(f): f["doctor.php"] = f["doctor.php"].replace("$this->_own_appointment($param2); } //V1-OWN-DELETE", "$this->_own_appointment($param3); } //V1-OWN-DELETE"); return f

# --- extension: remaining mutants from the 29-mutant catalogue (M15 is equivalent, M18 and M25
# are already exercised by M05-M07 and M08 respectively on this codebase, so they are not repeated) ---
def m13(f): f["nurse.php"] = sub_in_func(f["nurse.php"], "manage_bed", "userdata('nurse_login') != 1", "userdata('admin_login') != 1"); return f
def m14(f): f["admin.php"] = sub_in_func(f["admin.php"], "manage_patient", "userdata('admin_login') != 1", "userdata('admin_login') > 1"); return f
def m16(f): f["pharmacist.php"] = sub_in_func(f["pharmacist.php"], "manage_medicine", "userdata('pharmacist_login') != 1", "userdata('pharmacist_login') == 1"); return f
def m17(f): f["accountant.php"] = sub_in_func(f["accountant.php"], "manage_invoice", "userdata('accountant_login') != 1", "userdata('accountant_login') > 1"); return f
def m19(f):
    old = "$page_data['appointments'] = $this->db->get_where('appointment', array( 'doctor_id' => $this->session->userdata('doctor_id') ))->result_array();"
    new = "$page_data['appointments'] = $this->db->get('appointment')->result_array(); //MUTANT: filter removed"
    f["doctor.php"] = sub_in_func(f["doctor.php"], "manage_appointment", old, new); return f
def m20(f):
    old = "$page_data['appointments'] = $this->db->get_where('appointment', array( 'patient_id' => $this->session->userdata('patient_id') ))->result_array();"
    new = "$page_data['appointments'] = $this->db->get('appointment')->result_array(); //MUTANT: filter removed"
    f["patient.php"] = sub_in_func(f["patient.php"], "view_appointment", old, new); return f
def m21(f):
    old = "$page_data['payments'] = $this->db->get_where('payment', array( 'patient_id' => $this->session->userdata('patient_id') ))->result_array();"
    new = "$page_data['payments'] = $this->db->get('payment')->result_array(); //MUTANT: filter removed"
    f["patient.php"] = sub_in_func(f["patient.php"], "payment_history", old, new); return f
def m22(f):
    old = "$page_data['bed_allotments'] = $this->db->get_where('bed_allotment', array( 'patient_id' => $this->session->userdata('patient_id') ))->result_array();"
    new = "$page_data['bed_allotments'] = $this->db->get('bed_allotment')->result_array(); //MUTANT: filter removed"
    f["patient.php"] = sub_in_func(f["patient.php"], "view_admit_history", old, new); return f
def m23(f):
    old = "$page_data['reports'] = $this->db->get_where('report', array( 'patient_id' => $this->session->userdata('patient_id'), 'type' => 'operation' ))->result_array();"
    new = "$page_data['reports'] = $this->db->get_where('report', array('type' => 'operation'))->result_array(); //MUTANT: patient filter removed"
    f["patient.php"] = sub_in_func(f["patient.php"], "view_operation_history", old, new); return f
def m24(f):
    old = "$page_data['invoices'] = $this->db->get_where('invoice', array( 'patient_id' => $this->session->userdata('patient_id') ))->result_array();"
    new = "$page_data['invoices'] = $this->db->get('invoice')->result_array(); //MUTANT: filter removed"
    f["patient.php"] = sub_in_func(f["patient.php"], "view_invoice", old, new); return f
def m26(f):
    old = "'patient_id' => $this->session->userdata('patient_id')"
    new = "'patient_id' => ($this->input->post('patient_id') ? $this->input->post('patient_id') : $this->session->userdata('patient_id')) //MUTANT: ISR"
    f["patient.php"] = sub_in_func(f["patient.php"], "view_appointment", old, new); return f
def m27(f):
    old = "'patient_id' => $this->session->userdata('patient_id')"
    new = "'patient_id' => ($this->input->post('patient_id') ? $this->input->post('patient_id') : $this->session->userdata('patient_id')) //MUTANT: ISR"
    f["patient.php"] = sub_in_func(f["patient.php"], "payment_history", old, new); return f
def m28(f):
    old = "if ($row && $row->doctor_id != $this->session->userdata('doctor_id'))"
    new = "if ($row && $row->doctor_id != ($this->input->post('doctor_id') ? $this->input->post('doctor_id') : $this->session->userdata('doctor_id'))) //MUTANT: ISR"
    assert f["doctor.php"].count(old) == 1, "M28 anchor not found exactly once"
    f["doctor.php"] = f["doctor.php"].replace(old, new); return f
def m29(f):
    old = "$this->db->where('patient_id', $this->session->userdata('patient_id'));" + NL + "\t\t\t$this->db->update('patient', $data);"
    new = "$this->db->where('patient_id', $this->input->post('patient_id') ? $this->input->post('patient_id') : $this->session->userdata('patient_id')); //MUTANT: ISR" + NL + "\t\t\t$this->db->update('patient', $data);"
    f["patient.php"] = sub_in_func(f["patient.php"], "manage_profile", old, new); return f

mut("M01","B1","delete the session guard of doctor/manage_appointment",m01)
mut("M02","B1","delete the session guard of patient/view_prescription",m02)
mut("M03","B1","delete the session guard of admin/manage_doctor",m03)
mut("M04","B1","delete the session guard of patient/view_invoice",m04)
mut("M05","B2","delete the ownership check of appointment view/edit form",m05)
mut("M06","B2","delete the ownership check of appointment update",m06)
mut("M07","B2","delete the ownership check of appointment delete",m07)
mut("M08","B2","delete the ownership filter of prescription edit",m08)
mut("M09","B3","replace the role flag admin_login by doctor_login in admin/manage_doctor",m09)
mut("M10","B3","replace the role flag patient_login by doctor_login in patient/view_prescription",m10)
mut("M11","B4","appointment update check reads the identifier from the wrong URL segment",m11)
mut("M12","B4","appointment delete check reads the identifier from the wrong URL segment",m12)
mut("M13","B3","replace the role flag nurse_login by admin_login in nurse/manage_bed",m13)
mut("M14","ROR","relax the admin_login guard of admin/manage_patient (!= 1 becomes > 1, always false)",m14)
mut("M16","ROR","invert the pharmacist_login guard of pharmacist/manage_medicine (!= 1 becomes == 1, denies legitimate users)",m16)
mut("M17","ROR","relax the accountant_login guard of accountant/manage_invoice (!= 1 becomes > 1, always false)",m17)
mut("M19","B2","delete the doctor_id filter of the doctor/manage_appointment list",m19)
mut("M20","B2","delete the patient_id filter of patient/view_appointment",m20)
mut("M21","B2","delete the patient_id filter of patient/payment_history",m21)
mut("M22","B2","delete the patient_id filter of patient/view_admit_history",m22)
mut("M23","B2","delete the patient_id filter of patient/view_operation_history",m23)
mut("M24","B2","delete the patient_id filter of patient/view_invoice",m24)
mut("M26","B4","patient/view_appointment reads patient_id from POST instead of session when present",m26)
mut("M27","B4","patient/payment_history reads patient_id from POST instead of session when present",m27)
mut("M28","B4","the appointment ownership helper reads doctor_id from POST instead of session when present",m28)
mut("M29","B4","patient/manage_profile update reads patient_id from POST instead of session when present",m29)

def load():
    return {n: read(os.path.join(SRC, CT, n)) for n in FILES}
def save(name, files):
    for n, s in files.items(): write(os.path.join(OUT, name, "controllers", n), s)
shutil.rmtree(OUT, ignore_errors=True)
save("V0", load())
v1 = make_v1(load()); save("V1", v1)
with open(os.path.join(OUT, "mutant_list.csv"), "w") as lst:
    lst.write("id,operator,description\n")
    for mid, op, desc, fn in M:
        files = fn(make_v1(load())); save(mid, files)
        lst.write(f"{mid},{op},\"{desc}\"\n")
print("built V0, V1 and", len(M), "mutants in", OUT)
