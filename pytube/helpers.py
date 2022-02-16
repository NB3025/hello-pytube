"""Various helper functions implemented by pytube."""
import functools
import gzip
import json
import logging
import os
import re
import warnings
from typing import Any, Callable, Dict, List, Optional, TypeVar
from urllib import request

from pytube.exceptions import RegexMatchError

logger = logging.getLogger(__name__)


class DeferredGeneratorList:
    """목록 생성을 deferring하기 위한 래퍼 클래스.

    Pytube에는 웹 호출을 생성하는 몇 가지 연속 generator가 있다.
    즉, 전체 목록이 요청될 때마다 이러한 모든 웹 호출이
    한 번에 이루어져야하므로 속도가 느려질 수 있다.

    이렇게 하면 개별 요소를 쿼리할 수 있으므로 필요한 경우에만 속도 저하가 발생.
    옐르 들어, 목록의 모든 요소에 동시에 엑세스하지 않고 반복할 수 있다.
    이를 통해 재생 목록 및 채널 상호 작용의 속도를 개선    
    """
    def __init__(self,generator):
        """Construct a :class:`DeferredGeneratorList <DeferredGeneratorList>`.
        
        :param generator generator:
            The deferrable generator to create a wrapper for.
        :param func func:
            (Optional) A function to call on the generator items to produce the list.
        """
        self.gen = generator
        self._elements = []
    
    def __eq__(self,other):
        """We want to mimic list behavior for comparison."""
        return list(self) == other

    def __getitem__(self,key) -> Any:
        """Only generate items as they're asked for."""
        # We only allow querying with indexes.
        if not isinstance(key, (int, slice)):
            raise TypeError('Key must be either a slice or int.')

        # Convert int keys to slice
        key_slice = key
        if isinstance(key, int):
            key_slice = slice(key, key + 1, 1)
        
        # Generate all elements up to the final item
        while len(self._elements) < key_slice.stop: # TODO slice객체에 stop?
            try:
                next_item = next(self.gen)
            except StopIteration:
                # If we can't find enough elements for the slice, raise an IndexError
                raise IndexError
            else:
                self._elements.append(next_item)
        
        return self._elements[key]

    def __iter__(self):
        """Custom iterator for dynamically generated list."""
        iter_index = 0
        while True:
            try:
                curr_item = self[iter_index]
            except IndexError:
                return
            else:
                yield curr_item
                iter_index +=1
        
    def __next__(self) -> Any:
        """Fetch next element in iterator."""
        try:
            curr_element = self[self.iter_index]
        except IndexError:
            raise StopIteration
        self.iter_index += 1
        return curr_element
    
    def __len__(self) -> int:
        """Return length of list of all items."""
        self.generate_all()
        return len(self._elements)

    def __repr__(self) -> str:
        """String representation of all items."""
        self.generate_all()
        return str(self._elements)
    
    def __reversed__(self):
        self.generate_all()
        return self._elements[::-1]

    def generate_all(self):
        """Generate all items."""
        while True:
            try:
                next_item = next(self.gen)
            except StopIteration:
                break
            else:
                self._elements.append(next_item)


def regex_search(pattern: str, string: str, group: int) -> str:
    """Shortcut method to search a string for a given pattern.
    
    :param str pattern:
        A regular expression pattern.
    :param str string:
        A target string to search.
    :param int group:
        Index of group to return.
    :rtype:
        str or tuple
    :returns:
        Substring pattern matches.
    """
    regex = re.compile(pattern)
    results = regex.search(string)
    if not results:
        raise RegexMatchError(caller="regex_search", pattern=pattern)
    
    logger.debug("matched regex search: %s", pattern)

    return results.group(group)


def safe_filename(s: str, max_length: int = 255) -> str:
    """Sanitize a string making it safe to use as a filename.

    This function was based off the limitations outlined here:
    https://en.wikipedia.org/wiki/Filename.

    :param str s:
        A string to make safe for use as a file name.
    :param int max_length:
        The maximum filename character length.
    :rtype: str
    :returns:
        A sanitized string.    
    """
    # Characters in range 0-31 (0x00-0x1F) are not allowed in ntfs filenames.
    ntfs_characters = [chr(i) for i in range(0,31)]
    characters = [
        r'"',
        r"\#",
        r"\$",
        r"\%",
        r"'",
        r"\*",
        r"\,",
        r"\.",
        r"\/",
        r"\:",
        r'"',
        r"\;",
        r"\<",
        r"\>",
        r"\?",
        r"\\",
        r"\^",
        r"\|",
        r"\~",
        r"\\\\",
    ]
    pattern = "|".join(ntfs_characters + characters)
    regex = re.compile(pattern, re.UNICODE)
    filename = regex.sub("", s)
    return filename[:max_length].rsplit(" ", 0)[0]


def setup_logger(level: int = logging.ERROR, log_filename: Optional[str] = None) -> None:
    """Create a configured instance of logger.
    
    :param int level:
        Describe the severity level of the logs to handle.
    """
    fmt = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    date_fmt = "%H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    # https://
    logger = logging.getLogger("pytube")
    logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_filename is not None:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


GenericType = TypeVar("GenericType")


def cache(func: Callable[..., GenericType]) -> GenericType:
    """ mypy compatible annotation wrapper for lru_cache"""
    return functools.lru_cache()(func) # type: ignore




























def target_directory(output_path: Optional[str] = None) -> str:
    """
    다운로드 대상 디렉토리 결정 기능
    절대 경로(상대 경로가 제공된 경우) 또는 현재 경로(제공되지 않은 경우)를 반환.
    존재하지 않는 경우 디렉토리 생성

    :type output_path: str
        :rtype: str
    :returns:
        An absolute directory path as a string.
    """
    if output_path:
        if not os.path.isabs(output_path):
            output_path = os.path.join(os.getcwsd(), output_path)
    else:
        output_path = os.getcwd()
    os.makedirs(output_path, exist_ok=True)
    return output_path