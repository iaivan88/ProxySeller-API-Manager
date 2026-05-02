import requests
import json
import logging
from typing import List, Dict, Optional
from models import APIResponse, ExportFormat

logger = logging.getLogger(__name__)

class ProxySellerClient:
    API_VERSION = "v1"
    BASE_DOMAIN = "https://proxy-seller.com/personal/api"

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = f'{self.BASE_DOMAIN}/{self.API_VERSION}/{self.api_key}/resident'
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        })
        return session

    def _make_request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """HTTP request to resident API relative to base_url (e.g. lists, list/add)."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            # Raise exception for non-2xx statuses (except 400s which might hold API errors)
            if response.status_code >= 500:
                response.raise_for_status()

            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "success":
                        return APIResponse(success=True, data=data.get("data"))
                    errors = data.get("errors", "Unknown error")
                    return APIResponse(success=False, error=str(errors))
                except json.JSONDecodeError:
                    return APIResponse(success=True, data=response.text) # some endpoints might return raw text
            
            return APIResponse(
                success=False,
                error=f"HTTP {response.status_code}: {response.text}",
            )
        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return APIResponse(success=False, error=f"Request failed: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error during API request")
            return APIResponse(success=False, error=f"Unexpected error: {str(e)}")

    def get_lists(self) -> List[Dict]:
        """Get all existing IP lists"""
        response = self._make_request("GET", "lists")
        if not response.success:
            logger.warning(f"Failed to get lists: {response.error}")
            return []

        data = response.data
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "items" in data:
            return data["items"]

        logger.warning("Unexpected data structure in response.")
        return []

    def download_proxies_from_list(self, list_id: str, export_format: ExportFormat) -> Optional[requests.Response]:
        """Returns the raw requests.Response for the download endpoint"""
        url = f'{self.BASE_DOMAIN}/{self.API_VERSION}/{self.api_key}/proxy/download/resident'
        params = {
            'format': export_format.value,
            'listId': list_id
        }
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            return response
        except requests.RequestException as e:
            logger.error(f"Download failed for list {list_id}: {str(e)}")
            return None

    def create_list(self, title: str, geo_country: str, geo_region: str, geo_city: str, geo_isp: str, 
                    whitelist: str, num_ports: int) -> APIResponse:
        data = {
            'title': title,
            'whitelist': whitelist,
            'geo': {
                'country': geo_country,
                'region': geo_region,
                'city': geo_city,
                'isp': geo_isp
            },
            'ports': num_ports,
            'export': {
                'ports': 10000,
                'ext': 'txt'
            }
        }
        return self._make_request("POST", "list/add", json=data)

    def rename_list(self, list_id: str, new_title: str) -> APIResponse:
        data = {
            "id": list_id,
            "title": new_title,
        }
        return self._make_request("POST", "list/rename", json=data)

    def delete_list(self, list_id: str) -> APIResponse:
        data = {"id": list_id}
        return self._make_request("DELETE", "list/delete", json=data)

    def get_consumption(self, date_start: str, date_end: str, login: Optional[str] = None) -> APIResponse:
        """Get traffic consumption for a specific period"""
        data = {
            "date_start": date_start,
            "date_end": date_end
        }
        if login:
            data["login"] = login
        return self._make_request("POST", "consumption", json=data)
