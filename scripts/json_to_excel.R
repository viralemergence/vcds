library(dplyr)
library(purrr)
library(jsonlite)
library(openxlsx2)
library(fs)
library(stringr)

# get all schema versions
schema_paths <- fs::dir_ls("vcds_schema/",recurse = TRUE, regexp = "vcds_schema\\.json")


# for all schema paths, write a template
for(schema_path in schema_paths){
  print(schema_path)
  schema_dir <- fs::path_dir(schema_path)
  template_dir <- stringr::str_replace(string = schema_dir,pattern = "vcds_schema",replacement = "template")
  if(!fs::dir_exists(template_dir)){
    fs::dir_create(template_dir)
  }
  # parse schema
  vcds <- jsonlite::read_json(path = schema_path)

  property_names <- vcds$properties |> names()
  property_descriptions <- purrr::map_chr(vcds$properties, \(x){x$description})
  property_examples <- purrr::map_chr(vcds$properties, \(x){
                                                          example <- x$example |>
                                                          paste(collapse = ", ")
                                        })
  definitions_table <- data.frame(Field = property_names,
      Description = property_descriptions,
      Examples = property_examples,
      row.names = NULL)
  
  template_table <- data.frame(place_holder = "")

  template_table[property_names] <- ""
  template_table_final <- template_table[property_names]

  # insert values in definitions sheets
  # create template file -- include version number in file name because thats likely to get lost if folks are using the excel file.
  vcds_version <- stringr::str_extract(string = template_dir,pattern = "[0-9]+\\.[0-9]+\\.[0-9]+") |>
      stringr::str_replace_all(pattern = "\\.",replacement = "_")
  vcds_file <- sprintf("vcds_template_%s.xlsx",vcds_version)
  
  template_path <- fs::path(template_dir,vcds_file)
  

  wb <- openxlsx2::wb_workbook(creator = "VCDS team",title = vcds$title)
  wb$add_worksheet("definitions",)
  wb$add_worksheet("template")

  wb$add_data(sheet = "definitions",x = definitions_table)
  wb$add_data(sheet = "template", x = template_table_final)

  wb$save(file = template_path,overwrite = TRUE)

}



