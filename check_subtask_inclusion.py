#!/usr/bin/python3

# This script will run all testcases towards the validation for all testgroups,
# and report any potential testcases which could also be included in additional groups.

import subprocess
import yaml
import concurrent.futures
import re
import os
import resource
import shutil
import tempfile
from pathlib import Path
from typing import Iterable, List, Any
import argparse
import signal
import sys

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

PROGRESS_BAR_WIDTH = 40

def progress_enabled():
    # Transient bar on stderr; only on an interactive console, never in Markdown output.
    return not target_markdown and sys.stderr.isatty()

def clear_progress():
    if progress_enabled():
        sys.stderr.write("\r\033[K")
        sys.stderr.flush()

def show_progress(done, total):
    if not progress_enabled():
        return
    filled = PROGRESS_BAR_WIDTH * done // total if total else PROGRESS_BAR_WIDTH
    bar = '#' * filled + '-' * (PROGRESS_BAR_WIDTH - filled)
    sys.stderr.write(f"\r[{bar}] {done}/{total}")
    sys.stderr.flush()
    if done == total:
        # Erase the bar so it does not end up between the results
        clear_progress()

def get_problem_name(problem: Path) -> str:
    problem_name = green(problem.resolve().name, console_only=True)
    parent = problem.parent.name
    if parent != Path(__file__).parent.name and parent:
        problem_name = parent + '/' + problem_name
    return problem_name

# Discovery mirrors problemtools' run.find_programs on input_validators
# Only C++ validators are compiled; everything else problemtools would run is warned about.
CPP_SUFFIXES = {'.cc', '.C', '.cpp', '.cxx', '.c++'}
# Extensions of the other languages in problemtools' languages.yaml.
OTHER_LANGUAGE_SUFFIXES = {
    '.c', '.cs', '.cob', '.fs', '.go', '.hs', '.java', '.js', '.kt', '.lisp', '.cl', '.ml', '.m',
    '.pas', '.php', '.pl', '.py', '.py2', '.py3', '.rb', '.rs', '.sc', '.scala',
}
VALIDATION_SCRIPT_SUFFIXES = {'.viva', '.ctd'}

# Validators are compiled in the background while other problems are validated;
# lowest CPU priority so compiling only uses cores the validation leaves idle.
NICE_PREFIX = ['nice', '-n', '19'] if shutil.which('nice') else []

def discover_validators(problem: Path, messages: List[str]):
    """Find every C++ input validator of a problem.

    Returns a list of (name, [C++ sources]) sorted by name; warnings are appended to messages.
    """
    input_validators_dir = problem / "input_validators"
    if not input_validators_dir.is_dir():
        return []

    validators = []
    for entry in sorted(input_validators_dir.iterdir()):
        rel = f"input_validators/{entry.name}"
        if entry.is_dir():
            build = entry / 'build'
            if build.is_file() and os.access(build, os.X_OK):
                messages.append(orange(f"Ignoring validator {rel}/: build scripts are not supported"))
                continue
            files = sorted(f for f in entry.rglob('*') if f.is_file())
            cpp_sources = [f for f in files if f.suffix in CPP_SUFFIXES]
            if cpp_sources:
                validators.append((entry.name, cpp_sources))
            elif any(f.suffix in OTHER_LANGUAGE_SUFFIXES for f in files):
                messages.append(orange(f"Ignoring validator {rel}/: only C++ is supported"))
        elif entry.is_file():
            if entry.suffix in CPP_SUFFIXES:
                validators.append((entry.stem, [entry]))
            elif entry.suffix in VALIDATION_SCRIPT_SUFFIXES:
                messages.append(orange(f"Ignoring validator {rel}: {entry.suffix} validation scripts are not supported"))
            elif entry.suffix in OTHER_LANGUAGE_SUFFIXES:
                messages.append(orange(f"Ignoring validator {rel}: only C++ is supported"))
    return validators

def compile_validators(problem: Path):
    """Discover and compile every C++ input validator of a problem.

    Runs ahead of time in a background thread, so nothing is printed here; output is
    collected in messages and printed once the problem's turn comes.
    Returns (messages, build_dir, executables); executables is None if the problem cannot be checked.
    """
    messages = []
    validators = discover_validators(problem, messages)
    if not validators:
        if target_markdown:
            messages.append("")
        warning_text = f'Skipping {get_problem_name(problem)}: no C++ input validator found in input_validators/'
        if (problem / "input_format_validators").is_dir():
            warning_text += ' (input_format_validators/ is the legacy name and is not supported; rename it to input_validators/)'
        messages.append(f"{h2()}{orange(warning_text)}\n")
        return messages, None, None

    if len(validators) > 1:
        messages.append(gray(f"Using {len(validators)} input validators: " + ', '.join(name for name, _ in validators)))

    build_dir = tempfile.mkdtemp(prefix=f'validator_{problem.name}_')
    try:
        # Compile every validator; all of them must accept an input for it to count as valid.
        executables = []
        for name, cpp_sources in validators:
            output_executable = str(Path(build_dir) / f'{name}.out')
            compile_command = NICE_PREFIX + ['g++', '-O2', *[str(p) for p in cpp_sources], '-o', output_executable, '-std=c++20']
            compile_process = subprocess.run(compile_command, capture_output=True, text=True)
            if compile_process.returncode != 0:
                messages.append(f"{h2()}{red(f'Validator Compilation Failed ({name}):')}")
                messages.append(red(compile_process.stderr))
                return messages, build_dir, None
            executables.append((name, output_executable))
    except BaseException:
        shutil.rmtree(build_dir, ignore_errors=True)
        raise
    return messages, build_dir, executables

def validate_problem(problem: Path, compiled):
    messages, build_dir, executables = compiled
    try:
        for message in messages:
            print(message)
        if executables is None:
            return

        def run_validator(file, flags, group):
            # Pass only if every validator returns 42.
            for _name, executable in executables:
                run_command = [executable] + flags.split()
                with open(file) as inp:
                    run_process = subprocess.run(run_command, stdin=inp, capture_output=True, text=True)
                if run_process.returncode != 42:
                    return False
            return True

        _validate_problem_data(problem, run_validator)
    finally:
        if build_dir is not None:
            shutil.rmtree(build_dir, ignore_errors=True)

def _validate_problem_data(problem: Path, run_validator):
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

    def get_group_name(tc):
        if 'sample' in tc_to_groups[tc]:
            return 'sample'
        return min(tc_to_groups[tc])

    inputs = sorted(inputs, key=lambda x: (groups.index(get_group_name(x)), re.search(r'(\d+)\.in$', x) is None, x))

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
            clear_progress()
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

            try:
                show_progress(0, len(futures))
                for done, _ in enumerate(concurrent.futures.as_completed(futures.values()), start=1):
                    show_progress(done, len(futures))
            except BaseException:
                # Interrupted: drop the queued checks and wait only for the running ones,
                # so the validators are not deleted from under them.
                executor.shutdown(cancel_futures=True)
                raise

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
# Queue every problem's compilation up front on a pool, and validate each problem as soon as
# its own validators are built, while the rest keep compiling in the background.
def interrupt(signum, frame):
    # Ignore repeated Ctrl-C so the cleanup can finish quietly.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, interrupt)
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as compiler:
        compiles = [compiler.submit(compile_validators, problem) for problem in problems]
        done = 0
        try:
            for i, problem in enumerate(problems, start=1):
                print(f"{h2()}Problem {i}/{num_problems}: {get_problem_name(problem)}")
                compiled = compiles[i - 1].result()
                done = i
                validate_problem(problem, compiled)
        finally:
            # Interrupted: drop the builds that will never be used.
            for future in compiles[done:]:
                if future.cancel():
                    continue
                try:
                    build_dir = future.result()[1]
                except BaseException:
                    build_dir = None
                if build_dir is not None:
                    shutil.rmtree(build_dir, ignore_errors=True)
except KeyboardInterrupt:
    clear_progress()
    print("Interrupted", file=sys.stderr)
    sys.exit(130)
