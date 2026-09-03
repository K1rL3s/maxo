from yarl import URL

from maxo.transport.webhook.route.errors import InvalidBaseUrlError


def prepare_base_url(base_url: str | URL) -> URL:
    url = base_url if isinstance(base_url, URL) else URL(base_url)

    if not url.is_absolute():
        raise InvalidBaseUrlError(
            base_url=url,
            reason="base_url must be an absolute URL",
        )
    if url.query_string:
        raise InvalidBaseUrlError(
            base_url=url,
            reason="base_url must not contain query params; move them to Route(query=...)",  # noqa: E501
        )
    if url.fragment:
        raise InvalidBaseUrlError(
            base_url=url,
            reason="URL fragment is not supported for route",
        )

    return url
