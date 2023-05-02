# under active alpha development

bandcamp++ is a browser-based GUI for enhancing your bandcamp.com music discovery.

The primary features are:
- asynchronous scraping of profiles, purchases, labels/artists in your extended network
- improved UI for keeping up-to-date with new releases and purchases from your network
- tracking of previously "seen" releases to remove duplicate recommendations
- single-page exploration and "binning" to avoid tab explosion

Front-end technologies used:
- javascript
- HTML/CSS
- Bootstrap5
- d3.js

Back-end technologies used:
- python
- django
- celery (w/ celery_progress, requests, Redis, daphne, websockets)
- PostgreSQL

The project is provided as a container for Docker, with an initial setup in the browser UI upon first run.
