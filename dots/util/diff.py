import difflib

from dots.util import colors


def get_diff_line(string_a, string_b):
    output = []
    matcher = difflib.SequenceMatcher(None, string_a, string_b)

    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == "equal":
            output += [string_a[a0:a1]]
        elif opcode == "insert":
            output += [colors.fmt(string_b[b0:b1], bg="green")]
        elif opcode == "delete":
            output += [colors.fmt(string_a[a0:a1], bg="red")]
        elif opcode == "replace":
            output += [colors.fmt(string_b[b0:b1], bg="green")]
            output += [colors.fmt(string_a[a0:a1], bg="red")]

    return "".join(output)


def format_range_unified(start, stop):
    beginning = start + 1
    length = stop - start

    if length == 1:
        return "{}".format(beginning)

    if not length:
        beginning -= 1

    return "{},{}".format(beginning, length)


# flake8: noqa: C901
def _get_diff_lines(
    a,
    b,
    fromfile="",
    tofile="",
    fromfiledate=None,
    tofiledate=None,
    lineterm="\n",
):
    n = 2
    started = False
    for group in difflib.SequenceMatcher(None, a, b).get_grouped_opcodes(n):
        if not started:
            started = True
            fromdate = "\t{}".format(fromfiledate) if fromfiledate else ""
            todate = "\t{}".format(tofiledate) if tofiledate else ""

            yield "--- {}{}{}".format(fromfile, fromdate, lineterm)
            yield "+++ {}{}{}".format(tofile, todate, lineterm)

        first, last = group[0], group[-1]
        file1_range = format_range_unified(first[1], last[2])
        file2_range = format_range_unified(first[3], last[4])

        yield "@@ -{} +{} @@{}".format(file1_range, file2_range, lineterm)

        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                for line in a[i1:i2]:
                    yield " " + line
                continue

            if tag == "delete":
                for line in a[i1:i2]:
                    yield colors.fmt_line("-" + line, bg="red")

            if tag == "insert":
                for line in b[j1:j2]:
                    yield colors.fmt_line("+" + line, bg="green")

            if tag == "replace":
                for i in range(min(len(a[i1:i2]), len(b[j1:j2]))):
                    yield colors.fmt_line("~", bg="light_cyan") + get_diff_line(
                        a[i1:i2][i], b[j1:j2][i]
                    )

                for i in range(
                    min(len(a[i1:i2]), len(b[j1:j2])), max(len(a[i1:i2]), len(b[j1:j2]))
                ):
                    if i < len(a[i1:i2]):
                        yield colors.fmt_line("+" + a[i1:i2][i], bg="green")

                    elif i < len(b[j1:j2]):
                        yield colors.fmt_line("+" + b[j1:j2][i], bg="green")


def get_diff_lines(
    a, b, fromfile="", tofile="", fromfiledate=None, tofiledate=None, lineterm="\n"
):
    return list(
        _get_diff_lines(a, b, fromfile, tofile, fromfiledate, tofiledate, lineterm)
    )
