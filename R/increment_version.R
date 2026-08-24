

#' Increment Schema Version
#' 
#' Similar in spirit to usethis::use_version, this function increments the schema version by
#' major, minor, or patch releases. It also creates a new version of the schema in vcds_schema folder. 
#'
#' @param path String. Path to json schema's whose version you would like to increment. 
#' @param increment String. One of major, minor, or patch. 
#'
#' @returns
#'
#' @export
#' @examples
#' 
increment_schema_version <- function(path, increment = c("major","minor","patch")){
  match.arg(increment,c("major","minor","patch"))

  # extract current version
  schema_list <- jsonlite::read_json(path)
  version_current <- schema_list$title |>
    stringr::str_extract(pattern = "\\d+\\.\\d+\\.\\d+")
  
  version_numeric <- version_current |>
    stringr::str_split(pattern = "\\.",simplify = TRUE) |>
    as.numeric()

  if(increment == "major"){
    version_numeric[1] <- version_numeric[1]+1
    version_numeric[2:3] <- 0
  }
  
  if(increment == "minor"){
    version_numeric[2] <- version_numeric[2]+1
    version_numeric[3] <- 0
  }

  if(increment == "patch"){
    version_numeric[3] <- version_numeric[3]+1
  }

  # new version as character

  version_new <- paste(version_numeric,collapse = ".")

  # add the new title to the json schema
  schema_list_new <- schema_list
  schema_list_new$title <- stringr::str_replace(schema_list$title,pattern = version_current,replacement = version_new)

  # add a new folder in vcds_schema
  new_folder <- fs::path("vcds_schema",sprintf("v%s",version_new))
  if(fs::dir_exists(new_folder)){
    rlang::abort("This version of the schema already exists. Verify you are trying to increment from the proper schema path.")
  }
  fs::dir_create(new_folder)

  # new json
  new_json_path <- fs::path(new_folder,"vcds_schema.json")
  jsonlite::write_json(schema_list_new,path = new_json_path,pretty = TRUE, auto_unbox = TRUE,)

} 

