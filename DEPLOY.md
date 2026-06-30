# Barberowiec — deploy & daily auto-refresh

This folder is the **entire website**. Upload *only this folder* to GitHub — never the
parent "Claude Code" folder (that one holds your leads and other clients' sites).

## What's in here

```
barberowiec-site/
├─ index.html                         ← the website (one self-contained file)
├─ update_stats.py                    ← refreshes the Booksy count + rating
├─ DEPLOY.md                          ← this file
└─ .github/
   └─ workflows/
      └─ refresh-stats.yml            ← the daily job that runs update_stats.py
```

### About the `.github` folder

It's the hidden folder above, and the exact path **`.github/workflows/refresh-stats.yml`
must be preserved** — GitHub only looks there for scheduled jobs ("Actions"). You don't
create it on GitHub by hand; you just upload it with everything else. Two gotchas:

- Windows Explorer **hides folders that start with a dot**, so you may not see `.github`.
  It's there. Using `git` to push (below) includes it automatically.
- If you upload via the GitHub website's drag-and-drop, dotfolders are sometimes skipped.
  If the **Actions** tab shows no workflow after uploading, the `.github` folder didn't
  make it — push with `git` instead.

---

## How it all fits

```
barberowiec.pl (domain)  ──DNS──▶  Cloudflare Pages  ──serves──▶  visitors
        ▲
GitHub repo ──push──▶ redeploy
        ▲
        └─ once a day, GitHub Actions runs update_stats.py, grabs the live
           Booksy count, commits the change → triggers the redeploy
```

Free hosting + free SSL, and the numbers refresh **even when your PC is off**.
Cost = just the domain (~€15–30/yr).

---

## Part A — Buy `barberowiec.pl`

`.pl` is the Polish registry (NASK). Buy it at one of:

- **OVHcloud** (ovhcloud.com/pl) — English UI, sells `.pl`, allows custom nameservers.
- **nazwa.pl / cyberFolks / home.pl** — Polish registrars, Polish support, 1st-year promos.
- **Porkbun / Namecheap** — international, English checkout.

> Cloudflare Registrar does **not** sell `.pl`. Buy it at one of the above; you can still
> use Cloudflare for free DNS (Part B, step 3).

Steps: search `barberowiec.pl` → register → **turn on auto-renew** → enable WHOIS privacy.

---

## Part B — Host it + turn on the daily refresh

**1. Put this folder on GitHub**
- Create a free account at github.com → **New repository** (e.g. `barberowiec-site`, public is fine).
- Push this folder. Easiest with git:
  ```
  cd barberowiec-site
  git init
  git add .
  git commit -m "Barberowiec site"
  git branch -M main
  git remote add origin https://github.com/<you>/barberowiec-site.git
  git push -u origin main
  ```
- Check the repo's **Actions** tab shows "Refresh Booksy stats". If not, see the `.github`
  note above.

**2. Host with Cloudflare Pages (free)**
- cloudflare.com → **Workers & Pages → Create → Pages → Connect to Git** → pick the repo.
- Build settings: framework **None**, build command **empty**, output directory **`/`** → Deploy.
- You get a free `*.pages.dev` test URL.

**3. Point the domain at it**
- Cloudflare → **Add a site** → `barberowiec.pl` → it gives you 2 nameservers.
- At your registrar, replace the default nameservers with Cloudflare's two (propagates in a few hours).
- Cloudflare Pages → your project → **Custom domains** → add `barberowiec.pl` and
  `www.barberowiec.pl`. SSL is automatic.

**4. Daily refresh — already wired**
`refresh-stats.yml` runs every morning, commits any change, and the push auto-redeploys.
Run it on demand anytime: repo → **Actions → Refresh Booksy stats → Run workflow**.

---

## Updating the numbers manually (optional)

From this folder, with Python installed:

```
pip install requests
python update_stats.py            # writes index.html
python update_stats.py --dry-run  # preview only
```
