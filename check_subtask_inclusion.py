#!/usr/bin/python3

# This script will run all testcases towards the validation for all testgroups,
# and report any potential testcases which could also be included in additional groups.

import subprocess
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
    problem_name = green(problem.resolve().name, console_only=True)
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
    output_executable = f'/tmp/validator_{problem.name}.out'

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

    data_dir = problem / 'data'
    if not data_dir.exists():
        print(f"{h2()}{red('skipping')} {get_problem_name(problem)}: no data\n")
        return

    if not (data_dir / 'secret').exists():
        print(f"{h2()}{red('skipping')} {get_problem_name(problem)}: no secret data\n")
        return

    num_subtasks = len(list(p for p in (data_dir / 'secret').iterdir() if p.is_dir()))
    if num_subtasks == 0:
        print(f"{h2()}{red('skipping')} {get_problem_name(problem)}: no subtasks\n")
        return

    for in_file in data_dir.rglob('*.in'):
        group_file = in_file.parent
        group_name = group_file.name
        if group_name in ('data', 'secret'):
            # These test cases do not belong to a group
            continue

        # First time seeing this group
        if group_name not in group_to_flags:
            flags = ""
            search_dir = group_file.resolve()
            while True:
                config_path = search_dir / "testdata.yaml"
                if config_path.exists():
                    with open(config_path) as f:
                        parsed = yaml.safe_load(f)
                    flag_value = (parsed or {}).get("input_validator_flags")
                    if flag_value is not None:
                        flags = flag_value
                        break
                if search_dir == data_dir.resolve():
                    break
                search_dir = search_dir.parent

            group_to_flags[group_name] = flags
            group_testcases[group_name] = []

        root_testcase = in_file.resolve()
        testcase_name = str(root_testcase.relative_to(data_dir.resolve()))
        if testcase_name not in tc_to_groups:
            tc_to_groups[testcase_name] = []
        tc_to_groups[testcase_name].append(group_name)
        group_testcases[group_name].append(testcase_name)
        infiles_path[testcase_name] = str(root_testcase)

    inputs = sorted(tc_to_groups.keys())
    groups = sorted(group_to_flags.keys())
    if 'sample' in groups:
        # Ensure sample is always first
        groups.remove('sample')
        groups = ['sample'] + groups

    inputs = sorted(inputs, key=lambda x: (re.search(r'(\d+)\.in$', x) is None, x))

    data = []

    def go(file, group):
        try:
            can_be_included = run_validator(infiles_path[file], group_to_flags[group], group)
            is_included = 1 if group in tc_to_groups[file] else 0
            if can_be_included == is_included:
                return OK_YES_STR if can_be_included else OK_NO_STR
            elif can_be_included:
                return MISS_STR
            else:
                return BAD_STR
        except Exception as e:
            print(f"{red('Exception while validating')} {file} for group {group}: {e}")
            return "UNKNOWN"

    if 0:
        # For debugging purposes
        for file in inputs:
            row = [file] + [go(file, g) for g in groups]
            data.append(row)
    else:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                (file, group): executor.submit(go, file, group)
                for file in inputs
                for group in groups
            }

            for file in inputs:
                row = [file]
                for group in groups:
                    result = futures[(file, group)].result()
                    row.append(result)
                data.append(row)


    def print_table(data: Iterable[Iterable[Any]], headers: Iterable[Any]) -> str:
        ncols = max(len(headers), max((len(r) for r in data), default=0))

        col_widths: List[int] = []
        for col in range(ncols):
            max_width = len(headers[col])
            if col == 0:
                max_width = max(max_width, max((len(Path(r[col]).name) for r in data)))
            else:
                max_width = max(max_width, max((len(r[col]) for r in data)))
            col_widths.append(max(3, max_width))
        col_widths[0] = max(col_widths[0], max(len(g) for g in groups))

        def pad(text: str, width: int, text_width=None) -> str:
            if text_width is None:
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
            row = data[r][:]
            row[0] = Path(data[r][0]).name
            line = '| ' + ' | '.join(pad(color_cell(row[i]), col_widths[i], len(row[i])) for i in range(ncols)) + ' |'
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

    def count_verdict_occurrences(verdict, table):
        count = 0
        for row in table:
            for item in row[1:]:
                if verdict in item:
                    count += 1
        return count

    # We really dont care what couldve been put in sample
    if 'sample' in groups:
        for row in data:
            if row[groups.index('sample')+1] == MISS_STR:
                row[groups.index('sample')+1] = SKIP_STR

    # Warning/bad summary
    num_bads = count_verdict_occurrences(BAD_STR, data)
    num_misses = count_verdict_occurrences(MISS_STR, data)

    if num_misses > 0:
        p_misses = num_misses / (len(data)*len(groups)) * 100
        print(f"{h3()}{orange('Misses')}: {num_misses}, {p_misses:.2f}% of all checks.\n")

    if num_bads > 0:
        print(f"{h3()}{red('Bads')}: {num_bads}")

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

problems = sorted(discover_problems(args.directory))

num_problems = len(problems)
plural = '' if num_problems == 1 else 's'
print(f"Will check {num_problems} problem{plural}.")
i=1
for problem in problems:
    print(f"{h2()}Problem {i}/{num_problems}: {get_problem_name(problem)}")
    validate_problem(problem)
    i += 1
