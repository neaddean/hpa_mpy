import argparse
import os
import re
import subprocess

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--current-file', type=str, required=True)
parser.add_argument('--proj-dir', type=str, required=True)

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--run', action="store_true")
group.add_argument('--resume', action="store_true")
group.add_argument('--copy-and-run', action="store_true")
group.add_argument('--copy', action="store_true")
group.add_argument('--connect', action="store_true")
group.add_argument('--copy-all-main', action="store_true")
group.add_argument('--copy-current-main', action="store_true")
group.add_argument('--build-all', action="store_true")
group.add_argument('--wifi-config', action="store_true")
group.add_argument('--reset', action="store_true")

args = parser.parse_args()

src_dir = os.path.join(args.proj_dir, "src")
build_dir = os.path.join(args.proj_dir, "build")
fn_main = os.path.join(args.proj_dir, 'src/main.py')


def run(cmd='', *pos, **kwargs):
    if args.current_file in cmd and not args.wifi_config:
        p = os.path.dirname(args.current_file)
        if not p.startswith(src_dir):
            raise RuntimeError("Can only flash files from `src/`!")

    connect_str = r"..\venv\Scripts\python.exe -m mpremote connect COM5 "
    return subprocess.run(connect_str + cmd, *pos, shell=True, **kwargs)


def mkdirs_and_cp_cmd():
    cmd = ''
    for rel, files in all_files.items():
        files_in = [f for f in files]
        remote = os.path.join(":", rel)
        remote = remote.replace("\\.", "") + "\\"
        run(f"mkdir {remote}")
        cmd += f"cp {' '.join(files_in)} {remote} + "
    return cmd


def cp_current_file_cmd():
    cmd = ''
    remote = args.current_file.replace(src_dir, '')
    remote = os.path.dirname(remote)
    cmd += f"cp {args.current_file} :{remote}/ + "
    return cmd


all_files = {}
for path, _, files in os.walk(src_dir):
    all_files[os.path.relpath(path, src_dir)] = [os.path.join(path, f) for f in files]

if args.connect:
    run()

elif args.run:
    run(f"run {args.current_file} + repl")

elif args.resume:
    run(f"resume")

elif args.reset:
    run(f"reset + repl")

elif args.copy_and_run:
    run(f"cp {args.current_file} : + run {args.current_file} + repl")

elif args.copy:
    cmd = cp_current_file_cmd()
    run(f"{cmd} + repl")

elif args.copy_current_main:
    cmd = cp_current_file_cmd()
    run(f"{cmd} + run {fn_main} + repl")

elif args.copy_all_main:
    cmd = mkdirs_and_cp_cmd()
    run(f"{cmd} run {fn_main} + repl")

elif args.build_all:
    local_files_raw = run("fs ls", capture_output=True).stdout.decode()
    local_files = []
    for f in local_files_raw.split("\n"):
        if match := re.search(r"\d (.*?\.py)", f):
            local_files.append(match.group(1))

    run(f"rm {' '.join(local_files)}")

    cmd = mkdirs_and_cp_cmd()
    run(f"{cmd} run {fn_main} + repl")

elif args.wifi_config:
    run(f"run {os.path.join(build_dir, 'wifi_config.py')}")
