from collections import defaultdict
from parsel import Selector
from urllib.parse import urlencode
from httpx import AsyncClient
import asyncio
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Connection": "keep-alive",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US,en;q=0.8",
}


def parse_hotel(html: str):
    sel = Selector(text=html)
    css = lambda selector, sep="": sep.join(sel.css(selector).getall()).strip()
    css_first = lambda selector: sel.css(selector).get("")
    # get hotel features by type
    features = defaultdict(list)
    for feat_box in sel.css("[data-capla-component*=FacilitiesBlock]>div>div>div"):
        type_ = feat_box.xpath('.//span[contains(@data-testid, "facility-group-icon")]/../text()').get()
        feats = [f.strip() for f in feat_box.css("li ::text").getall() if f.strip()]
        features[type_] = feats
    data = {
        "title": css("h2#hp_hotel_name::text"),
        "description": css("div#property_description_content ::text", "\n"),
        "address": css(".hp_address_subtitle::text"),
        "features": dict(features),
        "id": re.findall(r"b_hotel_id:\s*'(.+?)'", html)[0],
    }
    return data


async def scrape_hotels(urls: list[str], session: AsyncClient):
    async def scrape_hotel(url: str):
        resp = await session.get(url)
        hotel = parse_hotel(resp.text)
        hotel["url"] = str(resp.url)
        return hotel

    hotels = await asyncio.gather(*[scrape_hotel(url) for url in urls])
    return hotels

    

async def run():
    async with AsyncClient(headers=HEADERS) as session:
        hotels = await scrape_hotels(["https://www.booking.com/hotel/gb/gardencourthotel.html"], session)
        print(json.dumps(hotels, indent=2))

if __name__ == "__main__":
    asyncio.run(run())