import os
import argparse
import re
from collections import defaultdict
from pathlib import Path

import yaml

ENTRY_TYPES = ('New Features',
               'API Changes', 'API changes',
               'Performance Improvements',
               'Bug Fixes', 'Bug fixes',
               'Miscellaneous',
               'General',
               'Other Changes and Additions',
               None)


yaml.Dumper.ignore_aliases = lambda *args : True


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)


def get_options(args=None):
    parser = argparse.ArgumentParser(
        description="Convert change log between formats")

    parser.add_argument("infile",
                        help="Input file")
    parser.add_argument("outfile",
                        help="Output file")
    parser.add_argument("--line-width",
                        help="Reformat output to line width (default=no reformatting)")
    parser.add_argument("--max-entries",
                        type=int,
                        help="Max number of RST entries to parse (default=None, for debug)")
    parser.add_argument("--print-info",
                        action='store_true',
                        help="Print releases and subpackages")

    args = parser.parse_args(args)
    return args


def get_pr_numbers(text):
    # Parse the PR numbers from text
    pr_text_match = re.search(r'\[ ([^]]+) \] [\.\s]* $', text, re.VERBOSE)
    if pr_text_match:
        pr_text = pr_text_match.group(1)
        prs = [int(match.group(1)) for match in re.finditer(r'#(\d+)', pr_text)]
    else:
        prs = []
    return prs


def get_entry(config, entry_lines):
    entry = config.copy()
    lines = [line[2:].strip() for line in entry_lines]
    entry['pull_requests'] = get_pr_numbers(' '.join(lines))

    # Now store text with newlines embedded
    entry['text'] = os.linesep.join(lines)

    return entry


def read_rst(filepath, max_entries=None):
    with open(filepath) as fh:
        lines = fh.readlines()
    lines.append('')

    config = {}
    entry_lines = []
    entries = []
    within_entry = False

    for line, line_next in zip(lines, lines[1:]):
        if within_entry or line.startswith('- '):
            entry_lines.append(line)

            if line_next.startswith('  '):
                within_entry = True
            else:
                within_entry = False
                entries.append(get_entry(config, entry_lines))
                if max_entries and len(entries) > max_entries:
                    break
                entry_lines.clear()

        elif re.match(r'[\^]+\s*$', line_next):
            config['subpackages'] = [line.strip()]

        elif re.match(r'[=]+\s*$', line_next):
            config['releases'] = [line.strip()]
            config['subpackages'] = [None]
            config['entry_types'] = [None]

        elif re.match(r'[-]+\s*$', line_next):
            config['entry_types'] = [line.strip()]
            config['subpackages'] = [None]

    return entries


def rst_header(text, section_char):
    if text is None:
        out = []
    else:
        out = [text, section_char * len(text), '']
    return out


def write_rst(entries, filepath):
    out = {}
    for entry in entries:
        text = entry['text']

        # If the text does not already have pull request numbers embedded
        # then add them now.
        text_prs = get_pr_numbers(text)
        entry_prs = entry.get('pull_requests')
        if not text_prs and entry_prs:
            text += ' [{}]'.format(', '.join(f'#{pr}' for pr in entry_prs))

        for release in entry['releases']:
            out.setdefault(release, {})
            for entry_type in entry['entry_types']:
                out[release].setdefault(entry_type, {})
                for subpackage in entry['subpackages']:
                    out[release][entry_type].setdefault(subpackage, [])
                    out[release][entry_type][subpackage].append(text)

    lines = []
    for release in reversed(sorted(out)):
        lines.extend(rst_header(release, '='))

        for entry_type in ENTRY_TYPES:
            if entry_type not in out[release]:
                continue

            lines.extend(rst_header(entry_type, '-'))
            subpackages = out[release][entry_type]
            if subpackages is None:
                print(release)
            for subpackage in subpackages:
                lines.extend(rst_header(subpackage, '^'))
                for text in out[release][entry_type][subpackage]:
                    for ii, text_line in enumerate(text.splitlines()):
                        hdr = '- ' if ii == 0 else '  '
                        lines.append(hdr + text_line)
                    lines.append('')

    with open(filepath, 'w') as fh:
        fh.writelines(line + os.linesep for line in lines)


def write_yaml(entries, filepath, line_width):
    if line_width is None:
        line_width = 100



    with open(filepath, 'w') as fh:
        yaml.dump(entries, fh, width=line_width)


def get_uniques(entries):
    uniques = defaultdict(set)
    for entry in entries:
        for key in ('subpackages', 'releases', 'entry_types'):
            vals = entry.get(key)
            if vals:
                for val in vals:
                    uniques[key].add(val)

    return uniques


if __name__ == '__main__':
    opt = get_options()
    infile = Path(opt.infile)
    outfile = Path(opt.outfile)

    if infile == outfile:
        raise ValueError('in-file and out-file must be different')

    # Input entries from either RST or YAML. The RST pathway is mostly for initial
    # testing and conversion of the legacy CHANGES.RST.
    if infile.suffix == '.rst':
        entries = read_rst(infile, opt.max_entries)
    elif infile.suffix == '.yml':
        with open(outfile, 'r') as fh:
            entries = yaml.safe_load(fh)
    else:
        raise ValueError('input must be .rst or .yml')

    # Output entries to either RST or YAML.  The YAML pathway is mostly for initial
    # testing and conversion of the legacy CHANGES.RST.
    if outfile.suffix == '.rst':
        write_rst(entries, outfile)
    elif outfile.suffix == '.yml':
        write_yaml(entries, outfile, opt.line_width)

    if opt.print_info:
        uniques = get_uniques(entries)
        for key in ('subpackages', 'releases', 'entry_types'):
            vals = uniques[key]
            print(key.title())
            for val in sorted(vals):
                print('  - ' + val)
            print()
