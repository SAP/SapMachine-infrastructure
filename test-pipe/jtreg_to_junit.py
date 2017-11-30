import os
import sys
import re

def main(argv=None):
    jtreg_in = argv[0]
    junit_out = argv[1]
    test_suite_name = argv[2]

    pattern = re.compile('(\S+/(\S+))\.([^\s#]+)(#id[0-9]+)?\s*(Not run|Passed|Failed|Error)\.(.*)?')
    num_tests_passed = 0
    num_tests_failed = 0
    num_tests_error = 0
    num_tests_skipped = 0

    with open(jtreg_in, 'r') as i:
        lines_in = i.readlines()
        lines_out = []

        for line in lines_in:
            match = pattern.match(line)

            if match is not None:
                classname = match.group(1).replace('/', '.')
                name = match.group(2)
                test_id = match.group(4)
                test_result = match.group(5)
                test_detail = match.group(6)

                if test_id is not None:
                    name = name + test_id

                if test_result == 'Passed':
                    num_tests_passed += 1
                    lines_out.append(str.format('    <testcase classname="{0}" name="{1}"/>', classname, name))

                if test_result == 'Failed' or test_result == 'Error':
                    lines_out.append(str.format('    <testcase classname="{0}" name="{1}">', classname, name))

                    if test_result == 'Failed':
                        num_tests_failed += 1
                        lines_out.append(str.format('        <failure message="{0}"/>', test_detail))
                    else:
                        num_tests_error += 1
                        lines_out.append(str.format('        <error message="{0}"/>', test_detail))

                    lines_out.append('    </testcase>')

                if test_result == 'Not run':
                    num_tests_skipped += 1
                    lines_out.append(str.format('    <testcase classname="{0}" name="{1}">', classname, name))
                    lines_out.append('        <skipped/>')
                    lines_out.append('    </testcase>')

            else:
                raise Exception(str.format('Failed to parse line "{0}"!', line))

        with open(junit_out, 'w+') as o:
            num_tests = num_tests_passed + num_tests_skipped + num_tests_failed + num_tests_error
            o.write(str.format('<testsuite name="{0}" tests="{1}">\n', test_suite_name, num_tests))
            o.write('\n'.join([line for line in lines_out]) )
            o.write('\n</testsuite>\n')

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))