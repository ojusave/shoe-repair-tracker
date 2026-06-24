from urllib.parse import urlencode


GITHUB_REPO_URL = "https://github.com/ojusave/shoe-repair-tracker"


def render_signup_url_with_utms(content: str = "footer_link") -> str:
    params = urlencode(
        {
            "utm_source": "github",
            "utm_medium": "referral",
            "utm_campaign": "ojus_demos",
            "utm_content": content,
        }
    )
    return f"https://dashboard.render.com/register?{params}"


def deploy_to_render_url(repo_url: str = GITHUB_REPO_URL) -> str:
    return f"https://render.com/deploy?repo={repo_url}"
