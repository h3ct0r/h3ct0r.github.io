---
layout: page
permalink: /publications/
title: Publications
description: Journal articles, conference papers, workshop papers and abstracts, newest first.
nav: true
nav_order: 1
---

{%- assign lattes = site.data.lattes -%}
{%- assign c = lattes.counts -%}
<p class="pub-summary">
  <strong>{{ c.journal }}</strong> journal articles ·
  <strong>{{ c.conference }}</strong> conference papers ·
  <strong>{{ c.abstract }}</strong> workshop papers and abstracts ·
  <strong>{{ lattes.patents | size }}</strong> patent filings.
  Also listed on <a href="https://scholar.google.com/citations?user={{ site.scholar_userid }}">Google Scholar</a>,
  <a href="https://orcid.org/{{ site.orcid_id }}">ORCID</a> and
  <a href="https://lattes.cnpq.br/{{ site.lattes_id }}">Lattes</a>.
</p>

<nav class="pub-years" aria-label="Jump to year">
  {%- for row in lattes.years %}
  <a href="#y{{ row.year }}">{{ row.year }}</a>
  {%- endfor %}
  <a href="#patents">Patents</a>
</nav>

<div class="publications">
{%- for row in lattes.years %}
  <h2 class="year" id="y{{ row.year }}">{{ row.year }}</h2>
  {%- if row.journal > 0 %}
  <h3 class="pub-type">Journal articles</h3>
  {% bibliography -f journal -q @*[year={{ row.year }}]* %}
  {%- endif %}
  {%- if row.conference > 0 %}
  <h3 class="pub-type">Conference papers</h3>
  {% bibliography -f conference -q @*[year={{ row.year }}]* %}
  {%- endif %}
  {%- if row.abstract > 0 %}
  <h3 class="pub-type">Workshop papers and abstracts</h3>
  {% bibliography -f abstract -q @*[year={{ row.year }}]* %}
  {%- endif %}
{%- endfor %}

  <h2 class="year" id="patents">Patents</h2>
  <ol class="bibliography patents">
  {%- for p in lattes.patents %}
    <li>
      <div class="row">
        <div class="col-sm-2 abbr"><abbr class="badge">Patent</abbr></div>
        <div class="col-sm-8">
          <div class="title">{{ p.title }}</div>
          <div class="periodical">
            <em>{{ p.office }}</em>{% if p.number != "" %}, {% if p.url != "" %}<a href="{{ p.url }}">{{ p.number }}</a>{% else %}{{ p.number }}{% endif %}{% endif %}, filed {{ p.filed | date: "%B %Y" }}
          </div>
          <div class="author">Applicants: {{ p.applicants }}</div>
        </div>
      </div>
    </li>
  {%- endfor %}
  </ol>
</div>
