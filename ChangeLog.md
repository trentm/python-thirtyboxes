## v0.6.0 ##

  * Updates from Kevin Unhammer that fix event and user unmarshalling, and add avatar to `python thirtyboxes.py user ID` output.

## v0.5.0 ##

  * New `ThirtyBoxes` class for main API methods. Method names are shorter and put a cleaner veneer on the raw 30boxes API names. Results are parsed into a reasonable Python complex data structure. (This adds a dependency on the ElementTree XML library.)
  * Cleaner command-line interface. Nicer output (default output format is YAML).
  * `RawThirtyBoxes` API class that just does the raw interface: methods mirror 30boxes.com/api methods, XML is returned.
  * The v0.1.0 top-level functions are deprecated.

## v0.1.0 ##

  * First release.
  * Top-level functions for each API method.
  * A simple command-line interface. (Run `python thirtyboxes.py` to get started.)