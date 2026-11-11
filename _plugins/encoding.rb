# Read source files (notably the .bib bibliography) as UTF-8 even when the
# shell has no UTF-8 locale set (e.g. LANG unset), which otherwise breaks
# bibtex-ruby with "invalid byte sequence in US-ASCII".
Encoding.default_external = Encoding::UTF_8
Encoding.default_internal = Encoding::UTF_8
