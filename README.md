# astropy-changelog: utility for managing the astropy changelog (demo)

This is a proof of concept for changing the basis of the astropy changelog from
the `CHANGES.rst` file to a new `CHANGES.yml` file.  The driver for this and initial
discussions were captured in an astropy-dev email thread in Oct 2016 (subject
"Proposal for a new changelog system").

An important point to note is that the current code strives to maintain
smooth compatibility with the current `CHANGES.rst` as a source for
users and developers to understand astropy changes.  

**However**, once
we have transitioned to a YAML structured representation then there 
are numerous possibilities for using this far more effectively and
providing much better ways to present and discover this information.

## Overview

The key element of this POC is the script `convert_changelog.py`.  It can handle
the following:

- Read a changelog from the legacy `CHANGES.rst` RST format and convert
  into a structured data changelog object (list of change entries, where each
  entry is a dict).
- Read a changelog from the new `CHANGES.yml` YAML format directly into a
  structured changelog object.
- Write a structured changelog object to YAML.
- Write a structured changelog object into the legacy RST format.  One key
  difference is that it does not preserve the empty subpackage entries, e.g.
  when there are no bug fixes for a particular subpackage, that is simply not
  reported.

The changelog YAML file contains four documents:

- Instructions for developers to add a changelog entry
- Template that they use
- Release dates (needed to generate the RST legacy format)
- Change entries

## Envisioned process

The envisioned process is to convert from `CHANGES.rst` to `CHANGES.yml` and
then convert back to RST to verify that the YAML representation accurately
captures the original changelog:
```
./convert_changelog.py CHANGES.rst CHANGES.yml
./convert_changelog.py CHANGES.yml CHANGES_new.rst

# Diff the two, preferably using a graphical diff too.  opendiff works well on Mac.
opendiff CHANGES.rst CHANGES_new.rst
```

At this point `CHANGES.yml` becomes the official source of changes and
`CHANGES.rst` is a derived product that is generated (by some TBD process) with:
```
./convert_changelog.py CHANGES.yml CHANGES.rst
```

## Example files

To allow looking at the files in a manageable form, this repo includes a
chopped down version of the astropy changelog as `changes_test.rst`.  From there:
```
./convert_changelog.py changes_test.rst changes_test.yml
./convert_changelog.py changes_test.yml changes_test_new.rst
```
