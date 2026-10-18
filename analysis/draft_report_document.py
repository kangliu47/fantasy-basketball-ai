"""Small escaped HTML/Markdown renderer for private, static analysis artifacts."""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ReportDocument:
    title: str
    markdown: list[str] = field(default_factory=list)
    fragments: list[str] = field(default_factory=list)

    def heading(self, title: str, anchor: str) -> None:
        self.markdown.append(f"## {title}\n")
        self.fragments.append(
            f'<h2 id="{html.escape(anchor, quote=True)}">{html.escape(title)}</h2>'
        )

    def paragraph(self, text: str) -> None:
        self.markdown.append(html.escape(text, quote=False) + "\n")
        self.fragments.append(f"<p>{html.escape(text)}</p>")

    def table(self, headers: list[str], rows: list[list[str]]) -> None:
        def cell(text: str) -> str:
            return html.escape(text, quote=False).replace("|", "\\|").replace("\n", " ")

        self.markdown.extend(
            [
                "| " + " | ".join(map(cell, headers)) + " |",
                "| " + " | ".join("---" for _ in headers) + " |",
                *["| " + " | ".join(map(cell, row)) + " |" for row in rows],
                "",
            ]
        )
        head = "".join(f'<th scope="col">{html.escape(v)}</th>' for v in headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(v)}</td>" for v in row) + "</tr>" for row in rows
        )
        self.fragments.append(
            f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>"
        )

    def figure(self, filename: str, caption: str) -> None:
        self.markdown.append(f"![{caption}]({filename})\n")
        self.fragments.append(
            f'<figure><img src="{html.escape(filename, quote=True)}" '
            f'alt="{html.escape(caption, quote=True)}">'
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )

    def source(self, title: str, url: str) -> None:
        self.markdown.append(f"- [{title}]({url})")
        self.fragments.append(
            f'<p><a href="{html.escape(url, quote=True)}">{html.escape(title)}</a></p>'
        )

    def write(self, directory: Path, shared_css: str) -> tuple[Path, Path]:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        md = directory / "draft-strategy-report.md"
        page = directory / "draft-strategy-report.html"
        md.write_text(f"# {self.title}\n\n" + "\n".join(self.markdown))
        css = """
        h2 { color:var(--showcase-heading); margin:36px 0 12px; scroll-margin-top:20px }
        p,li { line-height:1.65; max-width:95ch; overflow-wrap:anywhere }
        .table-wrap { overflow-x:auto; margin:18px 0; border:1px solid var(--showcase-line);
          background:var(--showcase-surface); border-radius:9px }
        table { width:100%; border-collapse:collapse; font-size:13px }
        th,td { text-align:left; padding:10px 12px; border-bottom:1px solid var(--showcase-line);
          vertical-align:top; min-width:85px }
        th { background:var(--showcase-surface-soft); color:var(--showcase-heading) }
        tr:last-child td { border-bottom:0 } img { max-width:100%; height:auto }
        figure { margin:22px 0; padding:16px; background:var(--showcase-surface);
          border:1px solid var(--showcase-line); border-radius:9px }
        figcaption { color:var(--showcase-muted); font-size:12px; line-height:1.5 }
        a { color:var(--showcase-blue) } nav { display:flex; gap:14px; flex-wrap:wrap;
          padding:16px 0; border-bottom:1px solid var(--showcase-line) }
        .provenance { overflow-wrap:anywhere } @media print { nav {display:none} }
        """
        page.write_text(
            '<!doctype html><html lang="en" data-ui-style="fantasy-analytics-v1"><head>'
            '<meta charset="utf-8"><meta name="viewport" '
            'content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(self.title)}</title><style>{shared_css}\n{css}</style></head><body>"
            '<header class="showcase-header"><div class="showcase-brand">Fantasy Basketball'
            '<small>Draft research</small></div><div class="showcase-status">'
            "Private · read-only analysis"
            '</div></header><main class="showcase-page"><p class="showcase-eyebrow">'
            '2026–27 · conditional stress test</p><h1 class="showcase-title">'
            f"{html.escape(self.title)}</h1>"
            '<div class="showcase-banner">Paid projection data stays on this Mac. '
            "Scenario frequencies are model outcomes, not championship probabilities.</div>"
            '<nav aria-label="Report sections">'
            '<a href="#decision">Draft advice</a><a href="#scarcity">Pool scarcity</a>'
            '<a href="#strategies">Strategy tests</a><a href="#investment">Spending plans</a>'
            '<a href="#method">Method and limits</a></nav>'
            + "\n".join(self.fragments)
            + '<footer class="showcase-footer">Local analysis artifact · '
            "no account access or application writes"
            "</footer></main></body></html>"
        )
        for path in (md, page):
            path.chmod(0o600)
        return md, page
