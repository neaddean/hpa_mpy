# noinspection PyUnresolvedReferences

import argparse
import json
import os
import subprocess
import time

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
group.add_argument('--nvs-config', action="store_true")
group.add_argument('--reset', action="store_true")
group.add_argument('--rm-all', action="store_true")
group.add_argument('--delta-main', action="store_true")

args = parser.parse_args()

proj_dir = os.path.normpath(args.proj_dir)

src_dir = os.path.join(proj_dir, "src")
build_dir = os.path.join(proj_dir, "build")
fn_main = os.path.join(os.path.join(proj_dir, 'src'), 'main.py')
fn_hash = os.path.join(build_dir, "files_hash.json")


def run(cmd='', *pos, **kwargs):
    if args.current_file in cmd and not any(x in cmd for x in ["nvs_config.py", "rm_all.py"]):
        p = os.path.dirname(args.current_file)
        if not p.startswith(src_dir):
            raise RuntimeError("Can only run/flash files from `src/`!")

    connect_str = r"..\venv\Scripts\python.exe -m mpremote connect COM5 "
    cmd = connect_str + cmd
    print("====== " + cmd)
    time.sleep(0.01)
    return subprocess.run(cmd, *pos, shell=True, **kwargs)


def mkdirs_and_cp_cmd():
    cmd = ''
    for rel, files in all_files.items():
        files_in = [f for f in files]
        remote = ":" + rel
        run(f"mkdir {remote}")
        cmd += f"cp {' '.join(files_in)} {remote}/ + "
    return cmd


def cp_current_file_cmd():
    cmd = 'soft-reset + '
    remote = args.current_file.replace(src_dir, '')
    remote = os.path.dirname(remote)
    cmd += f"cp {args.current_file} :{remote}/ "
    return cmd


def make_all_files():
    all_files_ = {}
    for path, _, files in os.walk(src_dir):
        all_files_[os.path.normpath(os.path.relpath(path, src_dir))] = [
            os.path.normpath(os.path.join(path, f))
            for
            f in files]
    return all_files_


all_files = make_all_files()


def hash_all_files():
    files = [file for _path, files in all_files.items() for file in files]
    hashes = {}
    for fn in files:
        hashes[fn] = os.path.getmtime(fn)
    return hashes


def update_files_hash():
    with open(os.path.join(build_dir, "files_hash.json"), "w") as f:
        f.write(json.dumps(hash_all_files(), indent=2))


def get_changed_files():
    hashes = hash_all_files()
    if not os.path.exists(fn_hash):
        return list(hashes.keys()), list(hashes.keys())
    with open(fn_hash) as f:
        old_hashes = json.loads(f.read())

    new_files = set(hashes.items())
    old_files = set(old_hashes.items())

    cp_files_ = new_files - old_files
    rm_files_ = old_files - new_files

    return set(x for x, y in cp_files_), set(x for x, y in rm_files_)


if args.connect:
    run()

elif args.run:
    run(f"run {args.current_file} + repl")

elif args.resume:
    run(f"resume")

elif args.reset:
    run('exec --no-follow "import time, machine; time.sleep_ms(100); machine.reset()"')

elif args.copy_and_run:
    run(f"cp {args.current_file} : + run {args.current_file} + repl")

elif args.copy:
    cmd = cp_current_file_cmd()
    run(f"{cmd} + repl")

elif args.copy_current_main:
    cmd = cp_current_file_cmd()
    run(f"{cmd} + soft-reset + run {fn_main} + repl")

elif args.copy_all_main:
    cmd = mkdirs_and_cp_cmd()
    run(f"{cmd} + run {fn_main} + repl")

elif args.delta_main:
    cp_files, _ = get_changed_files()

    cmd = ''
    for rel, files in all_files.items():
        files_in = [f for f in files if f in cp_files and not f.endswith("/")]
        remote = ":" + rel
        # run(f"mkdir {remote}")
        if files_in:
            cmd += f"cp {' '.join(files_in)} {remote}/ + "
        # else:
        #     cmd += f"mkdir {remote} + "

    if cmd:
        run(f"{cmd[:-3]}")
        update_files_hash()
    run(f"soft-reset + run {fn_main} + repl")


elif args.build_all:
    # run(f"run {os.path.join(build_dir, 'rm_all.py')}")

    erase_vfs = "esptool --baud 921600 --port COM5 --chip esp32 --before default_reset " \
                "--after hard_reset erase_region 0x310000 0x0f0000"
    subprocess.run(erase_vfs, shell=True)

    try:
        os.remove(fn_hash)
    except OSError:
        pass

    run(f"run {os.path.join(proj_dir, '../ext/nvs_config.py')}")
    run(mkdirs_and_cp_cmd())
    update_files_hash()
    run('exec --no-follow "import time, machine; time.sleep_ms(100); machine.reset()" + repl')

elif args.nvs_config:
    run(f"run {os.path.join(proj_dir, '../ext/nvs_config.py')}")

elif args.rm_all:
    run(f"run {os.path.join(build_dir, 'rm_all.py')}")
