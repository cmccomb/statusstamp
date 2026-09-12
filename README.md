# statusstamp

Distressed, reproducible document status stamps for LaTeX.

![Stamp examples: labels, dates, colors, wear, layering, and placement](docs/gallery.png)

[Full-size example sheet](docs/gallery.pdf) ·
[Example source](examples/gallery-samples.tex)

## Use in Overleaf

Upload [`statusstamp.sty`](statusstamp.sty) alongside your main `.tex` file,
then add this to the preamble:

```latex
\usepackage{statusstamp}
```

Compile normally. By default, a red **SUBMITTED** stamp appears behind the
text at the center of every page.

## Customize

```latex
\statusstampsetup{
  text=ACCEPTED,
  color=teal!70!black,
  scale=.48,
  angle=-8,
  position=top-right,
  layer=foreground,
  pages=first
}
```

Use `layer=background` to place the stamp under text or `layer=foreground`
to place it over text. Set `enabled=false` to turn page stamps off, or
`distressed=false` for clean borders.

For an inline stamp, use `\statusstamp[text=DRAFT,scale=.5]`.

[All options and usage notes](docs/usage.md) ·
[Development and builds](docs/development.md)

Copyright 2026 Chris McComb. [MIT License](LICENSE).
