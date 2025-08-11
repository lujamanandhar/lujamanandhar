"""
GitHub Profile Readme Generator
Generates beautiful, dynamic README with comprehensive GitHub statistics
"""

import os
import requests
import json
from datetime import datetime, timezone
from collections import defaultdict, Counter
import time

class GitHubStatsGenerator:
    def __init__(self):
        self.token = os.environ.get('GITHUB_TOKEN')
        self.username = os.environ.get('GITHUB_USERNAME')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        })

    def make_request(self, url, params=None):
        """Make GitHub API request with rate limit handling"""
        try:
            response = self.session.get(url, params=params)
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                wait_time = max(reset_time - int(time.time()), 60)
                print(f"Rate limit hit, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                response = self.session.get(url, params=params)

            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making request to {url}: {e}")
            return None

    def get_user_info(self):
        """Get user profile information"""
        url = f'https://api.github.com/users/{self.username}'
        return self.make_request(url)

    def get_repositories(self):
        """Get all user repositories"""
        repos = []
        page = 1
        while True:
            url = f'https://api.github.com/users/{self.username}/repos'
            params = {
                'type': 'owner',
                'sort': 'updated',
                'per_page': 100,
                'page': page
            }

            data = self.make_request(url, params)
            if not data:
                break

            repos.extend(data)
            if len(data) < 100:
                break
            page += 1

        return repos

    def get_language_stats(self, repos):
        """Get detailed language statistics"""
        languages = defaultdict(int)
        language_repos = defaultdict(set)

        for repo in repos[:30]:  # Limit to avoid rate limits
            if repo['fork']:
                continue

            url = f"https://api.github.com/repos/{self.username}/{repo['name']}/languages"
            lang_data = self.make_request(url)

            if lang_data:
                for lang, bytes_count in lang_data.items():
                    languages[lang] += bytes_count
                    language_repos[lang].add(repo['name'])

        return dict(languages), {k: list(v) for k, v in language_repos.items()}

    def get_contribution_stats(self):
        """Get contribution statistics for current year"""
        # This would require GraphQL API for detailed contribution data
        # For now, we'll use repository activity as a proxy
        current_year = datetime.now().year
        contributions = 0

        # Estimate based on recent commits (simplified)
        url = f'https://api.github.com/users/{self.username}/events'
        events = self.make_request(url)

        if events:
            current_year_events = [
                e for e in events
                if datetime.fromisoformat(e['created_at'].replace('Z', '+00:00')).year == current_year
            ]
            contributions = len(current_year_events)

        return contributions

    def calculate_advanced_stats(self, user, repos):
        """Calculate advanced statistics"""
        stats = {
            'total_repos': len(repos),
            'public_repos': len([r for r in repos if not r['private']]),
            'total_stars': sum(r['stargazers_count'] for r in repos),
            'total_forks': sum(r['forks_count'] for r in repos),
            'total_watchers': sum(r['watchers_count'] for r in repos),
            'total_size': sum(r['size'] for r in repos),  # in KB
            'followers': user['followers'],
            'following': user['following'],
        }

        # Repository type analysis
        original_repos = [r for r in repos if not r['fork']]
        forked_repos = [r for r in repos if r['fork']]

        stats.update({
            'original_repos': len(original_repos),
            'forked_repos': len(forked_repos),
            'avg_stars_per_repo': stats['total_stars'] / max(len(original_repos), 1),
            'most_starred_repo': max(repos, key=lambda x: x['stargazers_count'])['name'] if repos else 'None',
            'most_starred_stars': max(repos, key=lambda x: x['stargazers_count'])['stargazers_count'] if repos else 0,
        })

        return stats

    def generate_modern_readme(self, user, stats, languages, lang_repos):
        """Generate a modern, beautiful README"""

        # Calculate language percentages
        total_bytes = sum(languages.values())
        lang_percentages = {
            lang: (bytes_count / total_bytes * 100)
            for lang, bytes_count in languages.items()
        } if total_bytes > 0 else {}

        top_languages = sorted(lang_percentages.items(), key=lambda x: x[1], reverse=True)[:8]

        # Language color mapping
        lang_colors = {
            'Python': '#3776ab', 'JavaScript': '#f1e05a', 'TypeScript': '#2b7489',
            'Java': '#b07219', 'C++': '#f34b7d', 'C': '#555555', 'C#': '#239120',
            'Go': '#00ADD8', 'Rust': '#dea584', 'PHP': '#4F5D95', 'Ruby': '#701516',
            'Swift': '#ffac45', 'Kotlin': '#F18E33', 'Dart': '#00B4AB', 'R': '#276DC3',
            'Scala': '#c22d40', 'Shell': '#89e051', 'HTML': '#e34c26', 'CSS': '#1572B6',
            'Vue': '#4FC08D', 'React': '#61DAFB', 'Angular': '#DD0031'
        }

        current_time = datetime.now(timezone.utc)

        readme_content = f"""
<div align="center">

# 👋 Hello, I'm {user['name'] or user['login']}!

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=00D4AA&center=true&vCenter=true&width=600&lines=Welcome+to+my+GitHub+profile!;{user['public_repos']}%2B+repositories+and+counting...;{stats['total_stars']}+stars+earned+so+far!;Always+learning%2C+always+coding!" alt="Typing SVG" />

</div>

{f'> *{user["bio"]}*' if user.get('bio') else ''}

---

## 🎯 Quick Overview

<div align="center">

<table>
<tr>
<td align="center">
  <img src="https://github-readme-stats.vercel.app/api?username={self.username}&show_icons=true&theme=tokyonight&hide_border=true&bg_color=0D1117&title_color=00D4AA&text_color=FFFFFF&icon_color=00D4AA" alt="GitHub Stats" />
</td>
<td align="center">
  <img src="https://github-readme-streak-stats.herokuapp.com/?user={self.username}&theme=tokyonight&hide_border=true&background=0D1117&stroke=00D4AA&ring=00D4AA&fire=FF6B6B&currStreakLabel=00D4AA" alt="GitHub Streak" />
</td>
</tr>
</table>

</div>

---

## 📊 Detailed Statistics

<div align="center">

| 📈 **Metric** | 🔢 **Value** | 📈 **Metric** | 🔢 **Value** |
|:---:|:---:|:---:|:---:|
| **🏗️ Total Repositories** | `{stats['total_repos']}` | **⭐ Total Stars** | `{stats['total_stars']:,}` |
| **📚 Original Repos** | `{stats['original_repos']}` | **🍴 Total Forks** | `{stats['total_forks']:,}` |
| **🔄 Forked Repos** | `{stats['forked_repos']}` | **👥 Followers** | `{stats['followers']:,}` |
| **📦 Repository Size** | `{stats['total_size'] / 1024:.1f} MB` | **🏆 Most Starred** | `{stats['most_starred_repo']} ({stats['most_starred_stars']} ⭐)` |

</div>

---
<div align="center">
<table>
<tr>
<td valign="top" width="50%">

### 📅 Account Information

🗓️ **Joined GitHub:** {datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')).strftime('%B %Y')}

📍 **Location:** {user['location'] or 'Earth 🌍'}

🌐 **Website:** {f"[{user['blog']}]({user['blog']})" if user.get('blog') else 'Not specified'}

✉️ **Public Email:** {user['email'] or 'Not public'}

</td>
<td valign="top" width="50%">

### 🛠️ Technology Stack & Languages

<div align="center">

<img src="https://github-readme-stats.vercel.app/api/top-langs/?username={self.username}&layout=donut&theme=tokyonight&hide_border=true&bg_color=0D1117&title_color=00D4AA&text_color=FFFFFF&langs_count=5" alt="Top Languages" />

</div>

</td>
</tr>
</table>
</div>


## 🏆 GitHub Achievements

<div align="center">

<img src="https://github-profile-trophy.vercel.app/?username={self.username}&theme=tokyonight&no-frame=true&no-bg=true&margin-w=4&column=7" alt="GitHub Trophies" />

</div>

---

## 📈 Contribution Activity

<div align="center">

<img src="https://github-readme-activity-graph.vercel.app/graph?username={self.username}&bg_color=0D1117&color=00D4AA&line=00D4AA&point=FFFFFF&area=true&hide_border=true" alt="Contribution Graph" />

</div>

---

## 🤝 Let's Connect!

<div align="center">

{self._generate_social_links(user)}
[![Profile Views](https://komarev.com/ghpvc/?username={self.username}&color=00D4AA&style=for-the-badge&label=PROFILE+VIEWS)](https://github.com/{self.username})

</div>

---


<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer&text=Thanks%20for%20visiting!&fontSize=24&fontColor=fff&animation=twinkling" />

</div>
"""

        return readme_content.strip()


    def _generate_social_links(self, user):
        """Generate social media links"""
        links = []

        if user.get('blog'):
            links.append(f"[![Website](<https://img.shields.io/badge/Website-00D4AA?style=for-the-badge&logo=google-chrome&logoColor=white>)]({user['blog']})")

        if user.get('twitter_username'):
            links.append(f"[![Twitter](https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/{user['twitter_username']})")

        if user.get('email'):
            links.append(f"[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:{user['email']})")

        links.append(f"[![GitHub](https://img.shields.io/badge/GitHub-000000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/{self.username})")

        return ' '.join(links)

    def run(self):
        """Main execution function"""
        print("🚀 Starting GitHub Profile Stats Generation...")

        # Get user information
        print("📊 Fetching user information...")
        user = self.get_user_info()
        if not user:
            print("❌ Failed to fetch user information")
            return False

        # Get repositories
        print("📚 Fetching repositories...")
        repos = self.get_repositories()
        if not repos:
            print("❌ Failed to fetch repositories")
            return False

        print(f"✅ Found {len(repos)} repositories")

        # Get language statistics
        print("🔍 Analyzing language usage...")
        languages, lang_repos = self.get_language_stats(repos)

        # Calculate advanced statistics
        print("📈 Calculating advanced statistics...")
        stats = self.calculate_advanced_stats(user, repos)

        # Generate README
        print("📝 Generating README content...")
        readme_content = self.generate_modern_readme(user, stats, languages, lang_repos)

        # Write to file
        print("💾 Writing README.md...")
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print("✅ Profile README generated successfully!")
        print(f"📊 Stats Summary:")
        print(f"   - {stats['total_repos']} repositories")
        print(f"   - {stats['total_stars']} total stars")
        print(f"   - {len(languages)} programming languages")

        return True

if __name__ == "__main__":
    generator = GitHubStatsGenerator()
    success = generator.run()

    if not success:
        exit(1)
