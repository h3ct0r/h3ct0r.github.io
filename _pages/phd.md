---
layout: page
permalink: /phd/
title: Ph.D.
description: Dissertation in the autonomous exploration of confined and subterranean spaces
nav: true
nav_order: 1
---

<div>
    <h2>Terrain-Aware Autonomous Exploration of Unstructured Confined Spaces</h2>
<div>

<div class="publications">
    <h3>Abstract</h3>
    This thesis project addresses the problem of exploring confined environments autonomously using terrestrial mobile robots. Here we propose a methodology for path planning in rough three-dimensional terrains and two exploration techniques that use the map's navigable areas, the related navigation cost, and the information expected from a frontier to select the next exploration sector. The presented pipelines are built over a representation of the environment based on three-dimensional meshes and raw point clouds. The reconstructed meshes are converted into traversable graphs, and the dangerous or untraversable regions are filtered considering the expected pose of the robot at the time of planning. The generation of the most promising paths uses a linear combination of weights applied to multiple traversability metrics of the terrain, such as distance, roughness, and energy consumption of the robot. The proposed exploration method uses the expected volumetric information of frontiers after visitation; this way, the exploration areas are selected according to their expected utility and visit cost, considering the terrain's topography. We also propose an online planning phase using the raw point cloud to avoid obstacles in dynamic environments. The online phase is faster to compute and uses an RRT algorithm biased towards the most informative frontier, which is capable of planning and selecting a target frontier without specifying a hardcoded utility metric. The algorithms were validated in representative simulated and real environments, proving the viability of the proposed methodologies.
</div>

<div class="publications">
    <h3>Downloads</h3>
    <p><i class="fa fa-book" aria-hidden="true"></i><a href="https://repositorio.ufmg.br/bitstream/1843/44581/3/RC9_bibloteca_fix_summario.pdf">&nbsp;Ph.D. dissertation PDF document</a></p>
    <p><i class="fab fa-github-alt" aria-hidden="true"></i><a href="https://github.com/verlab/terrain_aware_exploration">&nbsp;Github source code (ROS1, C++ and Python)</a></p>
</div>

<div class="publications">
    <h3>Defense Information</h3>
    <div>
        <ul class="card-text font-weight-light list-group list-group-flush">
            <li class="list-group-item">
                <h5 class="font-italic">Advisors:</h5>
                <ul class="subitems">
                    <li><span class="subitem">Douglas G. Macharet (advisor)</span></li>
                    <li><span class="subitem">Mario F. M. Campos (co-advisor)</span></li>
                </ul>
            </li>
            <li class="list-group-item">
                <h5 class="font-italic">Defense date:</h5>
                <ul class="subitems">
                    <li><span class="subitem">08/07/2022</span></li>
                </ul>
            </li>
            <li class="list-group-item">
                <h5 class="font-italic">Comittee:</h5>
                <ul class="subitems">
                    <li><span class="subitem">Prof. Luiz Chaimowicz (DCC/UFMG)</span></li>
                    <li><span class="subitem">Prof. Gustavo Medeiros Freitas (DEE/UFMG)</span></li>
                    <li><span class="subitem">Prof. Gustavo Pessin (MI/ITV)</span></li>
                    <li><span class="subitem">Prof. Denis Fernando Wolf (ICMC/USP)</span></li>
                </ul>
            </li>
        </ul>
    </div>

</div>

<div class="publications">
    <h3>Videos</h3>
    <div class="video-desc-grid" style="display: flex; justify-content: space-between;">
        <iframe width="560" height="315" src="https://www.youtube.com/embed/yXycgBDhSME" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        &nbsp;
        <iframe width="560" height="315" src="https://www.youtube.com/embed/Otboyqh6GWI" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    </div>
    
    <div class="video-desc-grid" style="display: flex; justify-content: space-between; margin-top:10px;">
        <iframe width="560" height="315" src="https://www.youtube.com/embed/d6wrfBwOjv0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        &nbsp;
        <iframe width="560" height="315" src="https://www.youtube.com/embed/aZu_y8-CS9A" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    </div>
</div>

<div class="publications">
    <h3>Thesis Related Publications</h3>
    {% bibliography -f journal -q @*[phd=true]* %}
    {% bibliography -f conference -q @*[phd=true]* %}
    {% bibliography -f workshop -q @*[phd=true]* %}
</div>

<div class="publications">
    <h3>Other Associated Publications</h3>
    {% bibliography -f journal -q @*[otherphd=true]* %}
    {% bibliography -f conference -q @*[otherphd=true]* %}
    {% bibliography -f workshop -q @*[otherphd=true]* %}
</div>
