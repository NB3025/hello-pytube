from urllib import parse


def test(url):
    """Fetch size in bytes of file at given URL from sequential requests
    
    :param str url: The URL to get the size of
    :returns: int: size in byes of remote file
    """
    total_filesize = 0
    # YouTube expects a request sequence number as part of the parameters.
    split_url = parse.urlsplit(url)
    print (f'{split_url=}')
    # split_url=SplitResult(scheme='https', netloc='www.youtube.com', path='/watch', query='v=603xu2QjYcs', fragment='')        

    base_url = '%s://%s/%s?' % (split_url.scheme, split_url.netloc, split_url.path)
    print (f'{base_url=}')
    # base_url='https://www.youtube.com//watch?'

    querys = dict(parse.parse_qsl(split_url.query))
    print (f'{querys=}')
    # querys={'v': '603xu2QjYcs'}
    
    # The 0th sequential request provides the file headers, which tell us
    #  information about how the file is segmented.
    querys['sq'] = 0
    url = base_url + parse.urlencode(querys)
    print (f'{url=}')
    #url='https://www.youtube.com//watch?v=603xu2QjYcs%2Fadsfdsg&sq=0' 끝에 sq가 붙네 
    
test('https://www.youtube.com/watch?v=603xu2QjYcs/adsfdsg')