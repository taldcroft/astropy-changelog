#!/usr/bin/env python

import os
import argparse
import re
from collections import defaultdict
from pathlib import Path
import textwrap

import yaml

# This is the set of entry_type values from the astropy CHANGES.rst as of 4.0
LEGACY_ENTRY_TYPES = [
    'New Features',
    'API Changes', 'API changes',
    'Performance Improvements',
    'Bug Fixes', 'Bug fixes',
    'Miscellaneous',
    'General',
    'Other Changes and Additions',
    None]

# Allowed entry types for non-legacy entries
ENTRY_TYPES = [
    'New Features',
    'API Changes',
    'Performance Improvements',
    'Bug Fixes',
    'Other Changes']

# Recommended subpackages
SUBPACKAGES = [
    'astropy.config',
    'astropy.constants',
    'astropy.convolution',
    'astropy.coordinates',
    'astropy.cosmology',
    'astropy.io.ascii',
    'astropy.io.fits',
    'astropy.io.misc',
    'astropy.io.registry',
    'astropy.io.votable',
    'astropy.logger',
    'astropy.modeling',
    'astropy.nddata',
    'astropy.samp',
    'astropy.stats',
    'astropy.table',
    'astropy.tests',
    'astropy.time',
    'astropy.timeseries',
    'astropy.uncertainty',
    'astropy.units',
    'astropy.utils',
    'astropy.visualization',
    'astropy.wcs']

INSTRUCTIONS = """\
In order to add an entry to the astropy changelog, copy the template entry
(which immediately follows the --- below this text) to a quasi-random location
of this file (NOT the top or bottom).  The fill in each of the values:

entry_types: determine which of the types in the template apply to this change.
This maybe be just one or multiple, for instance "New Features" and
"Bug Fixes" are common. Enter the one or more types verbatim from the
template list, separated by comma.

pull_requests: enter one or more pull request numbers that relate to the change,
separated a comma.

releases: enter one or more releases where this change should be included.
Pure bug fixes may be backported to the current stable and LTS releases.
Enter the applicable release from the milestone list that can be found
at https://github.com/astropy/astropy/milestones.

subpackages: enter one or more astropy subpackages that are impacted by this
change, separated by a comma.  Available subpackages are:
  config, constants, convolution, coordinates, cosmology, io.ascii, io.fits,
  io.misc, io.registry, io.votable, logger, modeling, nddata, samp, stats,
  table, tests, time, timeseries, uncertainty, units, utils, visualization, wcs

text: Enter description of the update here, maintaining the example indentation
of two spaces before the text.  Use the past tense, for instance
"Added a new method ``Table.cstack()`` for column-wise stacking". Enclose
literals in double-back ticks as shown.
"""

ENTRY_TEMPLATE = {
    'entry_types': ENTRY_TYPES,
    'pull_requests': [],
    'releases': [],
    'subpackages': [],
    'text': ('Enter description of the update here, maintaining the example indentation\n'
             'of two spaces before the text.  Use the past tense, for instance\n'
             '"Added a new method ``Table.cstack()`` for column-wise stacking."')
}

yaml.Dumper.ignore_aliases = lambda *args: True


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
                        type=int,
                        help="Wrap RST output to line width (default=no reformatting)")
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


def read_rst(filepath):
    with open(filepath) as fh:
        lines = fh.readlines()
    lines.append('')

    config = {}
    entry_lines = []
    entries = []
    within_entry = False
    release_dates = {}

    for line, line_next in zip(lines, lines[1:]):
        if within_entry or line.startswith('- '):
            entry_lines.append(line)

            if line_next.startswith('  '):
                within_entry = True
            else:
                within_entry = False
                entries.append(get_entry(config, entry_lines))
                entry_lines.clear()

        elif re.match(r'[\^]+\s*$', line_next):
            if line.startswith('astropy.'):
                line = line[8:]
            config['subpackages'] = [line.strip()]

        elif re.match(r'[=]+\s*$', line_next):
            match = re.match(r'(\S+)'
                             r'\s+'
                             r'\('
                             r'( [^)]+ )'
                             r'\)', line, re.VERBOSE)
            if not match:
                raise ValueError('could not parse release')
            release = match.group(1)
            date = match.group(2)
            release_dates[release] = date

            config['releases'] = [release]
            config['subpackages'] = [None]
            config['entry_types'] = [None]

        elif re.match(r'[-]+\s*$', line_next):
            config['entry_types'] = [line.strip()]
            config['subpackages'] = [None]

    return entries, release_dates


def read_yaml(filepath):
    with open(filepath, 'r') as fh:
        instructions, template, release_dates, entries = yaml.safe_load_all(fh)

    return entries, release_dates['RELEASE_DATES']


def rst_header(text, section_char):
    if text is None:
        out = []
    else:
        out = [text, section_char * len(text), '']
    return out


def write_rst(entries, filepath, release_dates, line_width):
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
        release = str(release)
        release_date = release_dates[release]
        release_text = f'{release} ({release_date})'
        lines.extend(rst_header(release_text, '='))

        for entry_type in LEGACY_ENTRY_TYPES:
            if entry_type not in out[release]:
                continue

            lines.extend(rst_header(entry_type, '-'))
            subpackages = out[release][entry_type]
            if subpackages is None:
                print(release)
            for subpackage in subpackages:
                if subpackage not in ('Installation', 'Misc', None):
                    subpackage_text = f'astropy.{subpackage}'
                else:
                    subpackage_text = subpackage
                lines.extend(rst_header(subpackage_text, '^'))
                for text in out[release][entry_type][subpackage]:
                    if line_width is not None:
                        lines.extend(textwrap.wrap(
                            text, line_width, initial_indent='- ', subsequent_indent='  '))
                    else:
                        for ii, text_line in enumerate(text.splitlines()):
                            hdr = '- ' if ii == 0 else '  '
                            lines.append(hdr + text_line)
                    lines.append('')

    with open(filepath, 'w') as fh:
        fh.writelines(line + os.linesep for line in lines)


def write_yaml(entries, release_dates, filepath):
    template = [ENTRY_TEMPLATE]
    instructions = {'INSTRUCTIONS FOR ADDING A CHANGE LOG ENTRY': INSTRUCTIONS}
    release_dates = {'RELEASE_DATES': release_dates}

    with open(filepath, 'w') as fh:
        documents = [instructions, template, release_dates, entries]
        # Write YAML with a wide output. This is not meant for human-readability
        # so we don't care about width.
        yaml.dump_all(documents, fh, width=200)


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
        entries, release_dates = read_rst(infile)
    elif infile.suffix == '.yml':
        entries, release_dates = read_yaml(infile)
    else:
        raise ValueError('input must be .rst or .yml')

    # Output entries to either RST or YAML.  The YAML pathway is mostly for initial
    # testing and conversion of the legacy CHANGES.RST.
    if outfile.suffix == '.rst':
        write_rst(entries, outfile, release_dates, opt.line_width)
    elif outfile.suffix == '.yml':
        write_yaml(entries, release_dates, outfile)

    if opt.print_info:
        uniques = get_uniques(entries)
        for key in ('subpackages', 'releases', 'entry_types'):
            vals = uniques[key]
            print(key.title())
            for val in vals:
                print('  - ' + str(val))
            print()
