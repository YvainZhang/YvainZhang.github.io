---
layout: photos
title: "城市夜景"
description: ""
header-img: "img/home-bg-art.jpg"
album_slug: "city-nightscape"
permalink: /photos/city-nightscape/
nav_exclude: true
---

{% assign album = site.data.photos | where: "slug", page.album_slug | first %}
{% if album %}
{% include photo-album.html album=album %}
{% endif %}
