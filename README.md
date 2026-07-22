# The vector competence data standard 🦟✍️🔢

[![DOI](https://zenodo.org/badge/502667317.svg)](https://zenodo.org/badge/latestdoi/502667317)

## Repository guide

### How to use the data standard:

Follow guidance in the [manuscript](https://doi.org/10.1038/s41597-022-01741-4).

We suggest attaching a formatted raw dataset to your publications as a supplementary file / table. A blank template is available in this repository in .xlsx format. If you share your data using this template, you can also [send it to us](egallich@colostate.edu) directly for inclusion in the (currently under construction) COMET database.

### How to cite:

Please cite the  manuscript as: VY Wu, B Chen, R Christofferson, G Ebel, AC Fagre, E Gallichotte, AR Sweeny, CJ Carlson, SJ Ryan. (2022) A minimum data standard for vector competence experiments. _Scientific Data_ DOI: 10.1038/s41597-022-01741-4

### Versioning Guidelines

All versions of VCDS will include a version number in their title (e.g. v1.0.0).

- Changes including updating required fields, changing field names, adding or removing value restrictions, or other breaking changes will result in a major release bump (1.0.0 -> 2.0.0)
- Non-breaking changes that impact validation - refining regex patterns, correcting or refining enum values, modifying the directory structure, etc - will result in a minor release bump (1.0.0 -> 1.1.0)
- Non-breaking changes that do not impact validation - updating descriptions, adding examples, modifying templates, etc - will result in a patch release bump (1.0.0 -> 1.0.1)

All changes will be reflected in both the excel template and the JSON Schema.

Previous versions of the standard will be stored in the `Version history` folder. 
```
Version history
    |- v0.1 (paper)
    |- ...
    |- v9.9.9 (some future release)
```

## Changelog 

### v0.2 (October 2, 2024)
- added a locked definitions tab providing more detailed information of each column
- added a study naming section
  - Study (Last name, et al. Year Journal)
  - PMID (PubMed ID)
  - DOI	(Digital object identifier)
- add two new virus sections
  - Infectious clone / recombinant
  - Wildtype vs mutant
- added new sections in infection
  - changed temp (reared) and temp (EIT) to mean temperature and added a space for amplitude (both reared and EIT)
  - added column to note if mosquitoes are knowingly coinfected (e.g., Wolbachia, ISV, arbovirus, etc)
- changed experimental outcome section to no longer be infection/dissemination/transmission
  - updated to 5 sections to provide sample tested, diagnostic, number tested and number positive
  - also added a section to include results of transmission to a naive animal, including animal species, number of vectors fed on the animal and number positive, and number of recipient animals tested and positive
- for many of the sections, added dropdown lists for users to pick from 
