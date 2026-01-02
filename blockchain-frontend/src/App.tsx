import { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { Download, ExternalLink, Github, Tag, Calendar, Loader2 } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Blockchain {
  id: string
  name: string
  description: string
  github_url: string
}

interface Release {
  id: number
  tag_name: string
  name: string
  published_at: string
  zipball_url: string
  tarball_url: string
  html_url: string
  prerelease: boolean
  draft: boolean
}

interface TagInfo {
  name: string
  zipball_url: string
  tarball_url: string
  commit_sha: string
}

interface HistoricalRelease {
  tag_name: string
  name: string
  published_at: string
  description: string
  source: string
  format: string
}

const BLOCKCHAINS: Blockchain[] = [
  {
    id: 'bitcoin',
    name: 'Bitcoin',
    description: 'Bitcoin Core - The original cryptocurrency',
    github_url: 'https://github.com/bitcoin/bitcoin'
  },
  {
    id: 'bitcoin-sv',
    name: 'Bitcoin SV',
    description: 'Bitcoin SV (Satoshi Vision) - Restores the original Bitcoin protocol',
    github_url: 'https://github.com/bitcoin-sv/bitcoin-sv'
  },
  {
    id: 'bitcoin-cash',
    name: 'Bitcoin Cash',
    description: 'Bitcoin Cash Node - Peer-to-peer electronic cash',
    github_url: 'https://github.com/bitcoin-cash-node/bitcoin-cash-node'
  },
  {
    id: 'bitcoin-private',
    name: 'Bitcoin Private',
    description: 'Bitcoin Private - Privacy-focused Bitcoin fork using zk-SNARKs',
    github_url: 'https://github.com/BTCPrivate/BitcoinPrivate-legacy'
  },
  {
    id: 'litecoin',
    name: 'Litecoin',
    description: 'Litecoin - The silver to Bitcoin\'s gold',
    github_url: 'https://github.com/litecoin-project/litecoin'
  }
]

function BlockchainTab({ blockchain }: { blockchain: Blockchain }) {
  const [releases, setReleases] = useState<Release[]>([])
  const [tags, setTags] = useState<TagInfo[]>([])
  const [historicalReleases, setHistoricalReleases] = useState<HistoricalRelease[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [viewMode, setViewMode] = useState<'releases' | 'tags' | 'historical'>('releases')

  const fetchReleases = async (pageNum: number, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true)
      } else {
        setLoading(true)
      }
      
      const response = await fetch(
        `${API_BASE_URL}/api/blockchains/${blockchain.id}/releases?page=${pageNum}&per_page=30`
      )
      
      if (!response.ok) {
        throw new Error('Failed to fetch releases')
      }
      
      const data = await response.json()
      
      if (append) {
        setReleases(prev => [...prev, ...data.releases])
      } else {
        setReleases(data.releases)
      }
      
      setHasMore(data.releases.length === 30)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const fetchTags = async (pageNum: number, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true)
      } else {
        setLoading(true)
      }
      
      const response = await fetch(
        `${API_BASE_URL}/api/blockchains/${blockchain.id}/tags?page=${pageNum}&per_page=100`
      )
      
      if (!response.ok) {
        throw new Error('Failed to fetch tags')
      }
      
      const data = await response.json()
      
      if (append) {
        setTags(prev => [...prev, ...data.tags])
      } else {
        setTags(data.tags)
      }
      
      setHasMore(data.tags.length === 100)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const fetchHistorical = async () => {
    try {
      setLoading(true)
      
      const response = await fetch(
        `${API_BASE_URL}/api/blockchains/${blockchain.id}/historical`
      )
      
      if (!response.ok) {
        throw new Error('Failed to fetch historical releases')
      }
      
      const data = await response.json()
      setHistoricalReleases(data.historical_releases)
      setHasMore(false)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setPage(1)
    setReleases([])
    setTags([])
    setHistoricalReleases([])
    if (viewMode === 'releases') {
      fetchReleases(1)
    } else if (viewMode === 'tags') {
      fetchTags(1)
    } else if (viewMode === 'historical') {
      fetchHistorical()
    }
  }, [blockchain.id, viewMode])

  const loadMore = () => {
    const nextPage = page + 1
    setPage(nextPage)
    if (viewMode === 'releases') {
      fetchReleases(nextPage, true)
    } else {
      fetchTags(nextPage, true)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const handleDownload = async (tagName: string, useBackendApi: boolean = false) => {
    if (useBackendApi) {
      // For Releases tab: Use backend API to get S3 URL
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/blockchains/${blockchain.id}/download/${encodeURIComponent(tagName)}?format=zip`
        )
        if (response.ok) {
          const data = await response.json()
          window.open(data.download_url, '_blank')
          return
        }
      } catch (err) {
        console.error('Failed to get download URL from API:', err)
      }
    }
    // Fallback or for All Tags tab: Use direct GitHub URL
    const downloadUrl = `https://github.com/${blockchain.github_url.replace('https://github.com/', '')}/archive/refs/tags/${tagName}.zip`
    window.open(downloadUrl, '_blank')
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-10 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-700">Error</CardTitle>
          <CardDescription className="text-red-600">{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => viewMode === 'releases' ? fetchReleases(1) : fetchTags(1)} variant="outline">
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === 'releases' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('releases')}
          >
            <Tag className="mr-2 h-4 w-4" />
            Releases
          </Button>
          <Button
            variant={viewMode === 'tags' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('tags')}
          >
            <Github className="mr-2 h-4 w-4" />
            All Tags
          </Button>
          {blockchain.id === 'bitcoin' && (
            <Button
              variant={viewMode === 'historical' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('historical')}
            >
              <Calendar className="mr-2 h-4 w-4" />
              Historical (2008-2009)
            </Button>
          )}
        </div>
        <a
          href={blockchain.github_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-sm text-zinc-600 hover:text-zinc-900"
        >
          <Github className="h-4 w-4" />
          View on GitHub
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>

      <ScrollArea className="h-[600px] pr-4">
        <div className="space-y-3">
          {viewMode === 'releases' ? (
            releases.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-zinc-500">
                  No releases found. Try viewing all tags instead.
                </CardContent>
              </Card>
            ) : (
              releases.map((release) => (
                <Card key={release.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                          {release.name}
                          {release.prerelease && (
                            <Badge variant="secondary">Pre-release</Badge>
                          )}
                        </CardTitle>
                        <CardDescription className="flex items-center gap-2 mt-1">
                          <Tag className="h-3 w-3" />
                          {release.tag_name}
                          {release.published_at && (
                            <>
                              <span className="text-zinc-300">|</span>
                              <Calendar className="h-3 w-3" />
                              {formatDate(release.published_at)}
                            </>
                          )}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-2">
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleDownload(release.tag_name, true)}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download ZIP
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(release.html_url, '_blank')}
                      >
                        <ExternalLink className="mr-2 h-4 w-4" />
                        View Release
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )
          ) : viewMode === 'tags' ? (
            tags.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-zinc-500">
                  No tags found.
                </CardContent>
              </Card>
            ) : (
              tags.map((tag) => (
                <Card key={tag.name} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Tag className="h-4 w-4" />
                      {tag.name}
                    </CardTitle>
                    <CardDescription className="font-mono text-xs">
                      Commit: {tag.commit_sha.substring(0, 7)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-2">
                    <Button
                      size="sm"
                      onClick={() => handleDownload(tag.name)}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Download ZIP
                    </Button>
                  </CardContent>
                </Card>
              ))
            )
          ) : (
            historicalReleases.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-zinc-500">
                  No historical releases found.
                </CardContent>
              </Card>
            ) : (
              historicalReleases.map((release) => (
                <Card key={release.tag_name} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                          {release.name}
                          <Badge variant="outline">{release.format.toUpperCase()}</Badge>
                        </CardTitle>
                        <CardDescription className="flex items-center gap-2 mt-1">
                          <Tag className="h-3 w-3" />
                          {release.tag_name}
                          <span className="text-zinc-300">|</span>
                          <Calendar className="h-3 w-3" />
                          {formatDate(release.published_at)}
                        </CardDescription>
                        <p className="text-sm text-zinc-500 mt-2">{release.description}</p>
                        <p className="text-xs text-zinc-400 mt-1">Source: {release.source}</p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-2">
                    <Button
                      size="sm"
                      onClick={() => handleDownload(release.tag_name, true)}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Download {release.format.toUpperCase()}
                    </Button>
                  </CardContent>
                </Card>
              ))
            )
          )}
          
          {hasMore && (viewMode === 'releases' ? releases.length > 0 : viewMode === 'tags' ? tags.length > 0 : false) && (
            <div className="flex justify-center py-4">
              <Button
                variant="outline"
                onClick={loadMore}
                disabled={loadingMore}
              >
                {loadingMore ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading...
                  </>
                ) : (
                  'Load More'
                )}
              </Button>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

function App() {
  return (
    <div className="min-h-screen bg-zinc-50">
      <div className="container mx-auto py-8 px-4">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-zinc-900 mb-2">
            The Bitcoin Archive
          </h1>
          <p className="text-zinc-600">
            Download source code archives for major blockchain projects
          </p>
        </header>

        <Tabs defaultValue="bitcoin" className="w-full">
          <TabsList className="w-full flex flex-wrap justify-center gap-1 h-auto p-2 mb-6">
            {BLOCKCHAINS.map((blockchain) => (
              <TabsTrigger
                key={blockchain.id}
                value={blockchain.id}
                className="px-4 py-2"
              >
                {blockchain.name}
              </TabsTrigger>
            ))}
          </TabsList>

          {BLOCKCHAINS.map((blockchain) => (
            <TabsContent key={blockchain.id} value={blockchain.id}>
              <Card>
                <CardHeader>
                  <CardTitle>{blockchain.name}</CardTitle>
                  <CardDescription>{blockchain.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <BlockchainTab blockchain={blockchain} />
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>

        <footer className="mt-8 text-center text-sm text-zinc-500">
          <p className="mb-2">
            Source code is downloaded directly from GitHub repositories.
          </p>
          <p>
            &copy; {new Date().getFullYear()}{' '}
            <a 
              href="https://bitcoinpay.jp" 
              target="_blank" 
              rel="noopener noreferrer"
              className="hover:text-zinc-700 underline"
            >
              BitcoinPay株式会社
            </a>
          </p>
        </footer>
      </div>
    </div>
  )
}

export default App
