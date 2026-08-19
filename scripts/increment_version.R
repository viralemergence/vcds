source("R/increment_version.R")

## use this script to increment the schema version 
## make sure you set the path argument to increment the proper version
## minor and patch versions of older versions may continue to be produced after 
## a new major version is released.


increment_schema_version(path = "vcds_schema/v1.0.0/vcds_schema.json")