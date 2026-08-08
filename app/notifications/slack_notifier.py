"""Slack notification handler."""

import logging
import requests

logger = logging.getLogger(__name__)

def send_slack_notification(webhook_url: str, analysis_result: dict) -> bool:
    """Sends a formatted notification to Slack."""
    if not webhook_url:
        logger.warning("Slack webhook URL not configured. Skipping notification.")
        return False
        
    try:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 CI/CD Build Failure Detected",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{analysis_result.get('summary', 'Unknown error')}\n\n*Confidence:* {analysis_result.get('confidence', 0.0) * 100:.1f}%"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Suggested Fix:*\n```{analysis_result.get('suggested_fix', 'No fix suggested.')}```"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Dashboard",
                            "emoji": True
                        },
                        "url": "http://localhost:8000/dashboard/index.html"
                    }
                ]
            }
        ]
        
        response = requests.post(webhook_url, json={"blocks": blocks})
        response.raise_for_status()
        logger.info("Successfully sent Slack notification.")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {e}", exc_info=True)
        return False
