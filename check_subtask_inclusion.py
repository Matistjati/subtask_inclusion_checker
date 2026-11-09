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
import hashlib
import json
import signal
import sys
import time

def raise_soft_limit(limit):
    # The validators inherit these limits. An unprivileged process may only raise the soft
    # limit, and only up to the hard limit, which is not always infinite (the stack on macOS).
    try:
        _soft, hard = resource.getrlimit(limit)
        resource.setrlimit(limit, (hard, hard))
    except (ValueError, OSError):
        pass

raise_soft_limit(resource.RLIMIT_AS)
raise_soft_limit(resource.RLIMIT_STACK)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--target-markdown",
    action="store_true",
    help="Optimize output formatting for Markdown (otherwise console)"
)

parser.add_argument(
    "--no-cache",
    action="store_true",
    help="Compile every validator from scratch instead of reusing the builds of earlier runs"
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

def get_problem_name(problem: Path, colored=True) -> str:
    problem_name = problem.resolve().name
    if colored:
        problem_name = green(problem_name, console_only=True)
    parent = problem.parent.name
    if parent != Path(__file__).parent.name and parent:
        problem_name = parent + '/' + problem_name
    return problem_name

def count_str(count, singular, plural=None):
    if count == 1:
        return f"1 {singular}"
    return f"{count} {plural or singular + 's'}"

def print_summary(results):
    """Print one line per problem, so the outcome of a long run is visible without scrolling."""
    if len(results) < 2:
        # With a single problem, its own report is already the last thing printed
        return
    names = [get_problem_name(problem, colored=False) for problem, _ in results]
    if target_markdown:
        print("## Summary\n")
        print("| Problem | Result |")
        print("| ------- | ------ |")
        for name, (_, result) in zip(names, results):
            print(f"| {name} | {result} |")
        print("")
    else:
        print("Summary")
        width = max(len(name) for name in names)
        for name, (_, result) in zip(names, results):
            print(f"  {name.ljust(width)}  {result}")

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

COMPILE_FLAGS = ['-O2', '-std=c++20']

# Compiling takes far longer than validating, so builds are kept between runs. A build is
# reused only while every file it was compiled from (headers included) is unchanged.
CACHE_MAX_AGE = 30 * 24 * 3600
CACHE_SUFFIXES = ('.out', '.json', '.d')

def open_build_dir():
    """Returns (directory to compile into, whether to delete it afterwards)."""
    if not args.no_cache:
        cache_dir = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'subtask_inclusion_checker'
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            # Forget the builds that have not been used for a while
            oldest = time.time() - CACHE_MAX_AGE
            for entry in cache_dir.iterdir():
                if entry.name.endswith(CACHE_SUFFIXES) and entry.is_file() and entry.stat().st_mtime < oldest:
                    entry.unlink(missing_ok=True)
            return cache_dir, False
        except OSError:
            pass
    return Path(tempfile.mkdtemp(prefix='validators_')), True

def compiler_identity():
    compiler = shutil.which('g++')
    if compiler is None:
        return None
    compiler = os.path.realpath(compiler)
    stat = os.stat(compiler)
    return [compiler, stat.st_size, stat.st_mtime_ns]

COMPILER_IDENTITY = compiler_identity()

def file_hash(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def parse_dependencies(rules: str):
    """The files named as prerequisites in the Make rules a compiler writes."""
    dependencies = set()
    for rule in rules.replace('\\\n', ' ').splitlines():
        _target, separator, prerequisites = rule.partition(': ')
        if separator:
            for path in re.split(r'(?<!\\)\s+', prerequisites.strip()):
                if path:
                    dependencies.add(os.path.abspath(path.replace('\\ ', ' ').replace('\\#', '#').replace('$$', '$')))
    return dependencies

def is_up_to_date(executable: Path, manifest: Path):
    try:
        hashes = json.loads(manifest.read_text())
        return (isinstance(hashes, dict) and len(hashes) > 0 and executable.is_file()
                and all(file_hash(path) == expected for path, expected in hashes.items()))
    except (OSError, ValueError):
        return False

def compile_validator(cpp_sources: List[Path], build_dir: Path):
    """Compile one validator, or reuse the build of an earlier run.

    Returns (executable, None), or (None, compiler output) if it does not compile.
    """
    # Not resolved: includes are looked up next to the source as it is named, symlink or not
    sources = [os.path.abspath(p) for p in cpp_sources]
    key = hashlib.sha256(json.dumps([COMPILER_IDENTITY, COMPILE_FLAGS, sources]).encode()).hexdigest()[:32]
    executable = build_dir / f'{key}.out'
    manifest = build_dir / f'{key}.json'
    if is_up_to_date(executable, manifest):
        for path in (executable, manifest):
            os.utime(path)
        return str(executable), None

    # Compile under temporary names; a build only gets its real name once it is complete
    tmp_executable = build_dir / f'{key}.{os.getpid()}.tmp.out'
    tmp_manifest = build_dir / f'{key}.{os.getpid()}.tmp.json'
    tmp_dependencies = build_dir / f'{key}.{os.getpid()}.tmp.d'
    try:
        compile_command = NICE_PREFIX + ['g++', *COMPILE_FLAGS, *[str(p) for p in cpp_sources], '-o', str(tmp_executable)]
        # Have the compiler list the headers it reads. System headers are left out: they change
        # together with the compiler, which is part of the key. (One dependency file per
        # compiler run, so a validator of several sources is simply compiled every time.)
        track_dependencies = len(sources) == 1
        if track_dependencies:
            compile_command += ['-MMD', '-MF', str(tmp_dependencies)]
        compile_process = subprocess.run(compile_command, capture_output=True, text=True)
        if compile_process.returncode != 0:
            return None, compile_process.stderr

        manifest.unlink(missing_ok=True)
        os.replace(tmp_executable, executable)
        if track_dependencies:
            try:
                dependencies = parse_dependencies(tmp_dependencies.read_text()) | set(sources)
                tmp_manifest.write_text(json.dumps({path: file_hash(path) for path in sorted(dependencies)}))
                os.replace(tmp_manifest, manifest)
            except OSError:
                # Without its dependencies the build cannot be trusted next time; it is still good now
                pass
        return str(executable), None
    finally:
        for path in (tmp_executable, tmp_manifest, tmp_dependencies):
            path.unlink(missing_ok=True)

def compile_validators(problem: Path, build_dir: Path):
    """Discover and compile every C++ input validator of a problem.

    Runs ahead of time in a background thread, so nothing is printed here; output is
    collected in messages and printed once the problem's turn comes.
    Returns (messages, executables, failure); if the problem cannot be checked,
    executables is None and failure is its result for the summary.
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
        return messages, None, orange('skipped: no C++ input validator')

    if len(validators) > 1:
        messages.append(gray(f"Using {len(validators)} input validators: " + ', '.join(name for name, _ in validators)))

    # Compile every validator; all of them must accept an input for it to count as valid.
    executables = []
    for name, cpp_sources in validators:
        executable, error = compile_validator(cpp_sources, build_dir)
        if executable is None:
            messages.append(f"{h2()}{red(f'Validator Compilation Failed ({name}):')}")
            messages.append(red(error))
            return messages, None, red('validator compilation failed')
        executables.append(executable)
    return messages, executables, None

DEVNULL = os.open(os.devnull, os.O_RDWR)
# A plain dict: os.environ would be converted again for every run
ENVIRONMENT = dict(os.environ)

def run_executable(executable: str, arguments: List[str], input_path: str) -> int:
    """Run a program on an input file, discarding its output. Returns its exit code.

    subprocess.run costs about twice as much per run, which adds up over thousands of runs.
    """
    input_fd = os.open(input_path, os.O_RDONLY)
    try:
        pid = os.posix_spawn(executable, [executable, *arguments], ENVIRONMENT, file_actions=[
            (os.POSIX_SPAWN_DUP2, input_fd, 0),
            (os.POSIX_SPAWN_DUP2, DEVNULL, 1),
            (os.POSIX_SPAWN_DUP2, DEVNULL, 2),
        ])
    finally:
        os.close(input_fd)
    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)

def validate_problem(problem: Path, compiled):
    """Check one problem and print its report. Returns a one-line result for the summary."""
    messages, executables, failure = compiled
    for message in messages:
        print(message)
    if executables is None:
        return failure

    def run_validator(file, flags):
        # Pass only if every validator returns 42.
        arguments = flags.split()
        return all(run_executable(executable, arguments, file) == 42 for executable in executables)

    return _validate_problem_data(problem, run_validator)

def _validate_problem_data(problem: Path, run_validator):
    group_to_flags = {}
    tc_to_groups = {}
    infiles_path = {}
    group_testcases = {}

    data_dir = problem / 'data'
    if not data_dir.exists():
        print(f"{h2()}{red('skipping')} {get_problem_name(problem)}: no data\n")
        return orange('skipped: no data')

    if not (data_dir / 'secret').exists():
        print(f"{h2()}{red('skipping')} {get_problem_name(problem)}: no secret data\n")
        return orange('skipped: no secret data')

    num_subtasks = len(list(p for p in (data_dir / 'secret').iterdir() if p.is_dir()))
    if num_subtasks == 0:
        print(f"{h2()}{red('skipping')} {get_problem_name(problem)}: no subtasks\n")
        return orange('skipped: no subtasks')

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
                        # YAML parses a bare number (input_validator_flags: 10) as an int
                        flags = str(flag_value)
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

    # Groups with the same flags accept the same inputs, so each (input, flags) is validated once.
    # The largest inputs go first, which keeps the cores evenly loaded until the end.
    runs = sorted({(file, group_to_flags[group]) for file in inputs for group in groups},
                  key=lambda run: (-os.path.getsize(infiles_path[run[0]]), run))

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as executor:
        futures = {
            (file, flags): executor.submit(run_validator, infiles_path[file], flags)
            for file, flags in runs
        }

        try:
            show_progress(0, len(futures))
            for done, _ in enumerate(concurrent.futures.as_completed(futures.values()), start=1):
                show_progress(done, len(futures))
        except BaseException:
            # Interrupted: drop the queued checks and wait only for the running ones
            executor.shutdown(cancel_futures=True)
            raise

    def verdict(file, group):
        try:
            can_be_included = futures[(file, group_to_flags[group])].result()
        except Exception as e:
            print(f"{red('Exception while validating')} {file} for group {group}: {e}")
            return "UNKNOWN"
        is_included = group in tc_to_groups[file]
        if can_be_included == is_included:
            return OK_YES_STR if can_be_included else OK_NO_STR
        return MISS_STR if can_be_included else BAD_STR

    for file in inputs:
        data.append([file] + [verdict(file, group) for group in groups])


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
        if not target_markdown and len(lines) > shutil.get_terminal_size().lines:
            # The table does not fit on the screen: repeat the header below it,
            # so the columns can be read without scrolling back up.
            lines += [separator_line, header_line, separator_line]
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
    num_unknowns = count_verdict_occurrences("UNKNOWN", data)

    # The report is collected first: on a console it goes below the table, where the output ends.
    report = []
    if num_misses > 0:
        p_misses = num_misses / (len(data)*len(groups)) * 100
        report.append(f"{h3()}{orange('Misses')}: {num_misses}, {p_misses:.2f}% of all checks.\n")

    if num_bads > 0:
        report.append(f"{h3()}{red('Bads')}: {num_bads}")

    # Subtask inclusion misses
    all_missed_inclusions = []
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
            report.append(f"{warning_string}: {orange(g1, console_only=True)} can be included in {orange(missed_inclusions[0], console_only=True)}")
        else:
            report.append(f"{warning_string}: {orange(g1, console_only=True)} can be included in")
            for g2 in missed_inclusions:
                report.append(f" - {orange(g2, console_only=True)}")
        if target_markdown:
            report.append("")
        all_missed_inclusions += [(g1, g2) for g2 in missed_inclusions]

    headers = ['INPUT'] + groups
    if target_markdown:
        # The table is collapsed, so the report goes first
        for line in report:
            print(line)
        print("")
        print("<details>\n")
        print(print_table(data,headers))
        print("")
        print("</details>\n")
        print("")
    else:
        # The table can be long, so the report goes last: no scrolling back up to read it
        print(print_table(data,headers))
        print("")
        for line in report:
            print(line)
        if report:
            print("")

    # The result for the summary: short, the details are in the report above
    def count_testcases(verdict, skip=()):
        # How many test cases have this verdict in some group's column
        return sum(1 for row in data
                   if any(cell == verdict and (row[0], group) not in skip for group, cell in zip(groups, row[1:])))

    num_group_inclusions = sum(1 for g1, _ in all_missed_inclusions if g1 != 'sample')
    num_sample_inclusions = len(all_missed_inclusions) - num_group_inclusions
    # Misses that are not part of a whole group that could be included
    in_missed_inclusion = {(tc, g2) for g1, g2 in all_missed_inclusions for tc in group_testcases[g1]}
    num_stray = count_testcases(MISS_STR, skip=in_missed_inclusion)
    num_invalid = count_testcases(BAD_STR)

    result = []
    if num_group_inclusions > 0:
        result.append(red(count_str(num_group_inclusions, 'missed inclusion')))
    if num_sample_inclusions > 0:
        result.append(orange(count_str(num_sample_inclusions, 'missed sample inclusion')))
    if num_invalid > 0:
        result.append(red(count_str(num_invalid, 'invalid test case')))
    if num_unknowns > 0:
        result.append(red(count_str(num_unknowns, 'check') + ' could not be run'))
    if num_stray > 0:
        result.append(orange(f"{num_stray} of {len(data)} test cases {'fits' if num_stray == 1 else 'fit'} more groups"))
    return ', '.join(result) if result else green('OK')

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
build_dir, build_dir_is_temporary = open_build_dir()
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as compiler:
        compiles = [compiler.submit(compile_validators, problem, build_dir) for problem in problems]
        results = []
        try:
            for i, problem in enumerate(problems, start=1):
                print(f"{h2()}Problem {i}/{num_problems}: {get_problem_name(problem)}")
                results.append((problem, validate_problem(problem, compiles[i - 1].result())))
            print_summary(results)
        finally:
            # Interrupted: drop the compilations that have not started. Leaving the
            # block waits for the running ones, so nothing is deleted from under them.
            for future in compiles:
                future.cancel()
except KeyboardInterrupt:
    clear_progress()
    print("Interrupted", file=sys.stderr)
    sys.exit(130)
finally:
    if build_dir_is_temporary:
        shutil.rmtree(build_dir, ignore_errors=True)
