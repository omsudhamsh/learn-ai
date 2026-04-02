from flask import Blueprint, request, jsonify
from app.utils.decorators import login_required_api
from app.utils.ai_helpers import generate_mindmap_from_transcript

youtube_bp = Blueprint("youtube", __name__)


def get_transcript(video_id: str) -> str:
    """Fetch YouTube transcript using free youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript_list])
    except Exception as e:
        print(f"[YouTube] Transcript error: {e}")
        return ""


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    import re
    patterns = [
        r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


@youtube_bp.route("/mindmap", methods=["POST"])
@login_required_api
def create_mindmap():
    data = request.get_json()
    if not data or not data.get("url"):
        return jsonify({"error": "YouTube URL required"}), 400

    url = data["url"]
    video_id = extract_video_id(url)

    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    transcript = get_transcript(video_id)
    if not transcript:
        return jsonify({"error": "Could not fetch transcript. The video may not have captions."}), 400

    mermaid_code = generate_mindmap_from_transcript(transcript)

    # Clean up mermaid code
    if "```" in mermaid_code:
        lines = mermaid_code.split("\n")
        cleaned = []
        in_code = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or not any(line.strip().startswith(p) for p in ["```"]):
                cleaned.append(line)
        mermaid_code = "\n".join(cleaned)

    return jsonify({
        "mermaid_code": mermaid_code.strip(),
        "video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "transcript_length": len(transcript),
    })
