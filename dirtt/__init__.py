"""python-dirtt - Directory Tree Templater.

(c) 2011-2026 Robert Moggach and contributors.
Licensed under the MIT license: https://opensource.org/licenses/MIT

dirtt generates directory and file structures from XML or JSON
templates that describe repeatedly used filesystem layouts, such as
project structures.

Typical use::

    from dirtt import build

    build("project.xml", {"project_root": "/jobs", "project_path": "myproject"})

Or preview first::

    actions = build("project.xml", context, dry_run=True)
"""

__version__ = "1.0.0"

from dirtt.builder import build, execute, plan
from dirtt.exceptions import BuildError, DirttError, TemplateError
from dirtt.introspect import introspect
from dirtt.model import Action, Dir, File, Link, Tree
from dirtt.parser import TEMPLATES_DIR, load_template
from dirtt.template import placeholders, substitute

__all__ = [
    "__version__",
    "build",
    "plan",
    "execute",
    "load_template",
    "introspect",
    "substitute",
    "placeholders",
    "Action",
    "Dir",
    "File",
    "Link",
    "Tree",
    "DirttError",
    "TemplateError",
    "BuildError",
    "TEMPLATES_DIR",
]
