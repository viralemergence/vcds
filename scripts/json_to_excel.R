library(dplyr)
library(purrr)
library(jsonlite)
library(openxlsx2)

vcds <- jsonlite::read_json(path = "vcds_schema/v1.0.0/vcds_schema.json")

property_names <- vcds$properties |> names()
property_descriptions <- purrr::map_chr(vcds$properties, \(x){x$description})
property_examples <- purrr::map_chr(vcds$properties, \(x){
  example <- x$example |>
    paste(collapse = ", ")
    
})

definitions_table <- data.frame(Field = property_names, 	Description = property_descriptions,	Examples = property_examples)

# insert values in definitions sheet

openxlsx2::write_data(wb = "COMET template v1.0.0.xlsx",)
