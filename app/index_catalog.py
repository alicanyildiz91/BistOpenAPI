"""Official Borsa Istanbul benchmark index catalogue.

Constituent membership must be sourced from verified official Borsa Istanbul data.
Do not infer or fabricate members from index names.
"""
INDEX_NAMES = {
    "XU030": "BIST 30",
    "XU050": "BIST 50",
    "XU100": "BIST 100",
    "XU500": "BIST 500",
}


def get_index_catalog():
    return [
        {
            "code": code,
            "name": name,
            "constituentCount": None,
            "asOfDay": None,
            "constituents": [],
            "source": "borsaistanbul.com",
            "data_mode": "official_catalog_only",
            "membership_available": False,
        }
        for code, name in INDEX_NAMES.items()
    ]
