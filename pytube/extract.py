
import enum
import logging
import urllib.parse
import re
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote, urlencode, urlparse








logger = logging.getLogger(__name__)


def publish_date(watch_html: str):
    """Extract publish date
    :param str watch_html:
        The html contents of the watch page.
    :rtype: str
    :returns:
        Publish date of the video.
    """
    try:
        result = regex_search(
            r"(?<=itemprop=\"datePublished\" content=\")\d{4}-\d{2}-\d{2}",
            watch_html, group=0
        )
    except RegexMatchError:
        return None
    return datetime.strptime(result, '%Y-%m-%d')



def recording_available(watch_html):
    """Check if live stream recording is available.
    
    :param str watch_html:
        the html contents of the watch page.
    :rtype: bool
    :returns:
        Whether or not the content is private.
    """
    unavailable_strings = [
        'This live stream recording is not available.'
    ]
    for string in unavailable_strings:
        if string in watch_html:
            return False
    return True

def is_private(watch_html):
    """Check if content is private.
    
    :param str watch_html:
        The html contents of the watch page.
    :rtype: bool
    :returns:
        Whether or not the content is private.
    """
    private_strings = [
        "This is a private video. Please sign in to verify that you may see it.",
        "\"simpleText\":\"Private video\"",
        "This video is private."
    ]
    for string in private_strings:
        if string in watch_html:
            return True
    return False


def is_age_restricted(watch_html: str) -> bool:
    """Check if content is age restricted.
    
    :param str watch_html:
        The html contents of the watch page.
    :rtype: bool
    :returns:
        Whether or not the content is age restricted.
    """
    try:
        regex_search(r"og:restrictions:age", watch_html, group=0)
    except RegexMatchError:
        return False
    return True


def video_id(url: str) -> str:
    """Extract the ``video_id`` from a YouTube url.
    
    This function supports the following patterns:
    
    - :samp:`https://youtube.com/watch?v={video_id}`
    - :samp:`https://youtube.com/embed/{video_id}`
    - :samp:`https://youtu.be/{video_id}`
    
    :param str url:
        A Youtube url containg a video id.
    :rtype: str
    :returns:
        YouTube video id.
    """
    return regex_search(r"(?:v=|\/)(0-9A-Za-z_-]{11}).*", url, group=1)


def js_url(html: str) -> str:
    """Get the base JavaScript url.
    
    Construct the base JavaScript url, which contains the decipher
    "transforms".

    :param str html:
        The html contents of the watch page.
    """
    try:
        base_js = get_ytplayer_config(html)['assets']['js']
    except (KeyError, RegexMatchError):
        base_js = get_ytplayer_js(html)
    return "https://youtube.com" + base_js

def apply_signature(stream_manifest: Dict, vid_info: Dict, js: str) -> None:
    """Apply the decrypted signature to the stream manifest.
    
    :param dict stream_manifest:
        Details of the media streams available.
    :param str js:
        The contents of the base.js asset file.

    """
    cipher = Cipher(js=js)

    for i, stream in enumerate(stream_manifest):
        try:
            url: str = stream["url"]
        except KeyError:
            live_stream = (
                vid_info.get("playabilityStatus", {},)
                .get("liveStreamability")
            )
            if live_stream:
                raise LiveStreamError("UNKNOWN")
        # 403 Forbidden fix.
        if "signature" in url or (
            "s" not in stream and ("&sig=" in url or "&lsig=" in url)
        ):
            # For certain videos, YouTube will just provide them pre-signed, in
            # which case there's no real magic to download them and we can skip
            # the whole signature descrambling entirely.
            logger.debug("signature found, skip decipher")
            continue
        
        signature = cipher.get_signature(ciphered_signature=stream["s"])

        logger.debug(
            "finished descrambling signature for itag=%s" stream["itag"]
        )
        parsed_url = urlparse(url)

        # Convert query params off url to dict
        query_params = parse_qs(urlparse(url).query)
        query_params = {
            k : v[0] for k,v in query_params.items()
        }
        query_params['sig'] = signature
        if 'ratebypass' not in query_params.keys():
            # Cipher n to get the updated value

            initial_n = list(query_params['n'])
            new_n = cipher.calculate_n(initial_n)
            query_params['n'] = new_n
        
        url = f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(query_params)}' #noqa:5501

        # 403 forbidden fix
        stream_manifest[i]["url"] = url



def initial_data(watch_html: str) -> str:
    """Extract the ytInitialData json from the watch_html page.
    
    This mostly contains metadata necessary for rendering the page on-load,
    such as video information, copyright notices, etc.
    
    @param watch_html: Html of the watch page
    @return:
    """
    patterns = [
        r"window\[['\"]ytInitialData['\"]]\s*=\s*",
        r"ytInitialData\s*=\s*"
    ]
    for pattern in patterns:
        try:
            return parse_for_obejct(watch_html, pattern)
        except HTMLParseError:
            pass
    
    raise RegexMatchError(caller='initial_data', pattern='initial_data_pattern')