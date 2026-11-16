"""export_static.py - writes dashboard.html, a single file you can open without running Flask (live classifier disabled)."""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
from flask import render_template  # noqa: E402
import app as webapp  # noqa: E402

with webapp.app.test_request_context("/"):
    html = render_template("dashboard.html", static=True, **webapp.build_context())
out = os.path.join(HERE, "..", "dashboard.html")
open(out, "w", encoding="utf-8").write(html)
print("wrote", out, f"({len(html) / 1024:.0f} KB)")
