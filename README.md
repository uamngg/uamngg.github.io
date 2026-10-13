# Portfolio

Static site, no dependencies except Python 3. 

```
python build.py          # builds into dist/
python -m http.server -d dist 8000   # preview at http://localhost:8000
```

## Add a game
1. Copy any file in `content/games/` and rename it (the file name becomes the URL).
2. Edit the top lines and the text below `---`. `category:` (Released / Prototype) makes the filter buttons.
   `key:` is the main elements shown on the card, separated by `|`. `screenshots:` is a comma list of image paths.
3. Optional media (all optional, cards fall back to a coloured placeholder):
   - `youtube:` the video ID only (e.g. `dQw4w9WgXcQ`)
   - `clip:` path to a short looping video, e.g. `media/my-game.webm` (file goes in `static/media/`)
   - `cover:` path to an image, e.g. `media/my-game.jpg`
4. `git add . && git commit -m "Add game" && git push` and the site redeploys.

Set `draft: true` to hide a game. `featured: true` shows a game on the home page.

## Other edits
- Name, intro, links, skills, experience: `site.json`
- Colours and layout: `static/style.css` (colours are at the top)
- Resume: put `Umang_Pansuriya_Resume.pdf` in `static/` and a download button appears on About.

## Deploy (GitHub Pages, free)
1. Create a GitHub repo, push this folder to the `main` branch.
2. Repo Settings -> Pages -> Source: **GitHub Actions**.
3. Your site will be at `https://USERNAME.github.io/REPO/` (name the repo `USERNAME.github.io` for a root URL).

Cloudflare Pages alternative: build command `python build.py`, output directory `dist`.
