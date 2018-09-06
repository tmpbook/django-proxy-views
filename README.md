# django-proxy-views

## use [proxy_view](./views.py) like below

```python
def demo_view(request):

    requests_args = {}

    header = {
        "Content-Type": "application/json",
    }

    auth_params = {
        "token": token
    }

    requests_args['headers'] = header
    requests_args['params'] = auth_params

    return proxy_view(request, "https://api.qingcdn.com/v2/cache/refresh",
                      requests_args=requests_args)
```
