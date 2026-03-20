---
layout: photos
title: "无锡太湖周边"
description: ""
header-img: "img/home-bg-art.jpg"
album_slug: "wuxi-taihu"
permalink: /photos/wuxi-taihu/
nav_exclude: true
---

{% assign album = site.data.photos | where: "slug", page.album_slug | first %}
{% if album %}
{% include photo-album.html album=album %}
{% endif %}
