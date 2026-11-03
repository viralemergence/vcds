source("R/increment_version.R")

## use this script to increment the schema version 
## make sure you set the path argument to increment the proper version
## minor and patch versions of older versions may continue to be produced after 
## a new major version is released.

"### Versioning Guidelines

All versions of VCDS will include a version number in their title (e.g. v1.0.0).

- Changes including updating required fields, changing field names, adding or removing value restrictions, or other breaking changes will result in a major release bump (1.0.0 -> 2.0.0)
- Non-breaking changes that impact validation - refining regex patterns, correcting or refining enum values, modifying the directory structure, etc - will result in a minor release bump (1.0.0 -> 1.1.0)
- Non-breaking changes that do not impact validation - updating descriptions, adding examples, modifying templates, etc - will result in a patch release bump (1.0.0 -> 1.0.1)
"


increment_schema_version(path = "vcds_schema/v1.2.0/vcds_schema.json",increment = "patch")

