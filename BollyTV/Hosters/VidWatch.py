__author__ = 'Nikhil'

import BollyTV.Common
from BollyTV.Util import Packer
import re


def get_download_link(url):

    return None
    site = BollyTV.Common.read_url(url)
    match = re.compile('(eval\(function.*?)\s*</script>').search(site)
    if match:
        javascript = match.group(1)
        unpacked = Packer.Packer().unpack(javascript).replace(" ", "")

        matches = re.findall(',{file:"(.+?.mp4)",label:"(.+?)"}', unpacked)
        if matches:
            for match in matches:
                if match[1] == "720":
                    return match[0]
            return matches[0][0]


        match = re.search('{file:"(.+?\.mp4)"', unpacked)
        if match:
            return match.group(1)

    return None
