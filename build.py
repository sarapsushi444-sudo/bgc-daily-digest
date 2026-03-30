#!/usr/bin/env python3
"""
Build script for BGC Daily Digest website.
 Converts markdown archive files to standalone HTML pages.
 Run after each digest is generated.
"""
import json
import os
import re
import sys
from datetime import datetime

WORKSPACE = os.environ.get('WORKSPACE', '/home/ubuntu/.openclaw/workspace')
SKILL_DIR = os.environ.get('SKILL_DIR', '/home/ubuntu/.openclaw/workspace/skills/tech-news-digest')
ARCHIVE_DIR = os.path.join(WORKSPACE, 'archive/tech-news-digest')
OUTPUT_DIR = os.path.join(WORKSPACE, 'digests')

TOPIC_CLASSES = {
    'ai-llm': 'ai', 'llm': 'ai',
    'crypto': 'crypto',
    'oil-energy': 'oil', 'oil': 'oil',
    'finance': 'finance',
    'philippines': 'ph',
}

def extract_sections(markdown_content):
    """Split markdown into sections by emoji headers.
    Article format (per line):
      🔥 **11** • Title — Summary
      → https://url.com
    """
    sections = []
    current = {'emoji': '📰', 'label': 'Overview', 'id': 'overview', 'articles': []}

    lines = markdown_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Section header: ## emoji Label
        if re.match(r'^##\s+', line):
            if current['articles'] or sections:
                sections.append(current)
            header = re.sub(r'^##\s+', '', line)
            emoji_m = re.match(r'^([^\w\s]\S*)\s*(.+)', header)
            if emoji_m:
                emoji, label = emoji_m.group(1), emoji_m.group(2).strip()
            else:
                emoji, label = '📰', header
            # Build a URL-safe id, map to CSS-compatible short IDs via keyword matching
            raw_id = re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')
            label_lower = label.lower()
            if 'ai' in label_lower or 'llm' in label_lower or 'language model' in label_lower:
                topic_id = 'ai-llm'
            elif 'bitcoin' in label_lower or 'crypto' in label_lower:
                topic_id = 'crypto'
            elif 'oil' in label_lower or 'gas' in label_lower or 'geopolitic' in label_lower or 'energy' in label_lower:
                topic_id = 'oil'
            elif 'market' in label_lower or 'finance' in label_lower or 'econom' in label_lower or 'stock' in label_lower:
                topic_id = 'finance'
            elif 'philippine' in label_lower or 'manila' in label_lower or 'bgc' in label_lower or 'makati' in label_lower:
                topic_id = 'ph'
            else:
                topic_id = raw_id
            current = {'emoji': emoji, 'label': label, 'id': topic_id, 'articles': []}
            i += 1
            continue

        # Article line: starts with 🔥 **score**
        if '🔥' in line:
            score_m = re.search(r'🔥\s+\*\*([\d.]+)\*\*', line)
            if score_m:
                score = float(score_m.group(1))
                # Title is everything after the bullet (•) up to '—'
                # Format: "🔥 **11** • Title — Summary"
                bullet_idx = line.find('•')
                title = line[bullet_idx+1:] if bullet_idx != -1 else line
                title = title.split('—')[0].strip()
                title = title.strip('• ').strip()

                # Next line is URL (→ format)
                url = ''
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('→ '):
                        url = next_line[2:].strip()
                        i += 1

                if url:
                    current['articles'].append({
                        'score': score,
                        'title': title,
                        'url': url,
                        'summary': '',
                    })
        i += 1

    if current['articles'] or sections:
        sections.append(current)

    return sections

def render_article(a):
    score = a.get('score', 0)
    title = a.get('title', '')
    url = a.get('url', '#')
    summary = a.get('summary', '')

    score_html = f'<div class="article-score">🔥 {score}</div>' if score else ''
    summary_html = f'<div class="article-summary">{summary}</div>' if summary else ''

    return f"""
  <div class="article-item">
    {score_html}
    <a href="{url}" class="article-title" target="_blank" rel="noopener">{title}</a>
    {summary_html}
  </div>"""

def render_section(section):
    articles_html = ''.join(render_article(a) for a in section['articles'])
    return f"""
<section class="section" id="{section['id']}">
  <div class="section-header">
    <span class="emoji">{section['emoji']}</span>
    <h2>{section['label']}</h2>
  </div>
  {articles_html}
</section>"""

def build_digest_html(filename, date_display, day, markdown_content):
    """Build a full HTML page from a digest markdown file."""
    sections = extract_sections(markdown_content)

    # Build section nav
    nav_items = ''.join(
        f'<a href="#{s["id"]}">{s["emoji"]} {s["label"].split(" ")[0]}</a>'
        for s in sections if s.get('articles')
    )

    sections_html = ''.join(render_section(s) for s in sections if s.get('articles'))

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BGC Digest — {date_display}</title>
  <link rel="stylesheet" href="style.css">
  <meta name="description" content="BGC Daily Digest — {date_display}">
</head>
<body>

<nav class="navbar">
  <div class="navbar-inner">
    <a href="../index.html" class="navbar-brand">📰 <span>BGC</span> Daily Digest</a>
    <div class="nav-topics">
      <a href="#ai-llm" class="nav-topic ai">🧠 AI/LLM</a>
      <a href="#crypto" class="nav-topic crypto">₿ Crypto</a>
      <a href="#oil" class="nav-topic oil">🛢️ Oil &amp; Gas</a>
      <a href="#finance" class="nav-topic finance">📈 US Markets</a>
      <a href="#ph" class="nav-topic ph">🇵🇭 Philippines</a>
    </div>
  </div>
</nav>

<div class="container">
  <a href="index.html" class="back-link">← All Digests</a>

  <div class="digest-meta">
    <span class="date">{date_display}</span>
    <span class="day">{day}</span>
  </div>

  <div class="section-nav">
    {nav_items}
  </div>

  {sections_html}

</div>

<footer class="footer">
  <p>🤖 Powered by <a href="https://github.com/draco-agent/tech-news-digest" target="_blank">tech-news-digest</a> &amp; <a href="https://openclaw.ai" target="_blank">OpenClaw</a></p>
  <p style="margin-top:0.4rem; color: var(--text-muted);">BGC Daily Digest — Philippines 🦖</p>
</footer>

</body>
</html>'''
    return html

def build_manifest(archive_dir):
    """Build a manifest.json from all archive files."""
    import glob
    files = sorted(glob.glob(os.path.join(archive_dir, 'daily-*.md')), reverse=True)
    manifest = []
    for f in files:
        basename = os.path.basename(f)
        date_str = basename.replace('daily-', '').replace('.md', '')
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            date_display = dt.strftime('%B %d, %Y')
            day = dt.strftime('%A')
        except:
            date_display = date_str
            day = ''

        manifest.append({
            'date': date_str,
            'date_display': date_display,
            'day': day,
            'file': f'daily-{date_str}.html',
            'topics': [
                {'label': 'AI/LLM', 'cls': 'ai'},
                {'label': 'Crypto', 'cls': 'crypto'},
                {'label': 'Oil & Gas', 'cls': 'oil'},
                {'label': 'US Markets', 'cls': 'finance'},
                {'label': 'Philippines', 'cls': 'ph'},
            ],
            'topic_count': 5,
        })
    return manifest

def main():
    archive_dir = ARCHIVE_DIR
    output_dir = OUTPUT_DIR

    os.makedirs(os.path.join(output_dir, 'archive'), exist_ok=True)

    import glob
    md_files = sorted(glob.glob(os.path.join(archive_dir, 'daily-*.md')), reverse=True)

    print(f'Found {len(md_files)} digest files')

    for f in md_files:
        basename = os.path.basename(f)
        date_str = basename.replace('daily-', '').replace('.md', '')
        out_file = os.path.join(output_dir, 'archive', f'daily-{date_str}.html')

        # Always rebuild to pick up changes
        with open(f, 'r') as fh:
            content = fh.read()

        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            date_display = dt.strftime('%B %d, %Y')
            day = dt.strftime('%A')
        except:
            date_display = date_str
            day = ''

        html = build_digest_html(basename, date_display, day, content)

        with open(out_file, 'w') as fh:
            fh.write(html)

        print(f'  [built] {basename} ({len(extract_sections(content))} sections)')

    # Build manifest
    manifest = build_manifest(archive_dir)
    manifest_file = os.path.join(output_dir, 'archive', 'manifest.json')
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'Updated manifest with {len(manifest)} digests')

    # Copy index + css to archive directory too (for GitHub Pages root)
    os.system(f'cp {OUTPUT_DIR}/index.html {OUTPUT_DIR}/archive/')
    os.system(f'cp {OUTPUT_DIR}/style.css {OUTPUT_DIR}/archive/')
    print('Copied index.html and style.css to archive/ (GitHub Pages root)')

if __name__ == '__main__':
    main()
