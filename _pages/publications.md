---
layout: page
permalink: /publications/
title: Publications
description: Publications by categories in reversed chronological order.
years: [2022, 2021, 2020, 2019, 2018, 2017, 2016, 2014]
nav: true
nav_order: 2
---

Up-to-date list of publications available on <a href="https://scholar.google.com/citations?user=exfaeS8AAAAJ">Google Scholar</a>, or <a href="http://lattes.cnpq.br/8363001713282037">Lattes</a>.

<!-- _pages/publications.md -->
<div class="publications">

{%- for y in page.years %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f journal -q @*[year={{y}}]* %}
  {% bibliography -f conference -q @*[year={{y}}]* %}
{% endfor %}

</div>
