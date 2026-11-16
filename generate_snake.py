
import os
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape


# ==========================================
# SUFYAN SNAKE ENGINE
# ==========================================

USERNAME = "Sufyan-m"
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT_DIR = Path("dist")

CELL_SIZE = 11
GAP = 3
STEP = CELL_SIZE + GAP

ANIMATION_DURATION = 45

if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN environment variable is missing!")


# ==========================================
# 1. FETCH GITHUB CONTRIBUTIONS
# ==========================================

def fetch_contributions():

    end_date = datetime.now(timezone.utc)

    start_date = end_date - timedelta(days=365)

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "login": USERNAME,
            "from": start_date.isoformat(),
            "to": end_date.isoformat()
        }
    }

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Sufyan-Snake-Engine"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    if "errors" in result:
        raise RuntimeError(
            f"GitHub GraphQL error: {result['errors']}"
        )

    user = result.get("data", {}).get("user")

    if user is None:
        raise RuntimeError(f"GitHub user not found: {USERNAME}")

    calendar = (
        user["contributionsCollection"]["contributionCalendar"]
    )

    print("Total contributions:", calendar["totalContributions"])

    return calendar["weeks"]


# ==========================================
# 2. COLOR THEMES
# ==========================================

THEMES = {

    "dark": {
        "background": "#1a1b26",
        "empty": "#24283b",
        "levels": [
            "#24283b",
            "#414868",
            "#3d59a1",
            "#7aa2f7",
            "#bb9af7"
        ],
        "snake": "#7aa2f7",
        "glow": "#bb9af7",
        "text": "#a9b1d6"
    },

    "light": {
        "background": "#ffffff",
        "empty": "#ebedf0",
        "levels": [
            "#ebedf0",
            "#9be9a8",
            "#40c463",
            "#30a14e",
            "#216e39"
        ],
        "snake": "#0969da",
        "glow": "#58a6ff",
        "text": "#57606a"
    }
}


LEVEL_MAP = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4
}


# ==========================================
# 3. GENERATE ANIMATED SVG
# ==========================================

def generate_svg(weeks, theme_name):

    theme = THEMES[theme_name]

    columns = len(weeks)

    width = columns * STEP + 20
    height = 7 * STEP + 45

    cells = []
    snake_points = []
    month_labels = []

    day_index = 0

    # Build contribution calendar

    for col, week in enumerate(weeks):

        for row, day in enumerate(week["contributionDays"]):

            x = 10 + col * STEP
            y = 25 + row * STEP

            level = LEVEL_MAP.get(
                day["contributionLevel"], 0
            )

            count = day["contributionCount"]

            color = theme["levels"][level]

            date = day["date"]

            title = escape(
                f"{date}: {count} contributions"
            )

            # Contribution square

            cells.append(f"""
            <rect
                x="{x}"
                y="{y}"
                width="{CELL_SIZE}"
                height="{CELL_SIZE}"
                rx="2"
                fill="{color}"
                opacity="1">

                <title>{title}</title>

                <animate
                    attributeName="opacity"
                    values="1;0.45;1"
                    dur="{ANIMATION_DURATION}s"
                    begin="{day_index * ANIMATION_DURATION / max(1, columns * 7):.3f}s"
                    repeatCount="indefinite"
                />

            </rect>
            """)

            # Snake follows the real calendar positions

            center_x = x + CELL_SIZE / 2
            center_y = y + CELL_SIZE / 2

            snake_points.append(
                f"{center_x},{center_y}"
            )

            # Month labels

            parsed_date = datetime.strptime(date, "%Y-%m-%d")

            if parsed_date.day <= 7:
                month_labels.append(
                    f"""
                    <text
                        x="{x}"
                        y="15"
                        fill="{theme['text']}"
                        font-size="9"
                        font-family="monospace">
                        {escape(parsed_date.strftime("%b"))}
                    </text>
                    """
                )

            day_index += 1

    path_data = "M " + " L ".join(snake_points)

    # ======================================
    # SVG DOCUMENT
    # ======================================

    svg = f"""
    <svg
        xmlns="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        viewBox="0 0 {width} {height}"
        width="100%"
        role="img"
        aria-label="Animated GitHub contribution snake">

        <title>Sufyan's GitHub Contribution Snake</title>

        <defs>

            <filter id="glow">
                <feGaussianBlur
                    stdDeviation="4"
                    result="blur"
                />
                <feMerge>
                    <feMergeNode in="blur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>

        </defs>

        <rect
            width="100%"
            height="100%"
            rx="8"
            fill="{theme['background']}"
        />

        <!-- Month labels -->

        {''.join(month_labels)}

        <!-- Contribution grid -->

        {''.join(cells)}

        <!-- Snake movement path -->

        <path
            id="snake-path"
            d="{path_data}"
            fill="none"
            stroke="{theme['snake']}"
            stroke-width="5"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-dasharray="35 10000"
            pathLength="10000"
            opacity="0.95"
            filter="url(#glow)">

            <animate
                attributeName="stroke-dashoffset"
                from="0"
                to="-10035"
                dur="{ANIMATION_DURATION}s"
                repeatCount="indefinite"
            />

        </path>

        <!-- Animated snake head -->

        <circle
            r="5"
            fill="{theme['glow']}"
            stroke="{theme['snake']}"
            stroke-width="2"
            filter="url(#glow)">

            <animateMotion
                dur="{ANIMATION_DURATION}s"
                repeatCount="indefinite"
                rotate="auto">

                <mpath xlink:href="#snake-path"/>

            </animateMotion>

        </circle>

    </svg>
    """

    return svg


# ==========================================
# 4. SAVE BOTH THEMES
# ==========================================

def main():

    print("Fetching GitHub contributions...")

    weeks = fetch_contributions()

    if not weeks:
        raise RuntimeError("No contribution data received!")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    files = {
        "snake.svg": "light",
        "snake-dark.svg": "dark"
    }

    for filename, theme in files.items():

        svg = generate_svg(weeks, theme)

        output_path = OUTPUT_DIR / filename

        output_path.write_text(
            svg,
            encoding="utf-8"
        )

        print(f"Generated: {output_path}")

    print("Snake generation completed!")


if __name__ == "__main__":
    main()
