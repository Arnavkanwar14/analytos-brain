import sys, subprocess, shutil

print("python_version=", sys.version.split()[0])
print("crlf_source_ok=", True)  # if this runs, Python tolerated CRLF

def have(cmd):
    return shutil.which(cmd) or "MISSING"

for c in ["curl", "git", "python3", "pip3", "node", "npm", "cargo", "unzip", "make", "tar"]:
    print(f"{c}={have(c)}")

# prove subprocess arg-list execution works with no shell quoting issues
r = subprocess.run(["bash", "-lc", "echo shell_var_$((2+3))"], capture_output=True, text=True)
print("subprocess_stdout=", r.stdout.strip())
