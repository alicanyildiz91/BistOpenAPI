def get_provider():
    # Demo-only catalogue. This is not a complete or official BIST universe.
    stocks = [
        {"symbol": "THYAO", "name": "Türk Hava Yolları", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
        {"symbol": "ASELS", "name": "Aselsan", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
        {"symbol": "BIMAS", "name": "BİM Birleşik Mağazalar", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
        {"symbol": "TUPRS", "name": "Tüpraş", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
        {"symbol": "AKBNK", "name": "Akbank", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
        {"symbol": "GARAN", "name": "Garanti BBVA", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
        {"symbol": "ISCTR", "name": "Türkiye İş Bankası C", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
        {"symbol": "EREGL", "name": "Ereğli Demir ve Çelik", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
        {"symbol": "KCHOL", "name": "Koç Holding", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
        {"symbol": "SISE", "name": "Şişecam", "exchange": "BIST", "currency": "TRY", "source": "demo", "data_mode": "demo"},
    ]
    indexes = [
        {"code": "XU030", "name": "BIST 30", "constituents": [], "source": "demo", "data_mode": "demo", "note": "Not an authoritative index component list."},
        {"code": "XU050", "name": "BIST 50", "constituents": [], "source": "demo", "data_mode": "demo", "note": "Not an authoritative index component list."},
        {"code": "XU100", "name": "BIST 100", "constituents": [], "source": "demo", "data_mode": "demo", "note": "Not an authoritative index component list."},
    ]
    return {
        "name": "demo",
        "mode": "demo",
        "live_data_available": False,
        "stocks": stocks,
        "indexes": indexes,
        "notes": [
            "This is an API scaffold, not a live BIST feed.",
            "Sample stock list is not complete or authoritative.",
            "No fake quotes or candles are returned.",
            "Review data-provider terms and redistribution rights before serving real market data.",
        ],
    }
