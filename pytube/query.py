"""This module provides a qurey interface for media streams and captions."""
from collections.abc import Mapping, Sequence
from typing import Callable, List, Optional, Union

from pytube import Caption, Stream
from pytube.helpers import deprecated


class StreamQuery(Sequence):
    """Interface for querying the available media streams."""

    def __init__(self, fmt_streams):
        """Construct a :class:`StreamQuery <StreamQuery>`.
        
        parm list fmt_streams:
            list of :class:`Stream <Stream>` instances.
        """
        self.fmt_streams = fmt_streams
        self.itag_index = {int(s.itag): s for s in fmt_streams}

    def filter(
        self,
        fps=None,
        res=None,
        resolution=None,
        mime_type=None,
        type=None,
        subtype=None,
        file_extension=None,
        abr=None,
        bitrate=None,
        video_codec=None,
        audio_codec=None,
        only_audio=None,
        only_video=None,
        progressive=None,
        adaptive=None,
        is_dash=None,
        custom_filter_functions=None,
    ):
        """Apply the given filtering criterion.

        :param fps:
            (optional) The frames per second.
        :type fps:
            int or None

        :param resolution:
            (optional) Alias to ``res``.
        :type res:
            str or None

        :param res:
            (optional) The video resolution.
        :type resolution:
            str or None

        :param mime_type:
            (optional) Two-part identifier for file formats and format contents
            composed of a "type", a "subtype".
        :type mime_type:
            str or None

        :param type:
            (optional) Type part of the ``mime_type`` (e.g.: audio, video).
        :type type:
            str or None

        :param subtype:
            (optional) Sub-type part of the ``mime_type`` (e.g.: mp4, mov).
        :type subtype:
            str or None

        :param file_extension:
            (optional) Alias to ``sub_type``.
        :type file_extension:
            str or None

        :param abr:
            (optional) Average bitrate (ABR) refers to the average amount of
            data transferred per unit of time (e.g.: 64kbps, 192kbps).
        :type abr:
            str or None

        :param bitrate:
            (optional) Alias to ``abr``.
        :type bitrate:
            str or None

        :param video_codec:
            (optional) Video compression format.
        :type video_codec:
            str or None

        :param audio_codec:
            (optional) Audio compression format.
        :type audio_codec:
            str or None

        :param bool progressive:
            Excludes adaptive streams (one file contains both audio and video
            tracks).

        :param bool adaptive:
            Excludes progressive streams (audio and video are on separate
            tracks).

        :param bool is_dash:
            Include/exclude dash streams.

        :param bool only_audio:
            Excludes streams with video tracks.

        :param bool only_video:
            Excludes streams with audio tracks.

        :param custom_filter_functions:
            (optional) Interface for defining complex filters without
            subclassing.
        :type custom_filter_functions:
            list or None

        """
        filters = []
        if res or resolution:
            filters.append(lambda s: s.resolution == (res or resolution))

        if fps:
            filters.append(lambda s: s.fps == fps)

        if mime_type:
            filters.append(lambda s: s.mime_type == mime_type)

        if type:
            filters.append(lambda s: s.type == type)

        if subtype or file_extension:
            filters.append(lambda s: s.subtype == (subtype or file_extension))

        if abr or bitrate:
            filters.append(lambda s: s.abr == (abr or bitrate))

        if video_codec:
            filters.append(lambda s: s.video_codec == video_codec)

        if audio_codec:
            filters.append(lambda s: s.audio_codec == audio_codec)

        if only_audio:
            filters.append(
                lambda s: (
                    s.includes_audio_track and not s.includes_video_track
                ),
            )

        if only_video:
            filters.append(
                lambda s: (
                    s.includes_video_track and not s.includes_audio_track
                ),
            )

        if progressive:
            filters.append(lambda s: s.is_progressive)

        if adaptive:
            filters.append(lambda s: s.is_adaptive)

        if custom_filter_functions:
            filters.extend(custom_filter_functions)

        if is_dash is not None:
            filters.append(lambda s: s.is_dash == is_dash)

        return self._filter(filters)
