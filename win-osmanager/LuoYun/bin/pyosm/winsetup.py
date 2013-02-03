from distutils.core import setup
import py2exe

setup(
    options = {"py2exe": {"dll_excludes": ["MSVCP90.dll"]} },
    service = ["osmwinserv"],
    data_files = ["osm.ico",
                  "license.txt",
                  "osminstall.nsi",
                  "README.zh_CN.markdown"]
    )
