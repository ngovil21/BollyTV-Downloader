__author__ = 'Nikhil'

import Common
from BollyTV.Util.Packer import Packer
import re


def get_download_link(url):
    site = Common.read_url(url)
    match = re.compile('(eval\(function.*?)\s*</script>').search(site)
    if match:
        javascript = match.group(1)
        unpacked = Packer().unpack(javascript).replace(" ", "")

        matches = re.findall('{file:"(.+?)",label:"(.+?)"}', unpacked)
        if matches:
            for match in matches:
                if match[1] == "HD":
                    return match[0]
            return match[0]

        match = re.search('sources:\[{file:"(.+?)"', unpacked)
        if match:
            return match.group(1)

    return None
