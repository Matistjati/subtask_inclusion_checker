# Subtask Inclusion Checker

A Github action that checks the validity of the testdata in a [Kattis problem package](https://www.kattis.com/problem-package-format/spec/legacy.html).
More specifically, for problems with groups representing subtasks, it runs each testcase with the flags in each group and checks if
it could've been included in said group. If there are big columns of misses, this either means that you should include the testcases in said
group using symlinks or `include_group` if you're using testdata_tools, or tighten your input validator. Of course, some subtask constraints are impossible
to validate, such as "the input is generated uniformly at random", in which case you have to live with the false positive. The sample column will also frequently
contain false positives.

To add this to your problem repository, simply create the file `.github/workflows/ci.yaml`, and copy the contents of `ci.yaml` into it.
It will then trigger on every push. Note that this can easily consume lots of compute time. I am not responsible if the script acts up
and uses a lot of compute. As a safety measure, I have put in a 10 minute timeout.

A standalone, command-line version of the script is also provided in the file `standalone_subtask_inclusion.py`.

Credits to Joakim Blikstad for having the idea for the Python script and writing the first version.

Typical output (can be seen in the summary tab of the action in Github):

## ⚠️ online/tvakraft

### Misses: 1, 0.83% of all checks.

<details>

| INPUT        | sample | group1 | group2 |
| ------------ | ------ | ------ | ------ |
| 1.in         | ✅OK:Y  | ✅OK:Y  | ✅OK:Y  |
| 2.in         | ✅OK:Y  | ✅OK:Y  | ✅OK:Y  |
| 3.in         | ✅OK:Y  | ⚠️MISS | ✅OK:Y  |
| 4.in         | ✅OK:Y  | ✅OK:N  | ✅OK:Y  |
| 001-g1-01.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 002-g1-02.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 003-g1-03.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 004-g1-04.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 005-g1-05.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 006-g1-06.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 007-g1-07.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 008-g1-08.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 009-g1-09.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 010-g1-10.in | ⚠️MISS | ✅OK:Y  | ✅OK:Y  |
| 011-g2-01.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 012-g2-02.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 013-g2-03.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 014-g2-04.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 015-g2-05.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 016-g2-06.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 017-g2-07.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 018-g2-08.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 019-g2-09.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 020-g2-10.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 021-g2-11.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 022-g2-12.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 023-g2-13.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 024-g2-14.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 025-g2-15.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 026-g2-16.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 027-g2-17.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 028-g2-18.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 029-g2-19.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 030-g2-20.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 031-g2-21.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 032-g2-22.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 033-g2-23.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 034-g2-24.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 035-g2-25.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
| 036-g2-26.in | ⚠️MISS | ✅OK:N  | ✅OK:Y  |
</details>

## ✅ online/hemligvandring

<details>

| INPUT        | sample | group1 | group2 | group3 | group4 |
| ------------ | ------ | ------ | ------ | ------ | ------ |
| 1.in         | ✅OK:Y  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  |
| 2.in         | ✅OK:Y  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  |
| 001-g1-01.in | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  | ✅OK:N  |
| 002-g1-02.in | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  | ✅OK:N  |
| 003-g1-03.in | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  | ✅OK:N  |
| 004-g1-04.in | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  | ✅OK:N  |
| 005-g2-01.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 006-g2-02.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 007-g2-03.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 008-g2-04.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 009-g2-05.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 010-g2-06.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 011-g2-07.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 012-g2-08.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 013-g2-09.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 014-g2-10.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 015-g2-11.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 016-g2-12.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 017-g2-13.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 018-g2-14.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 019-g2-15.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 020-g2-16.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 021-g2-17.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 022-g2-18.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 023-g2-19.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 024-g2-20.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 025-g2-21.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 026-g2-22.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 027-g2-23.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 028-g2-24.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 029-g2-25.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 030-g2-26.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 031-g2-27.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 032-g2-28.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 033-g2-29.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 034-g2-30.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 035-g2-31.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 036-g2-32.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 037-g2-33.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 038-g2-34.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 039-g2-35.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 040-g2-36.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 041-g2-37.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 042-g2-38.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 043-g2-39.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 044-g2-40.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 045-g2-41.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 046-g2-42.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 047-g2-43.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 048-g2-44.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 049-g2-45.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 050-g2-46.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 051-g2-47.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 052-g2-48.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 053-g2-49.in | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  | ✅OK:N  |
| 054-g3-01.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 055-g3-02.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 056-g3-03.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 057-g3-04.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 058-g3-05.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 059-g3-06.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 060-g3-07.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 061-g3-08.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 062-g3-09.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 063-g3-10.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 064-g3-11.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 065-g3-12.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 066-g3-13.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 067-g3-14.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 068-g3-15.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 069-g3-16.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 070-g3-17.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 071-g3-18.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 072-g3-19.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 073-g3-20.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 074-g3-21.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 075-g3-22.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 076-g3-23.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 077-g3-24.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 078-g3-25.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 079-g3-26.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 080-g3-27.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 081-g3-28.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 082-g3-29.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 083-g3-30.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 084-g3-31.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 085-g3-32.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 086-g3-33.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 087-g3-34.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 088-g3-35.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 089-g3-36.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 090-g3-37.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 091-g3-38.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  | ✅OK:N  |
| 092-g4-01.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 093-g4-02.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 094-g4-03.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 095-g4-04.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 096-g4-05.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 097-g4-06.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 098-g4-07.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 099-g4-08.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 100-g4-09.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 101-g4-10.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 102-g4-11.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 103-g4-12.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 104-g4-13.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 105-g4-14.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 106-g4-15.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 107-g4-16.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 108-g4-17.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 109-g4-18.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 110-g4-19.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 111-g4-20.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 112-g4-21.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 113-g4-22.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 114-g4-23.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 115-g4-24.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 116-g4-25.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 117-g4-26.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 118-g4-27.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 119-g4-28.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 120-g4-29.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 121-g4-30.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 122-g4-31.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 123-g4-32.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 124-g4-33.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 125-g4-34.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 126-g4-35.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 127-g4-36.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 128-g4-37.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 129-g4-38.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 130-g4-39.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 131-g4-40.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 132-g4-41.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 133-g4-42.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 134-g4-43.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 135-g4-44.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 136-g4-45.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 137-g4-46.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 138-g4-47.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 139-g4-48.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 140-g4-49.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 141-g4-50.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 142-g4-51.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 143-g4-52.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 144-g4-53.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 145-g4-54.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 146-g4-55.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 147-g4-56.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 148-g4-57.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 149-g4-58.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 150-g4-59.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 151-g4-60.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 152-g4-61.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 153-g4-62.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 154-g4-63.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 155-g4-64.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 156-g4-65.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 157-g4-66.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 158-g4-67.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 159-g4-68.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 160-g4-69.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 161-g4-70.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 162-g4-71.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 163-g4-72.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 164-g4-73.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 165-g4-74.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 166-g4-75.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 167-g4-76.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 168-g4-77.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 169-g4-78.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 170-g4-79.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 171-g4-80.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 172-g4-81.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 173-g4-82.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 174-g4-83.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 175-g4-84.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 176-g4-85.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 177-g4-86.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 178-g4-87.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 179-g4-88.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 180-g4-89.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
| 181-g4-90.in | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:N  | ✅OK:Y  |
</details>

# Fragility
It's not uncommon for input validators to use assert. This can easily lead to the Github runner being overwhelmed by many Apport
instances spawning at once (one is created per crashing input validator). I have disabled it, but it's not unreasonable that
similar issues might present themselves in the future or on other systems.
