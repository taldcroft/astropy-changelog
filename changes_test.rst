4.0 (unreleased)
================

New Features
------------

astropy.config
^^^^^^^^^^^^^^

astropy.constants
^^^^^^^^^^^^^^^^^

- The version of constants can be specified via ScienceState in a way
  that ``constants`` and ``units`` will be consistent. [#8517]

- Default constants now use CODATA 2018 and IAU 2015 definitions. [#8761]

astropy.convolution
^^^^^^^^^^^^^^^^^^^

astropy.coordinates
^^^^^^^^^^^^^^^^^^^

- Changed ``coordinates.solar_system_ephemeris`` to also accept local files
  as input. The ephemeris can now be selected by either keyword (e.g. 'jpl',
  'de430'), URL or file path. [#8767]

- Added a ``cylindrical`` property to ``SkyCoord`` for shorthand access to a
  ``CylindricalRepresentation`` of the coordinate, as is already available
  for other common representations. [#8857]

astropy.table
^^^^^^^^^^^^^

- Improved the implementation of ``Table.replace_column()`` to provide
  a speed-up of 5 to 10 times for wide tables.  The method can now accept
  any input which convertible to a column of the correct length, not just
  ``Column`` subclasses.[#8902]

- Improved the implementation of ``Table.add_column()`` to provide a speed-up
  of 2 to 10 (or more) when adding a column to tables, with increasing benefit
  as the number of columns increases.  The method can now accept any input
  which is convertible to a column of the correct length, not just ``Column``
  subclasses. [#8933]

Bug Fixes
---------

astropy.config
^^^^^^^^^^^^^^

astropy.table
^^^^^^^^^^^^^

- Fix bug where adding a column consisting of a list of masked arrays was
  dropping the masks. [#9048]

- ``Quantity`` columns with custom units can now round-trip via FITS tables,
  as long as the custom unit is enabled during reading (otherwise, the unit
  will become an ``UnrecognizedUnit``). [#9015]

astropy.tests
^^^^^^^^^^^^^

astropy.time
^^^^^^^^^^^^

astropy.utils
^^^^^^^^^^^^^

- For the default ``IERS_Auto`` table, which combines IERS A and B values, the
  IERS nutation parameters "dX_2000A" and "dY_2000A" are now also taken from
  the actual IERS B file rather than from the B values stored in the IERS A
  file.  Any differences should be negligible for any practical application,
  but this may help exactly reproducing results. [#9237]

astropy.visualization
^^^^^^^^^^^^^^^^^^^^^

Other Changes and Additions
---------------------------

- Versions of Python <3.6 are no longer supported. [#8955]

- Matplotlib 2.1 and later is now required. [#8787]

- Updated the bundled CFITSIO library to 3.470. See
  ``cextern/cfitsio/docs/changes.txt`` for additional information. [#9233]


3.2.2 (unreleased)
==================

Bug fixes
---------

astropy.coordinates
^^^^^^^^^^^^^^^^^^^

- Fix concatenation of representations for cases where the units were different.
  [#8877]

- Check for NaN values in catalog and match coordinates before building and
  querying the ``KDTree`` for coordinate matching. [#9007]
- Fix sky coordinate matching when a dimensionless distance is provided. [#9008]

astropy.cosmology
^^^^^^^^^^^^^^^^^

astropy.nddata
^^^^^^^^^^^^^^

- Fix to ``add_array``, which now accepts ``array_small`` having dimensions
  equal to ``array_large``, instead of only allowing smaller sizes of
  arrays. [#9118]

Other Changes and Additions
---------------------------

- Fixed a bug that caused files outside of the astropy module directory to be
  included as package data, resulting in some cases in errors when doing
  repeated builds. [#9039]

0.1 (2012-06-19)
================

- Initial release.
