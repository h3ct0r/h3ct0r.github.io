---
layout: page
title: Research
permalink: /research/
description: Current and past research projects. Each project page lists its publications.
nav: true
nav_order: 2
---

My work spans field robotics, from the ground robots of my PhD and the EspeleoRobô project to aerial and multi-robot systems, and it increasingly uses learning-based methods. More detail on my thesis is on the <a href="{{ '/phd/' | relative_url }}">PhD page</a>, and code is on the <a href="{{ '/repositories/' | relative_url }}">repositories page</a>.

<div class="research">
  <h2 class="category" id="current">Current projects</h2>
  {%- assign projects = site.projects | where: "category", "current" | sort: "importance" %}
  <div class="row row-cols-1 row-cols-md-2">
  {%- for project in projects %}
    {% include research_card.html %}
  {%- endfor %}
  </div>

  <h2 class="category" id="earlier">Earlier work</h2>
  {%- assign projects = site.projects | where: "category", "earlier" | sort: "importance" %}
  <div class="row row-cols-1 row-cols-md-2">
  {%- for project in projects %}
    {% include research_card.html %}
  {%- endfor %}
  </div>
</div>
