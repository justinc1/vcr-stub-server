from urllib.parse import urlparse, quote

from vcr_stub_server.cassettes.base_vcr_cassette import (
    BaseVcrCassette,
    ResponseNotFound,
    MultipleHostsInCassette,
)

from vcr.cassette import Cassette
import vcr as vcrpy

vcr = vcrpy.VCR()


class VcrpyCassette(BaseVcrCassette):
    def __init__(self, cassette_path: str):
        config = vcr.get_merged_config()
        config.pop("path_transformer")
        config.pop("func_path_generator")

        self.vcrpy_cassette = Cassette.load(path=cassette_path, **config)
        self._host = None
        self._ind = 0

        for request in self.vcrpy_cassette.requests:
            parsed_url = urlparse(request.uri)
            current_interaction_request_host = (
                f"{parsed_url.scheme}://{parsed_url.netloc}"
            )

            if current_interaction_request_host != self._host and self._host != None:
                raise MultipleHostsInCassette(
                    "More than one host found in cassette interactions"
                )

            if self._host == None:
                self._host = current_interaction_request_host

    def response_for(self, method: str, path: str, body: str, headers: list):
        headers = vcrpy.request.HeadersDict(headers)
        request = vcrpy.request.Request(method, f"{self._host}{path}", body, headers)

        try:
            if 0:
                # orig code
                encoded_response = self.vcrpy_cassette.responses_of(request)[0]
            else:
                # just replay in same order as recorded
                request = self.vcrpy_cassette.requests[self._ind]
                assert method == request.method
                parsed_url = urlparse(request.uri)
                assert path == parsed_url.path
                assert body == request.body
                # assert headers == request.headers  # order, and port
                encoded_response = self.vcrpy_cassette.responses[self._ind]
                # print(f"ind={self._ind}")
                self._ind += 1
        except vcrpy.errors.UnhandledHTTPRequestError as e:
            raise ResponseNotFound(str(e))

        return vcrpy.filters.decode_response(encoded_response)
