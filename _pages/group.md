---
layout: page
title: Group
permalink: /group/
description: Students I advise or co-advise at UFMG, and former students.
nav: true
nav_order: 3
---

{%- assign g = site.data.group %}
<div class="group">
{% include group_list.html students=g.current level="phd" title="PhD students" %}
{% include group_list.html students=g.current level="msc" title="MSc students" %}
{% include group_list.html students=g.current level="undergrad" title="Undergraduate theses" %}
{% include group_list.html students=g.current level="ic" title="Undergraduate researchers (IC)" %}

<h2>Alumni</h2>
<table class="table table-sm alumni">
  <tbody>
  {%- for s in g.alumni %}
    <tr>
      <th scope="row">{{ s.year }}</th>
      <td>
        <span class="name">{{ s.name }}</span>
        <span class="level">{% case s.level %}{% when "phd" %}PhD{% when "msc" %}MSc{% when "undergrad" %}BSc thesis{% else %}Undergraduate research (IC){% endcase %}{% if s.role == "co-advisor" %}, co-advised{% endif %}{% unless s.institution contains "Minas Gerais" %}, {{ s.institution }}{% endunless %}</span>
        <div class="topic">{{ s.topic }}</div>
      </td>
    </tr>
  {%- endfor %}
  </tbody>
</table>
</div>

<div class="callout">
  <h2>Join the group</h2>
  <p>I am looking for MSc, PhD and undergraduate research (IC) students interested in robotics. E-mail <a href="mailto:{{ site.email | encode_email }}">{{ site.email }}</a> with your CV and a few lines on the problems you want to work on.</p>
</div>
