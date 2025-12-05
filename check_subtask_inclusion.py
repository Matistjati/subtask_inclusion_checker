#!/usr/bin/python3

# This script will run all testcases towards the validation for all testgroups,
# and report any potential testcases which could also be included in additional groups.
# Mostly written by chatgpt...

import sys
import subprocess
import os
import yaml
import concurrent.futures
import re
import resource
from pathlib import Path
import shutil
from typing import Iterable, List, Any

resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

out_dir = 'output'
out_path = Path(__file__).parent / out_dir
if out_path.exists():
    shutil.rmtree(out_path)
out_path.mkdir()
log_file = Path(out_path / 'test_group_inclusions.log')


summary_path = Path("summary.md")
if summary_path.exists():
    summary_path.unlink()

def write_log(*args):
    with log_file.open("a") as f:
        f.write(f"{' '.join(args)}\n")

def write_pretty_output(line):
    with summary_path.open("a") as f:
        f.write(f"{line}\n")
    
    if "GITHUB_STEP_SUMMARY" in os.environ:
        github_summary = Path(os.environ["GITHUB_STEP_SUMMARY"])
        with github_summary.open("a") as f:
            f.write(f"{line}\n")

def get_problem_name(problem: Path) -> str:
    problem_name = problem.name
    parent = problem.parent.name
    if parent != Path(__file__).parent.name:
        problem_name = parent + '/' + problem_name
    return problem_name

def validate_problem(problem: Path):
    write_log(f"Validating problem: {problem}")
    # Name of the C++ source file
    cpp_file = problem / "input_validators/validator/validator.cpp"
    # Name of the output executable
    output_executable = '/tmp/validator.out'

    # Compile the C++ file
    compile_command = ['g++', '-O2', cpp_file, '-o', output_executable, '-std=c++20']
    compile_process = subprocess.run(compile_command, capture_output=True, text=True)

    # Check if compilation was successful
    if compile_process.returncode == 0:
        write_log("Compilation successful.")
    else:
        print(f"## ❌ {get_problem_name(problem)} Validator Compilation Failed \n")
        write_pretty_output(f"## ❌ {get_problem_name(problem)} Validator Compilation Failed \n")
        write_log("Compilation failed:")
        write_log(compile_process.stderr)
        exit(0)

    def run_validator(file, flags, group):
        run_command = [output_executable] + flags.split()
        write_log("validating", os.path.basename(file), "for", group)
        with open(file) as inp:
            run_process = subprocess.run(run_command, stdin=inp, capture_output=True, text=True)
            return run_process.returncode == 42

    def run_validator_and_print(file, flags, group):
        run_command =  [output_executable] + flags.split()
        write_log("❌ WARNING:", os.path.basename(file), "not in", group)
        write_log("flags:", flags)
        with open(file) as inp:
            run_process = subprocess.run(run_command, stdin=inp, capture_output=True, text=True)
            write_log("stdout:", run_process.stdout)
            write_log("stderr:", run_process.stderr)
            write_log("returncode:", run_process.returncode)
            return run_process.returncode == 42

    group_to_flags = {}
    infiles = {}
    infiles_path = {}

    # os.walk generates the file names in a directory tree
    for dirpath, dirnames, filenames in os.walk(os.path.join(problem,'data')):
        group = os.path.basename(dirpath)
        if group not in ("data", "secret"):
            group_to_flags[group] = ""
        if "testdata.yaml" in filenames:
            with open(os.path.join(dirpath,'testdata.yaml'), 'r') as file:
                # Load the YAML content
                config = yaml.safe_load(file)
                if 'input_validator_flags' in config:
                    group_to_flags[group] = config['input_validator_flags']
        for file in filenames:
            if file.endswith('.in'):
                if file not in infiles:
                    infiles[file] = []
                infiles[file].append(group)
                infiles_path[file] = os.path.join(dirpath,file)

    #print(group_to_flags)
    #print(infiles)

    inputs = sorted(infiles.keys())
    groups = sorted(group_to_flags.keys())
    if 'sample' in groups:
        groups.remove('sample')
        groups = ['sample'] + groups

    inputs = sorted(inputs, key=lambda x: (re.match(r'(\d+)\.in', x) is None, x))

    data = []

    def go(file, g):
        try:
            val = run_validator(infiles_path[file],group_to_flags[g],g)
            inc = 1 if g in infiles[file] else 0
            if val == inc:
                return "OK:Y" if val else "OK:N"
            elif val:
                return "MISS"
            else:
                run_validator_and_print(infiles_path[file],group_to_flags[g],g)
                return "BAD"
        except Exception as e:
            write_log(f"Exception while validating {file} for group {g}: {e}")
            return "UNKNOWN"

    for file in inputs:
        #row = [file] + [go(file, g) for g in groups]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(go, file, g) for g in groups]
            row = [file] + [future.result() for future in futures]
        data.append(row)


    def print_table(data: Iterable[Iterable[Any]], headers: Iterable[Any]) -> str:
        """
        Build a markdown table from `headers` and `data`, print it, and return it as a string.
        ANSI escape sequences are stripped for sizing and output.
        """

        ncols = max(len(headers), max((len(r) for r in data), default=0))

        col_widths: List[int] = []
        for col in range(ncols):
            max_width = len(headers[col])
            for r in data:
                max_width = max(max_width, len(r[col]))
            col_widths.append(max(3, max_width))

        def pad(text: str, width: int) -> str:
            return text + ' ' * (width - len(text))

        def color_cell(cell: str) -> str:
            if "OK" in cell:
                return f"✅{cell}"
            elif "MISS" in cell:
                return f"⚠️{cell}"
            elif "BAD" in cell:
                return f"❌{cell}"
            return cell

        rows_colored = [[color_cell(cell) for cell in row] for row in data]

        header_line = '| ' + ' | '.join(pad(headers[i], col_widths[i]) for i in range(ncols)) + ' |'
        separator_line = '| ' + ' | '.join('-' * col_widths[i] for i in range(ncols)) + ' |'
        row_lines = [
            '| ' + ' | '.join(pad(rows_colored[r][i], col_widths[i]) for i in range(ncols)) + ' |'
            for r in range(len(rows_colored))
        ]

        lines = [header_line, separator_line] + row_lines
        table = '\n'.join(lines)

        return table

    def count_word_occurrences(word, table):
        count = 0
        for row in table:
            for item in row:
                if word in item:
                    count += 1
        return count

    removed_sample = [row[:] for row in data]
    any_bads = count_word_occurrences("BAD", data)>0
    if 'sample' in groups:
        for row in removed_sample:
            del row[groups.index('sample')+1]
    any_misses = count_word_occurrences("MISS", removed_sample)>0

    if any_bads:
        emoji = "❌"
    elif any_misses:
        emoji = "⚠️"
    else:
        emoji = "✅"
    
    write_pretty_output(f"## {emoji} {get_problem_name(problem)}\n")

    if any_misses:
        num_misses = count_word_occurrences("MISS", removed_sample)
        p_misses = num_misses / (len(removed_sample)*len(groups)) * 100
        write_pretty_output(f"### Misses: {num_misses}, {p_misses:.2f}% of all checks.\n")

    if any_bads:
        write_pretty_output(f"### Bads: {count_word_occurrences('BAD', data)}")


    headers = ['INPUT'] + groups
    write_pretty_output("<details>\n")
    write_pretty_output(print_table(data,headers))
    write_pretty_output("</details>\n")
    

def discover_problems(root: Path):
    if root.is_file():
        root = root.parent
    candidates = [p.parent for p in root.rglob('problem.yaml')]
    candidates = [p for p in candidates if "testdata_tools" not in str(p)]
    return candidates

if len(sys.argv) > 1:
    problems = discover_problems(Path(sys.argv[1]))
else:
    problems = discover_problems(Path(__file__))

num_problems = len(problems)
print(f"Will check {num_problems} problems.")
i=1
for problem in problems:
    print(f"Checking problem {i}/{num_problems}: {get_problem_name(problem)}")
    validate_problem(problem)
    i += 1

write_pretty_output("# NOTE:")
write_pretty_output("We don't count sample \"misses\" in most statistics")
