from bpi._core.params import integer


def region_banner_query(region_id: int) -> dict[str, str]:
    return {"region_id": integer(region_id, "region_id")}


def header_page_query(resource_id: int) -> dict[str, str]:
    return {"resource_id": integer(resource_id, "resource_id")}
