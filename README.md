# elijahbot-tools-hub

Unified Vercel deployment of 27 single-file tools by Elijah Purcell.

## What this is

Instead of `thebigjah.github.io/verse-vault/`, `thebigjah.github.io/counter/`, `thebigjah.github.io/solomon/` (one URL per tool, each on GitHub Pages), this hosts all 27 tools at a single clean domain.

After Vercel import + custom domain wiring, the URLs become:

  tools.purcellventures.co/verse-vault/
  tools.purcellventures.co/counter/
  tools.purcellventures.co/solomon/
  ... etc

Plus a landing page at the root with all 27 tools categorized.

## Deploy in 3 minutes (Elijah does this)

1. Push this repo to GitHub:
   ```
   cd C:/Users/elija/elijahbot-tools-hub
   gh repo create elijahbot-tools-hub --public --source=. --push
   ```

2. Go to https://vercel.com/new

3. Import the `elijahbot-tools-hub` repo. Vercel auto-detects it as a static project. Click Deploy.

4. After ~30 sec it's live at something like `elijahbot-tools-hub.vercel.app`. Click "View" to confirm.

5. Add custom domain:
   - Vercel project → Settings → Domains → Add Domain
   - Type `tools.purcellventures.co` (or `tools.elijahpurcell.com` if you prefer)
   - Vercel will give you a CNAME record to add to your DNS provider
   - DNS propagates in 5-60 min
   - Done. All 27 tools live at the new domain.

## Updating tools

Each tool's source is copied from `~/<tool-name>/index.html`. When you update the source, re-run the sync script (or just copy the file manually).

Quick sync script:

```bash
cd C:/Users/elija/elijahbot-tools-hub
for tool in $(ls public/); do
  if [ -f "/c/Users/elija/$tool/index.html" ]; then
    cp "/c/Users/elija/$tool/index.html" "public/$tool/index.html"
  fi
done
git add -A && git commit -m "sync tools" && git push
```

Vercel auto-redeploys on push to main, so the new version is live within ~30 sec.

## Tools included (27)

**Faith + Discipline:** verse-vault, prayer-journal, examen, counter-argument, worship-set, sermon-notes, solomon, calvinism-test

**Productivity + Growth:** decision-journal, brag-doc, friendship-map, future-self, rival, momentum, reading-log, weekly-skill, wisdom-prep

**Business + Lead-gen:** ai-readiness-test, ai-cost-calculator, ai-will

**UA + Planning:** milestone, dorm-pack, day-sheet

**Connection + Story:** echo, hangout, era

**Cryptography:** cipher-lab

## Why this matters

The github.io URLs work but they're not professional. They live on Elijah's *personal* GitHub username, scattered across 27 separate repos. They have no unified branding, no Purcell Ventures footer, no SEO meta tags.

This hub fixes all that with one deploy. The tools become **Purcell Ventures products** rather than personal weekend projects, which matters for:

- Sharing them with consulting clients
- Sharing in IG/LinkedIn marketing posts
- Showing them off in college applications, internships, interviews
- Bookmarking on a phone with a real domain

The marginal cost is ~$0 (Vercel free tier covers this easily).

Built 2026-05-18 workshop. Co-authored by ElijahBot (Claude Opus 4.7).
