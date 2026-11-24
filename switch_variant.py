"""Puts one variant (V0, V1, M01..M12, M13, M14, M16..M29) into the live HMS folder.
Usage: python switch_variant.py <hms folder with application/> <variants folder> <V0|V1|M01..M29>
The original 7 controllers touched by any variant are saved once in <variants>/_original_backup."""
import os, shutil, sys
hms, var, name = sys.argv[1:4]
dst = os.path.join(hms, "application", "controllers")
bak = os.path.join(var, "_original_backup")
if not os.path.isdir(bak):
    os.makedirs(bak)
    for f in ("doctor.php", "patient.php", "admin.php", "login.php", "nurse.php", "pharmacist.php", "accountant.php"):
        shutil.copy2(os.path.join(dst, f), bak)
src = os.path.join(var, name, "controllers")
assert os.path.isdir(src), "unknown variant " + name
for f in os.listdir(src):
    shutil.copy2(os.path.join(src, f), dst)
print("live HMS is now", name)
