"""
build_terms_page.py

Reads all versions of schema and generates docs/terms/index.html —
a terms reference page where each term has a stable id anchor.

Schemas covered:
  - vcds_schema
    - v1.0.0 +

Usage:
    python scripts/build_terms_page.py

Output:
    docs/VERSION/terms/index.html
"""

from __future__ import annotations

import html as html_lib
import json
import re
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = REPO_ROOT / "vcds_schema"
TEMPLATE_DIR = REPO_ROOT / "template"
VCDS_SCHEMA  =  SCHEMAS_DIR / "VERSION" / "vcds_schema.json"
OUTPUT_DIR_TERMS           = REPO_ROOT / "docs" / "VERSION" / "terms"
OUTPUT_PATH_JSON           = REPO_ROOT / "docs" / "VERSION" / "vcds_schema.json"
OUTPUT_PATH_HOME           = REPO_ROOT / "docs" / "index.html"
OUTPUT_PATH_TEMPLATE           = REPO_ROOT / "docs"
BASE_URI_GENERIC = "https://w3id.org/vcds"


BASE_URI_VCDS  = "https://w3id.org/vcds/VERSION/terms/"

# Schema source URIs shown in each term card
SCHEMA_URIS = {
    "vcds": (
        "https://viralemergence.github.io/vcds/"
        "VERSION/vcds_schema.json"
    )
}

SITE_URI = "https://viralemergence.github.io/vcds"



# ---------------------------------------------------------------------------
# Schema loading and $ref resolution
# ---------------------------------------------------------------------------

def get_schema_versions(path: Path) -> list:
    folders = [x.name for x in path.iterdir() if x.is_dir()]
    return folders

def insert_version(path: Path, version:str) -> Path:
    new_path = Path(str(path).replace("VERSION", version))
    return new_path

def load_schema(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_ref(ref: str, datacite: dict) -> dict:
    """
    Resolve a $ref string that points into the DataCite schema.
    Handles patterns like:
      datacite/datacite-v4.5.json#/properties/creators
      datacite/datacite-v4.5.json#/definitions/relatedIdentifierType
    Returns {} if the ref cannot be resolved.
    """
    if "#" not in ref:
        return {}
    _, pointer = ref.split("#", 1)
    parts = [p for p in pointer.split("/") if p]
    node = datacite
    try:
        for part in parts:
            node = node[part]
        return node
    except (KeyError, TypeError):
        return {}

# templates

def get_template_dict(path: Path) -> dict:
    folders = [x for x in path.iterdir() if x.is_dir()]
    out = {}
    for folder in folders:
        dir = folder.name
        file = ""
        for temp_file in folder.glob("*template*"):
            if temp_file.is_file():
                file = temp_file.name
            out.update({dir:file})
    reverse_sorted_dict = dict(sorted(out.items(), reverse=True))
    return reverse_sorted_dict

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def h(text: str) -> str:
    """HTML-escape a string."""
    return html_lib.escape(str(text))


def badge(label: str, css_class: str) -> str:
    return f'<span class="badge {css_class}">{h(label)}</span>'


def extract_dwc_uri(description: str) -> str | None:
    """Pull a 'See <url>' Darwin Core reference from a description string."""
    match = re.search(r"See (https?://\S+)", description)
    return match.group(1).rstrip(".") if match else None


def strip_see_url(description: str) -> str:
    """Remove trailing 'See <url>' from a description for display."""
    return re.sub(r"\s*See https?://\S+\.?$", "", description).strip()


def format_type(schema_node: dict) -> str:
    """
    Return badge HTML for the type of a schema node.
    Checks items.type (arrays) then type directly.
    """
    items = schema_node.get("items", {})
    type_val = items.get("type") if items else schema_node.get("type")

    if not type_val:
        return badge("object", "type")

    if isinstance(type_val, list):
        types    = [t for t in type_val if t != "null"]
        if schema_node.get("type") == "array":
            types = ["array"] + types
        nullable = "null" in type_val
    else:
        types    = [type_val]
        if schema_node.get("type") == "array":
            types = ["array"] + types
        nullable = False

    out = " ".join(badge(t, "type") for t in types)
    if nullable:
        out += " " + badge("nullable", "nullable")
   
    return out


def format_enum(values: list) -> str:
    non_null = [v for v in values if v is not None]
    pills = " ".join(badge(str(v), "enum-val") for v in non_null)
    return f'<div class="enum-list"><strong>Allowed values:</strong> {pills}</div>'


def format_examples(examples: list) -> str:
    items = ", ".join(f"<code>{h(str(e))}</code>" for e in examples)
    return f'<div class="examples"><strong>Examples:</strong> {items}</div>'


def format_constraints(schema_node: dict) -> list[str]:
    """Collect min/max/pattern constraints from a schema node or its items."""
    src = schema_node.get("items", schema_node)
    out = []
    if "minimum" in src:
        out.append(f"minimum: {src['minimum']}")
    if "maximum" in src:
        out.append(f"maximum: {src['maximum']}")
    if "minItems" in src:
        out.append(f"minItems: {src['minItems']}")
    if "pattern" in src:
        out.append(f"pattern: <code>{h(src['pattern'])}</code>")
    if "uniqueItems" in src:
        out.append(f"uniqueItems: <code>{h(src['uniqueItems'])}</code>")
    return out


def get_enum_from_node(node: dict) -> list | None:
    """Find enum values in a node, checking items sub-schema too."""
    if "enum" in node:
        return node["enum"]
    items = node.get("items", {})
    if "enum" in items:
        return items["enum"]
    return None


# ---------------------------------------------------------------------------
# Term card rendering
# ---------------------------------------------------------------------------

def render_term(
    anchor_id: str,
    display_name: str,
    definition: dict,
    *,
    source_key: str,
    is_required: bool = False,
    datacite_ref: str | None = None,
    base_uri: str | None = None,
    indent: int = 0,
    version = str,
) -> str:
    """
    Render a single term as a <section> card.

    anchor_id    : the HTML id attribute (used for fragment links)
    display_name : human-readable name shown in the card header
    definition   : the schema dict for this term
    source_key   : key into SCHEMA_URIS
    is_required  : whether this term is required
    datacite_ref : original $ref string if this term delegates to DataCite
    base_uri     : w3id.org base URI for this term; None suppresses the URI row
    indent       : 0 = top-level, 1 = nested sub-property (visual indent)
    """
    description  = definition.get("description", "")
    examples     = definition.get("examples", [])
    enum_vals    = get_enum_from_node(definition)
    dwc_uri      = extract_dwc_uri(description)
    display_desc = strip_see_url(description)
    constraints  = format_constraints(definition)
    type_html    = format_type(definition)
    schema_uri   = SCHEMA_URIS[source_key]
    indent_class = " nested" if indent else ""

    lines = [
        f'  <section class="term{indent_class}" id="{h(anchor_id)}">',
        '    <div class="term-header">',
        f'      <h3 class="term-name">{h(display_name)}</h3>',
        '      <div class="term-badges">',
        f'        {type_html}',
        f'        {badge("required", "required") if is_required else badge("optional", "optional")}',
        '      </div>',
        '    </div>',
        '    <div class="term-body">',
    ]

    if display_desc:
        lines.append(f'      <p class="term-desc">{h(display_desc)}</p>')

    if enum_vals:
        lines.append(f"      {format_enum(enum_vals)}")

    if examples:
        lines.append(f"      {format_examples(examples)}")

    if constraints:
        lines.append(
            f'      <div class="constraints">'
            f'<strong>Constraints:</strong> {"; ".join(constraints)}</div>'
        )

    if base_uri:
        base_uri_version = insert_version(base_uri,version)
        term_uri = f"{base_uri_version}/{anchor_id}"
        lines.append(
            f'      <div class="term-uri">'
            f'<strong>URI:</strong> <a href="{term_uri}">{term_uri}</a></div>'
        )

    if dwc_uri:
        lines.append(
            f'      <div class="dwc-ref">'
            f'<strong>Term Reference:</strong> '
            f'<a href="{dwc_uri}">{dwc_uri}</a></div>'
        )

    versioned_schema_uri = insert_version(schema_uri,version)
    lines.append(
        f'      <div class="schema-ref">'
        f'<strong>Defined in:</strong> '
        f'<a href="{versioned_schema_uri}">{versioned_schema_uri}</a></div>'
    )

    lines.append("    </div>")
    lines.append("  </section>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_vcds_data_section(schema: dict,
                            version: str) -> tuple[str, list[str]]:
    """
    Returns (html_string, list_of_anchor_ids) for vcds.
    Required terms first, then optional, both alphabetically sorted.
    """
    properties = schema.get("properties", {})
    required   = set(schema.get("required", []))

    req_terms = sorted(k for k in properties if k in required)
    opt_terms = sorted(k for k in properties if k not in required)
    ordered   = req_terms + opt_terms

    cards = []
    anchors = []
    for name in ordered:
        cards.append(render_term(
            anchor_id    = name,
            display_name = name,
            definition   = properties[name],
            source_key   = "vcds",
            is_required  = name in required,
            base_uri     = BASE_URI_VCDS,
            version = version,
        ))
        anchors.append(name)

    section_html = (
        '<div class="schema-section" id="section-vcds">\n'
        '  <h2 class="section-title">VCDS terms</h2>\n'
        '  <p class="section-desc">Fields defined in '
        '<code>vcds_schema/vcds_schema.json</code>. '
        'Each term URI follows the pattern '
        f'<code>{BASE_URI_VCDS}{{termName}}</code>.</p>\n'
        + "\n\n".join(cards)
        + "\n</div>"
    )
    return section_html, anchors

# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------

CSS = "../../styles.css"
CSS_HOME = "./styles.css"

JS = """
const input   = document.getElementById('filter');
const terms   = document.querySelectorAll('.term');
const sections = document.querySelectorAll('.schema-section');

input.addEventListener('input', () => {
  const q = input.value.toLowerCase().trim();

  terms.forEach(t => {
    if (!q) { t.classList.remove('hidden'); return; }
    const text = (t.id + ' ' + t.innerText).toLowerCase();
    t.classList.toggle('hidden', !text.includes(q));
  });

  // Hide section headers when all their terms are hidden
  sections.forEach(sec => {
    const visible = [...sec.querySelectorAll('.term')]
      .some(t => !t.classList.contains('hidden'));
    sec.style.display = (!q || visible) ? '' : 'none';
  });
});

// Enables click/tap toggling (needed for touch devices and accessibility),
// in addition to the CSS :hover behavior above.
document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
  toggle.addEventListener('click', function (e) {
    e.preventDefault();
    const parent = this.closest('.dropdown');
    const isOpen = parent.classList.contains('open');

    // Close any other open dropdowns first
    document.querySelectorAll('.dropdown.open').forEach(d => d.classList.remove('open'));

    if (!isOpen) parent.classList.add('open');
  });
});

// Close dropdown when clicking outside
document.addEventListener('click', function (e) {
  if (!e.target.closest('.dropdown')) {
    document.querySelectorAll('.dropdown.open').forEach(d => d.classList.remove('open'));
  }
});

"""


def build_toc(
    vcds_anchors: list[str]
) -> str:
    def link_list(anchors: list[str]) -> str:
        return "\n".join(
            f'      <a href="#{h(a)}">{h(a)}</a>' for a in anchors
        )

    return f"""<div class="toc" aria-label="Table of contents">
  <h2>Contents</h2>
  <div class="toc-group">
    <h3><a href="#section-vcds-terms">VCDS Terms</a></h3>
    <div class="toc-links">
{link_list(vcds_anchors)}
    </div>
  </div>
  </div>"""

def build_nav(
    schema_versions: list,
    
) -> str:
    # make terms page
    def link_list(versions: list[str],
                   page: str) -> str:
        return "\n".join(
            f'      <li><a href="{h(SITE_URI)}/{h(version)}/{h(page)}">{version}</a></li>' for version in reversed(versions)
        )

    def download_list(file_dict: dict) -> str:
        return "\n".join(
            f'      <li><a href="{h(SITE_URI)}/{h(file)}/{h(file_dict[file])}" download={h(file_dict[file])}>{file}</a></li>' for file in file_dict
            )
    # get template versions
    template_dict = get_template_dict(TEMPLATE_DIR)
    print(template_dict)
    template_list = download_list(template_dict)
    first_key = next(iter(template_dict))
    latest_template = f'"{h(SITE_URI)}/{h(first_key)}/{h(template_dict[first_key])}"'
    

    # latest version for main navbar item
    schema_versions_sorted = sorted(schema_versions)
    latest_version = schema_versions_sorted[-1]
    latest_term = f'"{h(SITE_URI)}/{h(latest_version)}/{h("terms/index.html")}"'
    latest_schema = f'"{h(SITE_URI)}/{h(latest_version)}/{h("vcds_schema.json")}"'

    # build terms items <li><a href="/v1.2.0/terms">v1.2.0 (latest)</a></li>
    term_items = link_list(versions=schema_versions_sorted,
        page="terms/index.html")

    # build schema items <li><a href="/v1.2.0/schema">v1.2.0 (latest)</a></li>
    schema_items = link_list(versions=schema_versions_sorted,
        page="vcds_schema.json")

    return f""" <nav class="navbar">
    <ul class="navbar-nav">
    <li><a href="https://viralemergence.github.io/vcds/">Home</a></li>
    <li><a href="https://github.com/viralemergence/vcds">GitHub</a></li>

    <!-- Dropdown terms -->
    <li class="dropdown">
      <a href={latest_term} class="dropdown-toggle">Terms ▾</a>
      <ul class="dropdown-menu">
        {term_items}
      </ul>
    </li>

    <!-- Dropdown schemas -->
    <li class="dropdown">
      <a href={latest_schema} class="dropdown-toggle">Schema ▾</a>
      <ul class="dropdown-menu">
        {schema_items}
      </ul>
    </li>

    <!-- Dropdown templates -->
    <li class="dropdown">
      <a href={latest_template} class="dropdown-toggle">Download Excel Template ▾</a>
      <ul class="dropdown-menu">
        {template_list}
      </ul>
    </li>
  </ul>
</nav>"""


def build_page(
    vcds_html: str,
    vcds_anchors: list[str],
    version_title: str,
    schema_version: str,
    nav_bar = str,
) -> str:
    toc = build_toc(vcds_anchors)
    total = len(vcds_anchors)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Terms — {h(version_title)}</title>
  <link rel="stylesheet" href={CSS}>
</head>
<body>

<header>
  <h1>{h(version_title)}</h1>
  <p>Controlled vocabulary — {total} term definitions</p>
</header>

{nav_bar}

<main>
  <p class="intro">
    VCDS terms with a <span class="badge required">required</span> badge are
    mandatory fields. Terms have stable URIs of the form
    <code>{BASE_URI_GENERIC}/{{version}}/{{termName}}</code>.
  </p>

{toc}

  <div class="filter-bar">
    <input id="filter" type="search"
           placeholder="Filter terms by name, badge, or description…"
           aria-label="Filter terms">
  </div>

{vcds_html}

</main>

<footer>
  Generated from
  <a href="https://github.com/viralemergence/vcds">viralemergence/vcds</a>.
  VCDS terms are available via the
  <a href="https://w3id.org/vcds/">w3id.org/vcds</a> persistent namespace.
</footer>

<script>
{JS}
</script>

</body>
</html>
"""

def build_home(
    nav_bar = str,
) -> str:
    site_title = "Vector Competence Data Standard"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{h(site_title)}</title>
  <link rel="stylesheet" href={CSS_HOME}>
</head>
<body>

<header>
  <h1>{h(site_title)}</h1>
  <p>A minimum data standard for vector competence experiments</p>
</header>

{nav_bar}

<main>
<section id="about">
<h2>About</h2> 
  <p class="intro">
    The Vector Competence Data Standards (VCDS) is maintained by <a href = "https://www.viralemergence.org/">Verena</a>
    and aims to provide consistent terminology for describing vector competence experiments.
    <br>
    <br>
    This data standard is extensible, that is you may include additional terms not in the standard.
    When validating data with the JSON schema, these terms will be ignored. 
    <br>
    <br>
    The growing threat of vector-borne diseases, highlighted by recent epidemics, 
    has prompted increased focus on the fundamental biology of vector-virus 
    interactions. To this end, experiments are often the most reliable way to 
    measure vector competence (the potential for arthropod vectors to transmit 
    certain pathogens). Data from these experiments are critical to understand 
    outbreak risk.
    <br>
    <br>
    Using the VCDS to describe vector competence studies facilitates interpretation and data sharing. 
  </p>

<section id="schema">
<h2>Schema</h2> 
  <p>
    VCDS uses a <a href="https://json-schema.org/">JSON schema</a> to describe the properties in a data set and the relationship between those
    properties. The JSON schema expects tabular data that contain at least the required fields.
  </p>

  <p>
    Data can  be validated against the JSON schema using a validation engine:
        <table class="version-table" style="margin-top: 0.5rem;">
          <thead>
            <tr>
              <th>Programing language</th>
              <th>Library</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>JavaScript</td>
              <td><a href="https://ajv.js.org/guide/getting-started.html">AJV</a></td>
            </tr>
            <tr>
              <td>R</td>
              <td><a href="https://docs.ropensci.org/jsonvalidate/">jsonvalidate</a></td>
            </tr>
            <tr>
              <td>Python</td>
              <td><a href="https://python-jsonschema.readthedocs.io/en/stable/">jsonschema</a></td>
            </tr>
          </tbody>
        </table>
  </p>
</section>  

<section id="terms">
    <h2>Terms</h2> 
    These are the properties of the JSON schema. 
    <br>
    <br>
    Each term card contains a plain language description and a link to a controlled vocabulary
    that provides a more technical description of the item. 
    <br>
    <br>
    The terms page has a search bar just below the table of contents. It can filter on any property of 
    a term card (e.g. name, description, badge, etc.)
    <br>
    <br>
    Coming soon: registering VCDS with w3id.org.
</section>

<section id="templates">
    <h2>Templates</h2>
    Excel templates are available to facilitate getting started with the VCDS. The columns in the excel spreadsheet correspond to the 
    the properties in the JSON schema schema. To download a template, select the version you woule like to do use from the 
    "download excel template" menu item.
</section>
<section id="versioning">
    <h2>Versioning</h2>
    <ol style="margin: 0.5rem 0 0.85rem 1.5rem; color: #333;">
      <li style="margin-bottom: 0.75rem;">
        All versions of VCDS will include a version number in their title (e.g. <code>v1.0.0</code>).
        <table class="version-table" style="margin-top: 0.5rem;">
          <thead>
            <tr>
              <th>Change type</th>
              <th>Examples</th>
              <th>Version bump</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Breaking</td>
              <td>Updating required fields, changing field names, adding or removing value restrictions</td>
              <td><code>1.0.0 → 2.0.0</code> (major)</td>
            </tr>
            <tr>
              <td>Non-breaking, affects validation</td>
              <td>Refining regex patterns, correcting or refining enum values, modifying the directory structure</td>
              <td><code>1.0.0 → 1.1.0</code> (minor)</td>
            </tr>
            <tr>
              <td>Non-breaking, no validation impact</td>
              <td>Updating descriptions, adding examples, modifying templates</td>
              <td><code>1.0.0 → 1.0.1</code> (patch)</td>
            </tr>
          </tbody>
        </table>
      </li>
      <li style="margin-bottom: 0.75rem;">
        When a new version of the schema is published, a new GitHub release must be created
        as well as a new version of the schema on
        <a href="https://doi.org/10.5281/zenodo.15020049">Zenodo</a>.
      </li>
    </ol>
  </section>

</main>

<footer>
  Generated from
  <a href="https://github.com/viralemergence/vcds">viralemergence/vcds</a>.
  VCDS terms are available via the
  <a href="https://w3id.org/vcds/">w3id.org/vcds</a> persistent namespace.
</footer>

<script>
{JS}
</script>

</body>
</html>
"""



# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    schema_versions = get_schema_versions(SCHEMAS_DIR)
    nav_bar = build_nav(schema_versions)
    for v in schema_versions:
        v_vcds_schema_path = insert_version(VCDS_SCHEMA,version=v)
        schema_json = load_schema(v_vcds_schema_path)
        version_title = schema_json.get("title","Vector Competence Data Standard")
        vcds_html,  vcds_anchors = build_vcds_data_section(schema_json, v)
        # make version specific output dir
        output_dir_v = insert_version(OUTPUT_DIR_TERMS,v)
        output_dir_v.mkdir(parents=True, exist_ok=True)
        # build page
        page = build_page(
                vcds_html, 
                vcds_anchors,
                version_title,
                v,
                nav_bar
        )
        output_file = output_dir_v / "index.html"

        output_file.write_text(page, encoding="utf-8")
        # write json files
        output_json = insert_version(OUTPUT_PATH_JSON,v)
        shutil.copy(v_vcds_schema_path, output_json)
    template_dict = get_template_dict(TEMPLATE_DIR)
    
    for t_version in template_dict:
        output_template = OUTPUT_PATH_TEMPLATE / t_version / template_dict[t_version]
        t_version.mkdir(parents=True, exist_ok=True)
        template_path = TEMPLATE_DIR / t_version / template_dict[t_version]
        shutil.copy(template_path, output_template)

        
    home_page = build_home(nav_bar)
    OUTPUT_PATH_HOME.write_text(home_page,encoding = "utf-8")

    print(f"Written: {output_file}")
    print(f"  VCDS terms:    {len(vcds_anchors)}")

if __name__ == "__main__":
    main()
