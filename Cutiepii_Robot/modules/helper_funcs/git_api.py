import urllib.request as url
import json

VERSION = "1.1.0"
APIURL = "http://api.github.com/repos/"


def vercheck() -> str:
    return str(VERSION)


# Repo-wise stuff


def getData(repoURL):
    try:
        with url.urlopen(APIURL + repoURL + "/releases") as data_raw:
            return json.loads(data_raw.read().decode())
    except:
        return None


def getReleaseData(repoData, index):
    return repoData[index] if index < len(repoData) else None


# Release-wise stuff


def getAuthor(releaseData):
    return None if releaseData is None else releaseData["author"]["login"]


def getAuthorUrl(releaseData):
    return None if releaseData is None else releaseData["author"]["html_url"]


def getReleaseName(releaseData):
    return None if releaseData is None else releaseData["name"]


def getReleaseTag(releaseData):
    return None if releaseData is None else releaseData["tag_name"]


def getReleaseDate(releaseData):
    return None if releaseData is None else releaseData["published_at"]


def getAssetsSize(releaseData):
    return None if releaseData is None else len(releaseData["assets"])


def getAssets(releaseData):
    return None if releaseData is None else releaseData["assets"]


def getBody(releaseData):  # changelog stuff
    return None if releaseData is None else releaseData["body"]


# Asset-wise stuff


def getReleaseFileName(asset):
    return asset["name"]


def getReleaseFileURL(asset):
    return asset["browser_download_url"]


def getDownloadCount(asset):
    return asset["download_count"]


def getSize(asset):
    return asset["size"]
