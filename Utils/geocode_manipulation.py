import re


def set_geocode_format(geocode):
    pattern = '^FR[0-9]{5}$'
    if re.match(pattern, geocode):
        return geocode
    else:
        if len(geocode) < 5:
            while len(geocode) < 5:
                geocode = '0' + geocode
        ret = 'FR' + geocode
        return ret


def set_counties_format(geocode):
    pattern = '^FR[0-9]{5}$'
    if re.match(pattern, geocode):
        return geocode
    else:
        if geocode == '99':
            ret = 'FR999' + geocode
        else:
            if len(geocode) < 2:
                while len(geocode) < 2:
                    geocode = '0' + geocode
            ret = 'FR992' + geocode
        return ret
