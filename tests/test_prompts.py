import pytest
from requests.exceptions import HTTPError
from vcr import VCR
from stuart.prompts import get_pypi_package
from stuart.typing import PypiPackage

vcr = VCR(
    cassette_library_dir="tests/fixtures/vcr_cassettes",
    record_mode="once",
    match_on=["uri", "method"],
    filter_headers=["user-agent", "accept-encoding"],
    ignore_localhost=True,
    serializer="yaml"
)

@pytest.mark.vcr()
def test_get_pypi_package_success():
    """Test successful PyPI package fetch with real API response"""
    result = get_pypi_package("requests")
    assert isinstance(result, PypiPackage)
    assert result.name == "requests"
    assert result.version
    assert result.description

@pytest.mark.vcr()
def test_get_pypi_package_not_found():
    """Test handling of non-existent package"""
    with pytest.raises(HTTPError) as exc_info:
        get_pypi_package("this-package-definitely-does-not-exist")
    assert "404" in str(exc_info.value)

@pytest.mark.vcr()
def test_get_pypi_package_server_error():
    """Test handling of PyPI server error"""
    with pytest.raises(HTTPError):
        # Force a server error by making an invalid request
        get_pypi_package("")
