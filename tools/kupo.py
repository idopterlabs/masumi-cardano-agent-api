#!/usr/bin/env python3

import requests
import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type

class KupoToolInput(BaseModel):
    address: str = Field(..., description="The Cardano address to query")

class KupoTool(BaseTool):
    name: str = "KupoTool"
    description: str = "Fetches and calculates total ADA amount stored in a given Cardano address"
    args_schema: Type[BaseModel] = KupoToolInput
    base_url: str = "The base URL of the Kupo API"

    def __init__(self, base_url: Optional[str] = None, **kwargs):     
        super().__init__(**kwargs)
        if not base_url:
            raise ValueError("base_url is required")

        self.base_url = base_url

    def _run(self, cardano_address: str) -> str:
        try:
            url = f"{self.base_url}/matches/{cardano_address}"
            
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            total_coins = 0
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'value' in item:
                        value = item['value']
                        if isinstance(value, dict) and 'coins' in value:
                            total_coins += value['coins']
            
            return total_coins
                
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None


# Example usage
if __name__ == "__main__":
    tool = KupoTool(base_url="http://192.168.1.12:1442")
    result = tool._run("addr_test1wp867cwenl586mcuft35d7qy56ucyjqg5pqy00vyd7c75hcq7cn8u")
    print(result)
