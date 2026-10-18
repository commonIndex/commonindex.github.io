# CommonIndex website

The launch site for CommonIndex: one static page with the launch video,
published with GitHub Pages.

## Build

```sh
python3 build.py                                  # for https://commonindex.github.io
SITE_URL=https://your-domain.example python3 build.py  # with your own domain
```

Edit `src/body.html` (the page) and `assets/` (video, poster, share image), then
rebuild. `docs/` is what gets published.

## Publish on GitHub Pages

1. Push this folder to `commonindex/commonindex.github.io` (the organization's
   own site, so it is served at the root, with no repository name in the URL).
2. Settings → Pages → Build and deployment: **Deploy from a branch**, branch
   `main`, folder **/docs**. (A branch publishes only from its root or
   `/docs`, which is why the build writes there.)
3. The site is live at `https://commonindex.github.io/`.

## Your own domain

1. Rebuild with `SITE_URL=https://<your-domain>`, so share cards and the
   sitemap point at it.
2. Push. The build writes `docs/CNAME` with the domain itself, so a rebuild
   keeps it.
3. At your domain registrar, add a `CNAME` record from the domain (or `www`)
   to `commonindex.github.io`. For an apex domain, use GitHub's `A` records
   instead (see GitHub's "Managing a custom domain" guide).
4. Settings → Pages: enter the domain and tick **Enforce HTTPS**.

## After launch

Add the site to Google Search Console and Bing Webmaster Tools and submit
`sitemap.xml`.
