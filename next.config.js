/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
  async redirects() {
    return [
      {
        source: '/book',
        destination: '/inspect',
        permanent: true,
      },
      {
        source: '/book/',
        destination: '/inspect/',
        permanent: true,
      },
      {
        source: '/estimate',
        destination: '/inspect',
        permanent: true,
      },
      {
        source: '/estimate/',
        destination: '/inspect/',
        permanent: true,
      },
      {
        source: '/projects',
        destination: '/gallery',
        permanent: true,
      },
      {
        source: '/projects/',
        destination: '/gallery/',
        permanent: true,
      },
    ]
  },
}

module.exports = nextConfig
