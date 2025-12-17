#!/usr/bin/python3

# This script will run all testcases towards the validation for all testgroups,
# and report any potential testcases which could also be included in additional groups.

import subprocess
import os
import yaml
import concurrent.futures
import re
import resource
from pathlib import Path
from typing import Iterable, List, Any
import argparse

resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

parser = argparse.ArgumentParser()
parser.add_argument(
    "--target-markdown",
    action="store_true",
    help="Optimize output formatting for Markdown (otherwise console)"
)

parser.add_argument(
    "directory",
    nargs="?",
    default=Path("."),
    type=Path,
    help="Directory to process (default: current directory)"
)

args = parser.parse_args()
target_markdown = args.target_markdown

# Formatting
OK_STR = "OK"
OK_NO_STR = "OK:N"
OK_YES_STR = "OK:Y"
SKIP_STR = "SKIP"
MISS_STR = "MISS"
BAD_STR = "BAD"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    ORANGE = '\033[93m'
    GRAY = '\033[90m'
    RESET = '\033[0m'

def orange(text, console_only=False):
    if target_markdown:
        if console_only:
            return text
        return f"⚠️{text}"
    return f"{Colors.ORANGE}{text}{Colors.RESET}"

def red(text, console_only=False):
    if target_markdown:
        if console_only:
            return text
        return f"❌{text}"
    return f"{Colors.RED}{text}{Colors.RESET}"

def green(text, console_only=False):
    if target_markdown:
        if console_only:
            return text
        return f"✅{text}"
    return f"{Colors.GREEN}{text}{Colors.RESET}"

def gray(text, console_only=False):
    if target_markdown:
        return text
    return f"{Colors.GRAY}{text}{Colors.RESET}"

def h2():
    if target_markdown:
        return "## "
    return ""

def h3():
    if target_markdown:
        return "### "
    return ""

def print_md_newline():
    if target_markdown:
        print("")

def get_problem_name(problem: Path) -> str:
    problem_name = green(problem.name, console_only=True)
    parent = problem.parent.name
    if parent != Path(__file__).parent.name and parent:
        problem_name = parent + '/' + problem_name
    return problem_name

def validate_problem(problem: Path):
    # Name of the C++ source file
    input_validator_path = "input_validators/validator/validator.cpp"
    cpp_file = problem / input_validator_path
    if not cpp_file.exists():
        print_md_newline()
        warning_text = f'Skipping {get_problem_name(problem)}: no C++ input validator found. Looked at {input_validator_path}'
        print(f"{h2()}{orange(warning_text)}\n")
        return
    # Name of the output executable
    output_executable = '/tmp/validator.out'

    # Compile the C++ file
    compile_command = ['g++', '-O2', cpp_file, '-o', output_executable, '-std=c++20']
    compile_process = subprocess.run(compile_command, capture_output=True, text=True)

    # Check if compilation was successful
    if compile_process.returncode != 0:
        print(f"{h2()}{red('Validator Compilation Failed:')}")
        print(red(compile_process.stderr))
        return

    def run_validator(file, flags, group):
        run_command = [output_executable] + flags.split()
        with open(file) as inp:
            run_process = subprocess.run(run_command, stdin=inp, capture_output=True, text=True)
            return run_process.returncode == 42

    group_to_flags = {}
    tc_to_groups = {}
    infiles_path = {}
    group_testcases = {}

    # os.walk generates the file names in a directory tree
    for dirpath, dirnames, filenames in os.walk(os.path.join(problem,'data')):
        group = os.path.basename(dirpath)
        if group not in ("data", "secret"):
            group_to_flags[group] = ""
            group_testcases[group] = []
        if "testdata.yaml" in filenames:
            with open(os.path.join(dirpath,'testdata.yaml'), 'r') as file:
                # Load the YAML content
                config = yaml.safe_load(file)
                if 'input_validator_flags' in config:
                    group_to_flags[group] = config['input_validator_flags']
        for file in filenames:
            if file.endswith('.in'):
                if file not in tc_to_groups:
                    tc_to_groups[file] = []
                group_testcases[group].append(file)
                tc_to_groups[file].append(group)
                infiles_path[file] = os.path.join(dirpath,file)

    inputs = sorted(tc_to_groups.keys())
    groups = sorted(group_to_flags.keys())
    if 'sample' in groups:
        groups.remove('sample')
        groups = ['sample'] + groups

    inputs = sorted(inputs, key=lambda x: (re.match(r'(\d+)\.in', x) is None, x))

    data = []

    def go(file, g):
        try:
            val = run_validator(infiles_path[file],group_to_flags[g],g)
            inc = 1 if g in tc_to_groups[file] else 0
            if val == inc:
                return f"{OK_YES_STR}" if val else f"{OK_NO_STR}"
            elif val:
                return MISS_STR
            else:
                return BAD_STR
        except Exception as e:
            print(f"{red('Exception while validating')} {file} for group {g}: {e}")
            return "UNKNOWN"

    for file in inputs:
        #row = [file] + [go(file, g) for g in groups]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(go, file, g) for g in groups]
            row = [file] + [future.result() for future in futures]
        data.append(row)


    def print_table(data: Iterable[Iterable[Any]], headers: Iterable[Any]) -> str:
        ncols = max(len(headers), max((len(r) for r in data), default=0))

        col_widths: List[int] = []
        for col in range(ncols):
            max_width = len(headers[col])
            for r in data:
                max_width = max(max_width, len(r[col]))
            col_widths.append(max(3, max_width))
        col_widths[0] = max(col_widths[0], max(len(g) for g in groups))

        def pad(text: str, width: int, text_width=None) -> str:
            if not text_width:
                text_width = len(text)
            w = (width - text_width)
            l_half = w//2
            r_half = w-l_half
            return ' ' * l_half + text + ' ' * r_half

        def color_cell(cell: str) -> str:
            if OK_STR in cell:
                return green(cell)
            elif MISS_STR in cell:
                return orange(cell)
            elif BAD_STR in cell:
                return red(cell)
            elif SKIP_STR in cell:
                return gray(cell)
            return cell

        def format_group(group_name, sep='-'):
            if target_markdown:
                group_name = pad(f"#{group_name}", col_widths[0])
            else:
                group_name = pad(green(group_name, console_only=True), col_widths[0], len(group_name))
            contents = [group_name] + [pad(sep * col_widths[i], col_widths[i]) for i in range(1, len(col_widths))]
            line = '| ' + ' | '.join(contents[i] for i in range(len(contents))) + ' |'
            return line

        row_lines = []
        if "sample" in groups:
            row_lines.append(format_group("sample", sep=' '))

        def get_group_name(tc):
            if 'sample' in tc_to_groups[tc]:
                return 'sample'
            return min(tc_to_groups[tc])

        for r in range(len(data)):
            line = '| ' + ' | '.join(pad(color_cell(data[r][i]), col_widths[i], len(data[r][i])) for i in range(ncols)) + ' |'
            row_lines.append(line)
            
            # Insert group names inbetween
            if r + 1 < len(data):
                curr_tc = data[r][0]
                next_tc = data[r+1][0]
                if get_group_name(curr_tc) != get_group_name(next_tc):
                    row_lines.append(format_group(get_group_name(next_tc)))

        header_line = '| ' + ' | '.join(pad(headers[i], col_widths[i]) for i in range(ncols)) + ' |'
        separator_line = '| ' + ' | '.join('-' * col_widths[i] for i in range(ncols)) + ' |'

        lines = [separator_line if not target_markdown else '', header_line, separator_line] + row_lines
        table = '\n'.join(lines)

        return table

    def count_word_occurrences(word, table):
        count = 0
        for row in table:
            for item in row:
                if word in item:
                    count += 1
        return count

    # We really dont care what couldve been put in sample
    if 'sample' in groups:
        for row in data:
            if row[groups.index('sample')+1] == MISS_STR:
                row[groups.index('sample')+1] = SKIP_STR

    # Warning/bad summary
    any_bads = count_word_occurrences(BAD_STR, data)>0
    any_misses = count_word_occurrences(MISS_STR, data)>0

    if any_misses:
        num_misses = count_word_occurrences(MISS_STR, data)
        p_misses = num_misses / (len(data)*len(groups)) * 100
        print(f"{h3()}{orange('Misses')}: {num_misses}, {p_misses:.2f}% of all checks.\n")

    if any_bads:
        print(f"{h3()}{red('Bads')}: {count_word_occurrences('BAD', data)}")

    # Subtask inclusion misses
    tc_index = {}
    for i in range(len(data)):
        tc_index[data[i][0]] = i
    for g1 in groups:
        missed_inclusions = []
        for g2_ind, g2 in enumerate(groups):
            if g2 == "sample":
                continue

            include_allowed = True
            any_miss = False
            for tc in group_testcases[g1]:
                verdict = data[tc_index[tc]][g2_ind + 1]
                if verdict in (OK_NO_STR, BAD_STR):
                    include_allowed = False
                    break
                if verdict == MISS_STR:
                    any_miss = True

            if include_allowed and any_miss:
                missed_inclusions.append(g2)

        warning_string = orange('Missed sample inclusion') if g1 == 'sample' else red('Missed inclusion')
        if not missed_inclusions:
            continue
        elif len(missed_inclusions) == 1:
            print(f"{warning_string}: {orange(g1, console_only=True)} can be included in {orange(missed_inclusions[0], console_only=True)}")
        else:
            print(f"{warning_string}: {orange(g1, console_only=True)} can be included in")
            for g2 in missed_inclusions:
                print(f" - {orange(g2, console_only=True)}")
        print_md_newline()

    # Table
    print("")
    headers = ['INPUT'] + groups
    if target_markdown:
        print("<details>\n")
    print(print_table(data,headers))
    print_md_newline()
    if target_markdown:
        print("</details>\n")
    print("")

def discover_problems(root: Path):
    if root.is_file():
        root = root.parent
    candidates = [p.parent for p in root.rglob('problem.yaml')]
    candidates = [p for p in candidates if "testdata_tools" not in str(p)]
    return candidates

directory = args.directory
problems = discover_problems(directory)

num_problems = len(problems)
plural = '' if num_problems == 1 else 's'
print(f"Will check {num_problems} problem{plural}.")
i=1
for problem in problems:
    print(f"{h2()}Problem {i}/{num_problems}: {get_problem_name(problem)}")
    validate_problem(problem)
    i += 1
