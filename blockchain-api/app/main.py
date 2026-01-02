from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import httpx
from typing import Optional
import os

app = FastAPI(title="Blockchain Source Code Downloader API")

S3_BUCKET = "bitcoinpay-visa-archive-1767099061"
S3_REGION = "us-east-1"
S3_BASE_URL = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com"

S3_RELEASES = {
    "bitcoin": {
        "v28.3", "v29.2", "v30.0", "v29.1", "v28.2", "v29.0", "v28.1", "v27.2", "v28.0",
        "v26.2", "v27.1", "v27.0", "v25.2", "v26.1", "v26.0", "v24.2", "v25.1", "v25.0",
        "v24.1", "v23.2", "v23.1", "v24.0.1", "v22.1", "v23.0", "v22.0", "v0.21.1",
        "v0.21.0", "v0.20.1", "v0.20.0", "v0.19.1", "v0.19.0.1", "v0.18.1", "v0.18.0",
        "v0.17.1", "v0.17.0.1", "v0.17.0", "v0.14.3", "v0.15.2", "v0.16.3", "v0.16.2",
        "v0.16.1", "v0.16.0", "v0.15.1", "v0.15.0.1", "v0.15.0", "v0.14.2", "v0.14.1",
        "v0.14.0", "v0.13.2", "v0.13.1", "v0.13.0", "v0.12.1", "v0.12.0", "v0.11.2",
        "v0.10.4", "v0.11.1", "v0.10.3", "v0.10.2", "v0.10.1", "v0.10.0",
        "v0.9.5", "v0.9.4", "v0.9.3", "v0.9.2.1", "v0.9.2", "v0.9.1", "v0.9.0",
        "v0.8.6", "v0.8.5", "v0.8.4", "v0.8.3", "v0.8.2", "v0.8.1", "v0.8.0",
        "v0.7.2", "v0.7.1", "v0.7.0",
        "v0.6.3", "v0.6.2.2", "v0.6.2.1", "v0.6.2", "v0.6.1", "v0.6.0",
        "v0.5.3", "v0.5.2", "v0.5.1", "v0.5.0",
        "v0.4.0",
        "v0.3.21", "v0.3.20", "v0.3.19", "v0.3.18", "v0.3.17", "v0.3.15", "v0.3.14",
        "v0.3.13", "v0.3.12", "v0.3.10", "v0.3.8", "v0.3.7", "v0.3.6", "v0.3.3",
        "v0.3.2", "v0.3.1", "v0.3.0",
        "v0.2.13", "v0.2.12", "v0.2.11", "v0.2.10", "v0.2.9", "v0.2.8", "v0.2.7",
        "v0.2.6", "v0.2.5", "v0.2.4", "v0.2.2", "v0.2.0",
        "v0.1.6test1", "v0.1.5", "v0.1.3", "v0.1.0",
        "bitcoin-pre-release-nov08"
    },
    "bitcoin-sv": {
        "v1.1.1", "v1.1.0", "v1.0.16", "v1.0.15.1", "v1.0.15", "v1.0.14", "v1.0.13",
        "v1.0.11", "v1.0.10", "v1.0.9", "v1.0.8", "v1.0.7.1", "v1.0.7", "v1.0.6",
        "v1.0.5", "v1.0.4", "v1.0.3", "v1.0.2", "v1.0.1", "v1.0.0", "v0.2.1", "v0.2.0",
        "v0.1.1", "v0.1.0"
    },
    "bitcoin-cash": {
        "v28.0.1", "v28.0.0", "v27.1.0", "v27.0.0", "v26.1.0", "v26.0.0", "v25.0.0",
        "v24.1.0", "v24.0.0", "v23.1.0", "v23.0.0", "v22.2.0", "v22.1.0", "v22.0.0",
        "v0.21.2", "v0.21.1", "v0.21.0"
    },
    "bitcoin-private": {
        "1.0.15", "1.0.14", "1.0.13", "1.0.12-1-b27c722", "1.0.12-1", "1.0.12-69aa9ce",
        "1.0.12-8e6c23c", "v1.0.11-d3905b0", "1.0.11-5d06772", "1.0.10-2", "1.0.10-9ee1d690"
    },
    "litecoin": {
        "v0.21.4", "v0.21.3", "v0.21.2.2", "v0.21.2.1", "v0.21.2", "v0.18.1", "v0.17.1",
        "v0.16.3", "v0.15.1", "v0.14.2", "v0.13.3", "v0.13.2.1", "v0.10.4.0"
    }
}

SPECIAL_FILE_EXTENSIONS = {
    "bitcoin": {
        "bitcoin-pre-release-nov08": "tgz",
        "v0.1.0": "tgz",
        "v0.1.3": "rar",
    }
}

# Correct release dates from bitcoin.org (GitHub dates are wrong for releases migrated on 2016-11-01)
BITCOIN_RELEASE_DATES = {
    # 2009
    "bitcoin-pre-release-nov08": "2008-11-15T00:00:00Z",
    "v0.1.0": "2009-01-08T00:00:00Z",
    "v0.1.3": "2009-01-13T00:00:00Z",
    "v0.1.5": "2009-02-04T00:00:00Z",
    # 2010
    "v0.2.0": "2009-12-16T00:00:00Z",
    "v0.3.0": "2010-07-06T00:00:00Z",
    "v0.3.21": "2010-09-23T00:00:00Z",
    # 2011
    "v0.3.24": "2011-07-08T00:00:00Z",
    "v0.4.0": "2011-09-23T00:00:00Z",
    "v0.5.0": "2011-11-21T00:00:00Z",
    "v0.5.1": "2011-12-15T00:00:00Z",
    # 2012
    "v0.5.2": "2012-01-09T00:00:00Z",
    "v0.5.3": "2012-03-14T00:00:00Z",
    "v0.6.0": "2012-03-30T00:00:00Z",
    "v0.6.1": "2012-05-04T00:00:00Z",
    "v0.6.2": "2012-05-08T00:00:00Z",
    "v0.6.3": "2012-06-25T00:00:00Z",
    "v0.7.0": "2012-09-17T00:00:00Z",
    "v0.7.1": "2012-10-19T00:00:00Z",
    "v0.7.2": "2012-12-14T00:00:00Z",
    # 2013
    "v0.8.0": "2013-02-19T00:00:00Z",
    "v0.8.1": "2013-03-18T00:00:00Z",
    "v0.8.2": "2013-05-29T00:00:00Z",
    "v0.8.3": "2013-06-25T00:00:00Z",
    "v0.8.4": "2013-09-03T00:00:00Z",
    "v0.8.5": "2013-09-13T00:00:00Z",
    "v0.8.6": "2013-12-09T00:00:00Z",
    # 2014
    "v0.9.0": "2014-03-19T00:00:00Z",
    "v0.9.1": "2014-04-08T00:00:00Z",
    "v0.9.2": "2014-06-16T00:00:00Z",
    "v0.9.2.1": "2014-06-19T00:00:00Z",
    "v0.9.3": "2014-09-27T00:00:00Z",
    # 2015
    "v0.10.0": "2015-02-16T00:00:00Z",
    "v0.10.1": "2015-04-27T00:00:00Z",
    "v0.10.2": "2015-05-19T00:00:00Z",
    "v0.10.3": "2015-10-14T00:00:00Z",
    "v0.10.4": "2015-10-15T00:00:00Z",
    "v0.11.0": "2015-07-12T00:00:00Z",
    "v0.11.1": "2015-10-15T00:00:00Z",
    "v0.11.2": "2015-11-13T00:00:00Z",
    # 2016
    "v0.12.0": "2016-02-23T00:00:00Z",
    "v0.12.1": "2016-04-15T00:00:00Z",
    "v0.13.0": "2016-08-23T00:00:00Z",
    "v0.13.1": "2016-10-27T00:00:00Z",
    # 2017 and later - GitHub dates are correct
}

def get_s3_url(blockchain_id: str, tag_name: str) -> str:
    safe_tag = tag_name.replace("/", "_")
    ext = "zip"
    if blockchain_id in SPECIAL_FILE_EXTENSIONS:
        ext = SPECIAL_FILE_EXTENSIONS[blockchain_id].get(tag_name, "zip")
    return f"{S3_BASE_URL}/blockchain-zips/{blockchain_id}/{safe_tag}.{ext}"

def is_release_in_s3(blockchain_id: str, tag_name: str) -> bool:
    if blockchain_id not in S3_RELEASES:
        return False
    return tag_name in S3_RELEASES[blockchain_id]

def get_correct_release_date(blockchain_id: str, tag_name: str, github_date: str) -> str:
    """Get the correct release date, using our mapping for Bitcoin releases with wrong GitHub dates."""
    if blockchain_id == "bitcoin" and tag_name in BITCOIN_RELEASE_DATES:
        return BITCOIN_RELEASE_DATES[tag_name]
    return github_date

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

BLOCKCHAIN_REPOS = {
    "bitcoin": {
        "owner": "bitcoin",
        "repo": "bitcoin",
        "name": "Bitcoin",
        "description": "Bitcoin Core - The original cryptocurrency"
    },
    "bitcoin-sv": {
        "owner": "bitcoin-sv",
        "repo": "bitcoin-sv",
        "name": "Bitcoin SV",
        "description": "Bitcoin SV (Satoshi Vision) - Restores the original Bitcoin protocol"
    },
    "bitcoin-cash": {
        "owner": "bitcoin-cash-node",
        "repo": "bitcoin-cash-node",
        "name": "Bitcoin Cash",
        "description": "Bitcoin Cash Node - Peer-to-peer electronic cash"
    },
    "bitcoin-private": {
        "owner": "BTCPrivate",
        "repo": "BitcoinPrivate-legacy",
        "name": "Bitcoin Private",
        "description": "Bitcoin Private - Privacy-focused Bitcoin fork using zk-SNARKs"
    },
    "litecoin": {
        "owner": "litecoin-project",
        "repo": "litecoin",
        "name": "Litecoin",
        "description": "Litecoin - The silver to Bitcoin's gold"
    }
}

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

async def get_github_headers():
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Blockchain-Source-Downloader"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/api/blockchains")
async def get_blockchains():
    return {
        "blockchains": [
            {
                "id": key,
                "name": value["name"],
                "description": value["description"],
                "github_url": f"https://github.com/{value['owner']}/{value['repo']}"
            }
            for key, value in BLOCKCHAIN_REPOS.items()
        ]
    }

@app.get("/api/blockchains/{blockchain_id}/releases")
async def get_releases(blockchain_id: str, page: int = 1, per_page: int = 30):
    if blockchain_id not in BLOCKCHAIN_REPOS:
        raise HTTPException(status_code=404, detail=f"Blockchain '{blockchain_id}' not found")
    
    repo_info = BLOCKCHAIN_REPOS[blockchain_id]
    owner = repo_info["owner"]
    repo = repo_info["repo"]
    
    async with httpx.AsyncClient() as client:
        headers = await get_github_headers()
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases",
            headers=headers,
            params={"page": page, "per_page": per_page}
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Repository not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="GitHub API error")
        
        releases = response.json()
        
        return {
            "blockchain": {
                "id": blockchain_id,
                "name": repo_info["name"],
                "description": repo_info["description"]
            },
            "releases": [
                {
                    "id": release["id"],
                    "tag_name": release["tag_name"],
                    "name": release["name"] or release["tag_name"],
                    "published_at": get_correct_release_date(blockchain_id, release["tag_name"], release["published_at"]),
                    "zipball_url": release["zipball_url"],
                    "tarball_url": release["tarball_url"],
                    "html_url": release["html_url"],
                    "prerelease": release["prerelease"],
                    "draft": release["draft"]
                }
                for release in releases
            ],
            "page": page,
            "per_page": per_page
        }

@app.get("/api/blockchains/{blockchain_id}/tags")
async def get_tags(blockchain_id: str, page: int = 1, per_page: int = 100):
    if blockchain_id not in BLOCKCHAIN_REPOS:
        raise HTTPException(status_code=404, detail=f"Blockchain '{blockchain_id}' not found")
    
    repo_info = BLOCKCHAIN_REPOS[blockchain_id]
    owner = repo_info["owner"]
    repo = repo_info["repo"]
    
    async with httpx.AsyncClient() as client:
        headers = await get_github_headers()
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/tags",
            headers=headers,
            params={"page": page, "per_page": per_page}
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Repository not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="GitHub API error")
        
        tags = response.json()
        
        return {
            "blockchain": {
                "id": blockchain_id,
                "name": repo_info["name"],
                "description": repo_info["description"]
            },
            "tags": [
                {
                    "name": tag["name"],
                    "zipball_url": tag["zipball_url"],
                    "tarball_url": tag["tarball_url"],
                    "commit_sha": tag["commit"]["sha"]
                }
                for tag in tags
            ],
            "page": page,
            "per_page": per_page
        }

HISTORICAL_RELEASES = {
    "bitcoin": [
        {
            "tag_name": "bitcoin-pre-release-nov08",
            "name": "Bitcoin Pre-Release (November 2008)",
            "published_at": "2008-11-15T00:00:00Z",
            "description": "Pre-release version shared by Satoshi Nakamoto before the official launch",
            "source": "Satoshi Nakamoto Institute",
            "format": "tgz"
        },
        {
            "tag_name": "v0.1.0",
            "name": "Bitcoin v0.1.0",
            "published_at": "2009-01-08T00:00:00Z",
            "description": "First public release of Bitcoin",
            "source": "Satoshi Nakamoto Institute",
            "format": "tgz"
        },
        {
            "tag_name": "v0.1.3",
            "name": "Bitcoin v0.1.3",
            "published_at": "2009-01-13T00:00:00Z",
            "description": "Early Bitcoin release",
            "source": "Satoshi Nakamoto Institute",
            "format": "rar"
        },
    ]
}

@app.get("/api/blockchains/{blockchain_id}/historical")
async def get_historical_releases(blockchain_id: str):
    if blockchain_id not in BLOCKCHAIN_REPOS:
        raise HTTPException(status_code=404, detail=f"Blockchain '{blockchain_id}' not found")
    
    repo_info = BLOCKCHAIN_REPOS[blockchain_id]
    
    historical = HISTORICAL_RELEASES.get(blockchain_id, [])
    
    return {
        "blockchain": {
            "id": blockchain_id,
            "name": repo_info["name"],
            "description": repo_info["description"]
        },
        "historical_releases": historical
    }

@app.get("/api/blockchains/{blockchain_id}/download/{tag_name}")
async def get_download_url(blockchain_id: str, tag_name: str, format: str = "zip", source: str = "auto"):
    if blockchain_id not in BLOCKCHAIN_REPOS:
        raise HTTPException(status_code=404, detail=f"Blockchain '{blockchain_id}' not found")
    
    repo_info = BLOCKCHAIN_REPOS[blockchain_id]
    owner = repo_info["owner"]
    repo = repo_info["repo"]
    
    use_s3 = False
    actual_format = format
    
    # Check for special file extensions (historical releases with non-zip formats)
    if blockchain_id in SPECIAL_FILE_EXTENSIONS and tag_name in SPECIAL_FILE_EXTENSIONS[blockchain_id]:
        actual_format = SPECIAL_FILE_EXTENSIONS[blockchain_id][tag_name]
    
    if source == "s3" or (source == "auto" and is_release_in_s3(blockchain_id, tag_name)):
        download_url = get_s3_url(blockchain_id, tag_name)
        use_s3 = True
    else:
        if format == "zip":
            download_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag_name}.zip"
        elif format == "tar.gz":
            download_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag_name}.tar.gz"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'zip' or 'tar.gz'")
    
    return {
        "blockchain_id": blockchain_id,
        "tag_name": tag_name,
        "format": actual_format,
        "download_url": download_url,
        "filename": f"{repo}-{tag_name}.{actual_format}",
        "source": "s3" if use_s3 else "github"
    }
