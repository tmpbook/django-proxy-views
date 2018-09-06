import requests
from django.http import HttpResponse
from django.http import QueryDict
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def proxy_view(request, url, requests_args=None):
    """
    尽可能向指定 url 转发相似的请求
    如果希望向请求发送任何参数，放到 requests_args 即可
    """
    requests_args = (requests_args or {}).copy()
    headers = get_headers(request.META)
    params = request.GET.copy()

    if 'headers' not in requests_args:
        requests_args['headers'] = {}
    if 'data' not in requests_args:
        requests_args['data'] = request.body
    if 'params' not in requests_args:
        # 只有对象是可变的时候才能使用 QueryDict 的 set
        # 例如通过 .copy() 方法创建的 requests_args 对象
        requests_args['params'] = QueryDict('', mutable=True)

    # 使用请求参数显示指定的值覆盖传入请求中的任何头信息和参数
    headers.update(requests_args['headers'])
    params.update(requests_args['params'])

    # 如果有来自 Django 的 content-length 头，它可能是大写的，requests 模块可能不会注意到
    # 它，所以需要删除它。
    for key in list(headers.keys()):
        if key.lower() in ['content-length', 'content-type']:
            del headers[key]

    requests_args['headers'] = headers
    requests_args['params'] = params
    response = requests.request(
        request.method, url, **requests_args, verify=False)

    proxy_response = HttpResponse(
        response.content,
        status=response.status_code)

    excluded_headers = set([
        # Hop-by-hop headers
        # ------------------
        # Certain response headers should NOT be just tunneled through.  These
        # are they.  For more info, see:
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html#sec13.5.1
        'connection', 'keep-alive', 'proxy-authenticate',
        'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
        'upgrade',

        # Although content-encoding is not listed among the hop-by-hop headers,
        # it can cause trouble as well.  Just let the server set the value as
        # it should be.
        'content-encoding',

        # Since the remote server may or may not have sent the content in the
        # same encoding as Django will, let Django worry about what the length
        # should be.
        'content-length'
    ])
    for key, value in response.headers.items():
        if key.lower() in excluded_headers:
            continue
        proxy_response[key] = value
    return proxy_response


def get_headers(environ):
    """
    Retrieve the HTTP headers from a WSGI environment dictionary.  See
    https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.META
    """
    headers = {}
    for key, value in environ.items():
        # Sometimes, things don't like when you send the requesting host through.
        if key.startswith('HTTP_') and key != 'HTTP_HOST':
            headers[key[5:].replace('_', '-')] = value
        elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            headers[key.replace('_', '-')] = value

    return headers
