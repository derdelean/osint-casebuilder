import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from phonenumbers import PhoneNumberType, PhoneNumberFormat

print("✅ Modul `phone_lookup` (libphonenumber, offline) aktiv")

_TYPE_NAMES = {
    PhoneNumberType.FIXED_LINE: "fixed_line",
    PhoneNumberType.MOBILE: "mobile",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
    PhoneNumberType.TOLL_FREE: "toll_free",
    PhoneNumberType.PREMIUM_RATE: "premium_rate",
    PhoneNumberType.SHARED_COST: "shared_cost",
    PhoneNumberType.VOIP: "voip",
    PhoneNumberType.PERSONAL_NUMBER: "personal_number",
    PhoneNumberType.PAGER: "pager",
    PhoneNumberType.UAN: "uan",
    PhoneNumberType.VOICEMAIL: "voicemail",
    PhoneNumberType.UNKNOWN: "unknown",
}


def _describe(num) -> dict:
    """Build the metadata dict for a parsed phonenumbers object."""
    e164 = phonenumbers.format_number(num, PhoneNumberFormat.E164)
    return {
        "valid": phonenumbers.is_valid_number(num),
        "possible": phonenumbers.is_possible_number(num),
        "country_code": num.country_code,
        "national_number": num.national_number,
        "carrier": carrier.name_for_number(num, "en") or None,
        "region": geocoder.description_for_number(num, "en") or None,
        "line_type": _TYPE_NAMES.get(phonenumbers.number_type(num), "unknown"),
        "timezones": list(timezone.time_zones_for_number(num)),
        "e164": e164,
        "international": phonenumbers.format_number(num, PhoneNumberFormat.INTERNATIONAL),
    }


def run_phone_lookup(phone: str, region: str = None) -> list:
    """Offline phone intelligence via libphonenumber: validity, carrier, region,
    line type and timezones. `region` (e.g. 'CH', 'US') is required for national-
    format numbers; numbers in +CC international format need no region."""
    try:
        num = phonenumbers.parse(phone, region)
    except phonenumbers.NumberParseException as e:
        print(f"⚠️  Telefonnummer nicht parsebar: {phone} ({e}). "
              f"Internationales Format (+41…) oder --phone-region angeben.")
        return []

    meta = _describe(num)
    print(f"✅ Phone: {meta['e164']} | {meta['line_type']} | "
          f"{meta['carrier'] or '–'} | {meta['region'] or '–'}")

    return [{
        "type": "phone",
        "value": meta["e164"],
        "source": f"tel:{meta['e164']}",
        "platform": "Phone/libphonenumber",
        "meta": meta,
    }]
